"""
TenderBot — Background Scraper Worker
Runs independently of the FastAPI web server.
Pulls live tenders from government portals, matches them against
ContractorPreference records, and sends WhatsApp alerts via Meta Cloud API.

Deploy on Railway as a separate "Worker" service:
  python scraper.py
"""

import os
import re
import time
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import urllib3
from datetime import datetime
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from database import SessionLocal, Base, engine, ContractorPreference, TenderRecord, TenderAlertLog, User, Analysis, ReminderLog
from bot import send_whatsapp_message
from strings import get_string
from analyzer import quick_tender_summary

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTAL REGISTRY
# Each entry: domain, state label, and optional custom parser
# All NICGEP-standard portals share the same HTML table structure
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCRAPE_PORTALS = [
    # --- Priority: Ladakh & J&K ---
    {"domain": "ladakhtenders.gov.in", "state": "Ladakh",            "type": "nicgep"},
    {"domain": "jktenders.gov.in",     "state": "Jammu & Kashmir",   "type": "nicgep"},
    # --- Central Government ---
    {"domain": "eprocure.gov.in",      "state": "All India",         "type": "cppp"},
    # --- Key State Portals (NICGEP framework) ---
    {"domain": "etender.up.nic.in",    "state": "Uttar Pradesh",     "type": "nicgep"},
    {"domain": "haryanaeprocurement.gov.in", "state": "Haryana",     "type": "nicgep"},
    {"domain": "eproc.rajasthan.gov.in", "state": "Rajasthan",       "type": "nicgep"},
    {"domain": "hptenders.gov.in",     "state": "Himachal Pradesh",  "type": "nicgep"},
    {"domain": "uktenders.gov.in",     "state": "Uttarakhand",       "type": "nicgep"},
    {"domain": "eproc.punjab.gov.in",  "state": "Punjab",            "type": "nicgep"},
    {"domain": "mahatenders.gov.in",   "state": "Maharashtra",       "type": "nicgep"},
    {"domain": "mptenders.gov.in",     "state": "Madhya Pradesh",    "type": "nicgep"},
    {"domain": "tntenders.gov.in",     "state": "Tamil Nadu",        "type": "nicgep"},
    {"domain": "etenders.kerala.gov.in","state": "Kerala",           "type": "nicgep"},
    {"domain": "assamtenders.gov.in",  "state": "Assam",             "type": "nicgep"},
    {"domain": "eproc.cgstate.gov.in", "state": "Chhattisgarh",      "type": "nicgep"},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NICGEP HTML PARSER
# Most Indian state tender portals use the NIC GePNIC
# framework which renders an HTML table of active tenders.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def scrape_nicgep_portal(domain: str, state_label: str, max_tenders: int = 20) -> list[dict]:
    """
    Scrapes the 'Latest Active Tenders' page from any NICGEP-based portal.
    Returns a list of tender dicts ready for DB insertion.
    """
    url = f"https://{domain}/nicgep/app?page=FrontEndLatestActiveTenders&service=page"
    print(f"  → Fetching {domain} ...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, verify=False, timeout=20, headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f"  ✗ HTTP error for {domain}: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    # NICGEP tables usually have id="table" or class="list_table"
    table = soup.find("table", {"id": "table"})
    if not table:
        table = soup.find("table", class_="list_table")
    if not table:
        print(f"  ✗ No tender table found on {domain}")
        return []

    rows = table.find_all("tr")[1:max_tenders + 1]  # Skip header row
    results = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        # Standard NICGEP column layout:
        # 0: S.No
        # 1: e-Published Date
        # 2: Closing Date / Bid Submission Date
        # 3: Opening Date
        # 4: Title / Ref No / Tender ID
        # 5: Organisation Chain

        # --- Extract Title ---
        title_td = cols[4]
        title_link = title_td.find("a")
        title = title_link.text.strip() if title_link else title_td.text.strip()
        title = title.split("[")[0].strip()  # Remove [Click to view...] suffixes
        if not title or len(title) < 10:
            continue

        # --- Extract Tender ID ---
        tender_id = None
        id_text = title_td.text
        
        # Regex for common patterns
        id_match = re.search(r"Tender\s*ID\s*[:\-]\s*([A-Z0-9_/.\-]+)", id_text, re.IGNORECASE)
        if id_match:
            tender_id = id_match.group(1).strip()
            
        if not tender_id:
            ref_match = re.search(r"Ref\.?\s*No\.?[\s\-]*[:\-]*\s*([A-Z0-9_/.\-]+)", id_text, re.IGNORECASE)
            if ref_match:
                tender_id = ref_match.group(1).strip()
        
        # Try finding in the link URL (nicgep specific)
        if not tender_id and title_link and title_link.get("href"):
            href = title_link.get("href")
            # Usually href contains something like tenderId=123
            url_id_match = re.search(r"tender(?:Id|ID)=([A-Z0-9_\-]+)", href, re.IGNORECASE)
            if url_id_match:
                tender_id = url_id_match.group(1).strip()

        if not tender_id:
            # Hash-based fallback if all else fails
            import hashlib
            h = hashlib.md5(title.encode()).hexdigest()[:8]
            tender_id = f"fallback_{h}"

        # Clean ID (remove trailing dots, brackets)
        tender_id = tender_id.rstrip(".]")

        # --- Organisation Chain ---
        org_chain = cols[5].text.strip()
        org_chain = " | ".join([line.strip() for line in org_chain.split("\n") if line.strip()])

        # --- Dates ---
        closing_raw = cols[2].text.strip() if len(cols) > 2 else ""

        # --- Build tender record ---
        # We prefix the external_id with domain to avoid collisions across portals
        ext_id = f"{state_label}_{tender_id}"

        results.append({
            "external_id": ext_id,
            "title": title[:500],  # Truncate very long titles
            "department": org_chain[:500],
            "state": state_label,
            "value_inr": 0,  # Value requires clicking into detail page; keyword-match instead
            "url": f"https://{domain}/nicgep/app?page=FrontEndLatestActiveTenders&service=page",
            "closing_date_raw": closing_raw,
        })

    print(f"  ✓ Found {len(results)} tenders from {domain}")
    return results


def scrape_cppp_portal(max_tenders: int = 20) -> list[dict]:
    """
    Scrapes the Central Public Procurement Portal (CPPP / eprocure.gov.in).
    CPPP uses a slightly different URL structure but same NICGEP engine.
    """
    url = "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"
    print(f"  → Fetching CPPP (eprocure.gov.in) ...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, verify=False, timeout=20, headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f"  ✗ HTTP error for CPPP: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table")
    if not table:
        print(f"  ✗ No tender table found on CPPP")
        return []

    rows = table.find_all("tr")[1:max_tenders + 1]
    results = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        title = cols[1].text.strip() if len(cols) > 1 else ""
        org = cols[2].text.strip() if len(cols) > 2 else ""
        tender_id = cols[0].text.strip() if len(cols) > 0 else f"CPPP_{hash(title) % 100000}"

        if not title or len(title) < 10:
            continue

        results.append({
            "external_id": f"CPPP_{tender_id}",
            "title": title[:500],
            "department": org[:500],
            "state": "All India",
            "value_inr": 0,
            "url": "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"
        })

    print(f"  ✓ Found {len(results)} tenders from CPPP")
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FETCH ALL PORTALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_all_portals() -> list[dict]:
    """Scrapes all registered portals and returns combined tender list."""
    all_tenders = []

    for portal in SCRAPE_PORTALS:
        try:
            if portal["type"] == "cppp":
                tenders = scrape_cppp_portal()
            else:
                tenders = scrape_nicgep_portal(portal["domain"], portal["state"])
            all_tenders.extend(tenders)
        except Exception as e:
            print(f"  ✗ Failed to scrape {portal['domain']}: {e}")

        # Be polite — wait between portal requests to avoid rate limits
        time.sleep(2)

    print(f"\n📊 Total tenders fetched: {len(all_tenders)}")
    return all_tenders


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MATCHING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def does_tender_match_pref(tender: dict, pref: ContractorPreference) -> bool:
    """Checks if a scraped tender matches a user's saved preferences."""

    # 1. STATE MATCH
    user_states = json.loads(pref.states_list) if pref.states_list else []
    if user_states:
        # Normalise for comparison
        user_state_names = [s.lower().strip() for s in user_states]
        tender_state = tender["state"].lower().strip()

        # "All India" matches everything
        if "all india" not in user_state_names and tender_state != "all india":
            if tender_state not in user_state_names:
                return False

    # 2. VALUE MATCH (only if tender has a known value > 0)
    if tender["value_inr"] > 0:
        if not (pref.min_value <= tender["value_inr"] <= pref.max_value):
            return False

    # 3. WORK TYPE keyword match (fuzzy — check if any work type keyword appears in title)
    user_work_types = json.loads(pref.work_types) if pref.work_types else []
    if user_work_types:
        title_lower = tender["title"].lower()
        dept_lower = tender["department"].lower()
        combined = title_lower + " " + dept_lower

        work_keywords = {
            "Roads & Highways": ["road", "highway", "nhai", "bro", "nhidcl", "pavement", "bituminous", "tar", "nh-", "sh-"],
            "Building / Civil": ["building", "civil", "construction", "housing", "pwd", "cpwd", "residential", "commercial", "school", "hospital"],
            "Electrical": ["electrical", "wiring", "transformer", "substation", "power", "electrification"],
            "Water Supply": ["water", "pipeline", "sewage", "drainage", "jal", "plumbing", "borewell", "tank"],
            "Bridges & Flyovers": ["bridge", "flyover", "overpass", "culvert", "rcc bridge", "steel bridge"],
            "Solar & Renewable": ["solar", "renewable", "photovoltaic", "wind", "biomass", "seci"],
        }

        match_found = False
        for wt in user_work_types:
            keywords = work_keywords.get(wt, [wt.lower()])
            if any(kw in combined for kw in keywords):
                match_found = True
                break

        if not match_found:
            return False

    # 4. DEPARTMENT keyword match (optional — only filter if user specified departments)
    user_depts = json.loads(pref.departments) if pref.departments else []
    if user_depts:
        dept_lower = tender["department"].lower()
        dept_keywords = {
            "All Gov": [],  # matches everything
            "PWD / CPWD / Municipal": ["pwd", "cpwd", "municipal", "mcd", "nagar"],
            "Highways (NHAI, BRO, NHIDCL)": ["nhai", "bro", "nhidcl", "highway", "border road"],
            "Railways & Metro": ["railway", "metro", "ircon", "rites", "dmrc"],
            "Jal Board / Water Depts": ["jal", "water", "phed", "sewage"],
            "Defence / MES": ["defence", "mes", "military", "army", "navy", "air force", "gref"],
        }

        dept_match = False
        for ud in user_depts:
            if ud == "All Gov":
                dept_match = True
                break
            keywords = dept_keywords.get(ud, [ud.lower()])
            if any(kw in dept_lower for kw in keywords):
                dept_match = True
                break

        if not dept_match:
            return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN JOB: SCRAPE → MATCH → ALERT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def match_and_alert():
    """
    The core scheduled job:
    1. Scrape all registered portals
    2. Store new tenders in DB (skip duplicates)
    3. Match each new tender against user preferences
    4. Send WhatsApp alerts
    """
    print(f"\n{'='*60}")
    print(f"🔄 Scraper Run @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    db: Session = SessionLocal()
    try:
        all_tenders = fetch_all_portals()
        new_count = 0
        alert_count = 0

        for t in all_tenders:
            # Skip if we already have this tender
            existing = db.query(TenderRecord).filter(
                TenderRecord.external_id == t["external_id"]
            ).first()
            if existing:
                continue

            # Save new tender
            record = TenderRecord(
                external_id=t["external_id"],
                title=t["title"],
                department=t["department"],
                state=t["state"],
                value_inr=t["value_inr"],
                url=t["url"],
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            new_count += 1

            # --- MATCH against all active user preferences ---
            active_prefs = db.query(ContractorPreference).filter(
                ContractorPreference.alerts_paused == False
            ).all()

            for pref in active_prefs:
                if not does_tender_match_pref(t, pref):
                    continue

                # Check if we already alerted this user for this tender
                already_alerted = db.query(TenderAlertLog).filter(
                    TenderAlertLog.user_phone == pref.phone_number,
                    TenderAlertLog.tender_id == t["external_id"]
                ).first()
                if already_alerted:
                    continue

                user = db.query(User).filter(
                    User.phone_number == pref.phone_number
                ).first()
                if not user:
                    continue

                from portals import format_free_alert, format_pack_alert, format_monthly_alert, format_ladakh_alert
                
                tender_data = {
                    "department": record.department,
                    "work_description": record.title,
                    "location": record.state,
                    "value": record.value_inr,
                    "deadline_date": record.closing_date_raw,
                    "days_remaining": "Coming Soon"
                }

                # Tiered Alert Formatting + Ladakh Focus
                is_ladakh = any(kw in record.state.lower() for kw in ["ladakh", "leh", "kargil"])
                tier = user.alert_tier or "free"
                
                if is_ladakh:
                    alert_msg = format_ladakh_alert(tender_data, user.paid_credits_remaining)
                elif tier == "full":
                    alert_msg = format_monthly_alert(tender_data)
                elif tier == "basic":
                    alert_msg = format_pack_alert(tender_data, user.paid_credits_remaining)
                else:
                    alert_msg = format_free_alert(tender_data)
                
                # Append URL directly for immediate access
                alert_msg += f"\n\n🔗 *Link:* {record.url}"

                send_whatsapp_message(user.phone_number, alert_msg)
                alert_count += 1

                # ── ₹799 MONTHLY PRO: Auto Gemini Analysis ──
                # Monthly Pro users get free AI analysis with every matching alert
                if user.alert_tier == "full" and user.subscription_type == "monthly":
                    try:
                        ai_summary = quick_tender_summary(
                            title=record.title,
                            department=record.department,
                            state=record.state,
                            value=record.value_inr,
                        )
                        if ai_summary:
                            send_whatsapp_message(user.phone_number,
                                f"🤖 *AI Quick Analysis (Pro Benefit):*\n\n{ai_summary}")
                            print(f"  → Sent auto-analysis for {record.external_id} to {user.phone_number}")
                    except Exception as ae:
                        print(f"  ✗ Auto-analysis failed for {record.external_id}: {ae}")

                # Log the alert and commit
                try:
                    log = TenderAlertLog(
                        user_phone=pref.phone_number,
                        tender_id=t["external_id"],
                        alert_type=user.alert_tier or "free",
                    )
                    db.add(log)
                    db.commit()
                except Exception as db_err:
                    db.rollback()
                    print(f"  ✗ Failed to log alert for {pref.phone_number}: {db_err}")

        print(f"\n✅ Run complete: {new_count} new tenders, {alert_count} alerts sent.")

    except Exception as e:
        print(f"❌ Scraper error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEADLINE REMINDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_deadlines_and_remind():
    """
    Scans all Analysis records for upcoming deadlines.
    Sends reminders at 7d, 2d, 1d, and 0d intervals.
    Run this daily at 7:00 AM.
    """
    print("\n⏰ Checking tender deadlines for reminders...")
    from database import SessionLocal, acquire_daemon_lock
    db = SessionLocal()
    if not acquire_daemon_lock(db, "deadline_reminders", 23):
        print("🔒 Deadline Reminder thread locked by another node.")
        db.close()
        return
    try:
        now = datetime.utcnow()
        today = now.date()

        # Get all analyses that have a deadline in the future or today
        active_analyses = db.query(Analysis).filter(
            Analysis.deadline_date >= today
        ).all()

        remind_count = 0
        for analysis in active_analyses:
            user = db.query(User).filter(User.phone_number == analysis.user_phone).first()
            if not user:
                continue

            days_left = (analysis.deadline_date.date() - today).days
            
            # Determine which reminder trigger to use
            trigger = None
            if days_left == 7: trigger = "7d"
            elif days_left == 2: trigger = "2d"
            elif days_left == 1: trigger = "1d"
            elif days_left == 0: trigger = "0d"

            if not trigger:
                continue

            # Check if already sent
            log = db.query(ReminderLog).filter(
                ReminderLog.analysis_id == analysis.id,
                ReminderLog.user_phone == user.phone_number
            ).first()

            if not log:
                log = ReminderLog(
                    user_phone=user.phone_number,
                    tender_id=str(analysis.id), # Fallback ID
                    analysis_id=analysis.id,
                    deadline=analysis.deadline_date,
                    reminders_sent="[]"
                )
                db.add(log)
                db.commit()
                db.refresh(log)

            sent_list = json.loads(log.reminders_sent)
            if trigger in sent_list:
                continue

            # Send reminder
            lang = user.language_preference
            tender_data = {}
            try:
                tender_data = json.loads(analysis.analysis_result or "{}")
            except: pass

            tender_name = tender_data.get("work_description", analysis.tender_summary or "Tender")
            dept = tender_data.get("department", "Govt Dept")
            deadline_str = analysis.deadline_date.strftime("%d-%m-%Y")
            deadline_time = tender_data.get("deadline_time", "5:00 PM")

            msg_key = f"reminder_{trigger}"
            msg_tmpl = get_string(lang, msg_key)
            
            if trigger in ["1d", "0d"]:
                msg = msg_tmpl.format(name=tender_name, time=deadline_time)
            elif trigger == "2d":
                msg = msg_tmpl.format(name=f"{tender_name} ({dept})", deadline=f"{deadline_str} {deadline_time}")
            else: # 7d
                msg = msg_tmpl.format(name=f"{tender_name} ({dept})", deadline=f"{deadline_str} {deadline_time}", short_name=tender_name[:20])

            send_whatsapp_message(user.phone_number, msg)
            
            # Update log
            sent_list.append(trigger)
            log.reminders_sent = json.dumps(sent_list)
            db.commit()
            remind_count += 1
            print(f"  → Sent {trigger} reminder to {user.phone_number} for {tender_name}")

        print(f"✅ Deadline check complete: {remind_count} reminders sent.")

    except Exception as e:
        print(f"❌ Reminder job error: {e}")
    finally:
        db.close()


def check_subscription_expiry_and_remind():
    """
    Checks if any paid subscriptions are expiring in 3 days or 1 day
    and sends a renewal notice to the user over WhatsApp.
    """
    print("\n💳 Checking for expiring subscriptions...")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today = now.date()
        
        # Get users with active subscriptions
        expiring_users = db.query(User).filter(User.subscription_expiry != None).all()
        remind_count = 0
        
        for user in expiring_users:
            days_left = (user.subscription_expiry.date() - today).days
            
            if days_left in [3, 1]:
                lang = user.language_preference
                if lang == "hi":
                    msg = f"⏰ आपका TenderBot plan {days_left} दिन में expire होगा।\\nसेवा जारी रखने के लिए Type करें: *Renew*"
                else:
                    msg = f"⏰ Your TenderBot subscription expires in {days_left} days!\\nReply *Renew* to keep your active alerts and analysis."
                
                send_whatsapp_message(user.phone_number, msg)
                remind_count += 1
                print(f"  → Sent {days_left}d expiry warning to {user.phone_number}")
                
        print(f"✅ Subscription check complete: {remind_count} notices sent.")
    except Exception as e:
        print(f"❌ Subscription check error: {e}")
    finally:
        db.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEDULER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_scraper_schedule():
    print("━" * 60)
    print("🤖 TenderBot Scraper Worker Started")
    print(f"   Portals: {len(SCRAPE_PORTALS)}")
    print(f"   Schedule: Every 6 hours")
    print("━" * 60)

    # APScheduler configuration
    scheduler = BlockingScheduler()
    
    # Run once immediately on boot
    print("⏳ Running initial fetch loop...")
    match_and_alert()
    check_deadlines_and_remind()
    check_subscription_expiry_and_remind()

    # Schedule: Every 6 hours for scraping
    scheduler.add_job(match_and_alert, 'interval', hours=6, name='Scrape Tenders')

    # Schedule: Every morning at 7am and 8am for reminders
    scheduler.add_job(check_deadlines_and_remind, 'cron', hour=7, minute=0, name='Deadline Reminders')
    scheduler.add_job(check_subscription_expiry_and_remind, 'cron', hour=8, minute=0, name='Subscription Expiry Check')

    print("🚀 Scheduler active and running...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    run_scraper_schedule()
