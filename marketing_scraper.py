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

def duckduckgo_search(query: str, max_results: int = 4) -> list:
    """Uses a lightweight headless search to autonomously find target websites."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    urls = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all('a', class_='result__url'):
            if len(urls) >= max_results: break
            href = a.get('href')
            if href and "http" in href:
                import urllib.parse
                if href.startswith("//duckduckgo.com/l/?uddg="):
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    href = parsed.get('uddg', [href])[0]
                urls.append(href)
    except Exception as e:
        print(f"   [!] Search engine connection failed: {e}")
    return urls

def fetch_leads_from_directory(db: Session, target_url: str = None):
    """
    Scrapes regional public contractor directories autonomously.
    """
    print(f"🔍 Starting Autonomous Marketing Hunter...")
    
    scraped_data = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    TARGET_URLS = []
    
    print("🌍 Autonomously searching the web for regional contractor lists...")
    search_queries = [
        "certified civil contractors contact list jammu and kashmir phone number",
        "pwd contractors association srinagar directory mobile",
        "registered construction companies leh ladakh contact details"
    ]
    for sq in search_queries:
        found_urls = duckduckgo_search(sq, max_results=3)
        TARGET_URLS.extend(found_urls)
    
    TARGET_URLS = list(set(TARGET_URLS)) # Remove duplicate domains
    print(f"🎯 Discovered {len(TARGET_URLS)} potential web targets to hunt through!")
    
    # 1. LIVE AUTONOMOUS CRAWL LOGIC 
    for url in TARGET_URLS:
        try:
            print(f"   [~] Crawling: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Universal Regex to find Indian phone numbers anywhere in raw website text
            phone_pattern = r'(?:(?:\+|0{0,2})91[\s.-]?)?([6-9]\d{9})'
            
            raw_text = soup.get_text(separator=" ")
            matches = re.finditer(phone_pattern, raw_text)
            
            for match in matches:
                raw_phone = match.group(0)
                
                # Context-Proximity Name Extraction:
                # Grab the 50 characters of text immediately preceding the phone number to guess the company
                start_idx = max(0, match.start() - 50)
                context_chunk = raw_text[start_idx:match.start()].strip()
                
                # Clean up nearby words to form a plausible Company Name string
                context_words = re.findall(r'[A-Za-z]+', context_chunk)
                company_guess = " ".join(context_words[-3:]) if len(context_words) >= 3 else "Local Contractor"
                
                scraped_data.append({
                    "name": "Team", 
                    "company": company_guess.title(),
                    "phone": raw_phone,
                    "source": url
                })
        except Exception as e:
            print(f"   [!] Failed to crawl {url}: {e}")

    # 2. SEED FALLBACK (If crawler list is empty, inject your numbers for demo testing)
    if not scraped_data:
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
