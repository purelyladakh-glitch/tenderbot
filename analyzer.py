import os
import json
import time
import google.generativeai as genai
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

def analyze_tender_document(file_path: str, language: str) -> dict:
    """
    Uploads the PDF to Gemini, runs the analysis, and returns the parsed JSON dict.
    Includes a retry mechanism.
    """
    retries = 3
    
    for attempt in range(retries):
        try:
            # Upload the file to Gemini via File API (needed for large PDFs)
            uploaded_file = genai.upload_file(path=file_path, mime_type="application/pdf")
            
            # Wait a short moment for Gemini to process the upload
            time.sleep(2)
            
            prompt = f"Please analyze this tender document. The response MUST be formatted predominantly in {language}."
            
            response = model.generate_content([uploaded_file, prompt])
            
            # Cleanup the file from Gemini
            genai.delete_file(uploaded_file.name)
            
            # Parse the JSON response
            result_text = response.text
            result_json = json.loads(result_text)
            
            # Additional Self-Review check implemented internally in prompt design
            # but we can do a secondary verification or parsing validation here
            if "quick_verdict_score" not in result_json or "part1_summary" not in result_json:
                raise ValueError("Missing critical fields in Gemini JSON output.")
                
            return result_json
            
        except Exception as e:
            time.sleep(2)
            if attempt == retries - 1:
                raise Exception(f"Failed to analyze document after {retries} attempts. Error: {str(e)}")
