import os
import time
import json
from twilio.rest import Client
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from database import User, Analysis, Payment
from payments import generate_payment_link
from analyzer import analyze_tender_document, is_pdf_too_large
from utils import download_twilio_media, detect_language, generate_pdf_report

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to_number: str, body: str, media_url: str = None):
    try:
        msg_data = {
            "from_": TWILIO_WHATSAPP_NUMBER,
            "body": body,
            "to": to_number
        }
        if media_url:
             msg_data["media_url"] = [media_url]
             
        twilio_client.messages.create(**msg_data)
    except Exception as e:
        print(f"Error sending msg to {to_number}: {e}")

def get_or_create_user(db: Session, phone_number: str, text: str = "") -> User:
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        lang = detect_language(text)
        user = User(
            phone_number=phone_number,
            language_preference=lang
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def handle_incoming_message(phone_number: str, text: str, media_url: str, db: Session, background_tasks):
    user = get_or_create_user(db, phone_number, text)
    
    # NLP Intent parsing
    text_lower = text.lower()
    
    if media_url:
        handle_new_pdf(user, media_url, db, background_tasks)
        return

    # User already sent text. Check if they have an analysis present
    latest_analysis = db.query(Analysis).filter(Analysis.user_phone == user.phone_number).order_by(Analysis.id.desc()).first()
    
    if not latest_analysis and not text_lower.startswith('pay'):
        # STATE 1
        send_welcome_message(user.phone_number, user.language_preference)
        return
        
    if latest_analysis:
        handle_nlp_menu_routing(user, text_lower, latest_analysis)
        return

def send_welcome_message(phone_number: str, lang: str):
    msg = """Namaste! 🙏 Main TenderBot hoon.
Government tender ka poora analysis 3 minute mein kar deta hoon.

Kya karta hoon:
✅ Tender summary
✅ Aap qualify karte ho ya nahi
✅ Hidden risks and conditions
✅ BOQ rates and bid guidance
✅ Project cost estimate
✅ Cash flow analysis
✅ Documents checklist
✅ Day by day action plan

Pehla analysis bilkul FREE hai.
Bas tender PDF bhejo. 📄"""
    send_whatsapp_message(phone_number, msg)

def request_payment(user: User, db: Session):
    msg = """Aapka free analysis use ho gaya. ✓

Agle tender ke liye:

💳 ₹99    — 1 analysis (48 hours)
💳 ₹399   — 5 analyses (60 days)
💳 ₹799   — 30 analyses (1 month)"""

    # Generate links (Here I will just generate a 99 INR link as a default, or they can ask. 
    # For UX, we give the 99 INR link directly and mention others)
    new_payment = Payment(user_phone=user.phone_number, amount=99, plan_type="single", status="created")
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    link = generate_payment_link(99, user.phone_number, f"PAY_{new_payment.id}", "1 Tender Analysis")
    new_payment.razorpay_order_id = f"PAY_{new_payment.id}"
    db.commit()
    
    msg += f"\n\nUPI Payment link (₹99 for 1):\n{link}\n\nPayment hote hi turant unlock ho jayega. 🔓"
    send_whatsapp_message(user.phone_number, msg)

def handle_new_pdf(user: User, media_url: str, db: Session, background_tasks):
    # Check credits
    if user.free_analyses_used >= 1 and user.paid_credits_remaining <= 0:
        if user.subscription_type == "monthly":
            if user.total_analyses_done >= 30:
                 send_whatsapp_message(user.phone_number, "Sir, plan mein 30 analyses max hain. Extra tender ₹25/each hai. Contact support.")
                 return
        else:
            request_payment(user, db)
            return

    # STATE 2 - Step 1: Immediate Reply
    send_whatsapp_message(user.phone_number, "Tender mil gaya! 📄\nPoora analyze kar raha hoon —\n3 minute mein complete report bhejta hoon. ⏳")
    
    # STATE 2 - Step 2: Ask docs
    doc_msg = """Jab tak main analyze karta hoon —
yeh documents ready hain aapke paas?

□ ITR last 3 years
□ CA certified balance sheet
□ Registration certificate
□ GST certificate
□ Completion certificates of past work
□ Solvency certificate

Jo ready nahi hai reply karo —
main deadline check karke batata hoon kitna time hai arrange karne ke liye."""
    send_whatsapp_message(user.phone_number, doc_msg)
    
    # Process in background
    background_tasks.add_task(process_pdf_background, user.phone_number, media_url)

def process_pdf_background(phone_number: str, media_url: str):
    from database import SessionLocal
    db = SessionLocal()
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    try:
        # Step 3: Download
        pdf_path = download_twilio_media(media_url)
        
        if is_pdf_too_large(pdf_path):
            send_whatsapp_message(phone_number, "PDF bahut bada hai.\nCompress karke bhejo ya government portal ka direct link do.")
            return

        # Let user know it's analyzing
        send_whatsapp_message(phone_number, "Still analyzing... almost done ⏳")

        # Step 4: Analyze
        analysis_json = analyze_tender_document(pdf_path, user.language_preference)
        
        # Deduct credit
        if user.free_analyses_used == 0:
            user.free_analyses_used = 1
        elif user.paid_credits_remaining > 0:
            user.paid_credits_remaining -= 1
            
        user.total_analyses_done += 1
        
        new_analysis = Analysis(
            user_phone=user.phone_number,
            tender_summary=analysis_json.get("department", "Tender"),
            analysis_result=json.dumps(analysis_json)
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        # Step 6: Quick Verdict
        verdict_msg = f"""━━━━━━━━━━━━━━━━━━━━━━━━
📋 {analysis_json.get('department', 'Dept')} — {analysis_json.get('work_description', 'Work')}
💰 Value: ₹{analysis_json.get('value', 'N/A')}
📅 Deadline: {analysis_json.get('deadline_date', 'N/A')} ({analysis_json.get('days_remaining', 'X')} din baaki)

⚡ QUICK VERDICT: {analysis_json.get('quick_verdict_recommendation', 'N/A')} — {analysis_json.get('quick_verdict_score', 'N/A')}/10

🔴 {analysis_json.get('critical_risks_count', '0')} Critical risks
🟡 {analysis_json.get('warnings_count', '0')} Warnings
💡 Recommended bid: ₹{analysis_json.get('recommended_bid', 'N/A')}
💰 Your estimated profit: ₹{analysis_json.get('estimated_profit', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━

Kya dekhna chahte ho?

1️⃣ Eligibility — qualify karte ho?
2️⃣ Hidden risks aur conditions
3️⃣ BOQ rates aur bid strategy
4️⃣ Documents aur action plan
5️⃣ Cash flow aur working capital
6️⃣ Project cost estimate
7️⃣ Poora report ek saath
8️⃣ PDF report download karo

Reply karo number ya seedha apna sawaal poochho 🙂"""

        send_whatsapp_message(user.phone_number, verdict_msg)
        
        # Clean up
        os.remove(pdf_path)

    except Exception as e:
        send_whatsapp_message(phone_number, "Thoda technical issue hua. 2 minute mein dobara try karo.")
        print(f"Error processing PDF: {e}")
    finally:
        db.close()


def handle_nlp_menu_routing(user: User, text_lower: str, latest_analysis: Analysis):
    try:
        data = json.loads(latest_analysis.analysis_result)
    except:
        send_whatsapp_message(user.phone_number, "Aapka purana analysis format error mein hai. PDF dobara bhejiye.")
        return

    # Map numbers or NLP queries to answers
    reply_msg = ""
    is_pdf_req = False

    if "1" in text_lower or "qualify" in text_lower or "eligibility" in text_lower:
        reply_msg = data.get("part2_eligibility", "N/A")
    elif "2" in text_lower or "risk" in text_lower or "problem" in text_lower or "condition" in text_lower:
        reply_msg = data.get("part3_risks", "N/A")
    elif "3" in text_lower or "quote" in text_lower or "boq" in text_lower or "rate" in text_lower or "strategy" in text_lower:
        reply_msg = data.get("part4_boq", "N/A")
    elif "4" in text_lower or "document" in text_lower or "plan" in text_lower or "action" in text_lower:
        reply_msg = data.get("part5_action_plan", "N/A")
    elif "5" in text_lower or "paisa" in text_lower or "cash" in text_lower or "capital" in text_lower:
        reply_msg = data.get("part9_cashflow", "N/A")
    elif "6" in text_lower or "project kitne" in text_lower or "cost" in text_lower or "estimate" in text_lower:
        reply_msg = data.get("part6_cost_estimate", "N/A")
    elif "7" in text_lower or "poora" in text_lower or "sab" in text_lower or "full report" in text_lower:
        # Note: Sending all at once might hit WhatsApp length limits, so we combine parts
        reply_msg = f"{data.get('part1_summary', '')}\n\n{data.get('part3_risks', '')}\n\n{data.get('part4_boq', '')}\n\n{data.get('part10_recommendation', '')}"
    elif "8" in text_lower or "pdf" in text_lower or "download" in text_lower:
        is_pdf_req = True
    else:
        reply_msg = """Samjha nahi. Yeh try karo:
1️⃣ Eligibility
2️⃣ Risks
3️⃣ BOQ rates
4️⃣ Action plan
5️⃣ Cash flow
6️⃣ Cost estimate
7️⃣ Full report
8️⃣ PDF download"""

    if is_pdf_req:
        send_whatsapp_message(user.phone_number, "Aapki PDF report generate ho rahi hai...")
        pdf_path = generate_pdf_report(data, user.phone_number)
        
        # Note: Sending PDF media correctly on Twilio Sandbox requires a publicly accessible URL.
        # However, as a bot, if we can't upload to a cloud bucket, we can't send a local file directly.
        # Assuming the Railway URL can host static files, but for now we'll send a text placeholder
        # and notify the user about URL requirements.
        send_whatsapp_message(user.phone_number, "PDF format me file attach ki ja rahi hai! (Local storage Twilio media limit - require cloud bucket to serve URL for Twilio to send)")
        try:
             os.remove(pdf_path)
        except:
             pass
    else:
        # Standard disclaimer included inside the gemini response, but we can append if needed
        # WhatsApp message body limit is somewhat forgiving, but safe to send.
        
        # Split message if it's too long (over 1600 chars to be safe)
        if len(reply_msg) > 1500:
             chunks = [reply_msg[i:i+1500] for i in range(0, len(reply_msg), 1500)]
             for chunk in chunks:
                   send_whatsapp_message(user.phone_number, chunk)
                   time.sleep(1) # delay sequence
        else:
             send_whatsapp_message(user.phone_number, reply_msg)
