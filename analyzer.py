import os
import json
import time
from google import genai
from google.genai import types
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv
from prompts import TENDER_ANALYSIS_PROMPT
from live_data import get_live_market_data

load_dotenv()

# Initialize the Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Use the latest stable Gemini Flash model alias
MODEL_NAME = "gemini-flash-latest"

print(f"✅ Gemini client initialized with model: {MODEL_NAME}")

def is_pdf_too_large(file_path: str, max_size_mb: int = 50) -> bool:
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return size_mb > max_size_mb

def extract_text_from_pdf(file_path: str) -> str:
    """
    Tries extracting text with pdfplumber. 
    If < 100 words, falls back to OCR with pytesseract.
    """
    all_text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")

    word_count = len(all_text.split())
    if word_count > 100:
        return all_text

    # --- OCR FALLBACK ---
    print(f"PDF looks like a scanned image ({word_count} words). Starting OCR...")
    try:
        images = convert_from_path(file_path)
        ocr_text = ""
        for i, image in enumerate(images):
            # Limit OCR to first 15 pages for performance
            if i >= 15: break 
            page_text = pytesseract.image_to_string(image)
            ocr_text += page_text + "\n"
        
        if len(ocr_text.split()) > 10:
            return ocr_text
    except Exception as e:
        print(f"OCR failed: {e}")

    return all_text # Return whatever we have

def self_review(result_json: dict) -> dict:
    """
    Validates the AI's output, checks for missing parts, calculation errors,
    and contradictions. Injects warnings if unfixable.
    """
    warnings = result_json.get("warnings", [])
    
    # Check all 9 parts exist
    required_parts = [
        "part1_summary", "part2_eligibility", "part3_risks", 
        "part4_boq", "part5_action_plan", "part6_cost_estimate",
        "part7_competitor", "part8_subcontractors", "part9_cashflow",
        "part10_recommendation"
    ]
    
    for part in required_parts:
        if part not in result_json or not str(result_json[part]).strip():
            result_json[part] = "⚠️ Information not found or analysis incomplete for this section."
            warnings.append(f"Missing {part}")

    # Check basic calculations
    try:
        val = int(result_json.get("value", 0))
        rec_bid = int(result_json.get("recommended_bid", 0))
        profit = int(result_json.get("estimated_profit", 0))
        
        if profit > (val * 0.5) and val > 0:
            warnings.append("Profit estimate seems unrealistically high (>50%).")
            result_json["part6_cost_estimate"] += "\n⚠️ Reviewer Note: Initial project cost estimates heavily underestimate expenses."
            
        if rec_bid > (val * 1.5) and val > 0:
             warnings.append("Recommended bid is >50% higher than tender value. Likely to be rejected.")
             
        days = int(result_json.get("days_remaining", 0))
        if days < 0:
             warnings.append("Tender deadline has already passed.")
             
    except Exception as e:
        print(f"Self-review calculation check failed: {e}")
        
    result_json["warnings"] = warnings
    return result_json

def analyze_tender_document(file_path: str, language: str) -> dict:
    """
    Analyzes the PDF document using the new google-genai SDK.
    """
    # Step 1: Extract text locally to check if it's scanned
    extracted_text = extract_text_from_pdf(file_path)
    is_scanned = len(extracted_text.split()) < 100

    gen_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
        response_mime_type="application/json",
        system_instruction=TENDER_ANALYSIS_PROMPT + "\n\n" + get_live_market_data()
    )

    retries = 2
    for attempt in range(retries):
        try:
            if is_scanned and len(extracted_text.split()) > 10:
                # Scanned PDF: Send OCR text
                prompt = (
                    f"Analyze this tender document text (extracted via OCR). "
                    f"The response MUST be formatted predominantly in {language}.\n\n"
                    f"DOCUMENT TEXT:\n{extracted_text}"
                )
                response = client.models.generate_content(
                    model=MODEL_NAME, 
                    contents=prompt,
                    config=gen_config
                )
            else:
                # Searchable PDF: Upload to Gemini Files API
                uploaded_file = client.files.upload(path=file_path)
                # Wait for file to be ready (though usually tiny ones are instant)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                
                prompt = f"Please analyze this tender document. The response MUST be formatted predominantly in {language}."
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[uploaded_file, prompt],
                    config=gen_config
                )
                client.files.delete(name=uploaded_file.name)
            
            # Parse response
            result_json = response.parsed if hasattr(response, 'parsed') else json.loads(response.text)
            
            # Run Self-Review
            reviewed_json = self_review(result_json)
            return reviewed_json

        except Exception as e:
            print(f"Analysis attempt {attempt+1} failed: {e}")
            time.sleep(2)
            if attempt == retries - 1:
                if len(extracted_text.split()) < 20:
                    return {"error": "OCR_FAILED_TINY"}
                raise e

def quick_tender_summary(title: str, department: str, state: str, value: float) -> str:
    """
    Generates a quick summary for the scraper.
    """
    value_display = ""
    if value and value > 0:
        if value >= 10000000:
            value_display = f"₹{value/10000000:.1f} Crore"
        elif value >= 100000:
            value_display = f"₹{value/100000:.1f} Lakh"
        else:
            value_display = f"₹{value:,.0f}"

    prompt = f"""You are a government tender analyst for Indian contractors.
Given this tender metadata, provide a SHORT (max 5 bullets) analysis in Hinglish:

TENDER: {title}
DEPARTMENT: {department}
STATE: {state}
VALUE: {value_display or 'Not specified'}

Your analysis must include:
1. What this tender is about (1 line)
2. Likely eligibility requirements (Class/registration)
3. Key risks or things to watch
4. Whether the value seems worth bidding
5. Recommended next step

Keep each bullet to ONE line. Use emojis. Be direct and practical."""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=500,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Quick summary error: {e}")
        return ""
