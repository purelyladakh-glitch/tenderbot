import os
import time
import json
import re
from typing import List, Optional
from twilio.rest import Client
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import User, Analysis, Payment, ContractorPreference, TenderAlertLog, ReminderLog
from payments import generate_payment_link
from analyzer import analyze_tender_document, is_pdf_too_large
from utils import download_twilio_media, detect_language, generate_pdf_report, PLANS, format_inr
from strings import get_string, build_menu
from portals import (
    detect_states_from_text, detect_work_types_from_text,
    detect_departments_from_text, parse_value_range,
    get_state_names, get_portals_for_states,
    format_ladakh_alert, format_free_alert, format_pack_alert, format_monthly_alert,
    PLAN_COMPARISON, SINGLE_PLAN_MSG, PACK_PLAN_MSG, MONTHLY_PLAN_MSG, STATES,
    search_portals_for_query, format_search_results,
)

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGING — with Interactive Buttons & Lists
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


def send_interactive_buttons(to_number: str, body: str, buttons: list, content_sid: str = None):
    """
    Send a WhatsApp message with Quick Reply buttons (up to 3).
    
    If a content_sid is provided (pre-approved Twilio Content Template),
    it uses that. Otherwise, falls back to a well-formatted text message
    with numbered options.
    
    buttons = [{"id": "btn_yes", "title": "Yes ✅"}, {"id": "btn_no", "title": "No ❌"}]
    """
    if content_sid:
        try:
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=to_number,
                content_sid=content_sid,
            )
            return
        except Exception as e:
            print(f"Interactive button send failed, falling back to text: {e}")

    # Fallback: formatted text with button labels
    btn_text = "\n".join([f"👉 *{b['title']}*" for b in buttons])
    fallback_msg = f"{body}\n\n{btn_text}"
    send_whatsapp_message(to_number, fallback_msg)


def send_interactive_list(to_number: str, body: str, button_text: str, sections: list, content_sid: str = None):
    """
    Send a WhatsApp List Message with scrollable options.
    
    If a content_sid is provided, uses the Twilio Content Template.
    Otherwise, falls back to a numbered text menu.
    
    sections = [
        {
            "title": "Analysis Menu",
            "rows": [
                {"id": "menu_1", "title": "Am I Eligible?", "description": "Qualification check"},
                {"id": "menu_2", "title": "Show Hidden Risks", "description": "Khatre & problems"},
            ]
        }
    ]
    """
    if content_sid:
        try:
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=to_number,
                content_sid=content_sid,
            )
            return
        except Exception as e:
            print(f"Interactive list send failed, falling back to text: {e}")

    # Fallback: well-formatted numbered menu for text-only interfaces
    menu_lines = [body, ""]
    for section in sections:
        if section.get("title"):
            menu_lines.append(f"*{section['title']}*")
        
        rows = section.get("rows", [])
        for i, row in enumerate(rows, 1):
            # Use unicode numbers for 1-10, fallback to standard numbers if > 10
            number_circle = [
                "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
            ]
            num_prefix = number_circle[i] if i < len(number_circle) else f"{i}."
            
            desc = f" — {row['description']}" if row.get("description") else ""
            menu_lines.append(f"{num_prefix} *{row['title']}*{desc}")
        menu_lines.append("")
        
    menu_lines.append(f"👉 *{button_text}*")
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

    # EXACT NUMBER MATCHES (The priority for our new numbered menus)
    if t_clean == "1": return "menu_1"
    if t_clean == "2": return "menu_2"
    if t_clean == "3": return "menu_3"
    if t_clean == "4": return "menu_4"
    if t_clean == "5": return "menu_5"
    if t_clean == "6": return "menu_6"
    if t_clean == "7": return "menu_7"
    if t_clean == "8": return "menu_8"

    # Forgiving matching arrays
    def matchesAny(keywords):
        return any(kw in t_clean for kw in keywords)

    # Analysis Menu Intends
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

    # Payment / plan intents
    if matchesAny(["plan", "price", "pricing", "upgrade", "subscrib", "kitne ka", "rate", "paisa", "payment"]): return "show_plans"
    if matchesAny(["99", "single", "ek", "one"]): return "buy_single"
    if matchesAny(["399", "pack", "five", "paanch", "5"]): return "buy_pack"
    if matchesAny(["799", "month", "unlimit", "mahina"]): return "buy_monthly"
    if matchesAny(["renew", "extend", "dobara", "phir"]): return "renew"

    # Preference intents
    if matchesAny(["pref", "alert", "tender bhejo", "dhundo", "set karo", "change location", "state", "portal"]): return "setup_preferences"

    # Alert control
    if matchesAny(["band", "stop", "pause", "rok", "busy"]): return "pause_alerts"
    if matchesAny(["shuru", "resume", "fir bhejo", "start", "ab bhejo"]): return "resume_alerts"

    # Balance / account
    if matchesAny(["credit", "balanc", "bache", "expire", "account", "mera plan"]): return "check_balance"

    # History
    if matchesAny(["histor", "past", "purana", "last", "meri"]): return "show_history"

    # Search
    if matchesAny(["search", "dhundo", "find", "naya tender"]): return "search"

    # Language change
    if matchesAny(["language", "bhasha", "lang", "english karo", "hindi karo", "marathi karo", "change language"]): return "change_language"

    # Restart
    if matchesAny(["restart", "reset", "naya shuru", "shuru se", "start over", "hi", "hello", "hey"]): return "restart"

    # Analyze (from alert)
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
    # ── Onboarding Capture (Referrals) ──
    # If a new user clicks a referral link, their first message will contain "Referral from"
    referrer_phone = None
    if "referral from" in text.lower():
        import re
        # Find the phone number at the end of the text string
        match = re.search(r'referral from\s*([+\d]+)', text, re.IGNORECASE)
        if match:
            referrer_phone = match.group(1).strip()
            # Clean up the text so intent detection works normally
            text = text.replace(match.group(0), "").strip()
            if not text: text = "hi"

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        lang = detect_language(text)
        user = User(
            phone_number=phone_number,
            language_preference=lang,
            conversation_state="new",
            referred_by=referrer_phone,  # Save the referrer here!
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    text_lower = text.lower().strip()

    # ── PDF at any point ──
    if media_url:
        handle_new_pdf(user, media_url, db, background_tasks)
        return
    
    # ── State Machine: Onboarding -> Language -> Location -> Work -> etc. ──
    state = user.conversation_state

    # === NEW: Language Selection ===
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
        else:
            # First time ever messaging the bot
            welcome_msg = get_string("hinglish", "welcome_new")
            lang_options = [
                {"id": "lang_en", "title": "English"},
                {"id": "lang_hi", "title": "Hindi (हिंदी)"},
                {"id": "lang_hinglish", "title": "Hinglish"},
                {"id": "lang_mr", "title": "Marathi (मराठी)"}
            ]
            sections = [{"title": "Select Language", "rows": [
                {"id": "en", "title": "1. English", "description": "English"},
                {"id": "hi", "title": "2. Hindi", "description": "हिंदी"},
                {"id": "hinglish", "title": "3. Hinglish", "description": "Default"},
                {"id": "mr", "title": "4. Marathi", "description": "मराठी"}
            ]}]
            send_interactive_list(user.phone_number, welcome_msg, "Select Language", sections)
            return
            
        # They picked a language, save and move to 'ready'
        user.conversation_state = "ready"
        db.commit()
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "lang_set_success"))
        return

    # Handle Alert setup states
    if state.startswith("awaiting_"):
        handle_preference_step(user, text, db)
        return

    # ── Analyzing — don't interrupt ──
    if state == "analyzing":
        send_whatsapp_message(user.phone_number,
            get_string(user.language_preference, "analyzing_wait"))
        return

    # ── Handling Payment Choice State ──
    if state == "awaiting_payment_choice":
        t_clean = text_lower.replace(".", "").replace(",", "").strip()
        if t_clean == "1": text_lower = "plan 1"
        if t_clean == "2": text_lower = "plan 2"
        if t_clean == "3": text_lower = "plan 3"
        user.conversation_state = "ready"
        db.commit()

    # ── Detect intent for all other states ──
    intent = detect_intent(text_lower)

    # ── Mapping Payment Choices from State ──
    if text_lower == "plan 1": intent = "buy_single"
    if text_lower == "plan 2": intent = "buy_pack"
    if text_lower == "plan 3": intent = "buy_monthly"

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
    if intent == "change_language":
        change_language_request(user, db)
        return

    # State-specific handling
    # The 'new' state is now handled above for language selection.
    # If user is in 'ready' or 'menu' state, and sends a PDF, it's handled by media_url check.
    # If user is in 'ready' or 'menu' state, and sends text, it's handled by detect_intent.

    if state in ("ready", "menu"):
        latest = db.query(Analysis).filter(
            Analysis.user_phone == user.phone_number
        ).order_by(Analysis.id.desc()).first()

        if latest:
            handle_menu(user, intent, text_lower, latest, db)
        else:
            send_whatsapp_message(user.phone_number,
                get_string(user.language_preference, "send_pdf_first"))
        return

    # Fallback for unrecognized input in any state not explicitly handled
    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "unrecognized"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WELCOME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_welcome(user: User):
    # This function is now primarily for the initial welcome after language selection,
    # or if a user explicitly restarts. The very first message for a new user
    # is handled by the 'new' state logic in handle_incoming_message.
    msg = get_string(user.language_preference, "welcome_message")
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREFERENCE SETUP — NATURAL CONVERSATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
                {"id": "loc_pnh", "title": "4. Pan-North (PB, HR, CH) 🚜", "description": "Punjab, Haryana, Chandigarh"},
                {"id": "loc_jk", "title": "5. J&K and Ladakh 🏔️", "description": "Paradise tenders"},
                {"id": "loc_up", "title": "6. Uttar Pradesh 🚂", "description": "Large state tenders"},
                {"id": "loc_ka", "title": "7. Karnataka 💻", "description": "South India focus"},
                {"id": "loc_gj", "title": "8. Gujarat 💎", "description": "Western region"},
            ]
        }
    ]
    send_interactive_list(user.phone_number, msg, "Select Location", sections)


def handle_preference_step(user: User, text: str, db: Session):
    state = user.conversation_state
    pref = get_or_create_preferences(db, user.phone_number)
    
    import re
    numbers = re.findall(r'\d+', text)

    if state == "awaiting_location":
        added_states = []
        if "1" in numbers: added_states.extend(list(STATES.keys()))
        if "2" in numbers: added_states.append("maharashtra")
        if "3" in numbers: added_states.append("delhi")
        if "4" in numbers: added_states.extend(["punjab", "haryana", "chandigarh"])
        if "5" in numbers: added_states.extend(["jammu kashmir", "ladakh"])
        if "6" in numbers: added_states.append("uttar pradesh")
        if "7" in numbers: added_states.append("karnataka")
        if "8" in numbers: added_states.append("gujarat")

        nlp_states = detect_states_from_text(text)
        states = list(set(added_states + nlp_states))

        if not states:
            send_whatsapp_message(user.phone_number,
                get_string(user.language_preference, "pref_location_error"))
            return

        pref.states_list = json.dumps(states)
        pref.updated_at = datetime.utcnow()
        db.commit()

        names = get_state_names(states)
        is_ladakh = "ladakh" in states

        ladakh_note = ""
        if is_ladakh:
            ladakh_note = get_string(user.language_preference, "pref_ladakh_note")

        user.conversation_state = "awaiting_work_type"
        db.commit()

        msg = get_string(user.language_preference, "pref_location_noted").format(names=names, ladakh_note=ladakh_note) + \
              "\n\n" + get_string(user.language_preference, "pref_work_type_prompt")
              
        sections = [
            {
                "title": "Common Work Types",
                "rows": [
                    {"id": "work_1", "title": "1. Road Construction 🛣️", "description": "Highways, link roads"},
                    {"id": "work_2", "title": "2. Building Construction 🏢", "description": "Civil, housing, infra"},
                    {"id": "work_3", "title": "3. Electrical Works ⚡", "description": "Substations, wiring, LT/HT"},
                    {"id": "work_4", "title": "4. Water Supply 💧", "description": "Pipes, Jal Jeevan, tanks"},
                    {"id": "work_5", "title": "5. Bridge Construction 🏗️", "description": "Flyovers, culverts"},
                    {"id": "work_6", "title": "6. Solar & Renewable ☀️", "description": "Panels, wind, green energy"},
                ]
            }
        ]
        send_interactive_list(user.phone_number, msg, "Select Work Type", sections)

    elif state == "awaiting_work_type":
        added_work = []
        if "1" in numbers: added_work.append("Road Construction")
        if "2" in numbers: added_work.append("Building Construction")
        if "3" in numbers: added_work.append("Electrical Works")
        if "4" in numbers: added_work.append("Water Supply")
        if "5" in numbers: added_work.append("Bridge Construction")
        if "6" in numbers: added_work.append("Solar & Renewable")
        
        nlp_work = detect_work_types_from_text(text)
        work_types = list(set(added_work + nlp_work))
        
        pref.work_types = json.dumps(work_types)
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_value_range"
        db.commit()

        msg = get_string(user.language_preference, "pref_work_type_noted").format(work_types=', '.join(work_types)) + \
              "\n\n" + get_string(user.language_preference, "pref_value_range_prompt")
              
        sections = [
            {
                "title": "Select Value Range",
                "rows": [
                    {"id": "val_1", "title": "1. Up to 50 Lakh", "description": "Small works"},
                    {"id": "val_2", "title": "2. 50 Lakh - 5 Crore", "description": "Medium projects"},
                    {"id": "val_3", "title": "3. 5 Crore - 20 Crore", "description": "Large infrastructure"},
                    {"id": "val_4", "title": "4. 20 Crore - 100 Crore", "description": "Major works"},
                    {"id": "val_5", "title": "5. All Amounts 🌐", "description": "No filter on value"},
                ]
            }
        ]
        send_interactive_list(user.phone_number, msg, "Select Range", sections)

    elif state == "awaiting_value_range":
        min_val, max_val = 0, 500000000
        
        if "1" in numbers: min_val, max_val = 0, 5000000
        elif "2" in numbers: min_val, max_val = 5000000, 50000000
        elif "3" in numbers: min_val, max_val = 50000000, 200000000
        elif "4" in numbers: min_val, max_val = 200000000, 1000000000
        elif "5" in numbers: min_val, max_val = 0, 10000000000
        else:
            min_val, max_val = parse_value_range(text)
        pref.min_value = min_val
        pref.max_value = max_val
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_departments"
        db.commit()

        min_disp = format_inr(min_val)
        max_disp = format_inr(max_val)

        msg = get_string(user.language_preference, "pref_value_range_noted").format(min_disp=min_disp, max_disp=max_disp) + \
              "\n\n" + get_string(user.language_preference, "pref_departments_prompt")
              
        sections = [
            {
                "title": "Select Departments",
                "rows": [
                    {"id": "dept_1", "title": "1. All Government 🏛️", "description": "Every department"},
                    {"id": "dept_2", "title": "2. PWD / CPWD / Municipal 🏢", "description": "Building & Civil"},
                    {"id": "dept_3", "title": "3. Highways (NHAI, BRO) 🛣️", "description": "Roads & Infra"},
                    {"id": "dept_4", "title": "4. Railways & Metro 🚂", "description": "Track & Station works"},
                    {"id": "dept_5", "title": "5. Water Board 💧", "description": "Sanitary & PHED"},
                    {"id": "dept_6", "title": "6. Defence / MES 🛡️", "description": "Military infra"},
                ]
            }
        ]
        send_interactive_list(user.phone_number, msg, "Select Departments", sections)

    elif state == "awaiting_departments":
        added_depts = []
        if "1" in numbers: added_depts.append("All Government")
        if "2" in numbers: added_depts.extend(["PWD", "CPWD", "Municipal"])
        if "3" in numbers: added_depts.extend(["NHAI", "BRO", "NHIDCL"])
        if "4" in numbers: added_depts.extend(["Railways", "Metro"])
        if "5" in numbers: added_depts.append("Water Board")
        if "6" in numbers: added_depts.append("MES")
        
        nlp_depts = detect_departments_from_text(text)
        depts = list(set(added_depts + nlp_depts))
        
        if not depts: depts = ["All Government"]
        
        pref.departments = json.dumps(depts)
        pref.updated_at = datetime.utcnow()
        user.conversation_state = "awaiting_alert_freq"
        db.commit()

        msg = get_string(user.language_preference, "pref_departments_noted").format(departments=', '.join(depts)) + \
              "\n\n" + get_string(user.language_preference, "pref_alert_freq_prompt")
              
        sections = [
            {
                "title": "Alert Frequency",
                "rows": [
                    {"id": "freq_1", "title": "1. Instant 🚀", "description": "As soon as tender is found"},
                    {"id": "freq_2", "title": "2. Daily Morning ☀️", "description": "8 AM digest"},
                    {"id": "freq_3", "title": "3. Weekly (Monday) 📅", "description": "Monday morning"},
                ]
            }
        ]
        send_interactive_list(user.phone_number, msg, "Select Frequency", sections)

    elif state == "awaiting_alert_freq":
        freq = "daily"
        t = text.lower()
        if "1" in numbers or any(kw in t for kw in ["turant", "instant", "immediately", "jab bhi", "real time"]):
            freq = "instant"
        elif "3" in numbers or any(kw in t for kw in ["weekly", "monday", "hafte", "hafta"]):
            freq = "weekly"
        elif "2" in numbers or any(kw in t for kw in ["subah", "daily", "roz", "8", "morning"]):
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

        freq_display = {
            "instant": get_string(user.language_preference, "freq_instant"),
            "daily": get_string(user.language_preference, "freq_daily"),
            "weekly": get_string(user.language_preference, "freq_weekly")
        }

        msg = get_string(user.language_preference, "pref_summary").format(
            state_names=state_names,
            work_types=', '.join(work_types),
            min_value=format_inr(pref.min_value),
            max_value=format_inr(pref.max_value),
            departments=', '.join(departments),
            alerts=freq_display.get(freq, freq),
            num_portals=len(portals)
        )

        send_whatsapp_message(user.phone_number, msg)

def change_language_request(user: User, db: Session):
    user.conversation_state = "new"  # Loop them back to the language picker
    db.commit()
    msg = get_string(user.language_preference, "lang_menu")
    sections = [{"title": "Select Language", "rows": [
        {"id": "en", "title": "1. English", "description": "English"},
        {"id": "hi", "title": "2. Hindi", "description": "हिंदी"},
        {"id": "hinglish", "title": "3. Hinglish", "description": "Default"},
        {"id": "mr", "title": "4. Marathi", "description": "मराठी"}
    ]}]
    send_interactive_list(user.phone_number, msg, "Select Language", sections)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLANS & PAYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def show_plans(user: User, db: Session):
    user.conversation_state = "awaiting_payment_choice"
    db.commit()
    msg = get_string(user.language_preference, "plan_options")
    sections = [
        {
            "title": "Available Plans",
            "rows": [
                {"id": "buy_1", "title": "1. Single Analysis", "description": "₹99 - 1 Report"},
                {"id": "buy_2", "title": "2. 5 Report Pack", "description": "₹399 - 60 Days"},
                {"id": "buy_3", "title": "3. Monthly Pro", "description": "₹799 - Unlimited Alerts"},
            ]
        }
    ]
    send_interactive_list(user.phone_number, msg, "View Plans", sections)


def handle_buy(user: User, intent: str, db: Session):
    # Determine plan type from intent
    plan_type = intent.replace("buy_", "")
    if plan_type not in PLANS:
        plan_type = "single"
        
    plan = PLANS[plan_type]
    amount = plan["price"]
    desc = plan["description"]

    # Show plan details
    plan_msgs = {
        "buy_single": get_string(user.language_preference, "single_plan_msg"),
        "buy_pack": get_string(user.language_preference, "pack_plan_msg"),
        "buy_monthly": get_string(user.language_preference, "monthly_plan_msg")
    }
    send_whatsapp_message(user.phone_number, plan_msgs.get(intent, get_string(user.language_preference, "single_plan_msg")))

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
        get_string(user.language_preference, "payment_link_message").format(link=link))


def show_balance(user: User):
    plan_names = {
        "free": get_string(user.language_preference, "plan_free"),
        "single": get_string(user.language_preference, "plan_single"),
        "pack": get_string(user.language_preference, "plan_pack"),
        "monthly": get_string(user.language_preference, "plan_monthly")
    }
    plan_name = plan_names.get(user.subscription_type, get_string(user.language_preference, "plan_free"))

    expiry = ""
    if user.subscription_expiry:
        days_left = (user.subscription_expiry - datetime.utcnow()).days
        expiry = get_string(user.language_preference, "balance_expiry").format(
            expiry_date=user.subscription_expiry.strftime('%d %b %Y'), days_left=days_left)

    msg = get_string(user.language_preference, "balance_details").format(
        plan_name=plan_name,
        credits=user.paid_credits_remaining,
        free_analysis_status=get_string(user.language_preference, "used") if user.free_analyses_used >= 1 else get_string(user.language_preference, "available"),
        total_analyses=user.total_analyses_done,
        expiry_info=expiry
    )

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
        get_string(user.language_preference, "alerts_paused"))


def resume_alerts(user: User, db: Session):
    pref = get_or_create_preferences(db, user.phone_number)
    pref.alerts_paused = False
    pref.pause_until = None
    db.commit()
    send_whatsapp_message(user.phone_number,
        get_string(user.language_preference, "alerts_resumed"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def show_history(user: User, db: Session):
    analyses = db.query(Analysis).filter(
        Analysis.user_phone == user.phone_number
    ).order_by(Analysis.id.desc()).limit(5).all()

    if not analyses:
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "no_past_analysis"))
        return

    msg = get_string(user.language_preference, "recent_analyses_header") + "\n\n"
    for i, a in enumerate(analyses, 1):
        msg += f"{i}. {a.tender_summary} — {a.created_at.strftime('%d %b %Y')}\n"
    msg += get_string(user.language_preference, "total_analyses_done").format(total=user.total_analyses_done)
    send_whatsapp_message(user.phone_number, msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEARCH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_search(user: User, text: str, db: Session):
    """Phase 1 search: matches keywords to relevant portal URLs."""
    results = search_portals_for_query(text)
    msg = format_search_results(results, user.language_preference)
    send_whatsapp_message(user.phone_number, msg)

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
        get_string(user.language_preference, "pdf_received_analyzing"))

    time.sleep(1)
    send_whatsapp_message(user.phone_number,
        get_string(user.language_preference, "documents_checklist_prompt"))

    background_tasks.add_task(process_pdf_background, user.phone_number, media_url)


def request_payment(user: User, db: Session):
    msg = get_string(user.language_preference, "free_analysis_used") + "\n\n"

    # Show comparison and generate ₹99 link as default
    payment = Payment(user_phone=user.phone_number, amount=99, plan_type="single", status="created")
    db.add(payment)
    db.commit()
    db.refresh(payment)

    link_99 = generate_payment_link(99, user.phone_number, f"PAY_{payment.id}", "1 Tender Analysis")
    payment.razorpay_order_id = f"PAY_{payment.id}"
    db.commit()

    msg += get_string(user.language_preference, "payment_options_prompt").format(link_99=link_99)

    user.conversation_state = "awaiting_payment_choice"
    db.commit()
    
    sections = [
        {
            "title": "Upgrade Now",
            "rows": [
                {"id": "pay_1", "title": "₹99 - 1 Analysis", "description": "Pay instantly"},
                {"id": "pay_2", "title": "₹399 - 5 Pack", "description": "Best value for small contractors"},
                {"id": "pay_3", "title": "₹799 - Monthly Pro", "description": "Auto-analysis & unlimited alerts"},
            ]
        }
    ]
    send_interactive_list(user.phone_number, msg, "Select Plan", sections)


def process_pdf_background(phone_number: str, media_url: str):
    from database import SessionLocal
    db = SessionLocal()
    user = db.query(User).filter(User.phone_number == phone_number).first()

    try:
        pdf_path = download_twilio_media(media_url)

        if is_pdf_too_large(pdf_path):
            send_whatsapp_message(phone_number,
                get_string(user.language_preference, "pdf_too_large"))
            user.conversation_state = "ready"
            db.commit()
            return

        send_whatsapp_message(phone_number, get_string(user.language_preference, "still_analyzing"))

        analysis_json = analyze_tender_document(pdf_path, user.language_preference)

        if "error" in analysis_json:
            if analysis_json["error"] == "OCR_FAILED_TINY":
                send_whatsapp_message(phone_number, get_string(user.language_preference, "ocr_failed_manual_download"))
                user.conversation_state = "ready"
                db.commit()
                return

        # Deduct credit
        # Increment usage AFTER successful analysis
        if user.subscription_type == "free" and user.paid_credits_remaining == 0:
            user.free_analyses_used += 1
        elif user.paid_credits_remaining > 0:
            user.paid_credits_remaining -= 1
        elif user.subscription_type == "monthly" and user.total_analyses_done < 30:
            # Monthly users have a soft limit, but we don't "deduct" a credit in the same way
            pass # No explicit credit deduction for monthly, just track total_analyses_done

        user.total_analyses_done += 1
        user.conversation_state = "menu"
        db.commit() # Commit user state and credit changes here

        # ── Viral Referral Credit Award System (Anti-Abuse Checked) ──
        # Award credit ONLY IF this is their very first successful analysis
        if user.total_analyses_done == 1 and user.referred_by:
            # Prevent self-referrals
            if user.referred_by != user.phone_number:
                referrer = db.query(User).filter(User.phone_number == user.referred_by).first()
                if referrer:
                    referrer.paid_credits_remaining += 1
                    db.commit()
                    # Notify the referrer!
                    reward_msg = get_string(user.language_preference, "referral_reward")
                    send_whatsapp_message(referrer.phone_number, reward_msg)

        # Extract deadline for reminders
        deadline_raw = analysis_json.get("deadline_date", "N/A")
        deadline_obj = None
        try:
            # Try to parse a date out of Gemini's response
            if deadline_raw and deadline_raw != "N/A":
                # Assuming Gemini gives ISO-ish or simple dates, we'll try basic parsing
                # For now, let's look for DD-MM-YYYY or YYYY-MM-DD
                match = re.search(r"(\d{4}-\d{2}-\d{2})", deadline_raw)
                if not match:
                    match = re.search(r"(\d{2}-\d{2}-\d{4})", deadline_raw)
                if match:
                    from datetime import datetime
                    dstr = match.group(1)
                    if "-" in dstr:
                        if dstr.index("-") == 4: # YYYY-MM-DD
                            deadline_obj = datetime.strptime(dstr, "%Y-%m-%d")
                        else: # DD-MM-YYYY
                            deadline_obj = datetime.strptime(dstr, "%d-%m-%d-%Y")
        except Exception as e:
            print(f"Deadline parsing failed: {e}")

        new_analysis = Analysis(
            user_phone=user.phone_number,
            tender_summary=analysis_json.get("department", "Tender"),
            analysis_result=json.dumps(analysis_json),
            deadline_date=deadline_obj
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
        verdict_text = get_string(user.language_preference, "verdict_header").format(
            department=analysis_json.get('department', 'Dept'),
            work=analysis_json.get('work_description', 'Work'),
            value=analysis_json.get('value', 'N/A'),
            deadline=analysis_json.get('deadline_date', 'N/A'),
            days=analysis_json.get('days_remaining', 'X'),
            verdict=analysis_json.get('quick_verdict_recommendation', 'N/A'),
            score=analysis_json.get('quick_verdict_score', 'N/A'),
            critical=analysis_json.get('critical_risks_count', '0'),
            warnings=analysis_json.get('warnings_count', '0'),
            bid=analysis_json.get('recommended_bid', 'N/A'),
            profit=analysis_json.get('estimated_profit', 'N/A'),
        )
        
        sections = [
            {
                "title": "Explore Analysis",
                "rows": [
                    {"id": "menu_1", "title": "Am I Eligible?", "description": "Check qualification info"},
                    {"id": "menu_2", "title": "Show Hidden Risks", "description": "Critical issues & warnings"},
                    {"id": "menu_3", "title": "Get Bid Strategy", "description": "BOQ Rates & Bid amount"},
                    {"id": "menu_4", "title": "Action & Documents", "description": "Required checklist"},
                    {"id": "menu_5", "title": "Cash Flow Check", "description": "Working capital needs"},
                    {"id": "menu_6", "title": "View Profit & Cost", "description": "Full breakdown"},
                    {"id": "menu_7", "title": "Full Report", "description": "Everything in one go"},
                    {"id": "menu_8", "title": "Download PDF", "description": "Save for later"},
                    {"id": "menu_9", "title": "Share & Earn", "description": "Refer a friend for +1 credit"},
                ]
            }
        ]
        send_interactive_list(phone_number, verdict_text, "View Analysis Menu", sections)

        # ── Upgrade nudge for free users ──
        if user.subscription_type == "free" and user.free_analyses_used >= 1:
            time.sleep(3)
            send_whatsapp_message(phone_number,
                get_string(user.language_preference, "upgrade_nudge_post_analysis"))

        os.remove(pdf_path)

    except Exception as e:
        send_whatsapp_message(phone_number,
            get_string(user.language_preference if user else "hinglish", "technical_error"))
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
            get_string(user.language_preference, "analysis_parse_error"))
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

    if intent == "menu_9":
        send_share_message(user, db)
        return

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
        get_string(user.language_preference, "menu_fallback"))

def send_share_message(user: User, db: Session):
    """Generates the viral referral loop message and link."""
    # Use the official Twilio WhatsApp number if RAILWAY_URL isn't strictly needed for wa.me
    # but we need the raw number without 'whatsapp:' prefix.
    bot_number = TWILIO_WHATSAPP_NUMBER.replace("whatsapp:", "")
    
    # URL Encode the payload
    import urllib.parse
    payload = f"Hi TenderBot! Referral from {user.phone_number}"
    encoded_payload = urllib.parse.quote(payload)
    
    wa_link = f"https://wa.me/{bot_number}?text={encoded_payload}"
    
    explanation = (
        "🎁 *Want FREE Paid Analysis credits?*\n\n"
        "Share TenderBot with your contractor friends! "
        "Jaise hi aapka dost apna pehla PDF analyze karega, "
        "aapke account mein *+1 Free Analysis* add ho jayega!\n\n"
        "👇 *Neeche wale message ko copy karke WhatsApp Groups mein forward karo:* 👇"
    )
    send_whatsapp_message(user.phone_number, explanation)
    
    time.sleep(2)
    
    forwardable_msg = (
        "🏗️ *Bhai, yeh AI TenderBot try karo!*\n\n"
        "Government tenders ka PDF isko bhejo, aur yeh 3 minute mein poora details nikal deta hai:\n"
        "✅ Eligibility check\n"
        "✅ BOQ Rates & Profit Estimate\n"
        "✅ Hidden Risks & Deadlines\n\n"
        "Pehla analysis bilkul *FREE* hai! Yahan click karke message bhejo:\n"
        f"👉 {wa_link}"
    )
    send_whatsapp_message(user.phone_number, forwardable_msg)


def generate_and_send_pdf(user: User, data: dict):
    send_whatsapp_message(user.phone_number, get_string(user.language_preference, "pdf_generating"))
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
                get_string(user.language_preference, "pdf_ready"), media_url=public_url)
        else:
            send_whatsapp_message(user.phone_number,
                get_string(user.language_preference, "pdf_link_not_set"))
    except Exception as e:
        print(f"Error serving PDF: {e}")
        send_whatsapp_message(user.phone_number, get_string(user.language_preference, "pdf_attach_error"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAYMENT WEBHOOK HANDLER (called from main.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_payment_success(user: User, amount: int, plan_type: str, db: Session):
    """Called by main.py webhook when Razorpay confirms payment."""
    # Ensure plan_type is valid
    if plan_type not in PLANS:
        # Fallback detection by amount if plan_type is corrupted
        plan_type = "single"
        for p_key, p_val in PLANS.items():
            if amount == p_val["price"]:
                plan_type = p_key
                break
    
    plan_config = PLANS[plan_type]
    
    user.subscription_type = plan_type
    user.alert_tier = plan_config["alert_tier"]
    user.paid_credits_remaining += plan_config["credits"]
    
    if plan_config["expiry_days"]:
        user.subscription_expiry = datetime.utcnow() + timedelta(days=plan_config["expiry_days"])
    
    # Success message based on plan type
    success_keys = {
        "single": "payment_single_success",
        "pack": "payment_pack_success",
        "monthly": "payment_monthly_success"
    }
    key = success_keys.get(plan_type, "payment_generic_success")
    unlock_msg = get_string(user.language_preference, key)

    db.commit()
    send_whatsapp_message(user.phone_number, unlock_msg)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE NUDGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_upgrade_nudge(user: User, db: Session):
    """Called periodically or after certain triggers."""
    if user.subscription_type == "free" and user.free_analyses_used >= 1:
        msg = get_string(user.language_preference, "upgrade_nudge_free")
        buttons = [
            {"id": "buy_pack", "title": "₹399 - 5 Pack 🔥"},
            {"id": "show_plans", "title": "View All Plans 💰"}
        ]
        send_interactive_buttons(user.phone_number, msg, buttons)

    elif user.subscription_type == "pack" and user.paid_credits_remaining <= 1:
        msg = get_string(user.language_preference, "upgrade_nudge_low_credits").format(credits=user.paid_credits_remaining)
        buttons = [
            {"id": "buy_pack", "title": "Renew ₹399 ♻️"},
            {"id": "buy_monthly", "title": "Upgrade ₹799 🚀"}
        ]
        send_interactive_buttons(user.phone_number, msg, buttons)

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
    
    # Savings calculation
    consultant_savings = analysis_count * 10000
    plan_cost = PLANS.get("monthly", {}).get("price", 799)
    total_savings = consultant_savings - plan_cost
    
    days_left = 30
    if user.subscription_expiry:
        days_left = max(0, (user.subscription_expiry - datetime.utcnow()).days)

    msg = get_string(user.language_preference, "monthly_report_template").format(
        analysis_count=analysis_count,
        alert_count=alert_count,
        free_alert_analyses=free_alert_analyses,
        savings=consultant_savings,
        paid=plan_cost,
        total_savings=total_savings,
        days_left=days_left
    )

    return msg

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Removed format_inr from bot.py as it is now in utils.py
