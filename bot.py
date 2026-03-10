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
from portals import (
    LOCATION_SELECTION_MSG, STATE_PORTALS,
    parse_location_input, get_state_names,
    get_ladakh_alert, get_portals_for_states,
)

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USER MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_or_create_user(db: Session, phone_number: str, text: str = "") -> User:
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        lang = detect_language(text)
        user = User(
            phone_number=phone_number,
            language_preference=lang,
            conversation_state="new",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_incoming_message(phone_number: str, text: str, media_url: str, db: Session, background_tasks):
    user = get_or_create_user(db, phone_number, text)
    text_lower = text.lower().strip()

    # ── PDF received at any point ──
    if media_url:
        handle_new_pdf(user, media_url, db, background_tasks)
        return

    # ── STATE MACHINE ──
    state = user.conversation_state or "new"

    # STATE: brand new user
    if state == "new":
        send_welcome_message(user.phone_number, user.language_preference)
        user.conversation_state = "awaiting_location"
        db.commit()
        return

    # STATE: waiting for location selection
    if state == "awaiting_location":
        handle_location_selection(user, text_lower, db)
        return

    # STATE: "ready" or "menu" — user has analysis or is idle
    if state in ("ready", "menu"):
        latest_analysis = db.query(Analysis).filter(
            Analysis.user_phone == user.phone_number
        ).order_by(Analysis.id.desc()).first()

        if latest_analysis:
            handle_nlp_menu_routing(user, text_lower, latest_analysis, db)
        else:
            send_whatsapp_message(user.phone_number,
                "Tender PDF bhejo aur main 3 minute mein poora analysis de dunga! 📄")
        return

    # STATE: analyzing (unlikely text during analysis, but handle gracefully)
    if state == "analyzing":
        send_whatsapp_message(user.phone_number,
            "Aapka tender abhi analyze ho raha hai... thoda wait karo ⏳")
        return

    # Fallback: treat like a ready user
    latest_analysis = db.query(Analysis).filter(
        Analysis.user_phone == user.phone_number
    ).order_by(Analysis.id.desc()).first()

    if latest_analysis:
        handle_nlp_menu_routing(user, text_lower, latest_analysis, db)
    else:
        send_welcome_message(user.phone_number, user.language_preference)
        user.conversation_state = "awaiting_location"
        db.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WELCOME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    # Follow up with location selection
    time.sleep(1)
    send_whatsapp_message(phone_number, LOCATION_SELECTION_MSG)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOCATION SELECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_location_selection(user: User, text: str, db: Session):
    keys = parse_location_input(text)

    if not keys:
        send_whatsapp_message(user.phone_number,
            "Samjha nahi. Number bhejo jaise '8' ya '7,8' ya '35' for All India.\n\n" + LOCATION_SELECTION_MSG)
        return

    user.preferred_states = ",".join(keys)
    user.conversation_state = "ready"
    db.commit()

    state_names = get_state_names(keys)

    # Check if Ladakh is selected
    is_ladakh = "8" in keys
    ladakh_note = ""
    if is_ladakh:
        ladakh_note = """

⛰️ LADAKH SPECIAL:
→ BRO, NHIDCL, MES, LAHDC Leh/Kargil tenders tracked
→ High altitude + winter shutdown alerts included
→ 5 portals monitored for Ladakh specifically"""

    portals = get_portals_for_states(keys)
    portal_count = len(portals)

    msg = f"""✅ Location set: {state_names}
📡 {portal_count} tender portals tracked{ladakh_note}

Ab tender PDF bhejo — main analyze kar deta hoon! 📄"""

    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def request_payment(user: User, db: Session):
    msg = """Aapka free analysis use ho gaya. ✓

Agle tender ke liye:

💳 ₹99    — 1 analysis (48 hours)
💳 ₹399   — 5 analyses (60 days)
💳 ₹799   — 30 analyses (1 month)"""

    new_payment = Payment(user_phone=user.phone_number, amount=99, plan_type="single", status="created")
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    link = generate_payment_link(99, user.phone_number, f"PAY_{new_payment.id}", "1 Tender Analysis")
    new_payment.razorpay_order_id = f"PAY_{new_payment.id}"
    db.commit()

    msg += f"\n\nUPI Payment link (₹99 for 1):\n{link}\n\nPayment hote hi turant unlock ho jayega. 🔓"
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_new_pdf(user: User, media_url: str, db: Session, background_tasks):
    # If user hasn't set location yet, skip the requirement and proceed anyway
    if user.conversation_state == "new" or user.conversation_state == "awaiting_location":
        user.conversation_state = "analyzing"
        db.commit()

    # Check credits
    if user.free_analyses_used >= 1 and user.paid_credits_remaining <= 0:
        if user.subscription_type == "monthly":
            if user.total_analyses_done >= 30:
                send_whatsapp_message(user.phone_number,
                    "Sir, plan mein 30 analyses max hain. Extra tender ₹25/each hai. Contact support.")
                return
        else:
            request_payment(user, db)
            return

    user.conversation_state = "analyzing"
    db.commit()

    # STATE 2 - Step 1: Immediate reply
    send_whatsapp_message(user.phone_number,
        "Tender mil gaya! 📄\nPoora analyze kar raha hoon —\n3 minute mein complete report bhejta hoon. ⏳")

    # STATE 2 - Step 2: Document checklist
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
            send_whatsapp_message(phone_number,
                "PDF bahut bada hai.\nCompress karke bhejo ya government portal ka direct link do.")
            user.conversation_state = "ready"
            db.commit()
            return

        send_whatsapp_message(phone_number, "Still analyzing... almost done ⏳")

        # Step 4: Analyze
        analysis_json = analyze_tender_document(pdf_path, user.language_preference)

        # Deduct credit
        if user.free_analyses_used == 0:
            user.free_analyses_used = 1
        elif user.paid_credits_remaining > 0:
            user.paid_credits_remaining -= 1

        user.total_analyses_done += 1
        user.conversation_state = "menu"

        new_analysis = Analysis(
            user_phone=user.phone_number,
            tender_summary=analysis_json.get("department", "Tender"),
            analysis_result=json.dumps(analysis_json)
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)

        # ── Check if Ladakh tender ──
        location = str(analysis_json.get("location", "")).lower()
        is_ladakh_tender = any(kw in location for kw in ["ladakh", "leh", "kargil"])
        preferred = (user.preferred_states or "").split(",")
        is_ladakh_user = "8" in preferred

        if is_ladakh_tender:
            ladakh_alert = get_ladakh_alert(analysis_json)
            send_whatsapp_message(user.phone_number, ladakh_alert)
            time.sleep(2)

        # ── Quick Verdict ──
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
        send_whatsapp_message(phone_number,
            "Thoda technical issue hua. 2 minute mein dobara try karo.")
        print(f"Error processing PDF: {e}")
        if user:
            user.conversation_state = "ready"
            db.commit()
    finally:
        db.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MENU / NLP ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_nlp_menu_routing(user: User, text_lower: str, latest_analysis: Analysis, db: Session):
    # Handle special commands first
    if text_lower in ("restart", "reset", "start over", "naya", "new"):
        user.conversation_state = "new"
        db.commit()
        send_welcome_message(user.phone_number, user.language_preference)
        user.conversation_state = "awaiting_location"
        db.commit()
        return

    if text_lower in ("location", "state", "portal", "portals", "change location"):
        send_whatsapp_message(user.phone_number, LOCATION_SELECTION_MSG)
        user.conversation_state = "awaiting_location"
        db.commit()
        return

    if text_lower in ("history", "past", "purana", "purane"):
        analyses = db.query(Analysis).filter(
            Analysis.user_phone == user.phone_number
        ).order_by(Analysis.id.desc()).limit(5).all()

        if not analyses:
            send_whatsapp_message(user.phone_number, "Koi past analysis nahi mila.")
            return

        msg = "📋 Aapke recent analyses:\n\n"
        for i, a in enumerate(analyses, 1):
            msg += f"{i}. {a.tender_summary} — {a.created_at.strftime('%d %b %Y')}\n"
        msg += "\nLatest analysis ke sections dekhne ke liye number bhejo (1-8)."
        send_whatsapp_message(user.phone_number, msg)
        return

    try:
        data = json.loads(latest_analysis.analysis_result)
    except Exception:
        send_whatsapp_message(user.phone_number,
            "Aapka purana analysis format error mein hai. PDF dobara bhejiye.")
        return

    reply_msg = ""
    is_pdf_req = False

    # Menu number matching (exact match at start to avoid false positives)
    if text_lower.startswith("1") or "qualify" in text_lower or "eligibility" in text_lower or "eligible" in text_lower:
        reply_msg = data.get("part2_eligibility", "N/A")
    elif text_lower.startswith("2") or "risk" in text_lower or "problem" in text_lower or "condition" in text_lower or "koi dikkat" in text_lower:
        reply_msg = data.get("part3_risks", "N/A")
    elif text_lower.startswith("3") or "quote" in text_lower or "boq" in text_lower or "rate" in text_lower or "kitna quote" in text_lower or "strategy" in text_lower:
        reply_msg = data.get("part4_boq", "N/A")
    elif text_lower.startswith("4") or "document" in text_lower or "action plan" in text_lower or "kya karna" in text_lower or "checklist" in text_lower:
        reply_msg = data.get("part5_action_plan", "N/A")
    elif text_lower.startswith("5") or "paisa" in text_lower or "cash" in text_lower or "capital" in text_lower or "working" in text_lower:
        reply_msg = data.get("part9_cashflow", "N/A")
    elif text_lower.startswith("6") or "project kitne" in text_lower or "cost" in text_lower or "estimate" in text_lower or "kitna lagega" in text_lower:
        reply_msg = data.get("part6_cost_estimate", "N/A")
    elif text_lower.startswith("7") or "poora" in text_lower or "sab" in text_lower or "full report" in text_lower or "sab bhejo" in text_lower:
        parts = [
            data.get("part1_summary", ""),
            data.get("part2_eligibility", ""),
            data.get("part3_risks", ""),
            data.get("part4_boq", ""),
            data.get("part5_action_plan", ""),
            data.get("part6_cost_estimate", ""),
            data.get("part7_competitor", ""),
            data.get("part8_subcontractors", ""),
            data.get("part9_cashflow", ""),
            data.get("part10_recommendation", ""),
        ]
        for part in parts:
            if part:
                send_long_message(user.phone_number, part)
                time.sleep(2)
        return
    elif text_lower.startswith("8") or "pdf" in text_lower or "download" in text_lower:
        is_pdf_req = True
    elif "competitor" in text_lower or "kitne log" in text_lower or "competition" in text_lower:
        reply_msg = data.get("part7_competitor", "N/A")
    elif "subcontract" in text_lower or "thekedar" in text_lower:
        reply_msg = data.get("part8_subcontractors", "N/A")
    elif "summary" in text_lower or "kya hai tender" in text_lower:
        reply_msg = data.get("part1_summary", "N/A")
    elif "bid" in text_lower or "skip" in text_lower or "lena chahiye" in text_lower:
        reply_msg = data.get("part10_recommendation", "N/A")
    else:
        reply_msg = """Samjha nahi. Yeh try karo:

1️⃣ Eligibility
2️⃣ Risks
3️⃣ BOQ rates
4️⃣ Action plan
5️⃣ Cash flow
6️⃣ Cost estimate
7️⃣ Full report
8️⃣ PDF download

Ya type karo:
• 'history' — past analyses
• 'location' — change location
• 'restart' — start fresh"""

    if is_pdf_req:
        send_whatsapp_message(user.phone_number, "Aapki PDF report generate ho rahi hai... ⏳")
        pdf_path = generate_pdf_report(data, user.phone_number)

        try:
            import shutil
            os.makedirs("static/pdfs", exist_ok=True)
            pdf_filename = f"report_{user.phone_number.replace('+', '')}_{int(time.time())}.pdf"
            new_pdf_path = os.path.join("static", "pdfs", pdf_filename)
            shutil.move(pdf_path, new_pdf_path)

            railway_url = os.getenv("RAILWAY_URL", "").rstrip('/')
            if railway_url:
                public_pdf_url = f"{railway_url}/static/pdfs/{pdf_filename}"
                send_whatsapp_message(user.phone_number, "Lijiye aapki PDF report ready hai! 📄", media_url=public_pdf_url)
            else:
                send_whatsapp_message(user.phone_number,
                    "PDF generate ho gayi! RAILWAY_URL set hone ke baad download link milega.")
        except Exception as e:
            print(f"Error serving PDF: {e}")
            send_whatsapp_message(user.phone_number, "Sorry, PDF attach karne me thoda technical issue aaya.")
    else:
        send_long_message(user.phone_number, reply_msg)


def send_long_message(phone_number: str, text: str):
    """Splits and sends long messages in chunks."""
    if len(text) > 1500:
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            send_whatsapp_message(phone_number, chunk)
            time.sleep(1)
    else:
        send_whatsapp_message(phone_number, text)
