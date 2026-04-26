import os
import json
import time
import hashlib
from google import genai
from google.genai import types
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv
from prompts import TENDER_ANALYSIS_PROMPT
from live_data import get_live_market_data, extract_location_from_text
from pydantic import BaseModel, Field

class TenderAnalysis(BaseModel):
    """Canonical schema for Gemini tender analysis output.
    Used as response_schema to guarantee JSON structure and types.
    Field names here are the SINGLE SOURCE OF TRUTH — bot.py reads these exact names.
    """

    # Header / summary card fields
    department: str = Field(description="Issuing department or agency name")
    work_description: str = Field(description="Brief work description, max 80 characters")
    tender_number: str = Field(description="Official tender reference number")
    value: int = Field(description="Estimated tender value in INR as plain integer (no commas, no symbols, e.g. 28500000)")
    emd_amount: str = Field(description="EMD amount and type, e.g. '₹2,85,000 (Bank Guarantee)'")
    deadline_date: str = Field(description="Submission deadline date in YYYY-MM-DD format")
    deadline_time: str = Field(description="Submission deadline time in HH:MM 24-hour format")
    days_remaining: int = Field(description="Number of days from today to the deadline as integer")
    completion_period: str = Field(description="Project completion period as text, e.g. '12 months'")
    location: str = Field(description="Project location: city, state")

    # Verdict fields
    quick_verdict_score: int = Field(description="0 to 10 attractiveness score", ge=0, le=10)
    quick_verdict_recommendation: str = Field(description="Exactly one of: 'BID' or 'SKIP'")
    critical_risks_count: int = Field(description="Number of HIGH-severity risks identified")
    warnings_count: int = Field(description="Number of MEDIUM-severity warnings identified")
    recommended_bid: int = Field(description="Recommended bid total in INR as integer")
    estimated_profit: int = Field(description="Estimated profit amount in INR as integer")

    # 10-part detailed analysis (each is a formatted text block in the user's language)
    part1_summary: str = Field(description="Part 1 — Tender summary at a glance")
    part2_eligibility: str = Field(description="Part 2 — Eligibility check (financial, experience, registration)")
    part3_risks: str = Field(description="Part 3 — Hidden risks coded with 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW")
    part4_boq: str = Field(description="Part 4 — BOQ rates and bid strategy with math")
    part5_action_plan: str = Field(description="Part 5 — Documents and day-by-day countdown checklist")
    part6_cost_estimate: str = Field(description="Part 6 — Cost breakdown: materials, labour, equipment, overheads")
    part7_competitor: str = Field(description="Part 7 — Expected bidders and competitive strategy")
    part8_subcontractors: str = Field(description="Part 8 — Subcontractor requirements and specialist trades")
    part9_cashflow: str = Field(description="Part 9 — Working capital, monthly cash flow, retention timeline")
    part10_recommendation: str = Field(description="Part 10 — Final BID/SKIP recommendation and opportunity score")


load_dotenv()

# Initialize the Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Use the latest stable Gemini Flash model alias
MODEL_NAME = "gemini-flash-latest"

print(f"[OK] Gemini client initialized with model: {MODEL_NAME}")

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
    
    # Check all parts exist
    required_parts = [
        "part1_summary", "part2_eligibility", "part3_risks", 
        "part4_boq", "part5_action_plan", "part6_cost_estimate",
        "part7_competitor", "part8_subcontractors", "part9_cashflow",
        "part10_recommendation", "part11_contractor_tip"
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

def analyze_tender_document(file_path: str, language: str, db_session=None) -> dict:
    """Analyzes the PDF document using the google-genai SDK with two-stage rates."""
    
    extracted_text = extract_text_from_pdf(file_path)
    is_scanned = len(extracted_text.split()) < 100
    
    # Check cache by PDF content hash
    pdf_hash = None
    if db_session:
        try:
            with open(file_path, 'rb') as f:
                pdf_hash = hashlib.sha256(f.read()).hexdigest()
            
            from database import Analysis
            cached = db_session.query(Analysis).filter(
                Analysis.tender_summary == pdf_hash
            ).first()
            
            if cached and cached.analysis_result:
                print(f"📦 Cache hit for PDF hash: {pdf_hash[:16]}...")
                return json.loads(cached.analysis_result)
        except Exception as e:
            print(f"Cache check failed (non-critical): {e}")

    # Two-stage approach: extract location from text, then fetch location-specific rates
    tender_location = extract_location_from_text(extracted_text)
    live_rates = get_live_market_data(location=tender_location, work_type=extracted_text[:200])
    print(f"📍 Tender location detected: '{tender_location}' — rates fetched for this area")

    active_facts = ""
    active_prompt = TENDER_ANALYSIS_PROMPT
    if db_session:
        from database import KnowledgeFact, SystemPrompt
        facts = db_session.query(KnowledgeFact).all()
        if facts:
            active_facts = "\n\n[RELEVANT GOVERNMENT UPDATES (AUTONOMOUSLY HARVESTED)]\n" + "\n".join([f.fact_text for f in facts])
            
        # 🧬 AI BRAIN OVERRIDE: Prioritize self-written database instructions
        db_prompt = db_session.query(SystemPrompt).filter(SystemPrompt.is_active == True).first()
        if db_prompt:
            active_prompt = db_prompt.prompt_text

    gen_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=TenderAnalysis,
        system_instruction=active_prompt + "\n\n[CURRENT MARKET RATES FOR THIS TENDER'S LOCATION]\n" + live_rates + active_facts
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
                uploaded_file = client.files.upload(file=file_path)
                # Wait for file to be ready (though usually tiny ones are instant)
                def get_state(f):
                    return f.state.name if hasattr(f.state, 'name') else str(f.state)
                    
                while get_state(uploaded_file) == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                
                prompt = f"Please analyze this tender document. The response MUST be formatted predominantly in {language}."
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[uploaded_file, prompt],
                    config=gen_config
                )
                client.files.delete(name=uploaded_file.name)
            
            # Parse response — handle multiple possible formats
            result_json = None

            # Try response.parsed first (structured output)
            if hasattr(response, 'parsed') and response.parsed is not None:
                if hasattr(response.parsed, 'model_dump'):
                    result_json = response.parsed.model_dump()
                elif hasattr(response.parsed, 'dict'):
                    result_json = response.parsed.dict()
                else:
                    result_json = response.parsed
                print(f"✅ Parsed via response.parsed")

            # Try response.text (raw JSON string)
            if result_json is None and hasattr(response, 'text') and response.text:
                raw_text = response.text.strip()
                # Remove markdown code fences if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()
                
                try:
                    result_json = json.loads(raw_text)
                    print(f"✅ Parsed via response.text ({len(raw_text)} chars)")
                except json.JSONDecodeError as je:
                    print(f"⚠️ JSON parse failed: {je}")
                    print(f"⚠️ Raw text preview: {raw_text[:200]}...")

            # Try response.candidates as last resort
            if result_json is None and hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                raw = part.text.strip()
                                if raw.startswith("```json"):
                                    raw = raw[7:]
                                if raw.startswith("```"):
                                    raw = raw[3:]
                                if raw.endswith("```"):
                                    raw = raw[:-3]
                                result_json = json.loads(raw.strip())
                                print(f"✅ Parsed via candidates fallback")
                                break
                except Exception as ce:
                    print(f"⚠️ Candidates parsing failed: {ce}")

            if result_json is None:
                print(f"❌ All parsing methods failed for Gemini response")
                # Log what we got for debugging
                if hasattr(response, 'text'):
                    print(f"response.text type: {type(response.text)}, value: {repr(response.text)[:300]}")
                if hasattr(response, 'candidates'):
                    print(f"response.candidates: {response.candidates}")
                raise Exception("Gemini returned empty or unparseable response")
            
            # Run Self-Review
            reviewed_json = self_review(result_json)
            
            # Save to cache if hash available
            if db_session and pdf_hash:
                try:
                    from database import Analysis
                    new_analysis = Analysis(
                        user_phone="CACHE", # Marker for shared cache if needed, or just use hash
                        tender_summary=pdf_hash,
                        analysis_result=json.dumps(reviewed_json)
                    )
                    db_session.add(new_analysis)
                    db_session.commit()
                    print(f"💾 Analysis saved to cache for hash: {pdf_hash[:16]}...")
                except Exception as cache_err:
                    print(f"Failed to save to cache: {cache_err}")
                    
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
