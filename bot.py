import os
import time
import json
from twilio.rest import Client
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import User, Analysis, Payment, ContractorPreference, TenderAlertLog
from payments import generate_payment_link
from analyzer import analyze_tender_document, is_pdf_too_large
from utils import download_twilio_media, detect_language, generate_pdf_report
from portals import (
    detect_states_from_text, detect_work_types_from_text,
    detect_departments_from_text, parse_value_range,
    get_state_names, get_portals_for_states,
    format_ladakh_alert, format_free_alert, format_pack_alert, format_monthly_alert,
    PLAN_COMPARISON, SINGLE_PLAN_MSG, PACK_PLAN_MSG, MONTHLY_PLAN_MSG, STATES,
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


def send_long_message(phone_number: str, text: str):
    """Splits and sends long messages in chunks."""
    if not text or text == "N/A":
        send_whatsapp_message(phone_number, "Is section mein information available nahi hai.")
        return
    if len(text) > 1500:
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            send_whatsapp_message(phone_number, chunk)
            time.sleep(1)
    else:
        send_whatsapp_message(phone_number, text)

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


def get_or_create_preferences(db: Session, phone_number: str) -> ContractorPreference:
    pref = db.query(ContractorPreference).filter(
        ContractorPreference.phone_number == phone_number
    ).first()
    if not pref:
        pref = ContractorPreference(phone_number=phone_number)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTENT DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_intent(text: str) -> str:
    """Detects user intent from natural language."""
    t = text.lower().strip()

    # Payment / plan intents
    if any(kw in t for kw in ["plan", "price", "pricing", "kaunsa plan", "upgrade", "subscribe",
                               "kitne ka", "kya rate", "subscription", "best plan", "compare"]):
        return "show_plans"
    if any(kw in t for kw in ["₹99", "99 wala", "single", "ek analysis"]):
        return "buy_single"
    if any(kw in t for kw in ["₹399", "399 wala", "5 pack", "pack", "five pack"]):
        return "buy_pack"
    if any(kw in t for kw in ["₹799", "799 wala", "monthly", "unlimited", "mahina"]):
        return "buy_monthly"
    if any(kw in t for kw in ["renew", "extend", "dobara", "phir lena"]):
        return "renew"

    # Preference intents
    if any(kw in t for kw in ["preference", "alert chahiye", "tenders bhejo", "dhundo",
                               "set karo", "preference update", "alert setting",
                               "mujhe tenders", "change location", "location change",
                               "state change", "portal"]):
        return "setup_preferences"

    # Alert control
    if any(kw in t for kw in ["alert band", "stop alert", "pause", "rok do", "busy hoon"]):
        return "pause_alerts"
    if any(kw in t for kw in ["alert shuru", "resume", "fir bhejo", "start alert", "ab bhejo"]):
        return "resume_alerts"

    # Balance / account
    if any(kw in t for kw in ["credit", "balance", "kitne bache", "plan expire", "account",
                               "kitne analysis", "mera plan"]):
        return "check_balance"

    # History
    if any(kw in t for kw in ["history", "past", "purana", "purane", "last week", "kitne tender",
                               "meri history"]):
        return "show_history"

    # Search
    if t.startswith("search") or t.startswith("dhundo") or t.startswith("find"):
        return "search"
    if "koi naya tender" in t or "naya tender hai" in t:
        return "search"

    # Restart
    if any(kw in t for kw in ["restart", "reset", "naya shuru", "start over"]):
        return "restart"

    # Analyze (from alert)
    if t in ("analyze", "yes", "haan", "ha", "analyse"):
        return "analyze_yes"
    if t in ("no", "nahi", "nah", "skip"):
        return "analyze_no"
    if t in ("later", "baad mein", "kal", "remind"):
        return "analyze_later"

    # Menu numbers or keywords for analysis sections
    if any(kw in t for kw in ["qualify", "eligibility", "eligible"]) or t.startswith("1"):
        return "menu_1"
    if any(kw in t for kw in ["risk", "problem", "condition", "dikkat"]) or t.startswith("2"):
        return "menu_2"
    if any(kw in t for kw in ["boq", "rate", "quote", "kitna quote", "strategy"]) or t.startswith("3"):
        return "menu_3"
    if any(kw in t for kw in ["document", "action plan", "kya karna", "checklist"]) or t.startswith("4"):
        return "menu_4"
    if any(kw in t for kw in ["cash", "capital", "paisa", "working"]) or t.startswith("5"):
        return "menu_5"
    if any(kw in t for kw in ["cost", "estimate", "kitna lagega", "project kitne"]) or t.startswith("6"):
        return "menu_6"
    if any(kw in t for kw in ["poora", "full report", "sab bhejo", "all"]) or t.startswith("7"):
        return "menu_7"
    if any(kw in t for kw in ["pdf", "download"]) or t.startswith("8"):
        return "menu_8"
    if any(kw in t for kw in ["competitor", "competition", "kitne log"]):
        return "menu_competitor"
    if any(kw in t for kw in ["subcontract", "thekedar"]):
        return "menu_subcontractor"
    if any(kw in t for kw in ["summary", "kya hai tender"]):
        return "menu_summary"
    if any(kw in t for kw in ["bid", "lena chahiye", "skip"]):
        return "menu_verdict"

    return "unknown"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_incoming_message(phone_number: str, text: str, media_url: str, db: Session, background_tasks):
    user = get_or_create_user(db, phone_number, text)
    text_lower = text.lower().strip()

    # ── PDF at any point ──
    if media_url:
        handle_new_pdf(user, media_url, db, background_tasks)
        return

    state = user.conversation_state or "new"

    # ── Preference setup multi-step conversation ──
    if state.startswith("awaiting_"):
        handle_preference_step(user, text, db)
        return

    # ── Analyzing — don't interrupt ──
    if state == "analyzing":
        send_whatsapp_message(user.phone_number,
            "Aapka tender abhi analyze ho raha hai... thoda wait karo ⏳")
        return

    # ── Detect intent for all other states ──
    intent = detect_intent(text_lower)

    # Global intents (work in any state)
    if intent == "show_plans":
        show_plans(user, db)
        return
    if intent in ("buy_single", "buy_pack", "buy_monthly"):
        handle_buy(user, intent, db)
        return
    if intent == "renew":
        handle_buy(user, "buy_monthly", db)
        return
    if intent == "check_balance":
        show_balance(user)
        return
    if intent == "show_history":
        show_history(user, db)
        return
    if intent == "setup_preferences":
        start_preference_setup(user, db)
        return
    if intent == "pause_alerts":
        pause_alerts(user, db)
        return
    if intent == "resume_alerts":
        resume_alerts(user, db)
        return
    if intent == "restart":
        user.conversation_state = "new"
        db.commit()
        send_welcome(user)
        return
    if intent == "search":
        handle_search(user, text, db)
        return

    # State-specific handling
    if state == "new":
        send_welcome(user)
        return

    if state in ("ready", "menu"):
        latest = db.query(Analysis).filter(
            Analysis.user_phone == user.phone_number
        ).order_by(Analysis.id.desc()).first()

        if latest:
            handle_menu(user, intent, text_lower, latest, db)
        else:
            send_whatsapp_message(user.phone_number,
                "Tender PDF bhejo — main 3 minute mein poora analysis de dunga! 📄")
        return

    # Fallback
    send_welcome(user)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WELCOME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_welcome(user: User):
    msg = """Namaste! 🙏 Main TenderBot hoon.
Government tender ka poora analysis 3 minute mein kar deta hoon.

Kya karta hoon:
✅ Tender summary
✅ Qualify karte ho ya nahi
✅ Hidden risks and conditions
✅ BOQ rates and bid guidance
✅ Project cost estimate
✅ Cash flow analysis
✅ Documents checklist
✅ Day by day action plan

🎁 Pehla analysis bilkul FREE hai.
📄 Bas tender PDF bhejo.

Ya preferences set karo —
type karo: "alert chahiye"
aur main aapke liye tenders dhunduga! 🔍"""
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREFERENCE SETUP — NATURAL CONVERSATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def start_preference_setup(user: User, db: Session):
    user.conversation_state = "awaiting_location"
    db.commit()
    send_whatsapp_message(user.phone_number,
        "Bilkul! Preferences set karte hain.\n"
        "Aap kahan kaam karte ho?\n"
        "State ya city ka naam batao.\n"
        "Multiple bhi bol sakte ho.\n\n"
        "Jaise: \"Ladakh aur J&K\"\n"
        "Ya: \"Mumbai, Pune\"\n"
        "Ya: \"All India\"")


def handle_preference_step(user: User, text: str, db: Session):
    state = user.conversation_state
    pref = get_or_create_preferences(db, user.phone_number)

    if state == "awaiting_location":
        states = detect_states_from_text(text)
        if not states:
            send_whatsapp_message(user.phone_number,
                "Samjha nahi. State ya city ka naam type karo.\n"
                "Jaise: \"Ladakh\" ya \"Mumbai\" ya \"All India\"")
            return

        pref.states_list = json.dumps(states)
        pref.updated_at = datetime.utcnow()
        db.commit()

        names = get_state_names(states)
        is_ladakh = "ladakh" in states

        ladakh_note = ""
        if is_ladakh:
            ladakh_note = "\n\n⛰️ Ladakh selected — BRO, NHIDCL, MES, LAHDC tenders bhi tracked honge!"

        user.conversation_state = "awaiting_work_type"
        db.commit()

        send_whatsapp_message(user.phone_number,
            f"✅ Location noted: {names}{ladakh_note}\n\n"
            f"Ab batao — kaunsa kaam karte ho?\n"
            f"Jaise: RCC, roads, buildings, bridges,\n"
            f"water supply, electrical, ya kuch aur?")

    elif state == "awaiting_work_type":
        work_types = detect_work_types_from_text(text)
        pref.work_types = json.dumps(work_types)
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_value_range"
        db.commit()

        send_whatsapp_message(user.phone_number,
            f"✅ Work types noted: {', '.join(work_types)}\n\n"
            f"Kitni value ke tenders chahiye?\n"
            f"Minimum aur maximum batao.\n\n"
            f"Jaise: \"50 lakh se 5 crore\"\n"
            f"Ya: \"1 crore se upar\"")

    elif state == "awaiting_value_range":
        min_val, max_val = parse_value_range(text)
        pref.min_value = min_val
        pref.max_value = max_val
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_departments"
        db.commit()

        min_disp = format_inr(min_val)
        max_disp = format_inr(max_val)

        send_whatsapp_message(user.phone_number,
            f"✅ Value range: {min_disp} to {max_disp}\n\n"
            f"Kaunse departments ke tenders?\n"
            f"Jaise: PWD, BRO, NHAI, Municipal,\n"
            f"Railway, Housing, ya \"sab sarkari\"")

    elif state == "awaiting_departments":
        depts = detect_departments_from_text(text)
        pref.departments = json.dumps(depts)
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_alert_freq"
        db.commit()

        send_whatsapp_message(user.phone_number,
            f"✅ Departments: {', '.join(depts)}\n\n"
            f"Kitni baar alert chahiye?\n\n"
            f"• \"turant\" — jab bhi naya aaye\n"
            f"• \"subah\" — daily 8 AM digest\n"
            f"• \"weekly\" — har Monday summary")

    elif state == "awaiting_alert_freq":
        freq = "daily"
        t = text.lower()
        if any(kw in t for kw in ["turant", "instant", "immediately", "jab bhi", "real time"]):
            freq = "instant"
        elif any(kw in t for kw in ["weekly", "monday", "hafte", "hafta"]):
            freq = "weekly"
        elif any(kw in t for kw in ["subah", "daily", "roz", "8", "morning"]):
            freq = "daily"

        pref.alert_frequency = freq
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "ready"
        db.commit()

        # Build summary
        states = json.loads(pref.states_list) if pref.states_list else []
        work_types = json.loads(pref.work_types) if pref.work_types else []
        departments = json.loads(pref.departments) if pref.departments else []
        state_names = get_state_names(states)
        portals = get_portals_for_states(states)

        freq_display = {"instant": "Turant — real time", "daily": "Daily 8 AM digest", "weekly": "Weekly Monday summary"}

        msg = f"""✅ Preferences save ho gayi!

📍 LOCATIONS: {state_names}
🔨 WORK TYPES: {', '.join(work_types)}
💰 VALUE: {format_inr(pref.min_value)} — {format_inr(pref.max_value)}
🏢 DEPARTMENTS: {', '.join(departments)}
⏰ ALERTS: {freq_display.get(freq, freq)}
📡 {len(portals)} portals tracked

Matching tenders milenge!

Change karna ho kabhi bhi:
Type karo "preference update"

Ab tender PDF bhejo ya wait karo alerts ke liye! 📄"""

        send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLANS & PAYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def show_plans(user: User, db: Session):
    send_whatsapp_message(user.phone_number, PLAN_COMPARISON)


def handle_buy(user: User, intent: str, db: Session):
    amount_map = {"buy_single": (99, "single", "1 Tender Analysis"),
                  "buy_pack": (399, "pack", "5 Tender Pack"),
                  "buy_monthly": (799, "monthly", "Monthly Unlimited")}

    amount, plan_type, desc = amount_map.get(intent, (99, "single", "1 Tender Analysis"))

    # Show plan details
    plan_msgs = {"buy_single": SINGLE_PLAN_MSG, "buy_pack": PACK_PLAN_MSG, "buy_monthly": MONTHLY_PLAN_MSG}
    send_whatsapp_message(user.phone_number, plan_msgs.get(intent, SINGLE_PLAN_MSG))

    # Generate payment link
    payment = Payment(user_phone=user.phone_number, amount=amount, plan_type=plan_type, status="created")
    db.add(payment)
    db.commit()
    db.refresh(payment)

    link = generate_payment_link(amount, user.phone_number, f"PAY_{payment.id}", desc)
    payment.razorpay_order_id = f"PAY_{payment.id}"
    db.commit()

    time.sleep(1)
    send_whatsapp_message(user.phone_number,
        f"UPI Payment Link:\n{link}\n\nPayment hote hi turant unlock ho jayega. 🔓")


def show_balance(user: User):
    plan_names = {"free": "Free", "single": "₹99 Single", "pack": "₹399 Pack", "monthly": "₹799 Monthly"}
    plan_name = plan_names.get(user.subscription_type, "Free")

    expiry = ""
    if user.subscription_expiry:
        days_left = (user.subscription_expiry - datetime.utcnow()).days
        expiry = f"\n📅 Expiry: {user.subscription_expiry.strftime('%d %b %Y')} ({days_left} din baaki)"

    msg = f"""📊 Aapka Account:

Plan: {plan_name}
Credits: {user.paid_credits_remaining}
Free analysis: {'Used ✓' if user.free_analyses_used >= 1 else 'Available ✅'}
Total analyses done: {user.total_analyses_done}{expiry}

Upgrade ya renew karna hai?
Type karo "plan" ya "799 wala"""

    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERT CONTROL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def pause_alerts(user: User, db: Session):
    pref = get_or_create_preferences(db, user.phone_number)
    pref.alerts_paused = True
    pref.pause_until = datetime.utcnow() + timedelta(days=7)
    db.commit()
    send_whatsapp_message(user.phone_number,
        "✅ Alerts 7 din ke liye pause ho gaye.\n"
        "Resume karne ke liye type karo: \"alerts shuru karo\"")


def resume_alerts(user: User, db: Session):
    pref = get_or_create_preferences(db, user.phone_number)
    pref.alerts_paused = False
    pref.pause_until = None
    db.commit()
    send_whatsapp_message(user.phone_number,
        "✅ Alerts fir shuru ho gaye!\n"
        "Matching tenders milte rahenge. 🔔")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def show_history(user: User, db: Session):
    analyses = db.query(Analysis).filter(
        Analysis.user_phone == user.phone_number
    ).order_by(Analysis.id.desc()).limit(5).all()

    if not analyses:
        send_whatsapp_message(user.phone_number, "Koi past analysis nahi mila. Tender PDF bhejo!")
        return

    msg = "📋 Aapke recent analyses:\n\n"
    for i, a in enumerate(analyses, 1):
        msg += f"{i}. {a.tender_summary} — {a.created_at.strftime('%d %b %Y')}\n"
    msg += f"\nTotal: {user.total_analyses_done} analyses kiye hain."
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEARCH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_search(user: User, text: str, db: Session):
    # Check subscription for search access
    if user.subscription_type not in ("pack", "monthly"):
        send_whatsapp_message(user.phone_number,
            "🔍 Search feature ₹399 Pack ya ₹799 Monthly mein available hai.\n\n"
            "Upgrade karo search access ke liye.\n"
            "Type karo: \"plan\"")
        return

    send_whatsapp_message(user.phone_number,
        "🔍 Search feature coming soon!\n"
        "Abhi ke liye eprocure.gov.in pe manually search karo.\n"
        "Ya tender PDF bhejo — main analyze kar dunga!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_new_pdf(user: User, media_url: str, db: Session, background_tasks):
    # Check credits
    has_credits = False
    if user.free_analyses_used < 1:
        has_credits = True
    elif user.paid_credits_remaining > 0:
        has_credits = True
    elif user.subscription_type == "monthly" and user.total_analyses_done < 30:
        has_credits = True

    if not has_credits:
        request_payment(user, db)
        return

    user.conversation_state = "analyzing"
    db.commit()

    send_whatsapp_message(user.phone_number,
        "Tender mil gaya! 📄\n"
        "Poora analyze kar raha hoon —\n"
        "3 minute mein complete report bhejta hoon. ⏳")

    time.sleep(1)
    send_whatsapp_message(user.phone_number,
        "Jab tak main analyze karta hoon —\n"
        "yeh documents ready hain aapke paas?\n\n"
        "□ ITR last 3 years\n"
        "□ CA certified balance sheet\n"
        "□ Registration certificate\n"
        "□ GST certificate\n"
        "□ Completion certificates of past work\n"
        "□ Solvency certificate\n\n"
        "Jo ready nahi hai batao —\n"
        "main deadline check karke batata hoon.")

    background_tasks.add_task(process_pdf_background, user.phone_number, media_url)


def request_payment(user: User, db: Session):
    msg = "Aapka free analysis use ho gaya. ✓\n\n"

    # Show comparison and generate ₹99 link as default
    payment = Payment(user_phone=user.phone_number, amount=99, plan_type="single", status="created")
    db.add(payment)
    db.commit()
    db.refresh(payment)

    link_99 = generate_payment_link(99, user.phone_number, f"PAY_{payment.id}", "1 Tender Analysis")
    payment.razorpay_order_id = f"PAY_{payment.id}"
    db.commit()

    msg += f"""Agle tender ke liye:

💳 ₹99  — 1 analysis
💳 ₹399 — 5 analyses (₹80 each) ⭐ Best Value
💳 ₹799 — 30/month + unlimited alerts

Abhi ₹99 mein shuru karo:
{link_99}

Ya type karo "399 wala" ya "799 wala"
for bigger plans."""

    send_whatsapp_message(user.phone_number, msg)


def process_pdf_background(phone_number: str, media_url: str):
    from database import SessionLocal
    db = SessionLocal()
    user = db.query(User).filter(User.phone_number == phone_number).first()

    try:
        pdf_path = download_twilio_media(media_url)

        if is_pdf_too_large(pdf_path):
            send_whatsapp_message(phone_number,
                "PDF bahut bada hai (>50MB).\n"
                "Compress karke bhejo ya portal ka link do.")
            user.conversation_state = "ready"
            db.commit()
            return

        send_whatsapp_message(phone_number, "Still analyzing... almost done ⏳")

        analysis_json = analyze_tender_document(pdf_path, user.language_preference)

        # Deduct credit
        if user.free_analyses_used < 1:
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

        # ── Ladakh detection ──
        location = str(analysis_json.get("location", "")).lower()
        is_ladakh = any(kw in location for kw in ["ladakh", "leh", "kargil"])
        if is_ladakh:
            send_whatsapp_message(phone_number, format_ladakh_alert(analysis_json))
            time.sleep(2)

        # ── Quick Verdict ──
        verdict = f"""━━━━━━━━━━━━━━━━━━━━━━━━
📋 {analysis_json.get('department', 'Dept')} — {analysis_json.get('work_description', 'Work')}
💰 Value: ₹{analysis_json.get('value', 'N/A')}
📅 Deadline: {analysis_json.get('deadline_date', 'N/A')} ({analysis_json.get('days_remaining', 'X')} din baaki)

⚡ VERDICT: {analysis_json.get('quick_verdict_recommendation', 'N/A')} — {analysis_json.get('quick_verdict_score', 'N/A')}/10

🔴 {analysis_json.get('critical_risks_count', '0')} Critical risks
🟡 {analysis_json.get('warnings_count', '0')} Warnings
💡 Recommended bid: ₹{analysis_json.get('recommended_bid', 'N/A')}
💰 Estimated profit: ₹{analysis_json.get('estimated_profit', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━

Kya dekhna chahte ho?
Type karo ya poochho:

• "eligibility" — qualify karte ho?
• "risks" — hidden risks kya hain?
• "boq" — rates aur bid strategy
• "documents" — action plan
• "cash flow" — working capital
• "cost" — project cost estimate
• "full report" — sab ek saath
• "pdf" — PDF download karo

Seedha apna sawaal bhi pooch sakte ho 🙂"""

        send_whatsapp_message(phone_number, verdict)

        # ── Upgrade nudge for free users ──
        if user.subscription_type == "free" and user.free_analyses_used >= 1:
            time.sleep(3)
            send_whatsapp_message(phone_number,
                "💡 Yeh analysis aapko kaisa laga?\n\n"
                "Agle tender ke liye:\n"
                "₹399 = 5 analyses (₹80 each)\n"
                "₹799 = Unlimited + auto alerts\n\n"
                "Type karo \"plan\" for details.")

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
# MENU / ANALYSIS SECTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_menu(user: User, intent: str, text: str, latest_analysis: Analysis, db: Session):
    try:
        data = json.loads(latest_analysis.analysis_result)
    except Exception:
        send_whatsapp_message(user.phone_number,
            "Purana analysis parse nahi ho raha. PDF dobara bhejo.")
        return

    section_map = {
        "menu_1": "part2_eligibility",
        "menu_2": "part3_risks",
        "menu_3": "part4_boq",
        "menu_4": "part5_action_plan",
        "menu_5": "part9_cashflow",
        "menu_6": "part6_cost_estimate",
        "menu_competitor": "part7_competitor",
        "menu_subcontractor": "part8_subcontractors",
        "menu_summary": "part1_summary",
        "menu_verdict": "part10_recommendation",
    }

    if intent in section_map:
        content = data.get(section_map[intent], "Information available nahi hai.")
        send_long_message(user.phone_number, content)
        return

    if intent == "menu_7":
        # Full report — send all sections
        parts = ["part1_summary", "part2_eligibility", "part3_risks", "part4_boq",
                 "part5_action_plan", "part6_cost_estimate", "part7_competitor",
                 "part8_subcontractors", "part9_cashflow", "part10_recommendation"]
        for key in parts:
            content = data.get(key, "")
            if content:
                send_long_message(user.phone_number, content)
                time.sleep(2)
        return

    if intent == "menu_8":
        generate_and_send_pdf(user, data)
        return

    # Unknown intent inside menu
    send_whatsapp_message(user.phone_number,
        "Samjha nahi. Type karo:\n\n"
        "• \"eligibility\" — qualify check\n"
        "• \"risks\" — hidden risks\n"
        "• \"boq\" — bid strategy\n"
        "• \"documents\" — action plan\n"
        "• \"cash flow\" — capital check\n"
        "• \"cost\" — cost estimate\n"
        "• \"full report\" — sab ek saath\n"
        "• \"pdf\" — download report\n\n"
        "Ya:\n"
        "• \"plan\" — subscription plans\n"
        "• \"history\" — past analyses\n"
        "• \"preference update\" — change alerts")


def generate_and_send_pdf(user: User, data: dict):
    send_whatsapp_message(user.phone_number, "PDF report generate ho rahi hai... ⏳")
    pdf_path = generate_pdf_report(data, user.phone_number)

    try:
        import shutil
        os.makedirs("static/pdfs", exist_ok=True)
        pdf_filename = f"report_{user.phone_number.replace('+', '')}_{int(time.time())}.pdf"
        new_pdf_path = os.path.join("static", "pdfs", pdf_filename)
        shutil.move(pdf_path, new_pdf_path)

        railway_url = os.getenv("RAILWAY_URL", "").rstrip('/')
        if railway_url:
            public_url = f"{railway_url}/static/pdfs/{pdf_filename}"
            send_whatsapp_message(user.phone_number,
                "Lijiye aapki PDF report ready hai! 📄", media_url=public_url)
        else:
            send_whatsapp_message(user.phone_number,
                "PDF generate ho gayi par download link abhi set nahi hai.")
    except Exception as e:
        print(f"Error serving PDF: {e}")
        send_whatsapp_message(user.phone_number, "PDF attach karne mein issue aaya. Dobara try karo.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAYMENT WEBHOOK HANDLER (called from main.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_payment_success(user: User, amount: int, plan_type: str, db: Session):
    """Called by main.py webhook when Razorpay confirms payment."""
    if plan_type == "single" or amount == 99:
        user.paid_credits_remaining += 1
        user.subscription_type = "single"
        user.alert_tier = "free"
        unlock_msg = "Payment received! ✅\n1 analysis unlock ho gaya.\n\nTender PDF bhejo! 📄"

    elif plan_type == "pack" or amount == 399:
        user.paid_credits_remaining += 5
        user.subscription_type = "pack"
        user.alert_tier = "basic"
        user.subscription_expiry = datetime.utcnow() + timedelta(days=60)
        unlock_msg = ("Payment received! ✅\n5 analyses unlock ho gaye.\n"
                      "60 din valid hai.\n\n"
                      "Ab alerts mein brief analysis bhi milega!\n"
                      "Tender PDF bhejo ya alerts ka wait karo! 📄")

    elif plan_type == "monthly" or amount == 799:
        user.paid_credits_remaining = 30
        user.subscription_type = "monthly"
        user.alert_tier = "full"
        user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        unlock_msg = ("Payment received! ✅\n⭐ Monthly Unlimited plan active!\n\n"
                      "30 analyses + UNLIMITED alert analyses\n"
                      "Bot tenders dhundega aapke liye\n"
                      "Full analysis with every alert — FREE\n\n"
                      "Preferences set karo: type \"alert chahiye\"\n"
                      "Ya tender PDF bhejo abhi! 📄")
    else:
        user.paid_credits_remaining += 1
        unlock_msg = "Payment received! ✅\nCredits add ho gaye."

    db.commit()
    send_whatsapp_message(user.phone_number, unlock_msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE NUDGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_upgrade_nudge(user: User, db: Session):
    """Called periodically or after certain triggers."""
    if user.subscription_type == "free" and user.free_analyses_used >= 1:
        send_whatsapp_message(user.phone_number,
            "Aapko matching tenders mil rahe hain.\n"
            "Ek bhi analyze nahi kiya abhi tak.\n\n"
            "₹399 mein 5 analyses milte hain.\n"
            "Sirf ₹80 per tender.\n\n"
            "Type karo: \"399 wala\"")

    elif user.subscription_type == "pack" and user.paid_credits_remaining <= 1:
        send_whatsapp_message(user.phone_number,
            f"Sirf {user.paid_credits_remaining} credit bacha hai.\n\n"
            "Renew karo ₹399 — 5 aur analyses\n"
            "Ya upgrade karo ₹799/month:\n"
            "→ 30 analyses\n"
            "→ Alert with full analysis\n"
            "→ Search unlimited\n\n"
            "Type karo: \"plan\"")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONTHLY REPORT (for ₹799 users)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_monthly_report(user: User, db: Session) -> str:
    analyses = db.query(Analysis).filter(
        Analysis.user_phone == user.phone_number,
        Analysis.created_at >= datetime.utcnow() - timedelta(days=30)
    ).all()

    alerts = db.query(TenderAlertLog).filter(
        TenderAlertLog.user_phone == user.phone_number,
        TenderAlertLog.sent_at >= datetime.utcnow() - timedelta(days=30)
    ).all()

    analysis_count = len(analyses)
    alert_count = len(alerts)
    free_alert_analyses = len([a for a in alerts if a.alert_type == "full"])
    consultant_savings = analysis_count * 10000

    msg = f"""📊 Aapka Monthly Report
━━━━━━━━━━━━━━━━━━━━━━

ANALYSES THIS MONTH: {analysis_count}/30
ALERTS RECEIVED: {alert_count}
ALERT ANALYSES: {free_alert_analyses} (free)

MONEY SAVED VS CONSULTANT:
{analysis_count} analyses × ₹10,000 = ₹{analysis_count * 10000:,}
You paid: ₹799
You saved: ₹{consultant_savings - 799:,}

━━━━━━━━━━━━━━━━━━━━━━
Aapka plan kal expire hoga.
Renew karo — koi tender miss mat ho.
Type karo: \"renew\""""

    return msg

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_inr(amount: int) -> str:
    """Formats amount in Indian style: 50,00,000 → ₹50 Lakhs"""
    if amount >= 10000000:
        return f"₹{amount / 10000000:.1f} Crores"
    elif amount >= 100000:
        return f"₹{amount / 100000:.1f} Lakhs"
    elif amount >= 1000:
        return f"₹{amount / 1000:.0f}K"
    else:
        return f"₹{amount}"
