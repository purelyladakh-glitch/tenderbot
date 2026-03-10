"""
Complete India Tender Portal Database + NLP Location Detection
All 28 States, 8 Union Territories, Central Government, PSUs, Defence portals.
Special focus on Ladakh UT.

CRITICAL UX: No number menus. All natural language detection.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CENTRAL GOVERNMENT PORTALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CENTRAL_PORTALS = [
    {"name": "Central Public Procurement Portal", "url": "https://eprocure.gov.in", "code": "CPPP", "priority": "high"},
    {"name": "Government e-Marketplace", "url": "https://gem.gov.in", "code": "GeM", "priority": "high"},
    {"name": "National Tender Portal", "url": "https://tenders.gov.in", "code": "NTP", "priority": "high"},
    {"name": "Indian Railways e-Procurement", "url": "https://ireps.gov.in", "code": "IREPS", "priority": "medium"},
    {"name": "NHAI Tenders", "url": "https://tenders.nhai.gov.in", "code": "NHAI", "priority": "medium"},
    {"name": "BRO Tenders", "url": "https://bro.gov.in/tenders", "code": "BRO", "priority": "high"},
    {"name": "CPWD Tenders", "url": "https://cpwd.gov.in/tenders", "code": "CPWD", "priority": "high"},
    {"name": "NHIDCL Border Highways", "url": "https://nhidcl.com/tenders", "code": "NHIDCL", "priority": "high"},
    {"name": "MES Tenders", "url": "https://mes.gov.in/tenders", "code": "MES", "priority": "medium"},
    {"name": "NTPC", "url": "https://ntpc.co.in/tenders", "code": "NTPC", "priority": "medium"},
    {"name": "BHEL", "url": "https://bhel.com/tenders", "code": "BHEL", "priority": "medium"},
    {"name": "ONGC", "url": "https://ongcindia.com/tenders", "code": "ONGC", "priority": "medium"},
    {"name": "Coal India", "url": "https://coalindia.in/tenders", "code": "CIL", "priority": "medium"},
    {"name": "AAI", "url": "https://aaiclas.aai.aero", "code": "AAI", "priority": "medium"},
    {"name": "SECI Solar", "url": "https://seci.co.in/tenders", "code": "SECI", "priority": "medium"},
    {"name": "Power Grid", "url": "https://pgcil.co.in/tenders", "code": "PGCIL", "priority": "medium"},
    {"name": "NPCIL Nuclear", "url": "https://npcil.nic.in/tenders", "code": "NPCIL", "priority": "low"},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATE/UT DATA — NLP keywords + city mappings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATES = {
    "uttar pradesh": {
        "name": "Uttar Pradesh", "code": "UP", "region": "north",
        "portals": ["https://etender.up.nic.in"],
        "keywords": ["up", "uttar pradesh", "lucknow", "noida", "agra", "kanpur", "varanasi", "allahabad", "prayagraj", "meerut", "ghaziabad", "mathura", "bareilly", "gorakhpur", "jhansi", "aligarh", "moradabad", "firozabad", "ayodhya"],
        "departments": ["UP PWD", "UP Jal Nigam", "UP Housing Board", "UPEIDA", "UP Metro", "UP Expressways Authority"],
    },
    "delhi": {
        "name": "Delhi", "code": "DL", "region": "north",
        "portals": ["https://ddtenders.gov.in", "https://delhigovt.nic.in/tenders"],
        "keywords": ["delhi", "dl", "new delhi", "ndmc", "dda", "dmrc", "delhi metro", "south delhi", "north delhi", "east delhi", "west delhi", "dwarka", "rohini", "saket"],
        "departments": ["DDA", "DMRC", "NDMC", "MCD", "Delhi PWD", "Delhi Jal Board", "DSIIDC"],
    },
    "haryana": {
        "name": "Haryana", "code": "HR", "region": "north",
        "portals": ["https://haryanaeprocurement.gov.in"],
        "keywords": ["haryana", "hr", "gurgaon", "gurugram", "faridabad", "panipat", "ambala", "karnal", "hisar", "rohtak", "sonipat", "jhajjar", "rewari", "panchkula", "bhiwani"],
        "departments": ["Haryana PWD", "HRERA", "HSVP", "Haryana Urban Development", "HSIIDC"],
    },
    "punjab": {
        "name": "Punjab", "code": "PB", "region": "north",
        "portals": ["https://eproc.punjab.gov.in"],
        "keywords": ["punjab", "pb", "chandigarh area", "ludhiana", "amritsar", "jalandhar", "patiala", "bathinda", "mohali", "hoshiarpur", "pathankot"],
        "departments": ["Punjab PWD", "PUDA", "Punjab Water Supply Board", "Punjab Housing Board", "PSPCL"],
    },
    "himachal pradesh": {
        "name": "Himachal Pradesh", "code": "HP", "region": "north",
        "portals": ["https://hptenders.gov.in"],
        "keywords": ["himachal", "hp", "himachal pradesh", "shimla", "manali", "kullu", "dharamsala", "mandi", "solan", "kangra", "hamirpur", "una", "bilaspur", "chamba", "kinnaur", "spiti", "lahaul"],
        "departments": ["HP PWD", "HP Housing Board", "HP Tourism", "HP Jal Shakti", "HPSEBL"],
    },
    "uttarakhand": {
        "name": "Uttarakhand", "code": "UK", "region": "north",
        "portals": ["https://uktenders.gov.in"],
        "keywords": ["uttarakhand", "uk", "dehradun", "haridwar", "rishikesh", "nainital", "mussoorie", "roorkee", "haldwani", "rudrapur", "kashipur", "char dham", "badrinath", "kedarnath", "pithoragarh", "almora", "chamoli"],
        "departments": ["UK PWD", "UPCL", "UK Housing Board", "UK Jal Sansthan", "Char Dham Project"],
    },
    "jammu kashmir": {
        "name": "Jammu & Kashmir", "code": "JK", "region": "north", "is_ut": True,
        "portals": ["https://jktenders.gov.in", "https://jkprocurement.gov.in"],
        "keywords": ["j&k", "jk", "jammu", "kashmir", "srinagar", "anantnag", "baramulla", "kupwara", "sopore", "pulwama", "kathua", "udhampur", "rajouri", "poonch", "doda", "kishtwar", "ramban", "reasi", "ganderbal", "budgam", "bandipora", "shopian", "kulgam"],
        "departments": ["JK PWD", "JK Housing Board", "JK Tourism", "JKPCC", "JK Power", "JK Jal Shakti", "SIDCO"],
    },
    "ladakh": {
        "name": "Ladakh", "code": "LA", "region": "north", "is_ut": True, "is_special": True,
        "portals": ["https://ladakhtenders.gov.in", "https://jktenders.gov.in", "https://eprocure.gov.in", "https://bro.gov.in/tenders", "https://nhidcl.com/tenders"],
        "keywords": ["ladakh", "leh", "kargil", "pangong", "nubra", "zanskar", "drass", "nyoma", "changthang", "hanle", "diskit", "turtuk", "padum", "khaltse", "nimmu", "choglamsar", "spituk", "hemis", "thiksey", "stakna", "zoji la", "tanglang la", "khardung la"],
        "departments": ["Ladakh PWD", "BRO Himank", "BRO Beacon", "BRO Vijayak", "NHIDCL", "NHAI Ladakh", "LAHDC Leh", "LAHDC Kargil", "Leh Municipal", "Kargil Municipal", "UT Admin Ladakh", "Jal Jeevan Mission", "Ladakh Power", "LREDA", "MES Ladakh", "GREF", "Ladakh Tourism", "Ladakh Agriculture", "BSNL Ladakh"],
        "special_notes": {
            "altitude": "High altitude (3500m-5500m)",
            "winter": "Oct-Apr limited work",
            "transport": "Zoji La/Rohtang closure risk",
            "bro": "BRO tenders ₹10Cr-₹500Cr, less competition, faster payments",
        },
    },
    "rajasthan": {
        "name": "Rajasthan", "code": "RJ", "region": "north",
        "portals": ["https://sppp.rajasthan.gov.in"],
        "keywords": ["rajasthan", "rj", "jaipur", "jodhpur", "udaipur", "kota", "ajmer", "bikaner", "alwar", "bharatpur", "sikar", "bhilwara", "chittorgarh", "pali", "nagaur", "tonk", "barmer", "jaisalmer"],
        "departments": ["Rajasthan PWD", "RUIDP", "Rajasthan Housing Board", "PHED", "RIICO"],
    },
    "maharashtra": {
        "name": "Maharashtra", "code": "MH", "region": "west",
        "portals": ["https://mahatenders.gov.in", "https://maharashtra.etenders.in"],
        "keywords": ["maharashtra", "mh", "maha", "mumbai", "pune", "nagpur", "nashik", "thane", "aurangabad", "solapur", "kolhapur", "sangli", "satara", "navi mumbai", "kalyan", "vasai", "virar", "panvel", "amravati", "akola", "latur", "nanded", "ratnagiri", "konkan", "mumbai wala"],
        "departments": ["Maharashtra PWD", "MMRDA", "MMRCL", "PMRDA", "Maha Metro", "CIDCO", "MHADA", "MSRDC", "BMC", "PMC", "MIDC", "MSEDCL"],
    },
    "gujarat": {
        "name": "Gujarat", "code": "GJ", "region": "west",
        "portals": ["https://nprocure.com"],
        "keywords": ["gujarat", "gj", "ahmedabad", "surat", "vadodara", "rajkot", "bhavnagar", "jamnagar", "gandhinagar", "junagadh", "anand", "bharuch", "morbi", "mehsana", "gift city", "kutch"],
        "departments": ["Gujarat PWD", "GMDA", "Surat Metro", "GHB", "GWSSB", "GSECL", "GIDC"],
    },
    "madhya pradesh": {
        "name": "Madhya Pradesh", "code": "MP", "region": "west",
        "portals": ["https://mptenders.gov.in"],
        "keywords": ["madhya pradesh", "mp", "bhopal", "indore", "jabalpur", "gwalior", "ujjain", "sagar", "dewas", "satna", "rewa", "burhanpur", "khandwa", "chhindwara"],
        "departments": ["MP PWD", "MP Housing Board", "Bhopal Metro", "Indore Metro", "MP Urban Development"],
    },
    "goa": {
        "name": "Goa", "code": "GA", "region": "west",
        "portals": ["https://goatenders.gov.in"],
        "keywords": ["goa", "ga", "panaji", "panjim", "margao", "vasco", "mapusa"],
        "departments": ["Goa PWD", "GDA", "Goa Housing Board", "Goa Tourism"],
    },
    "chhattisgarh": {
        "name": "Chhattisgarh", "code": "CG", "region": "west",
        "portals": ["https://cgeprocurement.gov.in"],
        "keywords": ["chhattisgarh", "cg", "raipur", "bhilai", "bilaspur", "durg", "korba", "rajnandgaon", "jagdalpur"],
        "departments": ["CG PWD", "CSPHCL", "CG Housing Board"],
    },
    "karnataka": {
        "name": "Karnataka", "code": "KA", "region": "south",
        "portals": ["https://kppp.karnataka.gov.in"],
        "keywords": ["karnataka", "ka", "bangalore", "bengaluru", "mysore", "mysuru", "hubli", "dharwad", "mangalore", "belgaum", "belagavi", "gulbarga", "davangere", "shimoga", "tumkur", "bellary"],
        "departments": ["Karnataka PWD", "BMRCL", "BDA", "BBMP", "KIADB", "BESCOM"],
    },
    "tamil nadu": {
        "name": "Tamil Nadu", "code": "TN", "region": "south",
        "portals": ["https://tntenders.gov.in"],
        "keywords": ["tamil nadu", "tn", "chennai", "madras", "coimbatore", "madurai", "trichy", "tiruchirappalli", "salem", "tirunelveli", "erode", "vellore", "thoothukudi", "thanjavur", "dindigul", "kanchipuram"],
        "departments": ["TN PWD", "CMDA", "CMRL", "TNHB", "TWAD", "TNEB"],
    },
    "telangana": {
        "name": "Telangana", "code": "TS", "region": "south",
        "portals": ["https://tender.telangana.gov.in"],
        "keywords": ["telangana", "ts", "hyderabad", "secunderabad", "warangal", "karimnagar", "nizamabad", "khammam", "nalgonda", "adilabad", "mahbubnagar"],
        "departments": ["Telangana PWD", "HMDA", "HMRL", "TSIIC", "GHMC", "HMWSSB"],
    },
    "andhra pradesh": {
        "name": "Andhra Pradesh", "code": "AP", "region": "south",
        "portals": ["https://tender.apeprocurement.gov.in"],
        "keywords": ["andhra", "ap", "andhra pradesh", "amaravati", "visakhapatnam", "vizag", "vijayawada", "tirupati", "guntur", "nellore", "kurnool", "rajahmundry", "kakinada", "eluru", "anantapur"],
        "departments": ["AP PWD", "CRDA Amaravati", "APEPDCL", "AP Housing"],
    },
    "kerala": {
        "name": "Kerala", "code": "KL", "region": "south",
        "portals": ["https://etenders.kerala.gov.in"],
        "keywords": ["kerala", "kl", "kochi", "cochin", "trivandrum", "thiruvananthapuram", "kozhikode", "calicut", "thrissur", "kollam", "kannur", "alappuzha", "palakkad", "malappuram", "ernakulam"],
        "departments": ["Kerala PWD", "KMRL", "Kerala Housing Board", "KWA", "KSEB", "KINFRA"],
    },
    "west bengal": {
        "name": "West Bengal", "code": "WB", "region": "east",
        "portals": ["https://wbtenders.gov.in"],
        "keywords": ["west bengal", "wb", "bengal", "kolkata", "calcutta", "howrah", "durgapur", "asansol", "siliguri", "kharagpur", "haldia", "barasat", "burdwan", "darjeeling"],
        "departments": ["WB PWD", "HIDCO", "KMRC", "KMC", "WBIDC"],
    },
    "bihar": {
        "name": "Bihar", "code": "BR", "region": "east",
        "portals": ["https://eproc.bihar.gov.in"],
        "keywords": ["bihar", "br", "patna", "gaya", "muzaffarpur", "bhagalpur", "darbhanga", "purnia", "arrah", "begusarai", "munger", "nalanda", "rajgir"],
        "departments": ["Bihar PWD", "BSPHCL", "Bihar Urban Development", "Patna Metro"],
    },
    "jharkhand": {
        "name": "Jharkhand", "code": "JH", "region": "east",
        "portals": ["https://jharkhandtenders.gov.in"],
        "keywords": ["jharkhand", "jh", "ranchi", "jamshedpur", "dhanbad", "bokaro", "hazaribagh", "deoghar", "giridih"],
        "departments": ["Jharkhand PWD", "JBVNL", "JIIDCO"],
    },
    "odisha": {
        "name": "Odisha", "code": "OD", "region": "east",
        "portals": ["https://tendersodisha.gov.in"],
        "keywords": ["odisha", "orissa", "od", "bhubaneswar", "cuttack", "rourkela", "berhampur", "sambalpur", "puri", "balasore", "bhadrak"],
        "departments": ["Odisha PWD", "OHPC", "Odisha Housing Board", "IDCO"],
    },
    "assam": {
        "name": "Assam", "code": "AS", "region": "east",
        "portals": ["https://assamtenders.gov.in"],
        "keywords": ["assam", "as", "guwahati", "dibrugarh", "silchar", "jorhat", "tezpur", "nagaon", "tinsukia"],
        "departments": ["Assam PWD", "APGCL", "Guwahati Metro"],
    },
    "meghalaya": {
        "name": "Meghalaya", "code": "ML", "region": "northeast",
        "portals": ["https://megtenders.gov.in", "https://eprocure.gov.in"],
        "keywords": ["meghalaya", "ml", "shillong", "tura", "cherrapunji"],
        "departments": ["Meghalaya PWD"],
    },
    "tripura": {
        "name": "Tripura", "code": "TR", "region": "northeast",
        "portals": ["https://tripuratenders.gov.in", "https://eprocure.gov.in"],
        "keywords": ["tripura", "tr", "agartala"],
        "departments": ["Tripura PWD"],
    },
    "manipur": {
        "name": "Manipur", "code": "MN", "region": "northeast",
        "portals": ["https://manipurtenders.gov.in", "https://eprocure.gov.in"],
        "keywords": ["manipur", "mn", "imphal"],
        "departments": ["Manipur PWD"],
    },
    "nagaland": {
        "name": "Nagaland", "code": "NL", "region": "northeast",
        "portals": ["https://tendersinnagaland.com", "https://eprocure.gov.in"],
        "keywords": ["nagaland", "nl", "kohima", "dimapur"],
        "departments": ["Nagaland PWD"],
    },
    "mizoram": {
        "name": "Mizoram", "code": "MZ", "region": "northeast",
        "portals": ["https://eprocure.gov.in", "https://mizoram.gov.in/tenders"],
        "keywords": ["mizoram", "mz", "aizawl"],
        "departments": ["Mizoram PWD"],
    },
    "arunachal pradesh": {
        "name": "Arunachal Pradesh", "code": "AR", "region": "northeast",
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["arunachal", "ar", "arunachal pradesh", "itanagar", "tawang", "naharlagun"],
        "departments": ["Arunachal PWD", "BRO Arunachal"],
    },
    "sikkim": {
        "name": "Sikkim", "code": "SK", "region": "northeast",
        "portals": ["https://sikkimtender.gov.in", "https://eprocure.gov.in"],
        "keywords": ["sikkim", "sk", "gangtok", "namchi"],
        "departments": ["Sikkim PWD"],
    },
    "chandigarh": {
        "name": "Chandigarh", "code": "CH", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["chandigarh", "ch"],
        "departments": ["Chandigarh Administration"],
    },
    "puducherry": {
        "name": "Puducherry", "code": "PY", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["puducherry", "pondicherry", "py"],
        "departments": ["Puducherry PWD"],
    },
    "andaman nicobar": {
        "name": "Andaman & Nicobar", "code": "AN", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in", "https://andaman.gov.in/tenders"],
        "keywords": ["andaman", "nicobar", "an", "port blair"],
        "departments": ["A&N Administration"],
    },
    "dadra nagar haveli": {
        "name": "Dadra & Nagar Haveli", "code": "DN", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["dadra", "nagar haveli", "silvassa"],
        "departments": ["DNH Administration"],
    },
    "daman diu": {
        "name": "Daman & Diu", "code": "DD", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["daman", "diu"],
        "departments": ["DD Administration"],
    },
    "lakshadweep": {
        "name": "Lakshadweep", "code": "LD", "region": "ut", "is_ut": True,
        "portals": ["https://eprocure.gov.in"],
        "keywords": ["lakshadweep", "kavaratti"],
        "departments": ["Lakshadweep Administration"],
    },
}

# Region keywords
REGION_KEYWORDS = {
    "north": ["north india", "north", "uttar bharat"],
    "south": ["south india", "south", "dakshin bharat", "dakshin"],
    "west": ["west india", "west", "paschim bharat", "paschim"],
    "east": ["east india", "east", "purv bharat", "purv", "poorv"],
    "northeast": ["northeast", "ne india", "north east"],
}

ALL_INDIA_KEYWORDS = ["all india", "sab jagah", "poora india", "puri india", "everywhere", "har jagah", "all states", "sabhi states", "pan india", "nationwide", "pura desh"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NLP DETECTION FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_states_from_text(text: str) -> list:
    """
    Detects states/UTs from natural language text.
    Handles: state names, city names, abbreviations, regional phrases.
    Returns list of state keys.
    """
    text_lower = text.lower().strip()

    # Check all-india first
    for kw in ALL_INDIA_KEYWORDS:
        if kw in text_lower:
            return list(STATES.keys())

    # Check region keywords
    matched = set()
    for region, keywords in REGION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                for state_key, state_data in STATES.items():
                    if state_data.get("region") == region:
                        matched.add(state_key)

    # Check each state's keywords (cities, abbreviations, names)
    for state_key, state_data in STATES.items():
        for kw in state_data.get("keywords", []):
            if kw in text_lower:
                matched.add(state_key)
                break

    # Also check the state name itself
    for state_key in STATES:
        if state_key in text_lower:
            matched.add(state_key)

    return list(matched)


def detect_work_types_from_text(text: str) -> list:
    """Detects work types from natural language."""
    text_lower = text.lower()
    detected = []

    work_map = {
        "RCC Construction": ["rcc", "reinforced", "concrete", "cement work"],
        "Road Construction": ["road", "roads", "highway", "highways", "sadak", "national highway", "nh"],
        "Building Construction": ["building", "buildings", "bhawan", "tower", "complex", "residential", "commercial"],
        "Bridge Construction": ["bridge", "bridges", "pul", "flyover", "overpass", "rub"],
        "Water Supply": ["water supply", "pipeline", "plumbing", "jal", "pani", "water tank", "bore well", "borewell"],
        "Electrical Works": ["electrical", "electrification", "wiring", "transformer", "substation", "power", "bijli"],
        "Drainage & Sewerage": ["drainage", "sewerage", "sewer", "nala", "drain", "stormwater"],
        "Irrigation": ["irrigation", "canal", "dam", "barrage", "check dam", "nahar"],
        "Solar & Renewable": ["solar", "renewable", "wind energy", "solar panel", "rooftop solar"],
        "Interior & Furnishing": ["interior", "furnishing", "furniture", "painting", "flooring", "tiles"],
        "Tunnel Construction": ["tunnel", "tunneling", "boring", "tbm"],
        "Metro & Rail": ["metro", "railway", "rail", "track", "station"],
        "Landscaping": ["landscaping", "garden", "park", "horticulture", "plantation"],
    }

    for work_type, keywords in work_map.items():
        for kw in keywords:
            if kw in text_lower:
                detected.append(work_type)
                break

    # Catch-all
    if not detected and text_lower.strip():
        detected.append(text_lower.strip().title())

    return detected


def detect_departments_from_text(text: str) -> list:
    """Detects department preferences from natural language."""
    text_lower = text.lower()
    detected = []

    dept_map = {
        "PWD": ["pwd", "public works", "pwb", "nirman vibhag"],
        "BRO": ["bro", "border roads", "border road", "gref"],
        "NHAI": ["nhai", "national highway", "highway authority"],
        "Municipal": ["municipal", "nagar palika", "nagar nigam", "corporation", "mcd", "bmc", "pmc"],
        "Railways": ["railway", "rail", "ircon", "rvnl"],
        "Water Board": ["water board", "jal", "phed", "jal nigam", "jal sansthan"],
        "Housing Board": ["housing", "awas", "housing board"],
        "CPWD": ["cpwd", "central public works"],
        "MES": ["mes", "military engineering", "army", "defence", "defense", "cantonment"],
        "NHIDCL": ["nhidcl"],
        "Metro": ["metro", "bmrcl", "dmrc", "cmrl", "mmrcl"],
        "All Government": ["sab", "all", "sab sarkari", "sab government", "all government", "har department", "sabhi"],
    }

    for dept, keywords in dept_map.items():
        for kw in keywords:
            if kw in text_lower:
                detected.append(dept)
                break

    if not detected and text_lower.strip():
        detected.append(text_lower.strip().title())

    return detected


def parse_value_range(text: str) -> tuple:
    """
    Parses value range from text like '50 lakh se 5 crore' or '10L to 2Cr'.
    Returns (min_value, max_value) in rupees.
    """
    import re
    text_lower = text.lower().replace(",", "").replace("₹", "").strip()

    def parse_amount(s):
        s = s.strip()
        multiplier = 1
        if "crore" in s or "cr" in s:
            multiplier = 10000000
            s = re.sub(r'(crore|cr)', '', s).strip()
        elif "lakh" in s or "lac" in s or "l" in s:
            multiplier = 100000
            s = re.sub(r'(lakh|lac|l\b)', '', s).strip()
        elif "k" in s:
            multiplier = 1000
            s = s.replace("k", "").strip()

        try:
            return int(float(s) * multiplier)
        except:
            return None

    # Find "X se Y" or "X to Y" or "X - Y"
    patterns = [
        r'(\d+[\d.]*\s*(?:crore|cr|lakh|lac|l|k)?)\s*(?:se|to|—|-|–|and|aur|tak)\s*(\d+[\d.]*\s*(?:crore|cr|lakh|lac|l|k)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            min_val = parse_amount(match.group(1))
            max_val = parse_amount(match.group(2))
            if min_val and max_val:
                return (min(min_val, max_val), max(min_val, max_val))

    # Try single value
    single = re.search(r'(\d+[\d.]*\s*(?:crore|cr|lakh|lac|l|k)?)', text_lower)
    if single:
        val = parse_amount(single.group(1))
        if val:
            return (0, val)

    return (0, 500000000)  # default 0 to 50cr


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERT FORMATTERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_free_alert(tender: dict) -> str:
    return f"""🔔 Naya Tender — {tender.get('department', '')}
━━━━━━━━━━━━━━━━━━━━
{tender.get('work_description', '')}
{tender.get('location', '')}
Value: ₹{tender.get('value', 'N/A')}
Deadline: {tender.get('deadline_date', 'N/A')} ({tender.get('days_remaining', 'X')} din)
━━━━━━━━━━━━━━━━━━━━
⚡ Jaldi karo — {tender.get('days_remaining', 'X')} din baaki

Analyze karna hai?
₹99 mein poora analysis milega:
→ Qualify karte ho ya nahi
→ Hidden risks
→ BOQ rates aur bid amount
→ Documents list
→ Cash flow check

Reply: ANALYZE
Ya plan upgrade karo."""


def format_pack_alert(tender: dict, credits_left: int) -> str:
    return f"""🔔 Matching Tender Found!
━━━━━━━━━━━━━━━━━━━━━━━
{tender.get('department', '')} — {tender.get('work_description', '')}
{tender.get('location', '')}
Value: ₹{tender.get('value', 'N/A')}
Deadline: {tender.get('deadline_date', 'N/A')} ({tender.get('days_remaining', 'X')} din)
━━━━━━━━━━━━━━━━━━━━━━━
⚡ QUICK CHECK:
✅ Value matches your preference
✅ Work type matches
✅ Location matches

ELIGIBILITY: Likely YES

TOP 3 RISKS:
🔴 Check original document for specifics
🟡 Deadline approaching
🟢 Value within your range

SUGGESTED BID: See full analysis

━━━━━━━━━━━━━━━━━━━━━━━━
1 credit use hoga full analysis ke liye.
Baaki credits: {credits_left}/5

Full analysis chahiye?
Reply: YES — poora 9-part analysis
Reply: NO — skip karo
Reply: LATER — kal remind karo"""


def format_monthly_alert(tender: dict) -> str:
    return f"""🔔 MATCHING TENDER — FULL ANALYSIS READY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tender.get('department', '')} — {tender.get('work_description', '')}
{tender.get('location', '')}
Value: ₹{tender.get('value', 'N/A')}
EMD: {tender.get('emd_amount', 'N/A')}
Deadline: {tender.get('deadline_date', 'N/A')} ({tender.get('days_remaining', 'X')} din baaki)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ VERDICT: {tender.get('quick_verdict_recommendation', 'N/A')} — {tender.get('quick_verdict_score', 'N/A')}/10

🔴 {tender.get('critical_risks_count', '0')} critical risks
💰 Recommended bid: ₹{tender.get('recommended_bid', 'N/A')}
💵 Profit estimate: ₹{tender.get('estimated_profit', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Poora analysis ready hai.
Kya dekhna chahte ho?

Type karke poochho ya
number reply karo.
Credit use nahi hoga —
alert analysis FREE hai. ✓"""


def format_ladakh_alert(tender: dict) -> str:
    return f"""🔔 LADAKH TENDER ALERT!
━━━━━━━━━━━━━━━━━━━━━━━━
🏢 {tender.get('department', 'N/A')}
📋 {tender.get('work_description', 'N/A')}
📍 {tender.get('location', 'Ladakh UT')}
💰 Value: ₹{tender.get('value', 'N/A')}
📅 Deadline: {tender.get('deadline_date', 'N/A')} ({tender.get('days_remaining', 'X')} din baaki)
━━━━━━━━━━━━━━━━━━━━━━━━
⛰️ LADAKH SPECIFIC NOTES:
→ High altitude construction (3500m-5500m)
→ Winter shutdown: Oct-Apr limited work
→ Material transport: Zoji La / Rohtang closure risk
→ Factor higher material/transport costs
→ BRO coordination may be required
→ Strategic location = faster govt payments
━━━━━━━━━━━━━━━━━━━━━━━━
Analyze karna hai?
Reply: YES / NO / LATER"""


def get_state_names(state_keys: list) -> str:
    """Returns comma-separated state names."""
    names = []
    for key in state_keys:
        state = STATES.get(key)
        if state:
            names.append(state["name"])
    if len(names) == len(STATES):
        return "All India 🇮🇳"
    return ", ".join(names) if names else "Not set"


def get_portals_for_states(state_keys: list) -> list:
    """Returns all relevant portals for given state keys."""
    portals = []
    seen = set()
    for key in state_keys:
        state = STATES.get(key)
        if state:
            for url in state.get("portals", []):
                if url not in seen:
                    portals.append({"state": state["name"], "url": url})
                    seen.add(url)
    for cp in CENTRAL_PORTALS:
        if cp["url"] not in seen:
            portals.append({"state": "Central", "url": cp["url"]})
            seen.add(cp["url"])
    return portals


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUBSCRIPTION MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLAN_COMPARISON = """Kaunsa plan aapke liye:

FREE:
→ 1 analysis + basic alerts
→ Sirf notification — no detail
→ Analysis karne ke liye pay karo

₹99 — Ek Baar:
→ 1 full analysis
→ 48 hours valid
→ Alerts continue (basic)
→ Best: Occasional tender

₹399 — 5 Pack:
→ 5 full analyses (₹80 each)
→ Alert mein brief analysis
→ Live search feature
→ 60 days valid
→ Best: Regular contractor

₹799/month — Unlimited:
→ 30 analyses + UNLIMITED alert analyses
→ Bot khud dhundta hai tenders
→ Full analysis with every alert
→ All India all portals
→ Daily digest + instant alerts
→ Search unlimited
→ Best: Active contractor

Meri salah:
Pehle FREE try karo.
Active ho toh ₹799 best value hai.
Ek tender jeeta = 62x return. 🎯"""

SINGLE_PLAN_MSG = """💳 ₹99 — Single Analysis

✅ Complete 9-part analysis
✅ Live market rates
✅ BOQ guidance
✅ Cost estimate
✅ Cash flow check
✅ PDF report

Valid: 48 hours"""

PACK_PLAN_MSG = """💳 ₹399 — 5 Tender Pack

✅ 5 complete analyses (₹80 each)
✅ Full 9-part analysis each
✅ Live BOQ rates + cost estimate
✅ Alert + brief analysis when matching tender found
✅ Search any tender live
✅ PDF reports all 5
✅ Valid 60 days

Sabse popular plan hai yeh."""

MONTHLY_PLAN_MSG = """⭐ ₹799/month — Unlimited Plan

ANALYSIS:
✅ 30 full analyses/month
✅ Priority processing
✅ All 9 parts every time
✅ Live rates — steel, cement, labour

ALERTS — AUTOMATIC:
✅ Bot hunts tenders FOR you
✅ All India — all portals
✅ FULL ANALYSIS with every alert (not just notification)
✅ Alert analyses don't use credits
✅ Daily digest + weekly summary

SEARCH:
✅ Search any tender anytime — unlimited

INTELLIGENCE:
✅ Past tender win data
✅ Competitor analysis
✅ Best bid strategy per department

Ek ₹50 lakh tender jeeto —
62x return mil gaya. 🎯"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEARCH — Phase 1 (Portal URL matching)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Work type → relevant central portals mapping
WORK_PORTAL_MAP = {
    "road": ["BRO", "NHAI", "NHIDCL", "CPWD"],
    "highway": ["NHAI", "NHIDCL", "BRO"],
    "bridge": ["BRO", "NHAI", "NHIDCL", "CPWD"],
    "tunnel": ["BRO", "NHIDCL", "NHAI"],
    "rcc": ["CPWD", "CPPP"],
    "building": ["CPWD", "MES", "CPPP"],
    "power": ["NTPC", "PGCIL", "SECI"],
    "solar": ["SECI"],
    "electrical": ["PGCIL", "SECI"],
    "railway": ["IREPS"],
    "rail": ["IREPS"],
    "metro": ["CPPP"],
    "water": ["CPPP"],
    "airport": ["AAI"],
    "oil": ["ONGC"],
    "coal": ["CIL"],
    "nuclear": ["NPCIL"],
    "defence": ["MES"],
    "army": ["MES"],
    "military": ["MES"],
    "cantonment": ["MES"],
}


def search_portals_for_query(query: str) -> dict:
    """
    Phase 1 search: match query keywords to relevant portals.
    Returns dict with 'state_portals', 'central_portals', 'tips'.
    """
    query_lower = query.lower().strip()
    # Remove "search", "dhundo", "find" prefix
    for prefix in ["search ", "dhundo ", "find ", "koi naya tender hai ", "koi tender hai "]:
        if query_lower.startswith(prefix):
            query_lower = query_lower[len(prefix):]

    result = {
        "state_portals": [],
        "central_portals": [],
        "keyword": query_lower,
        "tips": [],
    }

    # Detect states from query
    matched_states = detect_states_from_text(query_lower)

    # Get state-specific portals
    seen = set()
    for state_key in matched_states:
        state = STATES.get(state_key)
        if state:
            for url in state.get("portals", []):
                if url not in seen:
                    result["state_portals"].append({
                        "name": state["name"],
                        "url": url,
                    })
                    seen.add(url)

    # Detect work-type related central portals
    for work_kw, portal_codes in WORK_PORTAL_MAP.items():
        if work_kw in query_lower:
            for cp in CENTRAL_PORTALS:
                if cp["code"] in portal_codes and cp["url"] not in seen:
                    result["central_portals"].append({
                        "name": cp["name"],
                        "url": cp["url"],
                    })
                    seen.add(cp["url"])

    # Always include eprocure.gov.in (covers everything)
    eprocure_url = "https://eprocure.gov.in"
    if eprocure_url not in seen:
        result["central_portals"].append({
            "name": "Central Public Procurement Portal (all tenders)",
            "url": eprocure_url,
        })

    # Ladakh-specific tips
    if "ladakh" in query_lower or "leh" in query_lower or "kargil" in query_lower:
        result["tips"].append("⛰️ Ladakh: BRO aur NHIDCL ke portals zaroor check karo — high value tenders milte hain")
        result["tips"].append("📝 jktenders.gov.in pe bhi Ladakh ke tenders aate hain")

    # BRO tip for border states
    if any(kw in query_lower for kw in ["border", "bro", "defence", "army", "military"]):
        result["tips"].append("🛡️ BRO tenders: Less competition, strategic priority, faster payments")

    return result


def format_search_results(results: dict) -> str:
    """Formats search results into a WhatsApp-friendly message."""
    keyword = results.get("keyword", "")
    state_portals = results.get("state_portals", [])
    central_portals = results.get("central_portals", [])
    tips = results.get("tips", [])

    if not state_portals and not central_portals:
        return (
            f"🔍 \"{keyword}\" ke liye koi specific portal nahi mila.\n\n"
            f"Yeh try karo:\n"
            f"→ eprocure.gov.in — All India search\n"
            f"→ gem.gov.in — Government marketplace\n\n"
            f"Portal pe search karke PDF milo toh mujhe bhejo — main analyze kar dunga! 📄"
        )

    msg = f"🔍 \"{keyword}\" ke liye yeh portals check karo:\n\n"

    if state_portals:
        msg += "📍 STATE PORTALS:\n"
        for i, p in enumerate(state_portals[:5], 1):
            msg += f"  {i}. {p['name']}\n     → {p['url']}\n"
        msg += "\n"

    if central_portals:
        msg += "🏛️ CENTRAL PORTALS:\n"
        for i, p in enumerate(central_portals[:5], 1):
            msg += f"  {i}. {p['name']}\n     → {p['url']}\n"
        msg += "\n"

    if tips:
        msg += "💡 TIPS:\n"
        for tip in tips:
            msg += f"  {tip}\n"
        msg += "\n"

    msg += (
        "In portals pe ja ke search karo.\n"
        "PDF mila toh mujhe bhejo —\n"
        "main 3 min mein analyze kar dunga! 📄"
    )

    return msg

