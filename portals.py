"""
Complete India Tender Portal Database
Covers all 28 States, 8 Union Territories, Central Government, PSUs, and Defence portals.
Special focus on Ladakh UT.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CENTRAL GOVERNMENT PORTALS (Always monitor)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CENTRAL_PORTALS = [
    {"name": "Central Public Procurement Portal", "url": "https://eprocure.gov.in", "code": "CPPP", "priority": "high"},
    {"name": "Government e-Marketplace", "url": "https://gem.gov.in", "code": "GeM", "priority": "high"},
    {"name": "National Tender Portal", "url": "https://tenders.gov.in", "code": "NTP", "priority": "high"},
    {"name": "Central Public Procurement", "url": "https://cppp.gov.in", "code": "CPPP2", "priority": "high"},
    {"name": "Indian Railways e-Procurement", "url": "https://ireps.gov.in", "code": "IREPS", "priority": "medium"},
    {"name": "NHAI Tenders", "url": "https://tenders.nhai.gov.in", "code": "NHAI", "priority": "medium"},
    {"name": "NTPC Power Projects", "url": "https://ntpc.co.in/tenders", "code": "NTPC", "priority": "medium"},
    {"name": "BHEL Engineering", "url": "https://bhel.com/tenders", "code": "BHEL", "priority": "medium"},
    {"name": "ONGC Oil and Gas", "url": "https://ongcindia.com/tenders", "code": "ONGC", "priority": "medium"},
    {"name": "Coal India", "url": "https://coalindia.in/tenders", "code": "CIL", "priority": "medium"},
    {"name": "Border Roads Organisation", "url": "https://bro.gov.in/tenders", "code": "BRO", "priority": "high"},
    {"name": "Military Engineering Services", "url": "https://mes.gov.in/tenders", "code": "MES", "priority": "medium"},
    {"name": "Central Public Works Department", "url": "https://cpwd.gov.in/tenders", "code": "CPWD", "priority": "high"},
    {"name": "NHIDCL Border Highways", "url": "https://nhidcl.com/tenders", "code": "NHIDCL", "priority": "high"},
    {"name": "Airports Authority of India", "url": "https://aaiclas.aai.aero", "code": "AAI", "priority": "medium"},
    {"name": "Solar Energy Corporation", "url": "https://seci.co.in/tenders", "code": "SECI", "priority": "medium"},
    {"name": "Power Grid Corporation", "url": "https://pgcil.co.in/tenders", "code": "PGCIL", "priority": "medium"},
    {"name": "Nuclear Power Corporation", "url": "https://npcil.nic.in/tenders", "code": "NPCIL", "priority": "low"},
    {"name": "JICA Funded Projects", "url": "https://jica.go.jp/india", "code": "JICA", "priority": "low"},
    {"name": "World Bank Funded Projects", "url": "https://worldbank.org/india", "code": "WB", "priority": "low"},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALL STATES AND UNION TERRITORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATE_PORTALS = {
    # ── NORTH INDIA ──
    "1": {
        "name": "Uttar Pradesh",
        "code": "UP",
        "region": "NORTH",
        "portals": ["https://etender.up.nic.in"],
        "departments": ["UP PWD", "UP Jal Nigam", "UP Housing Board", "UPEIDA", "UP Metro", "Lucknow Metro", "Kanpur Metro", "Agra Metro", "UP Expressways Authority"],
    },
    "2": {
        "name": "Delhi",
        "code": "DL",
        "region": "NORTH",
        "portals": ["https://ddtenders.gov.in", "https://delhigovt.nic.in/tenders"],
        "departments": ["DDA", "DMRC (Delhi Metro)", "NDMC", "MCD", "Delhi PWD", "Delhi Jal Board", "DSIIDC", "Delhi Urban Shelter Board"],
    },
    "3": {
        "name": "Haryana",
        "code": "HR",
        "region": "NORTH",
        "portals": ["https://haryanaeprocurement.gov.in"],
        "departments": ["Haryana PWD", "HRERA", "HSVP (Housing Board)", "Haryana Urban Development", "HSIIDC Industrial"],
    },
    "4": {
        "name": "Punjab",
        "code": "PB",
        "region": "NORTH",
        "portals": ["https://eproc.punjab.gov.in"],
        "departments": ["Punjab PWD", "PUDA", "Punjab Water Supply Board", "Punjab Housing Board", "PSPCL Power"],
    },
    "5": {
        "name": "Himachal Pradesh",
        "code": "HP",
        "region": "NORTH",
        "portals": ["https://hptenders.gov.in"],
        "departments": ["HP PWD", "HP Housing Board", "HP Tourism", "HP Jal Shakti", "HPSEBL Power", "HP Urban Development"],
    },
    "6": {
        "name": "Uttarakhand",
        "code": "UK",
        "region": "NORTH",
        "portals": ["https://uktenders.gov.in"],
        "departments": ["UK PWD", "UPCL Power", "UK Housing Board", "UK Jal Sansthan", "RISHDA Industrial", "Char Dham Project"],
    },
    "7": {
        "name": "Jammu & Kashmir",
        "code": "JK",
        "region": "NORTH",
        "is_ut": True,
        "portals": ["https://jktenders.gov.in", "https://jkprocurement.gov.in"],
        "departments": ["JK PWD", "JK Housing Board", "JK Tourism", "JK Urban Development", "JKPCC Construction Corp", "JK Power Development", "JK Jal Shakti Vibhag", "SIDCO Industrial", "JK Economic Reconstruction"],
    },
    "8": {
        "name": "Ladakh",
        "code": "LA",
        "region": "NORTH",
        "is_ut": True,
        "is_special": True,
        "portals": [
            "https://ladakhtenders.gov.in",
            "https://jktenders.gov.in",
            "https://eprocure.gov.in",
            "https://bro.gov.in/tenders",
            "https://nhidcl.com/tenders",
        ],
        "departments": [
            "Ladakh PWD", "BRO — Project Himank (Leh)", "BRO — Project Beacon (Zoji La)",
            "BRO — Project Vijayak (Kargil)", "NHIDCL Ladakh Highways",
            "NHAI Ladakh Zone", "LAHDC Leh", "LAHDC Kargil",
            "Leh Municipal Committee", "Kargil Municipal Committee",
            "UT Administration Ladakh", "Jal Jeevan Mission Ladakh",
            "Ladakh Power Development", "LREDA (Renewable Energy)",
            "MES Ladakh", "GREF (BRO Maintenance)", "Ladakh Tourism",
            "Ladakh Agriculture", "BSNL Ladakh",
        ],
        "special_notes": {
            "altitude": "High altitude construction (3500m - 5500m)",
            "winter_shutdown": "October to April — limited work possible",
            "transport": "Material via Zoji La / Rohtang — seasonal closure risk",
            "bro_coordination": "BRO tenders: ₹10Cr to ₹500Cr, less competition, strategic priority, faster payments",
            "districts": ["Leh", "Kargil"],
        },
    },
    "9": {
        "name": "Rajasthan",
        "code": "RJ",
        "region": "NORTH",
        "portals": ["https://sppp.rajasthan.gov.in", "https://rajasthan.gov.in/tenders"],
        "departments": ["Rajasthan PWD", "RUIDP", "Rajasthan Housing Board", "PHED Water", "RVNL Railways", "Rajasthan Urban Development", "RIICO Industrial"],
    },

    # ── WEST INDIA ──
    "10": {
        "name": "Maharashtra",
        "code": "MH",
        "region": "WEST",
        "portals": ["https://mahatenders.gov.in", "https://maharashtra.etenders.in"],
        "departments": ["Maharashtra PWD", "MMRDA", "Mumbai Metro (MMRCL)", "Pune Metro (PMRDA)", "Nagpur Metro (Maha Metro)", "CIDCO", "MHADA Housing", "Maharashtra Jeevan Pradhikaran", "MSRDC", "BMC", "PMC", "NMC", "MIDC Industrial", "MSEDCL Power"],
    },
    "11": {
        "name": "Gujarat",
        "code": "GJ",
        "region": "WEST",
        "portals": ["https://nprocure.com", "https://gujarat.gov.in/tenders"],
        "departments": ["Gujarat PWD", "GMDA Ahmedabad Metro", "Surat Metro", "GIFT City", "GHB Housing", "GWSSB Water", "GSECL Power", "GIDC Industrial", "Sardar Sarovar Dam"],
    },
    "12": {
        "name": "Madhya Pradesh",
        "code": "MP",
        "region": "WEST",
        "portals": ["https://mptenders.gov.in"],
        "departments": ["MP PWD", "MP Housing Board", "Bhopal Metro", "Indore Metro", "MP Urban Development", "MPWRD Water Resources", "MP Power"],
    },
    "13": {
        "name": "Goa",
        "code": "GA",
        "region": "WEST",
        "portals": ["https://goatenders.gov.in"],
        "departments": ["Goa PWD", "GDA", "Goa Housing Board", "EDC Industrial Goa", "Goa Tourism"],
    },
    "14": {
        "name": "Chhattisgarh",
        "code": "CG",
        "region": "WEST",
        "portals": ["https://cgeprocurement.gov.in"],
        "departments": ["CG PWD", "CSPHCL Power", "CG Housing Board", "CSEB Industrial"],
    },

    # ── SOUTH INDIA ──
    "15": {
        "name": "Karnataka",
        "code": "KA",
        "region": "SOUTH",
        "portals": ["https://kppp.karnataka.gov.in"],
        "departments": ["Karnataka PWD", "Bangalore Metro (BMRCL)", "BDA", "BBMP", "KIADB Industrial", "KUWSDB Water", "BESCOM Power", "Karnataka Housing Board"],
    },
    "16": {
        "name": "Tamil Nadu",
        "code": "TN",
        "region": "SOUTH",
        "portals": ["https://tntenders.gov.in"],
        "departments": ["TN PWD", "CMDA Chennai", "Chennai Metro (CMRL)", "TNHB Housing", "TWAD Water", "TIDCO Industrial", "TNEB Power"],
    },
    "17": {
        "name": "Telangana",
        "code": "TS",
        "region": "SOUTH",
        "portals": ["https://tender.telangana.gov.in"],
        "departments": ["Telangana PWD", "HMDA", "Hyderabad Metro (HMRL)", "TSIIC Industrial", "TSGENCO Power", "GHMC", "HMWSSB Water"],
    },
    "18": {
        "name": "Andhra Pradesh",
        "code": "AP",
        "region": "SOUTH",
        "portals": ["https://tender.apeprocurement.gov.in"],
        "departments": ["AP PWD", "CRDA Amaravati", "APEPDCL Power", "AP Housing Corporation", "Visakhapatnam Metro"],
    },
    "19": {
        "name": "Kerala",
        "code": "KL",
        "region": "SOUTH",
        "portals": ["https://etenders.kerala.gov.in"],
        "departments": ["Kerala PWD", "Kochi Metro (KMRL)", "Kerala Housing Board", "KWA Water", "KSEB Power", "KINFRA Industrial"],
    },

    # ── EAST INDIA ──
    "20": {
        "name": "West Bengal",
        "code": "WB",
        "region": "EAST",
        "portals": ["https://wbtenders.gov.in"],
        "departments": ["WB PWD", "HIDCO", "Kolkata Metro (KMRC)", "WBHIDCO Housing", "WBSEDCL Power", "KMC", "WBIDC Industrial"],
    },
    "21": {
        "name": "Bihar",
        "code": "BR",
        "region": "EAST",
        "portals": ["https://eproc.bihar.gov.in"],
        "departments": ["Bihar PWD", "BSPHCL Power", "Bihar Urban Development", "BUDA Housing", "Patna Metro"],
    },
    "22": {
        "name": "Jharkhand",
        "code": "JH",
        "region": "EAST",
        "portals": ["https://jharkhandtenders.gov.in"],
        "departments": ["Jharkhand PWD", "JBVNL Power", "Jharkhand Housing Board", "JIIDCO Industrial"],
    },
    "23": {
        "name": "Odisha",
        "code": "OD",
        "region": "EAST",
        "portals": ["https://tendersodisha.gov.in"],
        "departments": ["Odisha PWD", "OHPC Power", "Odisha Housing Board", "IDCO Industrial", "Bhubaneswar Metro"],
    },
    "24": {
        "name": "Assam",
        "code": "AS",
        "region": "EAST",
        "portals": ["https://assamtenders.gov.in"],
        "departments": ["Assam PWD", "APGCL Power", "Assam Housing Board", "Guwahati Metro", "ASTC Transport"],
    },

    # ── NORTHEAST ──
    "25": {
        "name": "Meghalaya",
        "code": "ML",
        "region": "NORTHEAST",
        "portals": ["https://megtenders.gov.in", "https://eprocure.gov.in"],
        "departments": ["Meghalaya PWD"],
    },
    "26": {
        "name": "Tripura",
        "code": "TR",
        "region": "NORTHEAST",
        "portals": ["https://tripuratenders.gov.in", "https://eprocure.gov.in"],
        "departments": ["Tripura PWD"],
    },
    "27": {
        "name": "Manipur",
        "code": "MN",
        "region": "NORTHEAST",
        "portals": ["https://manipurtenders.gov.in", "https://eprocure.gov.in"],
        "departments": ["Manipur PWD"],
    },
    "28": {
        "name": "Nagaland",
        "code": "NL",
        "region": "NORTHEAST",
        "portals": ["https://tendersinnagaland.com", "https://eprocure.gov.in"],
        "departments": ["Nagaland PWD"],
    },
    "29": {
        "name": "Mizoram",
        "code": "MZ",
        "region": "NORTHEAST",
        "portals": ["https://eprocure.gov.in", "https://mizoram.gov.in/tenders"],
        "departments": ["Mizoram PWD"],
    },
    "30": {
        "name": "Arunachal Pradesh",
        "code": "AR",
        "region": "NORTHEAST",
        "portals": ["https://eprocure.gov.in", "https://arunachalpradesh.gov.in/tenders"],
        "departments": ["Arunachal PWD", "BRO Arunachal"],
    },
    "31": {
        "name": "Sikkim",
        "code": "SK",
        "region": "NORTHEAST",
        "portals": ["https://sikkimtender.gov.in", "https://eprocure.gov.in"],
        "departments": ["Sikkim PWD"],
    },

    # ── OTHER UTs ──
    "32": {
        "name": "Chandigarh",
        "code": "CH",
        "region": "UT",
        "is_ut": True,
        "portals": ["https://eprocure.gov.in", "https://chandigarh.gov.in/tenders"],
        "departments": ["Chandigarh Administration"],
    },
    "33": {
        "name": "Puducherry",
        "code": "PY",
        "region": "UT",
        "is_ut": True,
        "portals": ["https://eprocure.gov.in", "https://pudutenders.gov.in"],
        "departments": ["Puducherry PWD"],
    },
    "34": {
        "name": "Andaman & Nicobar",
        "code": "AN",
        "region": "UT",
        "is_ut": True,
        "portals": ["https://eprocure.gov.in", "https://andaman.gov.in/tenders"],
        "departments": ["A&N Administration"],
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOCATION SELECTION MESSAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOCATION_SELECTION_MSG = """Kahan kaam karte ho? 📍

NORTH:
1️⃣ Uttar Pradesh
2️⃣ Delhi
3️⃣ Haryana
4️⃣ Punjab
5️⃣ Himachal Pradesh
6️⃣ Uttarakhand
7️⃣ Jammu & Kashmir
8️⃣ Ladakh ⛰️
9️⃣ Rajasthan

WEST:
🔟 Maharashtra
1️⃣1️⃣ Gujarat
1️⃣2️⃣ Madhya Pradesh
1️⃣3️⃣ Goa
1️⃣4️⃣ Chhattisgarh

SOUTH:
1️⃣5️⃣ Karnataka
1️⃣6️⃣ Tamil Nadu
1️⃣7️⃣ Telangana
1️⃣8️⃣ Andhra Pradesh
1️⃣9️⃣ Kerala

EAST:
2️⃣0️⃣ West Bengal
2️⃣1️⃣ Bihar
2️⃣2️⃣ Jharkhand
2️⃣3️⃣ Odisha
2️⃣4️⃣ Assam

NORTHEAST:
2️⃣5️⃣–3️⃣1️⃣ Meghalaya to Sikkim

UTs:
3️⃣2️⃣ Chandigarh
3️⃣3️⃣ Puducherry
3️⃣4️⃣ Andaman & Nicobar

3️⃣5️⃣ ALL INDIA 🇮🇳

Reply: Number ya numbers
eg: '8' for Ladakh only
    '7,8' for J&K + Ladakh
    '35' for All India"""


def get_ladakh_alert(tender_data: dict) -> str:
    """Generates a Ladakh-specific alert message with high-altitude warnings."""
    return f"""🔔 LADAKH TENDER ALERT!
━━━━━━━━━━━━━━━━━━━━━━━━
🏢 {tender_data.get('department', 'N/A')}
📋 {tender_data.get('work_description', 'N/A')}
📍 {tender_data.get('location', 'Ladakh UT')}
💰 Value: ₹{tender_data.get('value', 'N/A')}
📅 Deadline: {tender_data.get('deadline_date', 'N/A')} ({tender_data.get('days_remaining', 'X')} din baaki)
🔢 Tender No: {tender_data.get('tender_number', 'N/A')}
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


def get_portals_for_states(state_keys: list) -> list:
    """Returns all relevant portals for given state keys."""
    portals = []
    for key in state_keys:
        state = STATE_PORTALS.get(key)
        if state:
            for url in state.get("portals", []):
                portals.append({"state": state["name"], "url": url})
    # Always include central portals
    for cp in CENTRAL_PORTALS:
        portals.append({"state": "Central", "url": cp["url"]})
    return portals


def parse_location_input(text: str) -> list:
    """Parses user location input like '7,8' or '35' into state keys."""
    text = text.strip()
    if "35" in text:
        return list(STATE_PORTALS.keys())
    
    keys = []
    for part in text.replace(" ", "").split(","):
        part = part.strip()
        if part in STATE_PORTALS:
            keys.append(part)
    return keys


def get_state_names(keys: list) -> str:
    """Returns comma-separated state names for given keys."""
    names = []
    for k in keys:
        state = STATE_PORTALS.get(k)
        if state:
            names.append(state["name"])
    return ", ".join(names) if names else "All India"
