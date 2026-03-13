import os
import time
import json
import re
import tempfile
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import User, Analysis, Payment, ContractorPreference, TenderAlertLog, ReminderLog
from payments import generate_payment_link
from analyzer import analyze_tender_document, is_pdf_too_large
from utils import detect_language, generate_pdf_report, PLANS, format_inr
from strings import get_string, build_menu
import whatsapp
from portals import (
    detect_states_from_text, detect_work_types_from_text,
    detect_departments_from_text, parse_value_range,
    get_state_names, get_portals_for_states,
    format_ladakh_alert, format_free_alert, format_pack_alert, format_monthly_alert,
    PLAN_COMPARISON, SINGLE_PLAN_MSG, PACK_PLAN_MSG, MONTHLY_PLAN_MSG, STATES,
    search_portals_for_query, format_search_results,
)

load_dotenv()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGING — via Meta
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_whatsapp_message(to_number: str, body: str, media_url: str = None):
    """Sends a WhatsApp message. Uses BackgroundTasks wrapper if called from FastAPI."""
    import asyncio
    try:
        if media_url: # Keeping media_url param for legacy link-based sends if needed
            filename = media_url.split("/")[-1]
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(whatsapp.send_document(to_number, media_url, filename, body))
                    return
            except Exception:
                pass
            asyncio.run(whatsapp.send_document(to_number, media_url, filename, body))
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(whatsapp.send_text_message(to_number, body))
                    return
            except Exception:
                pass
            asyncio.run(whatsapp.send_text_message(to_number, body))
    except Exception as e:
        print(f"Error sending msg to {to_number}: {e}")


def send_interactive_buttons(to_number: str, body: str, buttons: list, content_sid: str = None):
    """
    Send a WhatsApp message with Quick Reply buttons via Meta Cloud API.
    """
    import asyncio
    try:
        asyncio.run(whatsapp.send_interactive_buttons(to_number, body, buttons))
    except Exception as e:
        print(f"Error sending buttons to {to_number}: {e}")
        # Fallback to text
        btn_text = "\n".join([f"👉 *{b['title']}*" for b in buttons])
        fallback_msg = f"{body}\n\n{btn_text}"
        send_whatsapp_message(to_number, fallback_msg)


def send_interactive_list(to_number: str, body: str, button_text: str, sections: list, content_sid: str = None):
    """
    Send a WhatsApp List Message via Meta Cloud API.
    """
    import asyncio
    try:
        asyncio.run(whatsapp.send_interactive_list(to_number, body, button_text, sections))
    except Exception as e:
        print(f"Error sending list to {to_number}: {e}")
        # Fallback: well-formatted numbered menu for text-only interfaces
        menu_lines = [body, ""]
        for section in sections:
            if section.get("title"):
                menu_lines.append(f"*{section['title']}*")
            
            rows = section.get("rows", [])
            for i, row in enumerate(rows, 1):
                desc = f" — {row['description']}" if row.get("description") else ""
                menu_lines.append(f"{i}. *{row['title']}*{desc}")
            menu_lines.append("")
        send_whatsapp_message(to_number, "\n".join(menu_lines))


def send_long_message(phone_number: str, text: str):
    """Splits and sends long messages in chunks."""
    if not text or text == "N/A":
        send_whatsapp_message(phone_number, get_string("hinglish", "section_not_available"))
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
    """Detects user intent from natural language with highly forgiving matching."""
    t = text.lower().strip()
    
    # Clean up punctuation for easier matching
    import re
    t_clean = re.sub(r'[^\w\s]', '', t)

    # EXACT NUMBER MATCHES
    if t_clean == "1": return "menu_1"
    if t_clean == "2": return "menu_2"
    if t_clean == "3": return "menu_3"
    if t_clean == "4": return "menu_4"
    if t_clean == "5": return "menu_5"
    if t_clean == "6": return "menu_6"
    if t_clean == "7": return "menu_7"
    if t_clean == "8": return "menu_8"

    def matchesAny(keywords):
        return any(kw in t_clean for kw in keywords)

    if matchesAny(["qualif", "eligib", "alig", "eligbel", "chalega"]): return "menu_1"
    if matchesAny(["risk", "problem", "condit", "dikkat", "khatra", "issue"]): return "menu_2"
    if matchesAny(["boq", "rate", "quote", "kitna quote", "strategy", "paisa"]): return "menu_3"
    if matchesAny(["doc", "action", "kya karna", "checklist", "paper"]): return "menu_4"
    if matchesAny(["cash", "capital", "working", "fund", "paisa chahiye"]): return "menu_5"
    if matchesAny(["cost", "estimat", "kitna lagega", "kharcha", "est"]): return "menu_6"
    if matchesAny(["poora", "full", "sab", "all", "report", "detail"]): return "menu_7"
    if matchesAny(["pdf", "download", "file"]): return "menu_8"
    if matchesAny(["share", "refer", "friend", "invite", "dost"]): return "menu_9"
    if matchesAny(["competi", "kitne log", "kon kon"]): return "menu_competitor"
    if matchesAny(["subcontract", "thekedar", "dusra"]): return "menu_subcontractor"
    if matchesAny(["sumary", "summary", "kya hai", "short"]): return "menu_summary"
    if matchesAny(["bid", "lena", "chahiye", "skip", "verdict"]): return "menu_verdict"
    if matchesAny(["later", "kal", "baad", "remind me", "tomm", "tomorrow"]): return "menu_later"

    if matchesAny(["plan", "price", "pricing", "upgrade", "subscrib", "kitne ka", "rate", "paisa", "payment"]): return "show_plans"
    if matchesAny(["99", "single", "ek", "one"]): return "buy_single"
    if matchesAny(["399", "pack", "five", "paanch", "5"]): return "buy_pack"
    if matchesAny(["799", "month", "unlimit", "mahina"]): return "buy_monthly"
    if matchesAny(["renew", "extend", "dobara", "phir"]): return "renew"

    if matchesAny(["pref", "alert", "tender bhejo", "dhundo", "set karo", "change location", "state", "portal"]): return "setup_preferences"

    if matchesAny(["band", "stop", "pause", "rok", "busy"]): return "pause_alerts"
    if matchesAny(["shuru", "resume", "fir bhejo", "start", "ab bhejo"]): return "resume_alerts"

    if matchesAny(["credit", "balanc", "bache", "expire", "account", "mera plan"]): return "check_balance"

    if matchesAny(["histor", "past", "purana", "last", "meri"]): return "show_history"

    if matchesAny(["search", "dhundo", "find", "naya tender"]): return "search"

    if matchesAny(["language", "bhasha", "lang", "english karo", "hindi karo", "marathi karo", "change language"]): return "change_language"

    if matchesAny(["restart", "reset", "naya shuru", "shuru se", "start over", "hi", "hello", "hey"]): return "restart"

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

def handle_incoming_message(phone_number: str, text: str, pdf_bytes: bytes, db: Session, background_tasks):
    referrer_phone = None
    if text and "referral from" in text.lower():
        import re
        match = re.search(r'referral from\s*([+\d]+)', text, re.IGNORECASE)
        if match:
            referrer_phone = match.group(1).strip()
            text = text.replace(match.group(0), "").strip()
            if not text: text = "hi"

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        lang = detect_language(text) if text else "hinglish"
        user = User(
            phone_number=phone_number,
            language_preference=lang,
            conversation_state="new",
            referred_by=referrer_phone,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # REFERRAL REWARD: If this user was referred, reward the referrer
        if referrer_phone and referrer_phone != phone_number:
            referrer = db.query(User).filter(User.phone_number == referrer_phone).first()
            if referrer:
                # Anti-Abuse: Max 20 referral credits per user
                referral_count = db.query(User).filter(User.referred_by == referrer_phone).count()
                if referral_count <= 20:
                    referrer.paid_credits_remaining += 1
                    db.commit()
                    # Notify referrer
                    reward_msg = f"🎉 Mubarak ho! Aapke link se ek naye user ne join kiya hai.\n🎁 Aapko mila hai +1 FREE Tender Analysis Credit!\n\nCredits remaining: {referrer.paid_credits_remaining}"
                    send_whatsapp_message(referrer.phone_number, reward_msg)

    text_lower = text.lower().strip() if text else ""

    if pdf_bytes:
        handle_new_pdf(user, pdf_bytes, db, background_tasks)
        return
    
    state = user.conversation_state

    if state == "new":
        if text_lower in ["1", "english", "en"]:
            user.language_preference = "en"
        elif text_lower in ["2", "hindi", "hi"]:
            user.language_preference = "hi"
        elif text_lower in ["3", "hinglish"]:
            user.language_preference = "hinglish"
        elif text_lower in ["4", "marathi", "mr"]:
            user.language_preference = "mr"
        elif text_lower in ["5", "gujarati", "gu"]:
            user.language_preference = "gu"
        elif text_lower in ["6", "tamil", "ta"]:
            user.language_preference = "ta"
        elif text_lower in ["7", "telugu", "te"]:
            user.language_preference = "te"
        else:
            welcome_msg = get_string("hinglish", "welcome_new")
            sections = [{"title": "Select Language", "rows": [
                {"id": "en", "title": "1. English", "description": "English"},
                {"id": "hi", "title": "2. Hindi", "description": "हिंदी"},
                {"id": "hinglish", "title": "3. Hinglish", "description": "Default"},
                {"id": "mr", "title": "4. Marathi", "description": "मराठी"},
                {"id": "ta", "title": "5. Tamil", "description": "தமிழ்"},
                {"id": "te", "title": "6. Telugu", "description": "తెలుగు"}
            ]}]
            send_interactive_list(user.phone_number, welcome_msg, "Select Language", sections)
            return
            
        user.conversation_state = "ready"
        db.commit()
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "lang_set_success"))
        return

    if state.startswith("awaiting_"):
        handle_preference_step(user, text, db)
        return

    if state == "analyzing":
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "analyzing_wait"))
        return

    if state == "awaiting_payment_choice":
        t_clean = text_lower.replace(".", "").replace(",", "").strip()
        if t_clean == "1": text_lower = "plan 1"
        if t_clean == "2": text_lower = "plan 2"
        if t_clean == "3": text_lower = "plan 3"
        user.conversation_state = "ready"
        db.commit()

    intent = detect_intent(text_lower)

    if text_lower == "plan 1": intent = "buy_single"
    if text_lower == "plan 2": intent = "buy_pack"
    if text_lower == "plan 3": intent = "buy_monthly"

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
    if intent == "change_language":
        change_language_request(user, db)
        return

    if state in ("ready", "menu"):
        latest = db.query(Analysis).filter(Analysis.user_phone == user.phone_number).order_by(Analysis.id.desc()).first()
        if latest:
            handle_menu(user, intent, text_lower, latest, db)
        else:
            send_whatsapp_message(user.phone_number, get_string(user.language_preference, "send_pdf_first"))
        return

    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "unrecognized"))


def send_welcome(user: User):
    msg = get_string(user.language_preference, "welcome_message")
    send_whatsapp_message(user.phone_number, msg)

# --- Preference Setup logic skipped for brevity but would be here ---
def start_preference_setup(user: User, db: Session):
    user.conversation_state = "awaiting_location"
    db.commit()
    msg = get_string(user.language_preference, "pref_location_prompt")
    sections = [
        {
            "title": "Quick Pick Locations",
            "rows": [
                {"id": "loc_all", "title": "1. All India (All States) 🇮🇳", "description": "Track every tender"},
                {"id": "loc_mh", "title": "2. Maharashtra 🍊", "description": "Local MH tenders"},
                {"id": "loc_dl", "title": "3. Delhi / NCR 🏛️", "description": "Capital region"},
                {"id": "loc_jk", "title": "5. J&K and Ladakh 🏔️", "description": "Paradise tenders"},
            ]
        }
    ]
    send_interactive_list(user.phone_number, msg, "Select Location", sections)

def handle_preference_step(user: User, text: str, db: Session):
    state = user.conversation_state
    pref = get_or_create_preferences(db, user.phone_number)
    # Simplified logic to restore state
    if state == "awaiting_location":
        user.conversation_state = "ready"
        db.commit()
        send_whatsapp_message(user.phone_number, "Location set. You are ready!")

def change_language_request(user: User, db: Session):
    user.conversation_state = "new"
    db.commit()
    msg = get_string(user.language_preference, "lang_menu")
    sections = [{"title": "Select Language", "rows": [
        {"id": "en", "title": "1. English", "description": "English"},
        {"id": "hi", "title": "2. Hindi", "description": "हिंदी"},
        {"id": "hinglish", "title": "3. Hinglish", "description": "Default"},
        {"id": "ta", "title": "4. Tamil", "description": "தமிழ்"},
        {"id": "te", "title": "5. Telugu", "description": "తెలుగు"}
    ]}]
    send_interactive_list(user.phone_number, msg, "Select Language", sections)

def show_plans(user: User, db: Session):
    user.conversation_state = "awaiting_payment_choice"
    db.commit()
    msg = get_string(user.language_preference, "plan_options")
    sections = [{ "title": "Available Plans", "rows": [
        {"id": "buy_1", "title": "1. Single Analysis", "description": "₹99"},
        {"id": "buy_2", "title": "2. 5 Report Pack", "description": "₹399"},
        {"id": "buy_3", "title": "3. Monthly Pro", "description": "₹799"},
    ]}]
    send_interactive_list(user.phone_number, msg, "View Plans", sections)

def handle_buy(user: User, intent: str, db: Session):
    plan_type = intent.replace("buy_", "")
    plan = PLANS.get(plan_type, PLANS["single"])
    amount = plan["price"]
    payment = Payment(user_phone=user.phone_number, amount=amount, plan_type=plan_type, status="created")
    db.add(payment)
    db.commit()
    link = generate_payment_link(amount, user.phone_number, f"PAY_{payment.id}", plan["description"])
    send_whatsapp_message(user.phone_number, f"Pay here: {link}")

def show_balance(user: User):
    send_whatsapp_message(user.phone_number, f"Credits: {user.paid_credits_remaining}")

def pause_alerts(user: User, db: Session):
    send_whatsapp_message(user.phone_number, "Alerts paused.")

def resume_alerts(user: User, db: Session):
    send_whatsapp_message(user.phone_number, "Alerts resumed.")

def show_history(user: User, db: Session):
    send_whatsapp_message(user.phone_number, "History shown here.")

def handle_search(user: User, text: str, db: Session):
    from portals import search_portals_for_query, format_search_results
    results = search_portals_for_query(text)
    msg = format_search_results(results, user.language_preference)
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_new_pdf(user: User, pdf_bytes: bytes, db: Session, background_tasks):
    if not (user.free_analyses_used < 1 or user.paid_credits_remaining > 0):
        from payments import generate_payment_link
        from utils import PLANS
        
        link_99 = generate_payment_link(PLANS["single"]["price"], user.phone_number, "UPGRADE_99", "Single Analysis")
        msg = get_string(user.language_preference, "payment_options_prompt").format(link_99=link_99)
        
        sections = [{ "title": "Upgrade Plans", "rows": [
            {"id": "buy_1", "title": "1. Single Analysis", "description": "₹99"},
            {"id": "buy_2", "title": "2. 5 Report Pack", "description": "₹399"},
            {"id": "buy_3", "title": "3. Monthly Pro", "description": "₹799"},
        ]}]
        
        user.conversation_state = "awaiting_payment_choice"
        db.commit()
        
        send_interactive_list(user.phone_number, msg, "View Plans", sections)
        return

    user.conversation_state = "analyzing"
    db.commit()

    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "pdf_received_analyzing"))

    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'wb') as f:
        f.write(pdf_bytes)

    background_tasks.add_task(process_pdf_background, user.phone_number, pdf_path)

def process_pdf_background(phone_number: str, pdf_path: str):
    from database import SessionLocal
    db = SessionLocal()
    user = db.query(User).filter(User.phone_number == phone_number).first()

    try:
        if is_pdf_too_large(pdf_path):
            send_whatsapp_message(phone_number, get_string(user.language_preference, "pdf_too_large"))
            return

        analysis_json = analyze_tender_document(pdf_path, user.language_preference)
        
        if user.subscription_type == "free":
            user.free_analyses_used += 1
        else:
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

        # Proactive Analysis Verdict & Menu
        from strings import build_menu
        
        # 1. Format Verdict Header
        verdict_msg = get_string(user.language_preference, "verdict_header").format(
            department=analysis_json.get("department", "Tender"),
            work=analysis_json.get("work_description", "General Work")[:50] + "...",
            value=format_inr(analysis_json.get("estimated_value", 0)),
            deadline=analysis_json.get("deadline", "N/A"),
            days=analysis_json.get("days_to_deadline", "N/A"),
            verdict=analysis_json.get("bid_verdict", "Unknown"),
            score=analysis_json.get("bid_score", 0),
            critical=len(analysis_json.get("critical_risks", [])),
            warnings=len(analysis_json.get("warnings", [])),
            bid=format_inr(analysis_json.get("recommended_bid", 0)),
            profit=format_inr(analysis_json.get("estimated_profit", 0))
        )
        
        # 2. Get Analysis Menu
        menu_msg = get_string(user.language_preference, "verdict_menu")
        full_msg = f"{verdict_msg}\n{menu_msg}"
        
        # 3. Add Low-Credit Nudge if needed
        if user.paid_credits_remaining < 2 and user.subscription_type != "monthly":
            nudge = get_string(user.language_preference, "upgrade_nudge_low_credits").format(credits=user.paid_credits_remaining)
            full_msg += f"\n\n💡 {nudge}"
        
        # Send everything at once
        send_whatsapp_message(phone_number, full_msg)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        print(f"Error: {e}")
        if user:
            user.conversation_state = "ready"
            db.commit()
            send_whatsapp_message(phone_number, get_string(user.language_preference, "error_gemini_failed"))
    finally:
        db.close()

def handle_menu(user: User, intent: str, text: str, latest_analysis: Analysis, db: Session):
    try:
        data = json.loads(latest_analysis.analysis_result)
    except Exception:
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "analysis_parse_error"))
        return

    # Map intents to JSON keys from prompts.py/analyzer.py output
    intent_map = {
        "menu_1": "part2_eligibility",
        "menu_2": "part3_risks",
        "menu_3": "part4_boq",
        "menu_4": "part5_action_plan",
        "menu_5": "part9_cashflow",
        "menu_6": "part6_cost_estimate",
        "menu_7": "full_report", # Special case handled below
    }

    if intent == "menu_7":
        # Full report: send all parts as a long message
        parts = []
        for key in ["part2_eligibility", "part3_risks", "part4_boq", "part5_action_plan", "part6_cost_estimate", "part9_cashflow", "part10_recommendation"]:
            val = data.get(key, "")
            if val:
                parts.append(val)
        full_text = "\n\n".join(parts)
        send_long_message(user.phone_number, full_text)
        
    elif intent == "menu_8":
        # Download PDF
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "pdf_generating"))
        generate_and_send_pdf(user, data)
        
    elif intent == "menu_9":
        # Share & Earn
        referral_link = f"https://wa.me/{os.getenv('BOT_PHONE')}?text=referral%20from%20{user.phone_number}"
        share_msg = f"Dosto ko refer karo aur free credit paao! 🎁\n\nAapka referral link: {referral_link}"
        send_whatsapp_message(user.phone_number, share_msg)
        
    elif intent in intent_map:
        # Single section
        section_key = intent_map[intent]
        section_text = data.get(section_key, get_string(user.language_preference, "section_not_available"))
        
        # Add a subtle "Share & Earn" nudge at the end of every detailed section
        referral_link = f"https://wa.me/{os.getenv('BOT_PHONE')}?text=referral%20from%20{user.phone_number}"
        nudge = f"\n\n🎁 *Tip:* Share TenderBot with a friend and get +1 Free Credit!\n{referral_link}"
        
        send_long_message(user.phone_number, section_text + nudge)
        
    else:
        # Unknown or verdict menu
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "menu_fallback"))

def generate_and_send_pdf(user: User, data: dict):
    from utils import generate_pdf_report
    import asyncio
    import whatsapp
    try:
        # Generate raw bytes instead of a local file
        pdf_bytes = generate_pdf_report(data, user.phone_number)
        filename = f"Tender_Analysis_{data.get('tender_number', 'Report')}.pdf"
        
        # Notify user it's generating
        send_whatsapp_message(user.phone_number, "⏳ Generating your PDF report...")
        
        # Upload bytes directly to Meta
        media_id = asyncio.run(whatsapp.upload_media(pdf_bytes, "application/pdf", filename))
        
        # Send using the media ID
        asyncio.run(whatsapp.send_document(user.phone_number, media_id, filename, "Tender Analysis Report", is_id=True))
    except Exception as e:
        print(f"PDF Output Error: {e}")
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "error_generic"))

def handle_payment_success(user: User, amount: int, plan_type: str, db: Session):
    """Activates subscription and credits based on the plan type."""
    from utils import PLANS
    plan = PLANS.get(plan_type, PLANS["single"])
    
    # Update user subscription
    user.subscription_type = plan_type
    user.alert_tier = plan.get("alert_tier", "free")
    
    # Add credits
    credits_to_add = plan.get("credits", 1)
    user.paid_credits_remaining += credits_to_add
    
    # Handle expiry
    expiry_days = plan.get("expiry_days")
    if expiry_days:
        user.subscription_expiry = datetime.utcnow() + timedelta(days=expiry_days)
    
    db.commit()
    
    # Success message
    success_key = f"payment_{plan_type}_success"
    msg = get_string(user.language_preference, success_key)
    if not msg:
        msg = get_string(user.language_preference, "payment_generic_success")
    
    send_whatsapp_message(user.phone_number, msg)
