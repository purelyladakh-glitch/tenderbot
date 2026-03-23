"""
TenderBot — Live Market Data via Two-Stage Gemini Approach

Stage 1: Before analyzing a tender, Gemini fetches current market rates 
         for the tender's specific location/state.
Stage 2: Those rates are injected into the analysis prompt for accurate cost estimation.

This eliminates stale hardcoded rates and provides location-specific pricing.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client
_client = None
def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client

# Cache for rates to avoid repeated API calls for the same location
_rates_cache = {}

# Fallback rates if Gemini call fails
FALLBACK_RATES = """
[FALLBACK MARKET RATES - INDIA AVERAGE (Use only if location-specific rates unavailable)]

BASIC MATERIALS:
- Cement (OPC 43/53): Rs.350-420 per 50kg bag
- Cement (PPC): Rs.330-400 per 50kg bag
- TMT Steel Rebar (Fe500/Fe500D): Rs.52,000-58,000 per MT
- Structural Steel: Rs.60,000-68,000 per MT
- River Sand: Rs.4,000-6,000 per brass
- M-Sand: Rs.3,500-5,000 per brass
- Aggregate 20mm: Rs.2,500-4,000 per brass
- Bricks (Red Clay): Rs.8-12 per piece
- Fly Ash Bricks: Rs.6-9 per piece
- AAC Blocks: Rs.3,500-4,500 per cum

CONCRETE (Ready Mix):
- M20: Rs.4,500-5,500 per cum
- M25: Rs.5,000-6,000 per cum
- M30: Rs.5,500-6,500 per cum
- M40: Rs.6,500-7,500 per cum

ROAD MATERIALS:
- Bitumen VG30: Rs.48,000-52,000 per MT
- WBM: Rs.180-250 per cum
- WMM: Rs.200-280 per cum
- DBM: Rs.8,000-10,000 per cum
- BC: Rs.9,000-11,000 per cum

PIPES:
- RCC NP3 600mm: Rs.2,800-3,500 per meter
- DI K9 150mm: Rs.1,200-1,600 per meter
- HDPE PE100 110mm: Rs.180-250 per meter

LABOUR (Per Day):
- Unskilled: Rs.400-600
- Semi-Skilled: Rs.550-800
- Skilled (Mason/Carpenter): Rs.700-1,100
- Highly Skilled (Plumber/Electrician): Rs.800-1,200
- Operator: Rs.800-1,200

EQUIPMENT (Per Hour):
- JCB/Backhoe: Rs.1,800-2,500
- Excavator PC200: Rs.3,000-4,000
- Tipper 10T: Rs.15,000-20,000/day
- Transit Mixer: Rs.18,000-25,000/day
- Vibratory Roller: Rs.12,000-18,000/day

ESTIMATION RULES:
- Contractor Profit Margin: 10-15% (max 20% for high-risk/remote)
- Overhead & Contingencies: 5-8%
- GST on Construction: 18% (12% for govt works contract)
- EMD: 2% of Tender Value (1% for MSME)
- Performance Security: 3-5%
- Mobilization Advance: Usually 10% (if available)

REGIONAL MODIFIERS:
- Ladakh/Leh/Kargil: +30-40% transport, +20-30% labour, May-Oct only
- J&K Kashmir Valley: +15-20% transport
- Northeast India: +20-30% transport
- Himalayan high altitude: +15-25%
- Island UTs (Andaman/Lakshadweep): +40-50% transport
- Metro Cities: +10-15% labour premium
"""


def fetch_live_rates_for_location(location: str, work_type: str = "construction") -> str:
    """
    Stage 1: Uses Gemini to fetch current market rates for a specific location.
    Returns a formatted string of rates to inject into the analysis prompt.
    
    Caches results for 6 hours to avoid repeated API calls.
    """
    import time
    
    # Check cache (6-hour TTL)
    cache_key = f"{location.lower().strip()}_{work_type.lower().strip()}"
    if cache_key in _rates_cache:
        cached_data, cached_time = _rates_cache[cache_key]
        if time.time() - cached_time < 21600:  # 6 hours
            print(f"📦 Using cached rates for: {location}")
            return cached_data
    
    try:
        client = _get_client()
        
        prompt = f"""You are a construction cost database for India. 
Provide CURRENT market rates (as of today) for construction materials, labour, and equipment 
specifically for this location: {location}

Work type context: {work_type}

Output a structured list with these categories. Use ACTUAL current rates, not outdated data.
Account for local supply conditions, transport costs, and regional factors.

FORMAT (plain text, no JSON):

MATERIALS (for {location}):
- Cement OPC 53 Grade: Rs.XXX per 50kg bag
- Cement PPC: Rs.XXX per 50kg bag  
- TMT Steel Fe500D: Rs.XX,XXX per MT
- Sand (local type): Rs.XXX per brass/cum
- Aggregate 20mm: Rs.XXX per brass/cum
- Bricks/Blocks (local standard): Rs.XX per piece
- Ready Mix Concrete M20: Rs.XXX per cum
- Ready Mix Concrete M25: Rs.XXX per cum
- Ready Mix Concrete M30: Rs.XXX per cum
[Add road materials if work_type involves roads]
[Add pipe rates if work_type involves water supply/drainage]
[Add electrical rates if work_type involves electrical]

LABOUR RATES (for {location}, per day):
- Unskilled: Rs.XXX
- Skilled Mason/Carpenter: Rs.XXX  
- Plumber/Electrician: Rs.XXX
- Equipment Operator: Rs.XXX

EQUIPMENT HIRE (for {location}):
- JCB/Backhoe: Rs.XXX per hour
- Excavator: Rs.XXX per hour
- Tipper/Dumper: Rs.XXX per day

LOCAL FACTORS for {location}:
- Transport difficulty: [Easy/Medium/Hard]
- Working season: [months available]
- Any material scarcity issues
- Nearest major supply hub

ESTIMATION RULES:
- Standard profit margin: 10-15%
- GST on works contract: 12-18%
- EMD: 2% of tender value
- Performance security: 3-5%

Be specific to {location}. Do NOT give generic all-India averages.
If {location} is in a remote/high-altitude area, factor in transport premiums."""

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2000,
            )
        )
        
        rates_text = response.text.strip()
        
        if len(rates_text) > 100:  # Sanity check — got meaningful response
            # Cache the result
            _rates_cache[cache_key] = (rates_text, time.time())
            print(f"✅ Fetched live rates for: {location} ({len(rates_text)} chars)")
            return rates_text
        else:
            print(f"⚠️ Gemini returned thin rates for {location}, using fallback")
            return FALLBACK_RATES
            
    except Exception as e:
        print(f"⚠️ Live rates fetch failed for {location}: {e}. Using fallback rates.")
        return FALLBACK_RATES


def get_live_market_data(location: str = None, work_type: str = None) -> str:
    """
    Main entry point. If location is provided, fetches live location-specific rates.
    Otherwise returns fallback national average rates.
    
    Called by analyzer.py before the analysis prompt.
    """
    if location and location.strip():
        return fetch_live_rates_for_location(location, work_type or "general construction")
    return FALLBACK_RATES


def extract_location_from_text(text: str) -> str:
    """
    Quick extraction of location from tender text for the rates lookup.
    Looks for common patterns like 'District:', 'Location:', state names, city names.
    """
    import re
    
    # Try common tender patterns
    patterns = [
        r'(?:location|place of work|site|district|city)\s*[:\-]\s*([A-Za-z\s,]+)',
        r'(?:state)\s*[:\-]\s*([A-Za-z\s]+)',
        r'(?:at|in|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    text_lower = text.lower()
    
    # FIRST: Check for known Indian state/city names (most reliable)
    known_locations = [
        "Ladakh", "Leh", "Kargil", "Srinagar", "Jammu",
        "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", 
        "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
        "Chandigarh", "Dehradun", "Shimla", "Bhopal", "Patna", 
        "Ranchi", "Bhubaneswar", "Guwahati", "Thiruvananthapuram",
        "Kochi", "Gandhinagar", "Raipur", "Panaji",
        "Uttar Pradesh", "Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat",
        "Rajasthan", "Madhya Pradesh", "Bihar", "West Bengal", "Telangana",
        "Andhra Pradesh", "Kerala", "Punjab", "Haryana", "Jharkhand",
        "Chhattisgarh", "Uttarakhand", "Himachal Pradesh", "Assam", "Odisha",
        "Jammu & Kashmir", "J&K", "Arunachal Pradesh", "Sikkim",
        "Meghalaya", "Mizoram", "Manipur", "Nagaland", "Tripura", "Goa",
    ]
    
    for loc in known_locations:
        if loc.lower() in text_lower:
            return loc
            
    # SECOND: Try regex patterns as fallback
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip().rstrip(',.')
            if len(location) > 3 and len(location) < 50:
                skip_words = ["colony", "office", "building", "quarter", "road", "highway", "camp"]
                if not any(sw in location.lower() for sw in skip_words):
                    return location
    
    return ""
