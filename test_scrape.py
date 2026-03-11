import requests
from bs4 import BeautifulSoup
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_nicgep(domain, state_label):
    url = f"https://{domain}/nicgep/app?page=FrontEndLatestActiveTenders&service=page"
    print(f"Fetching {url}")
    try:
        res = requests.get(url, verify=False, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", {"id": "table"})
        if not table:
            print("Table not found!")
            return []
            
        rows = table.find_all("tr")[1:5] # First few rows
        results = []
        for r in rows:
            cols = r.find_all("td")
            if len(cols) > 5:
                # Based on NICGEP standard (e.g., eprocure):
                # 0: S.No
                # 1: e-Published Date
                # 2: Closing Date
                # 3: Opening Date
                # 4: Title and Ref.No/Tender ID
                # 5: Organisation Chain
                
                title_td = cols[4]
                title_link = title_td.find("a")
                title = title_link.text.strip() if title_link else title_td.text.strip()
                
                # Extract Tender ID from the text below title
                tender_id = "UNKNOWN"
                match = re.search(r"Tender ID :\s*([A-Za-z0-9_]+)", title_td.text)
                if match:
                    tender_id = match.group(1)
                    title = title.split("[")[0].strip() # Clean up title
                    
                org_chain = cols[5].text.strip()
                # Clean up org chain, sometimes it has 
                
                # We don't get 'value' easily from this page, it requires clicking. 
                # But we can keyword match on title/org for now.
                
                results.append({
                    "external_id": tender_id,
                    "title": title,
                    "department": org_chain,
                    "state": state_label,
                    "value_inr": 0, # Cannot get without details page, defaulting to 0 for blind matching
                    "url": url # Direct link to active tenders page
                })
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    tenders = scrape_nicgep("ladakhtenders.gov.in", "Ladakh")
    for t in tenders:
        print(t)
    
    print("---")
    tenders_jk = scrape_nicgep("jktenders.gov.in", "Jammu & Kashmir")
    for t in tenders_jk:
        print(t)

