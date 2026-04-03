import os
import re
import requests
from bs4 import BeautifulSoup
from database import SessionLocal, MarketingLead
from sqlalchemy.orm import Session

def clean_phone(phone_str: str) -> str:
    """Normalizes phone numbers to standard 91 format."""
    digits = re.sub(r'\D', '', str(phone_str))
    if len(digits) == 10:
        return f"91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        return digits
    elif len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"
    return None

def fetch_leads_from_directory(db: Session, target_url: str = None):
    """
    Scrapes regional public contractor directories.
    Designed to parse standard HTML tables containing Name, Company, and Contact info.
    """
    print(f"🔍 Starting Marketing Scraper...")
    
    # ---------------------------------------------------------
    # INSERT LIVE SCRAPING LOGIC HERE
    # Example:
    # response = requests.get("https://raw_directory_link_here")
    # soup = BeautifulSoup(response.text, "html.parser")
    # ... extraction logic ...
    # ---------------------------------------------------------
    
    # For safety and immediate pipeline testing, we inject test seeds.
    # In production, this array is populated by the BeautifulSoup parser above.
    scraped_data = [
        {"name": "Rajesh Kumar", "company": "RK Builders Ladakh", "phone": "916006224209", "source": "demo_seed"},
        {"name": "Tariq Ahamad", "company": "Valley Civils J&K", "phone": "919796700386", "source": "demo_seed"}
    ]
    
    leads_added = 0
    for data in scraped_data:
        phone = clean_phone(data["phone"])
        if not phone:
            continue
        
        # Check if lead already exists to prevent duplicate outreach
        existing_lead = db.query(MarketingLead).filter(MarketingLead.phone_number == phone).first()
        if not existing_lead:
            new_lead = MarketingLead(
                phone_number=phone,
                name=data.get("name", "Contractor"),
                company=data.get("company", "Your Company"),
                source=data.get("source", "web_scraper"),
                status="new",
                follow_up_count=0
            )
            db.add(new_lead)
            leads_added += 1
            print(f"   [+] Added New Lead: {new_lead.name} ({new_lead.phone_number})")
    
    try:
        db.commit()
        print(f"✅ Marketing Scraper completed. Saved {leads_added} new leads to database.")
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        
    return leads_added

if __name__ == "__main__":
    db = SessionLocal()
    fetch_leads_from_directory(db)
    db.close()
