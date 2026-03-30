import os
import time
import json
import re
import tempfile
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import User, Analysis, Payment, ContractorPreference, TenderAlertLog, ReminderLog, WebhookLog
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

def run_async_task(coro):
    """Helper to run a coroutine, handling existing event loops (e.g. in FastAPI/uvicorn)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in a running loop (like FastAPI), create a background task
            return loop.create_task(coro)
        else:
            # Not in a running loop, safe to use asyncio.run
            return asyncio.run(coro)
    except RuntimeError:
        # No loop in this thread, safe to use asyncio.run
        return asyncio.run(coro)
    except Exception as e:
        print(f"❌ Error in run_async_task: {e}")

def send_whatsapp_message(to_number: str, body: str, media_url: str = None):
    """Sends a WhatsApp message. Safe to call from sync or async contexts."""
    if media_url: 
        filename = media_url.split("/")[-1]
        run_async_task(whatsapp.send_document(to_number, media_url, filename, body))
    else:
        run_async_task(whatsapp.send_text_message(to_number, body))


def send_interactive_buttons(to_number: str, body: str, buttons: list, content_sid: str = None):
    """
    Send a WhatsApp message with Quick Reply buttons via Meta Cloud API.
    """
    try:
        run_async_task(whatsapp.send_interactive_buttons(to_number, body, buttons))
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
    try:
        run_async_task(whatsapp.send_interactive_list(to_number, body, button_text, sections))
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
    """Splits and sends long messages in chunks at paragraph boundaries."""
    if not text or text == "N/A":
        send_whatsapp_message(phone_number, get_string("hinglish", "section_not_available"))
        return
    
    MAX_LENGTH = 4000
    if len(text) <= MAX_LENGTH:
        send_whatsapp_message(phone_number, text)
        return
    
    # Split at paragraph boundaries (double newlines)
    paragraphs = text.split("\n\n")
    chunk = ""
    for para in paragraphs:
        if len(chunk) + len(para) + 2 > MAX_LENGTH:
            if chunk.strip():
                send_whatsapp_message(phone_number, chunk.strip())
                time.sleep(1)
            chunk = para + "\n\n"
        else:
            chunk += para + "\n\n"
    if chunk.strip():
        send_whatsapp_message(phone_number, chunk.strip())


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

def generate_referral_link(user_phone: str) -> str:
    """Generate a WhatsApp deep link with pre-filled referral text."""
    # Use the actual WhatsApp number, not the phone number ID
    bot_wa_number = os.getenv("BOT_PHONE", "919796700386")
    encoded_text = f"referral%20from%20{user_phone}"
    return f"https://wa.me/{bot_wa_number}?text={encoded_text}"

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
    # --- ADMIN COMMANDS ---
    if text and text.strip().lower() in ["!stats", "!admin", "stats", "admin", "admin stats"]:
        # Give access to authorized admin numbers
        admin_phones = [os.getenv("ADMIN_PHONE", "6006224209"), "6006224209", "6006788068", "9796700386"]
        if any(p in phone_number for p in admin_phones):
            from sqlalchemy import func
            
            total_users = db.query(User).count()
            active_today = db.query(User).filter(User.created_at > datetime.utcnow() - timedelta(days=1)).count()
            
            # Source grouping
            # Note: We use getattr in case the column doesn't exist yet while Railway migrations run
            sources = []
            try:
                sources = db.query(User.source, func.count(User.phone_number)).group_by(User.source).all()
            except Exception:
                pass
            
            source_text = "\n".join([f"  • {str(s[0]).replace('_', ' ').title()}: {s[1]}" for s in sources if s[0]])
            if not source_text:
                source_text = "  • Organic: 100%"
                
            total_analyses = db.query(Analysis).count()
            total_payments = db.query(Payment).filter(Payment.status == "paid").count()
            total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "paid").scalar() or 0
            
            stats_msg = (
                "📊 *BidMaster AI Live Analytics*\n\n"
                f"👥 Total Users: {total_users}\n"
                f"🔥 New Users (24h): {active_today}\n\n"
                f"📍 *Traffic Sources:*\n{source_text}\n\n"
                f"📄 Total Analyses: {total_analyses}\n"
                f"💳 Paid Orders: {total_payments}\n"
                f"💰 Total Revenue: ₹{total_revenue:,.2f}\n\n"
                f"🕒 Server Time: {datetime.utcnow().strftime('%H:%M UTC')}"
            )
            send_whatsapp_message(phone_number, stats_msg)
            return
    # --- END ADMIN COMMANDS ---

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
        # Determine User Source
        user_source = "organic"
        if referrer_phone:
            user_source = "referral"
        elif text and "bidmaster" in text.lower():
            user_source = "landing_page"

        lang = detect_language(text) if text else "hinglish"
        user = User(
            phone_number=phone_number,
            language_preference=lang,
            conversation_state="new",
            referred_by=referrer_phone,
            source=user_source,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # REFERRAL REWARD: If this user was referred, reward the referrer
        if referrer_phone:
            import re
            safe_referrer = re.sub(r'\D', '', str(referrer_phone))
            safe_me = re.sub(r'\D', '', str(phone_number))
            
            if safe_referrer and safe_me and safe_referrer not in safe_me and safe_me not in safe_referrer:
                # We need to find the user by partial match since DB might have it with/without country code
                referrer = db.query(User).filter(User.phone_number.like(f"%{safe_referrer}%")).first()
                if referrer:
                    # Anti-Abuse: Max 20 referral credits per user
                    referral_count = db.query(User).filter(User.referred_by == referrer_phone).count()
                    if referral_count <= 20:
                        referrer.paid_credits_remaining += 2
                        db.commit()
                        # Notify referrer
                        reward_msg = f"🎉 Mubarak ho! Aapke link se ek naye user ne join kiya hai.\n🎁 Aapko mila hai +2 FREE Tender Analysis Credits!\n\nCredits remaining: {referrer.paid_credits_remaining}"
                        send_whatsapp_message(referrer.phone_number, reward_msg)

    # Global timeout check BEFORE overriding updated_at
    old_updated_at = user.updated_at

    # Track activity
    user.updated_at = datetime.utcnow()
    db.commit()

    # Auto-reset ANY stuck state after 30 minutes
    stuck_states = ["analyzing", "awaiting_payment_choice", "awaiting_location", 
                    "awaiting_work_type", "awaiting_value_range", "awaiting_departments",
                    "awaiting_alert_freq"]
    if user.conversation_state in stuck_states:
        if old_updated_at:
            time_in_state = (datetime.utcnow() - old_updated_at).total_seconds()
            if time_in_state > 1800:  # 30 minutes
                user.conversation_state = "ready"
                db.commit()
                # We update the local 'state' variable so the rest of the flow treats them as 'ready'
                # but we also send a timeout warning.
                send_whatsapp_message(user.phone_number, 
                    "⚠️ Session timeout ho gaya. Koi baat nahi — aap phir se shuru kar sakte ho!\n\nType 'Menu' for options.")
                return

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

    if state.startswith("awaiting_") and state != "awaiting_payment_choice":
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

    if text_lower in ("plan 1", "buy_1"): intent = "buy_single"
    if text_lower in ("plan 2", "buy_2"): intent = "buy_pack"
    if text_lower in ("plan 3", "buy_3"): intent = "buy_monthly"

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
    sections = [{ "title": "States", "rows": [
        {"id": "J&K & Ladakh", "title": "J&K & Ladakh ⛰️"},
        {"id": "All India", "title": "All India 🇮🇳"},
        {"id": "Maharashtra", "title": "Maharashtra 🏙️"},
        {"id": "Delhi NCR", "title": "Delhi NCR 🏛️"},
        {"id": "Punjab & Haryana", "title": "Punjab & Haryana 🌾"},
        {"id": "Uttar Pradesh", "title": "Uttar Pradesh 🕌"},
        {"id": "Karnataka", "title": "Karnataka 🏢"},
        {"id": "Gujarat", "title": "Gujarat 🏭"}
    ]}]
    send_interactive_list(user.phone_number, msg, "Select State", sections)

def handle_preference_step(user: User, text: str, db: Session):
    state = user.conversation_state
    pref = get_or_create_preferences(db, user.phone_number)
    
    if state == "awaiting_location":
        loc_map = {"1": "J&K & Ladakh", "2": "All India", "3": "Maharashtra", "4": "Delhi NCR", "5": "Punjab & Haryana", "6": "Uttar Pradesh", "7": "Karnataka", "8": "Gujarat"}
        mapped_text = loc_map.get(text.strip(), text.strip()[:100])
        pref.states_list = json.dumps([mapped_text])
        user.conversation_state = "awaiting_work_type"
        db.commit()
        msg = get_string(user.language_preference, "pref_work_type_prompt")
        sections = [{ "title": "Work Types", "rows": [
            {"id": "Roads & Highways", "title": "Roads & Highways 🛣️"},
            {"id": "Building / Civil", "title": "Building / Civil 🏗️"},
            {"id": "Electrical", "title": "Electrical ⚡"},
            {"id": "Water Supply", "title": "Water Supply 💧"},
            {"id": "Bridges & Flyovers", "title": "Bridges & Flyovers 🌉"},
            {"id": "Solar & Renewable", "title": "Solar & Renewable ☀️"}
        ]}]
        send_interactive_list(user.phone_number, msg, "Select Work", sections)
        
    elif state == "awaiting_work_type":
        work_map = {"1": "Roads & Highways", "2": "Building / Civil", "3": "Electrical", "4": "Water Supply", "5": "Bridges & Flyovers", "6": "Solar & Renewable"}
        mapped_text = work_map.get(text.strip(), text.strip()[:100])
        pref.work_types = json.dumps([mapped_text])
        user.conversation_state = "awaiting_value_range"
        db.commit()
        msg = get_string(user.language_preference, "pref_value_range_prompt")
        sections = [{ "title": "Values", "rows": [
            {"id": "5000000", "title": "Upto 50 Lakh", "description": "0-50L"},
            {"id": "50000000", "title": "50L - 5 Crore", "description": "50L-5C"},
            {"id": "200000000", "title": "5C - 20 Crore", "description": "5C-20C"},
            {"id": "1000000000", "title": "20C - 100 Crore", "description": "20C-100C"},
            {"id": "99999000000", "title": "All Amounts", "description": "Any value"}
        ]}]
        send_interactive_list(user.phone_number, msg, "Select Value", sections)
        
    elif state == "awaiting_value_range":
        try:
            val_map = {"1": 5000000, "2": 50000000, "3": 200000000, "4": 1000000000, "5": 99999000000}
            max_val = val_map.get(text.strip(), int(text.strip()))
        except:
            max_val = 99999000000
        pref.min_value = 0
        pref.max_value = max_val
        user.conversation_state = "awaiting_departments"
        db.commit()
        msg = get_string(user.language_preference, "pref_departments_prompt")
        sections = [{ "title": "Departments", "rows": [
            {"id": "All Gov", "title": "All Gov 🏛️"},
            {"id": "PWD / CPWD / Municipal", "title": "PWD / Municipal 🏢"},
            {"id": "Highways", "title": "Highways 🛣️"},
            {"id": "Railways & Metro", "title": "Railways & Metro 🚂"},
            {"id": "Water Depts", "title": "Water Depts 💧"},
            {"id": "Defence / MES", "title": "Defence / MES 🛡️"}
        ]}]
        send_interactive_list(user.phone_number, msg, "Select Dept", sections)
        
    elif state == "awaiting_departments":
        dept_map = {"1": "All Gov", "2": "PWD / CPWD / Municipal", "3": "Highways", "4": "Railways & Metro", "5": "Water Depts", "6": "Defence / MES"}
        mapped_text = dept_map.get(text.strip(), text.strip()[:100])
        pref.departments = json.dumps([mapped_text])
        user.conversation_state = "awaiting_alert_freq"
        db.commit()
        msg = get_string(user.language_preference, "pref_alert_freq_prompt")
        sections = [{ "title": "Speed", "rows": [
            {"id": "instant", "title": "Instant 🚀", "description": "Real-time alerts"},
            {"id": "daily", "title": "Daily Morning ☀️", "description": "8 AM digest"},
            {"id": "weekly", "title": "Weekly 📅", "description": "Monday summary"}
        ]}]
        send_interactive_list(user.phone_number, msg, "Select Speed", sections)
        
    elif state == "awaiting_alert_freq":
        pref.alert_frequency = text.strip() if text.strip() in ["instant", "daily", "weekly"] else "daily"
        pref.alerts_paused = False
        user.conversation_state = "ready"
        db.commit()
        
        from utils import format_inr
        max_v = format_inr(pref.max_value) if pref.max_value < 99999000000 else "Any"
        summary = get_string(user.language_preference, "pref_summary").format(
            state_names=pref.states_list or "All",
            work_types=pref.work_types or "All",
            min_value="All",
            max_value=max_v,
            departments=pref.departments or "All",
            alerts=pref.alert_frequency,
            num_portals="15+"
        )
        send_whatsapp_message(user.phone_number, summary)

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
        {"id": "buy_1", "title": "1. Basic Pack", "description": "₹99 - 3 Reports (14d)"},
        {"id": "buy_2", "title": "2. Value Pack", "description": "₹399 - 15 Reports (60d)"},
        {"id": "buy_3", "title": "3. Quarterly Pro", "description": "₹699 - 30 Reports (90d)"},
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
    pref = get_or_create_preferences(db, user.phone_number)
    pref.alerts_enabled = False
    db.commit()
    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "alerts_paused"))

def resume_alerts(user: User, db: Session):
    pref = get_or_create_preferences(db, user.phone_number)
    pref.alerts_enabled = True
    db.commit()
    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "alerts_resumed"))

def show_history(user: User, db: Session):
    analyses = db.query(Analysis).filter(Analysis.user_phone == user.phone_number).order_by(Analysis.id.desc()).limit(3).all()
    if not analyses:
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "no_past_analysis"))
        return
    msg = get_string(user.language_preference, "recent_analyses_header") + "\n\n"
    for a in analyses:
        desc = (a.tender_summary or "Custom Tender")[:40]
        msg += f"📄 *{desc}*\n🗓️ {str(a.created_at)[:10]}\n\n"
    msg += get_string(user.language_preference, "total_analyses_done").format(total=user.total_analyses_done)
    send_whatsapp_message(user.phone_number, msg)

def handle_search(user: User, text: str, db: Session):
    from portals import search_portals_for_query, format_search_results
    results = search_portals_for_query(text)
    msg = format_search_results(results, user.language_preference)
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_new_pdf(user: User, pdf_bytes: bytes, db: Session, background_tasks):
    if not (user.free_analyses_used < 5 or user.paid_credits_remaining > 0):
        from payments import generate_payment_link
        from utils import PLANS
        
        link_99 = generate_payment_link(PLANS["single"]["price"], user.phone_number, "UPGRADE_99", "Basic Pack")
        msg = get_string(user.language_preference, "payment_options_prompt").format(link_99=link_99)
        
        sections = [{ "title": "Upgrade Plans", "rows": [
            {"id": "buy_1", "title": "1. Basic Pack", "description": "₹99 - 3 Reports"},
            {"id": "buy_2", "title": "2. Value Pack", "description": "₹399 - 15 Reports"},
            {"id": "buy_3", "title": "3. Quarterly Pro", "description": "₹699 - 30 Reports"},
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

        try:
            analysis_json = analyze_tender_document(pdf_path, user.language_preference, db_session=db)
            
            if isinstance(analysis_json, dict) and analysis_json.get("error") == "OCR_FAILED_TINY":
                user.conversation_state = "ready"
                db.commit()
                send_whatsapp_message(user.phone_number, 
                    "❌ Yeh PDF readable nahi hai — bahut blurry ya empty lag raha hai.\n\n"
                    "Please ek clear, readable PDF bhejo. Scanned documents bhi chalte hain "
                    "agar text readable ho.")
                return
                
        except Exception as e:
            print(f"❌ Analysis failed for {user.phone_number}: {e}")
            user.conversation_state = "ready"
            db.commit()
            
            base_err = get_string(user.language_preference, "error_generic")
            full_err = (f"{base_err}\n\n"
                        "Possible reasons:\n"
                        "• PDF is too large (>50MB)\n"
                        "• PDF is password protected\n"  
                        "• PDF is corrupt/damaged\n\n"
                        "Please try again or send a different PDF.")
            send_whatsapp_message(user.phone_number, full_err)
            return

        if user.subscription_type == "free":
            user.free_analyses_used += 1
        else:
            user.paid_credits_remaining -= 1

        user.total_analyses_done += 1
        user.conversation_state = "menu"
        
        # Parse deadline from Gemini response
        deadline_dt = None
        deadline_str = analysis_json.get("deadline_date", "")
        if deadline_str and isinstance(deadline_str, str):
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    deadline_dt = datetime.strptime(deadline_str.strip(), fmt)
                    break
                except ValueError:
                    continue

        new_analysis = Analysis(
            user_phone=user.phone_number,
            tender_summary=analysis_json.get("department", "Tender"),
            analysis_result=json.dumps(analysis_json),
            deadline_date=deadline_dt
        )
        db.add(new_analysis)
        db.commit()

        # Proactive Analysis Verdict & Menu
        from strings import build_menu
        
        # 1. Format Verdict Header
        # 1. Format Verdict Header - Defensive Data Types (FIX A)
        value = analysis_json.get("estimated_value", 0)
        if isinstance(value, str):
            import re
            nums = re.findall(r'[\d,]+', value.replace(',', ''))
            if nums:
                try:
                    value = int(nums[0].replace(',', ''))
                except:
                    value = 0
        if isinstance(value, (int, float)) and value > 0:
            if value >= 10000000:
                value_display = f"₹{value/10000000:.1f} Crores"
            elif value >= 100000:
                value_display = f"₹{value/100000:.1f} Lakhs"
            else:
                value_display = f"₹{value:,.0f}"
        else:
            value_display = "Not specified"

        deadline = analysis_json.get("deadline_date", "")
        days_remaining = analysis_json.get("days_to_deadline", "")
        if deadline and str(deadline) != "N/A" and str(deadline).strip():
            deadline_display = f"📅 Deadline: {deadline}"
            if days_remaining and str(days_remaining).strip() and str(days_remaining) != "0" and str(days_remaining) != "N/A":
                deadline_display += f" ({days_remaining} din baaki)"
        else:
            deadline_display = "📅 Deadline: Document mein check karein"

        verdict_score = analysis_json.get("bid_score", 0)
        verdict_text = analysis_json.get("bid_verdict", "")
        if not verdict_text or verdict_text == "Bid or Skip" or verdict_text == "Unknown":
            part10 = analysis_json.get("part10_recommendation", "")
            if "BID" in str(part10).upper():
                verdict_text = "BID ✅"
            elif "SKIP" in str(part10).upper():
                verdict_text = "SKIP ❌"
            else:
                verdict_text = "Review needed"
                
        if not verdict_score or verdict_score == 0:
            import re
            score_match = re.search(r'(\d+)/10', str(analysis_json.get("part10_recommendation", "")))
            if score_match:
                verdict_score = int(score_match.group(1))

        verdict_msg = (
            f"💼 *{analysis_json.get('department', 'Tender')}*\n"
            f"📝 {str(analysis_json.get('work_description', 'General Work'))[:50]}...\n"
            f"💰 Value: {value_display}\n"
            f"{deadline_display}\n\n"
            f"🎯 *Verdict:* {verdict_text} — {verdict_score}/10\n"
            f"⚠️ Critical Risks: {len(analysis_json.get('critical_risks', []))}\n"
            f"📌 Warnings: {len(analysis_json.get('warnings', []))}\n"
            f"📈 Rec. Bid: {format_inr(analysis_json.get('recommended_bid', 0))}\n"
            f"💸 Est. Profit: {format_inr(analysis_json.get('estimated_profit', 0))}"
        )
        
        # 2. Get Analysis Menu
        menu_msg = get_string(user.language_preference, "verdict_menu")
        full_msg = f"{verdict_msg}\n{menu_msg}"
        
        # 3. Add Low-Credit Nudge if needed
        if user.paid_credits_remaining <= 0 and user.subscription_type != "monthly":
            upsell = (
                "\n\n💡 *Credits khatam ho gaye!*\n"
                "Naya plan lein aur analysis jaari rakhein:\n\n"
                "1️⃣ ₹99 — Basic Pack (3 Reports)\n"
                "2️⃣ ₹399 — Value Pack (15 Reports) 🔥\n"
                "3️⃣ ₹699 — Quarterly Pro (30 Reports) 🚀\n\n"
                "Type *\"plan\"* to buy!"
            )
            full_msg += upsell
        elif user.paid_credits_remaining <= 2 and user.subscription_type != "monthly":
            full_msg += f"\n\n💡 Sirf {user.paid_credits_remaining} credit bacha hai. Type *\"plan\"* for more!"
        
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
        sections = [
            ("📋 ELIGIBILITY CHECK", data.get("part2_eligibility", "")),
            ("⚠️ HIDDEN RISKS", data.get("part3_risks", "")),
            ("📊 BOQ & BID STRATEGY", data.get("part4_boq", "")),
            ("📝 ACTION PLAN", data.get("part5_action_plan", "")),
            ("💰 COST ESTIMATE", data.get("part6_cost_estimate", "")),
            ("💼 CASH FLOW", data.get("part9_cashflow", "")),
            ("👥 COMPETITOR INTELLIGENCE", data.get("part7_competitor", "")),
            ("🏗️ SUBCONTRACTORS", data.get("part8_subcontractors", "")),
            ("🏆 FINAL VERDICT", data.get("part10_recommendation", "")),
            ("💡 INSIDER TIP", data.get("part11_contractor_tip", "")),
        ]
        full_report = ""
        for title, content in sections:
            if content:
                full_report += f"\n{'━' * 30}\n*{title}*\n{'━' * 30}\n{content}\n"
        
        send_long_message(user.phone_number, full_report.strip())
        
    elif intent == "menu_8":
        # Download PDF
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "pdf_generating"))
        generate_and_send_pdf(user, data)
        
    elif intent == "menu_9":
        # Share & Earn
        referral_msg = (
            "🎁 *Dost ko bhi bhejo — aap dono ko free credit milega!*\n"
            f"👇 Yeh link COPY karke apne contractor friends ko WhatsApp pe bhejo:\n\n"
            f"https://wa.me/?text=Hey!%20Use%20TenderBot%20to%20analyse%20government%20tenders%20instantly.%20Click%20here%20to%20start:%20https://wa.me/919796700386?text=referral%20from%20%2B{user.phone_number.replace('+', '')}\n\n"
            "Jab woh is link se TenderBot join karega, aapko +1 free analysis milega! 🎉"
        )
        send_whatsapp_message(user.phone_number, referral_msg)
        
    elif intent in intent_map:
        # Single section
        section_key = intent_map[intent]
        section_text = data.get(section_key, get_string(user.language_preference, "section_not_available"))
        
        # Add a subtle "Share & Earn" nudge at the end of every detailed section
        referral_link = generate_referral_link(user.phone_number)
        nudge = f"\n\n🎁 *Tip:* Yeh link COPY karke dosto ko bhejo and get free credit!\nhttps://wa.me/919796700386?text=referral%20from%20+{user.phone_number.replace('+', '')}"
        
        send_long_message(user.phone_number, section_text + nudge)
        
    else:
        text_lower = text.lower()
        keyword_map = {
            "eligib": "part2_eligibility",
            "risk": "part3_risks",
            "boq": "part4_boq",
            "bid": "part4_boq",
            "strategy": "part4_boq",
            "action": "part5_action_plan",
            "document": "part5_action_plan",
            "cost": "part6_cost_estimate",
            "estimate": "part6_cost_estimate",
            "competitor": "part7_competitor",
            "subcontract": "part8_subcontractors",
            "cash": "part9_cashflow",
            "capital": "part9_cashflow",
            "verdict": "part10_recommendation",
            "recommend": "part10_recommendation",
            "summary": "part1_summary",
        }
        for keyword, part_key in keyword_map.items():
            if keyword in text_lower:
                content = data.get(part_key, get_string(user.language_preference, "section_not_available"))
                nudge = f"\n\n🎁 *Tip:* Yeh link COPY karke dosto ko bhejo and get free credit!\nhttps://wa.me/919796700386?text=referral%20from%20+{user.phone_number.replace('+', '')}"
                send_long_message(user.phone_number, content + nudge)
                return
                
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
