import os
import json
import time
import google.generativeai as genai
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv
from prompts import TENDER_ANALYSIS_PROMPT

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use gemini-3-flash-preview as per the prompt requirements
MODEL_NAME = "gemini-3-flash-preview"

generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json"
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    system_instruction=TENDER_ANALYSIS_PROMPT
)

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
            # Limit OCR to first 15 pages for performance for now
            if i >= 15: break 
            page_text = pytesseract.image_to_string(image)
            ocr_text += page_text + "\n"
        
        if len(ocr_text.split()) > 10:
            return ocr_text
    except Exception as e:
        print(f"OCR failed: {e}")

    return all_text # Return whatever we have (even if tiny)

def analyze_tender_document(file_path: str, language: str) -> dict:
    """
    Analyzes the PDF. 
    1. Tries direct PDF upload to Gemini.
    2. If that fails or text is sparse, uses local OCR and sends text.
    """
    # Step 1: Extract text locally to check if it's scanned
    extracted_text = extract_text_from_pdf(file_path)
    is_scanned = len(extracted_text.split()) < 100 # Or whatever threshold we used

    retries = 2
    for attempt in range(retries):
        try:
            if is_scanned and len(extracted_text.split()) > 10:
                # Scanned PDF: Send the OCR'd text directly
                prompt = (
                    f"Analyze this tender document text (extracted via OCR). "
                    f"The response MUST be formatted predominantly in {language}.\n\n"
                    f"DOCUMENT TEXT:\n{extracted_text}"
                )
                response = model.generate_content(prompt)
            else:
                # Searchable PDF: Upload file to Gemini
                uploaded_file = genai.upload_file(path=file_path, mime_type="application/pdf")
                time.sleep(2)
                prompt = f"Please analyze this tender document. The response MUST be formatted predominantly in {language}."
                response = model.generate_content([uploaded_file, prompt])
                genai.delete_file(uploaded_file.name)
            
            # Parse response
            result_json = json.loads(response.text)
            if "quick_verdict_score" not in result_json:
                raise ValueError("Incomplete analysis result")
            return result_json

        except Exception as e:
            print(f"Analysis attempt {attempt+1} failed: {e}")
            time.sleep(2)
            if attempt == retries - 1:
                # If everything failed, and it was a tiny file, maybe notify bot.py
                if len(extracted_text.split()) < 20:
                    return {"error": "OCR_FAILED_TINY"}
                raise e


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUICK TENDER SUMMARY (for scraper auto-analysis)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Lightweight model for quick summaries (no PDF upload needed)
quick_model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": 0.3,
        "max_output_tokens": 500,
    },
)

def quick_tender_summary(title: str, department: str, state: str, value: float) -> str:
    """
    Generates a short AI summary of a tender from metadata only (no PDF).
    Used by the scraper for ₹799 Monthly Pro auto-analysis alerts.
    Returns a concise WhatsApp-friendly summary string.
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
        response = quick_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Quick summary error: {e}")
        return ""
