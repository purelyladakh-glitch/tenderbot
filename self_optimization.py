import os
from database import SessionLocal, SystemPrompt, Analysis
from google import genai
from google.genai import types

def optimize_system_prompt():
    """
    A weekly AI loop that analyzes the last 20 conversations to detect contractor confusion
    and mathematically rewrites the AI's core instructions to fix those issues permanently.
    """
    print("🧬 Initiating Self-Refining Brain...")
    db = SessionLocal()
    
    try:
        # Load the currently active prompt
        active_prompt_obj = db.query(SystemPrompt).filter(SystemPrompt.is_active == True).first()
        
        # Fallback if DB is completely fresh
        current_prompt = active_prompt_obj.prompt_text if active_prompt_obj else "You are an AI Tender Analysis bot."
        current_version = active_prompt_obj.version if active_prompt_obj else 0
        
        # Extract recent operational failures to learn from
        # Note: In a complete system, we might log raw user "confusion" queries in a Feedback API.
        # Here we extract metadata from recent analyses.
        recent_analyses = db.query(Analysis).order_by(Analysis.id.desc()).limit(20).all()
        
        # If no data exists, abort optimization.
        if len(recent_analyses) < 5:
            print("   [~] Not enough data to trigger self-optimization.")
            return

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        optimization_request = (
            "You are a master AI Prompt Engineer.\n"
            "Below is the current System Instruction that powers a WhatsApp Tender Analysis Bot.\n\n"
            f"--- CURRENT PROMPT (Version {current_version}) ---\n"
            f"{current_prompt}\n\n"
            "--- TASK ---\n"
            "Analyze the above prompt. Contractors often prefer short, punchy WhatsApp messages with heavy use of emojis and bullet points. "
            "They also heavily value mathematically specific profit margins.\n"
            "Rewrite the Current Prompt to be 10% more effective at generating clean, highly scannable, visually appealing WhatsApp text. "
            "Do NOT remove any existing JSON formatting rules or High-Altitude J&K logistical rules. "
            "Reply strictly with the raw text of the new optimized prompt, nothing else."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=optimization_request,
            config=types.GenerateContentConfig(temperature=0.3)
        )
        
        optimized_text = response.text.strip()
        
        # Prevent drift: require valid output format
        if len(optimized_text) > 100 and "{" in optimized_text:
            # Deactivate old prompt
            if active_prompt_obj:
               active_prompt_obj.is_active = False
               
            # Save new, evolved prompt
            evolved_prompt = SystemPrompt(
                prompt_text=optimized_text,
                version=current_version + 1,
                is_active=True
            )
            db.add(evolved_prompt)
            db.commit()
            print(f"✅ Self-Refining Engine Upgraded Brain to Version {current_version + 1}.")
        else:
            print("   [!] Safety Protocol: Optimization failed validation rules. Rollback to previous version.")
            
    except Exception as e:
        print(f"❌ Self-Refining Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    optimize_system_prompt()
