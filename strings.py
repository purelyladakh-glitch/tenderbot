# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MULTI-LANGUAGE STRINGS — COMPLETE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Hinglish is the default fallback for any missing key in other languages.

_HINGLISH = {
    # Onboarding
    "welcome_new": "👋 Welcome to *TenderBot*!\n\nMain kisi bhi Government Tender PDF ko 3 minute mein padh kar bata sakta hoon:\n✅ Kya aap qualify karte ho?\n✅ Hidden Risks & problems\n✅ BOQ Rates aur Profit estimate\n\nShuru karne ke liye, apni bhasha chunein (Sirf Number reply karo):",
    "lang_menu": "🌐 *Bhasha Chunein / Select Language:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (Default)\n4️⃣ Marathi (मराठी)\n\n👉 *Sirf 1, 2, 3, ya 4 type karo!*",
    "lang_set_success": "✅ Language *Hinglish* set ho gayi hai.\n\nAb, mujhe koi bhi Tender ka *PDF file* ya link bhejo, aur main turant analyze kar dunga! 📄",
    "welcome_message": "👋 TenderBot mein wapas swagat hai!\n\n📄 Tender PDF bhejo — 3 min mein full report.\n⚙️ \"Alert chahiye\" type karo preferences set karne ke liye.\n💰 \"Plan\" type karo plans dekhne ke liye.\n🌐 \"Language\" type karo bhasha badalne ke liye.",

    # Analysis Menu
    "menu_title": "📊 *Tender Analysis Menu*",
    "menu_opt_1": "1️⃣ Eligibility Check (Qualify karte ho?)",
    "menu_opt_2": "2️⃣ Hidden Risks & Problems",
    "menu_opt_3": "3️⃣ BOQ Rates & Bid Amount",
    "menu_opt_4": "4️⃣ Required Documents",
    "menu_opt_5": "5️⃣ Cash Flow Required (Kitna paisa chahiye)",
    "menu_opt_6": "6️⃣ View Profit & Cost Estimate",
    "menu_opt_7": "7️⃣ Full Report (Sab ek saath)",
    "menu_opt_8": "8️⃣ Download PDF ⬇️",
    "menu_opt_9": "9️⃣ Share & Earn (Free credits) 🎁",
    "menu_footer": "👉 *Sirf 1, 2, 3... type karke bhej do!*",

    # Status Messages
    "analyzing_wait": "⏳ Aapka tender abhi analyze ho raha hai... thoda wait karo (2-3 min).",
    "still_analyzing": "Still analyzing... almost done ⏳",
    "error_generic": "❌ Sorry, kuch error aa gaya. Thodi der baad try karo.",
    "unrecognized": "❓ Samjha nahi. PDF bhejo ya menu mein se number choose karo.",
    "send_pdf_first": "📄 Pehle ek Tender PDF bhejo — main 3 minute mein poora analysis de dunga!",

    # PDF Handling
    "pdf_received_analyzing": "📄 Tender mil gaya!\n⏳ Poora analyze kar raha hoon — 3 minute mein complete report bhejta hoon.",
    "pdf_too_large": "⚠️ PDF bahut bada hai (>50MB).\nCompress karke bhejo ya portal ka link do.",
    "documents_checklist_prompt": "Jab tak main analyze karta hoon —\nyeh documents ready hain aapke paas?\n\n□ ITR last 3 years\n□ CA certified balance sheet\n□ Registration certificate\n□ GST certificate\n□ Completion certificates of past work\n□ Solvency certificate\n\nJo ready nahi hai batao — main deadline check karke batata hoon.",

    # Preference Setup
    "pref_location_prompt": "📍 *Aap kahan kaam karte ho?*\n(Sirf *Number* reply karo. Multiple ke liye comma lagao, jaise: 2, 4):\n\n1️⃣ All India 🇮🇳\n2️⃣ Maharashtra 🏙️\n3️⃣ Delhi NCR 🏛️\n4️⃣ Punjab & Haryana 🌾\n5️⃣ J&K & Ladakh ⛰️\n6️⃣ Uttar Pradesh 🕌\n7️⃣ Karnataka 🏢\n8️⃣ Gujarat 🏭\n\n👉 *Ya apna State/City type karo!*",
    "pref_location_error": "❓ Samjha nahi. Sirf Option Number bhi bhej sakte ho (1 se 8 tak).",
    "pref_location_noted": "✅ Location noted: {names}{ladakh_note}",
    "pref_ladakh_note": "\n\n⛰️ Ladakh selected — BRO, NHIDCL, MES, LAHDC tenders bhi tracked honge!",
    "pref_work_type_prompt": "🔨 *Kaunsa kaam karte ho?*\n(Sirf *Number* reply karo. Multiple = 1, 3):\n\n1️⃣ Roads & Highways 🛣️\n2️⃣ Building / Civil Works 🏗️\n3️⃣ Electrical Works ⚡\n4️⃣ Water Supply / Plumbing 💧\n5️⃣ Bridges & Flyovers 🌉\n6️⃣ Solar & Renewable ☀️\n\n👉 *Ya apna work type likh do!*",
    "pref_work_type_noted": "✅ Work types noted: {work_types}",
    "pref_value_range_prompt": "💰 *Kitni value ke tenders chahiye?*\n(Sirf *Number* reply karo):\n\n1️⃣ Upto 50 Lakh\n2️⃣ 50 Lakh - 5 Crore\n3️⃣ 5 Crore - 20 Crore\n4️⃣ 20 Crore - 100 Crore\n5️⃣ All Amounts (Sabhi)\n\n👉 *Ya apni range likho (Jaise: \"2 Cr se 5 Cr\")*",
    "pref_value_range_noted": "✅ Value range: {min_disp} to {max_disp}",
    "pref_departments_prompt": "🏢 *Kaunse depts ke tenders chahiye?*\n(Sirf *Number* reply karo. Jaise: 1, 2):\n\n1️⃣ Sabhi Sarkari (All Gov) 🏛️\n2️⃣ PWD / CPWD / Municipal 🏢\n3️⃣ Highways (NHAI, BRO, NHIDCL) 🛣️\n4️⃣ Railways & Metro 🚂\n5️⃣ Jal Board / Water Depts 💧\n6️⃣ Defence / MES 🛡️\n\n👉 *Ya apna dept likh do!*",
    "pref_departments_noted": "✅ Departments: {departments}",
    "pref_alert_freq_prompt": "⏰ *Kitni baar alert chahiye?*\n(Sirf *Number* reply karo):\n\n1️⃣ Instant 🚀 (Naya aate hi turant alert)\n2️⃣ Daily Morning ☀️ (Subah 8 baje digest)\n3️⃣ Weekly 📅 (Monday summary)",
    "pref_summary": "✅ Preferences save ho gayi!\n\n📍 LOCATIONS: {state_names}\n🔨 WORK TYPES: {work_types}\n💰 VALUE: {min_value} — {max_value}\n🏢 DEPARTMENTS: {departments}\n⏰ ALERTS: {alerts}\n📡 {num_portals} portals tracked\n\nMatching tenders milenge!\n\nChange karna ho kabhi bhi:\nType karo \"preference update\"\n\nAb tender PDF bhejo ya wait karo alerts ke liye! 📄",
    "freq_instant": "Turant — real time 🚀",
    "freq_daily": "Daily 8 AM digest ☀️",
    "freq_weekly": "Weekly Monday summary 📅",

    # Plans & Payment
    "plan_options": "⭐ *TenderBot Plans:*\n\n1️⃣ *Buy 1 Report (₹99)*\nBest for occasional use. Valid 48 hrs.\n\n2️⃣ *Starter Pack - 5 Reports (₹399) 🔥 Best Value*\nLive searches, full analysis reports. Valid 60 days.\n\n3️⃣ *Unlimited Pro + Alerts (₹799/month)*\n30 reports + Unlimited AI alert analysis. Bot hunts tenders for you!\n\n👉 *Kaunsa plan chahiye? Sirf Number reply karo!*",
    "single_plan_msg": "📄 *₹99 — Single Analysis*\n1 complete tender report. Valid 48 hours.",
    "pack_plan_msg": "⭐ *₹399 — 5 Analysis Pack*\n5 full tender reports. Valid 60 days. Best value!",
    "monthly_plan_msg": "🚀 *₹799 — Monthly Pro*\n30 reports + Unlimited AI tender alerts. Bot hunts for you!",
    "payment_link_message": "💳 UPI Payment Link:\n{link}\n\nPayment hote hi turant unlock ho jayega. 🔓",
    "free_analysis_used": "✅ Aapka free analysis use ho gaya.",
    "payment_options_prompt": "Agle tender ke liye:\n\n1️⃣ ₹99  — 1 Analysis 📄\n2️⃣ ₹399 — 5 Analyses Pack ⭐ (Best Value)\n3️⃣ ₹799 — Monthly Pro + Alerts 🚀\n\n👉 *Abhi ₹99 se shuru karne ke liye link pe click karein:*\n{link_99}\n\n👉 *Bade plan (2 ya 3) ke liye sirf Number reply karo!*",

    # Balance
    "plan_free": "Free",
    "plan_single": "₹99 Single",
    "plan_pack": "₹399 Pack",
    "plan_monthly": "₹799 Monthly",
    "balance_expiry": "\n📅 Expiry: {expiry_date} ({days_left} din baaki)",
    "balance_details": "📊 Aapka Account:\n\nPlan: {plan_name}\nCredits: {credits}\nFree analysis: {free_analysis_status}\nTotal analyses done: {total_analyses}{expiry_info}\n\nUpgrade ya renew karna hai?\nType karo \"plan\" ya \"799 wala\"",
    "used": "Used ✓",
    "available": "Available ✅",

    # Alerts
    "alerts_paused": "✅ Alerts 7 din ke liye pause ho gaye.\nResume karne ke liye type karo: \"alerts shuru karo\"",
    "alerts_resumed": "✅ Alerts fir shuru ho gaye!\nMatching tenders milte rahenge. 🔔",

    # History
    "no_past_analysis": "📋 Koi past analysis nahi mila. Tender PDF bhejo!",
    "recent_analyses_header": "📋 Aapke recent analyses:",
    "total_analyses_done": "\nTotal: {total} analyses kiye hain.",

    # Verdict (after PDF analysis)
    "verdict_header": "━━━━━━━━━━━━━━━━━━━━━━━━\n📋 {department} — {work}\n💰 Value: ₹{value}\n📅 Deadline: {deadline} ({days} din baaki)\n\n⚡ VERDICT: {verdict} — {score}/10\n\n🔴 {critical} Critical risks\n🟡 {warnings} Warnings\n💡 Recommended bid: ₹{bid}\n💰 Estimated profit: ₹{profit}\n━━━━━━━━━━━━━━━━━━━━━━━━",
    "verdict_menu": "\nKya dekhna chahte ho?\n(Sirf *Number* reply karo!)\n\n1️⃣ *Am I Eligible?*\n2️⃣ *Show Hidden Risks*\n3️⃣ *Get Bid Strategy*\n4️⃣ *Action & Documents*\n5️⃣ *Cash Flow Check*\n6️⃣ *View Profit & Cost*\n7️⃣ *Full Report*\n8️⃣ *Download PDF* ⬇️\n9️⃣ *Share & Earn* 🎁\n\n👉 *Sirf 1, 2, 3... type karke bhej do!*",
    "menu_fallback": "Samjha nahi. Sirf option ka *Number* reply karo:\n\n1️⃣ Am I Eligible?\n2️⃣ Show Hidden Risks\n3️⃣ Get Bid Strategy\n4️⃣ Action & Documents\n5️⃣ Cash Flow Check\n6️⃣ View Profit & Cost\n7️⃣ Full Report\n8️⃣ Download PDF\n9️⃣ Share & Earn 🎁\n\nYa type karo:\n💳 *Plan* — Upgrade karne ke liye\n⚙️ *Alerts* — Preferences set karne ke liye",
    "section_not_available": "Is section mein information available nahi hai.",
    "analysis_parse_error": "Purana analysis parse nahi ho raha. PDF dobara bhejo.",

    # Payment Success
    "payment_single_success": "Payment received! ✅\n1 analysis unlock ho gaya.\n\nTender PDF bhejo! 📄",
    "payment_pack_success": "Payment received! ✅\n5 analyses unlock ho gaye.\n60 din valid hai.\n\nAb alerts mein brief analysis bhi milega!\nTender PDF bhejo ya alerts ka wait karo! 📄",
    "payment_monthly_success": "Payment received! ✅\n⭐ Monthly Unlimited plan active!\n\n30 analyses + UNLIMITED alert analyses\nBot tenders dhundega aapke liye\nFull analysis with every alert — FREE\n\nPreferences set karo: type \"alert chahiye\"\nYa tender PDF bhejo abhi! 📄",
    "payment_generic_success": "Payment received! ✅\nCredits add ho gaye.",

    # Upgrade Nudge
    "upgrade_nudge_post_analysis": "💡 Yeh analysis aapko kaisa laga?\n\nAgle tender ke liye:\n₹399 = 5 analyses (₹80 each)\n₹799 = Unlimited + auto alerts\n\nType karo \"plan\" for details.",
    "upgrade_nudge_free": "Aapko matching tenders mil rahe hain.\nEk bhi analyze nahi kiya abhi tak.\n\n₹399 mein 5 analyses milte hain.\nSirf ₹80 per tender.\n\nType karo: \"399 wala\"",
    "upgrade_nudge_low_credits": "Sirf {credits} credit bacha hai.\n\nRenew karo ₹399 — 5 aur analyses\nYa upgrade karo ₹799/month:\n→ 30 analyses\n→ Alert with full analysis\n→ Search unlimited\n\nType karo: \"plan\"",
    "monthly_report_template": "📊 *Aapka Monthly Report*\n━━━━━━━━━━━━━━━━━━━━━━\n\nANALYSES THIS MONTH: {analysis_count}/30\nALERTS RECEIVED: {alert_count}\nALERT ANALYSES: {free_alert_analyses} (free)\n\nMONEY SAVED VS CONSULTANT:\n{analysis_count} analyses × ₹10,000 = ₹{savings:,}\nYou paid: ₹{paid}\nYou saved: ₹{total_savings:,}\n━━━━━━━━━━━━━━━━━━━━━━\nAapka plan {days_left} din mein expire hoga.\nRenew karo — koi tender miss mat ho.\nType karo: \"renew\"",

    # Referral Reward
    "referral_reward": "🎉 *Badhai Ho!*\n\nAapke dost ne abhi TenderBot ka use kiya.\nAapke account mein *+1 FREE Paid Analysis* add kar diya gaya hai! 🎁\n\nAap abhi koi bhi naya Tender PDF bhej kar isko use kar sakte hain.",

    # PDF Generation
    "pdf_generating": "PDF report generate ho rahi hai... ⏳",
    "pdf_ready": "Lijiye aapki PDF report ready hai! 📄",
    "pdf_link_not_set": "PDF generate ho gayi par download link abhi set nahi hai.",
    "pdf_attach_error": "PDF attach karne mein issue aaya. Dobara try karo.",

    # Error
    "technical_error": "Thoda technical issue hua. 2 minute mein dobara try karo.",
}

_ENGLISH = {
    "welcome_new": "👋 Welcome to *TenderBot*!\n\nI can analyze any Government Tender PDF in 3 minutes:\n✅ Eligibility Check\n✅ Hidden Risks\n✅ BOQ Rates & Profit Estimate\n\nTo begin, please select your preferred language:",
    "lang_menu": "🌐 *Select Language:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (Default)\n4️⃣ Marathi (मराठी)\n\n👉 *Reply with 1, 2, 3, or 4!*",
    "lang_set_success": "✅ Language set to *English*.\n\nPlease send me a Tender *PDF file* and I will analyze it instantly! 📄",
    "welcome_message": "👋 Welcome back to TenderBot!\n\n📄 Send a Tender PDF — full report in 3 minutes.\n⚙️ Type \"alerts\" to set preferences.\n💰 Type \"plan\" to view plans.\n🌐 Type \"language\" to change language.",
    "menu_title": "📊 *Tender Analysis Menu*",
    "menu_opt_1": "1️⃣ Eligibility Check",
    "menu_opt_2": "2️⃣ Hidden Risks & Issues",
    "menu_opt_3": "3️⃣ BOQ Rates & Bid Amount",
    "menu_opt_4": "4️⃣ Required Documents",
    "menu_opt_5": "5️⃣ Cash Flow Required",
    "menu_opt_6": "6️⃣ Profit & Cost Estimate",
    "menu_opt_7": "7️⃣ Full Report",
    "menu_opt_8": "8️⃣ Download PDF ⬇️",
    "menu_opt_9": "9️⃣ Share & Earn Credits 🎁",
    "menu_footer": "👉 *Reply with 1, 2, 3...*",
    "analyzing_wait": "⏳ Analyzing your tender... please wait 2-3 minutes.",
    "still_analyzing": "Still analyzing... almost done ⏳",
    "error_generic": "❌ Sorry, an error occurred. Please try again later.",
    "unrecognized": "❓ I didn't understand. Please send a PDF or pick a menu option.",
    "send_pdf_first": "📄 Please send a Tender PDF first — I'll deliver a full report in 3 minutes!",
    "pdf_received_analyzing": "📄 Tender received!\n⏳ Running full AI analysis — report ready in 3 minutes.",
    "pdf_too_large": "⚠️ PDF is too large (>50MB).\nPlease compress and resend.",
    "documents_checklist_prompt": "While I analyze, do you have these documents ready?\n\n□ ITR (last 3 years)\n□ CA certified balance sheet\n□ Registration certificate\n□ GST certificate\n□ Past work completion certificates\n□ Solvency certificate\n\nLet me know what you're missing.",
    "pref_location_prompt": "📍 *Where do you work?*\n(Reply with numbers, e.g.: 2, 4):\n\n1️⃣ All India 🇮🇳\n2️⃣ Maharashtra 🏙️\n3️⃣ Delhi NCR 🏛️\n4️⃣ Punjab & Haryana 🌾\n5️⃣ J&K & Ladakh ⛰️\n6️⃣ Uttar Pradesh 🕌\n7️⃣ Karnataka 🏢\n8️⃣ Gujarat 🏭\n\n👉 *Or type your State/City!*",
    "pref_location_error": "❓ Didn't understand. Please reply with option numbers (1 to 8).",
    "pref_location_noted": "✅ Location noted: {names}{ladakh_note}",
    "pref_ladakh_note": "\n\n⛰️ Ladakh selected — BRO, NHIDCL, MES, LAHDC tenders will also be tracked!",
    "pref_work_type_prompt": "🔨 *What type of work do you do?*\n(Reply with numbers, e.g.: 1, 3):\n\n1️⃣ Roads & Highways 🛣️\n2️⃣ Building / Civil 🏗️\n3️⃣ Electrical ⚡\n4️⃣ Water Supply 💧\n5️⃣ Bridges & Flyovers 🌉\n6️⃣ Solar & Renewable ☀️\n\n👉 *Or type your work type!*",
    "pref_work_type_noted": "✅ Work types noted: {work_types}",
    "pref_value_range_prompt": "💰 *What tender value range?*\n\n1️⃣ Up to 50 Lakh\n2️⃣ 50 Lakh - 5 Crore\n3️⃣ 5 Crore - 20 Crore\n4️⃣ 20 Crore - 100 Crore\n5️⃣ All Amounts\n\n👉 *Or type your range (e.g.: \"2 Cr to 5 Cr\")*",
    "pref_value_range_noted": "✅ Value range: {min_disp} to {max_disp}",
    "pref_departments_prompt": "🏢 *Which departments?*\n\n1️⃣ All Government 🏛️\n2️⃣ PWD / CPWD / Municipal 🏢\n3️⃣ Highways (NHAI, BRO, NHIDCL) 🛣️\n4️⃣ Railways & Metro 🚂\n5️⃣ Water Board 💧\n6️⃣ Defence / MES 🛡️\n\n👉 *Or type your department!*",
    "pref_departments_noted": "✅ Departments: {departments}",
    "pref_alert_freq_prompt": "⏰ *How often should we alert you?*\n\n1️⃣ Instant 🚀\n2️⃣ Daily Morning ☀️\n3️⃣ Weekly (Monday) 📅",
    "pref_summary": "✅ Preferences saved!\n\n📍 LOCATIONS: {state_names}\n🔨 WORK TYPES: {work_types}\n💰 VALUE: {min_value} — {max_value}\n🏢 DEPARTMENTS: {departments}\n⏰ ALERTS: {alerts}\n📡 {num_portals} portals tracked\n\nYou will receive matching tender alerts!\n\nTo change anytime, type \"update preferences\"\n\nSend a tender PDF now or wait for alerts! 📄",
    "freq_instant": "Instant — real time 🚀",
    "freq_daily": "Daily 8 AM digest ☀️",
    "freq_weekly": "Weekly Monday summary 📅",
    "plan_options": "⭐ *TenderBot Plans:*\n\n1️⃣ *1 Report (₹99)* — Valid 48 hrs\n2️⃣ *5 Reports (₹399)* 🔥 Best Value — Valid 60 days\n3️⃣ *Unlimited Pro (₹799/mo)* 🚀 — 30 reports + alerts\n\n👉 *Reply with 1, 2, or 3!*",
    "single_plan_msg": "📄 *₹99 — Single Analysis*\n1 complete tender report. Valid 48 hours.",
    "pack_plan_msg": "⭐ *₹399 — 5 Analysis Pack*\n5 reports. Valid 60 days. Best value!",
    "monthly_plan_msg": "🚀 *₹799 — Monthly Pro*\n30 reports + AI tender alerts.",
    "payment_link_message": "💳 Payment Link:\n{link}\n\nCredits unlock instantly after payment. 🔓",
    "free_analysis_used": "✅ Your free analysis has been used.",
    "payment_options_prompt": "For your next tender:\n\n1️⃣ ₹99  — 1 Analysis 📄\n2️⃣ ₹399 — 5 Pack ⭐\n3️⃣ ₹799 — Monthly Pro 🚀\n\n👉 *Quick pay ₹99:*\n{link_99}\n\n👉 *For plan 2 or 3, reply with the number!*",
    "plan_free": "Free",
    "plan_single": "₹99 Single",
    "plan_pack": "₹399 Pack",
    "plan_monthly": "₹799 Monthly",
    "balance_expiry": "\n📅 Expiry: {expiry_date} ({days_left} days left)",
    "balance_details": "📊 Your Account:\n\nPlan: {plan_name}\nCredits: {credits}\nFree analysis: {free_analysis_status}\nTotal analyses: {total_analyses}{expiry_info}\n\nTo upgrade, type \"plan\"",
    "used": "Used ✓",
    "available": "Available ✅",
    "alerts_paused": "✅ Alerts paused for 7 days.\nTo resume, type \"resume alerts\"",
    "alerts_resumed": "✅ Alerts resumed!\nYou will receive matching tenders. 🔔",
    "no_past_analysis": "📋 No past analyses found. Send a Tender PDF!",
    "recent_analyses_header": "📋 Your recent analyses:",
    "total_analyses_done": "\nTotal: {total} analyses done.",
}

_HINDI = {
    "welcome_new": "👋 *TenderBot* में आपका स्वागत है!\n\nमैं किसी भी सरकारी टेंडर PDF को 3 मिनट में एनालाइज़ कर सकता हूँ:\n✅ क्या आप योग्य हैं?\n✅ छुपे खतरे\n✅ BOQ रेट्स और प्रॉफिट अनुमान\n\nकृपया अपनी भाषा चुनें:",
    "lang_menu": "🌐 *भाषा चुनें:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (डिफ़ॉल्ट)\n4️⃣ Marathi (मराठी)\n\n👉 *1, 2, 3, या 4 टाइप करें!*",
    "lang_set_success": "✅ भाषा *हिंदी* सेट हो गई है।\n\nअब, मुझे टेंडर *PDF फ़ाइल* भेजें! 📄",
    "welcome_message": "👋 TenderBot में वापसी!\n\n📄 टेंडर PDF भेजें — 3 मिनट में रिपोर्ट।\n⚙️ \"अलर्ट चाहिए\" लिखें।\n💰 \"प्लान\" लिखें।\n🌐 \"भाषा\" लिखें भाषा बदलने के लिए।",
    "menu_title": "📊 *टेंडर एनालिसिस मेनू*",
    "menu_opt_1": "1️⃣ योग्यता चेक",
    "menu_opt_2": "2️⃣ छुपे खतरे और दिक्कतें",
    "menu_opt_3": "3️⃣ BOQ रेट्स और बिड अमाउंट",
    "menu_opt_4": "4️⃣ ज़रूरी कागज़ात",
    "menu_opt_5": "5️⃣ कितना पैसा चाहिए?",
    "menu_opt_6": "6️⃣ प्रॉफिट और लागत अनुमान",
    "menu_opt_7": "7️⃣ पूरी रिपोर्ट",
    "menu_opt_8": "8️⃣ PDF डाउनलोड ⬇️",
    "menu_opt_9": "9️⃣ शेयर करें, फ्री क्रेडिट पाएं 🎁",
    "menu_footer": "👉 *सिर्फ 1, 2, 3... टाइप करें!*",
    "analyzing_wait": "⏳ टेंडर एनालाइज़ हो रहा है... 2-3 मिनट रुकें।",
    "still_analyzing": "अभी भी एनालाइज़ हो रहा है... लगभग हो गया ⏳",
    "error_generic": "❌ माफ़ करना, कुछ गड़बड़ हो गई। बाद में कोशिश करें।",
    "unrecognized": "❓ समझा नहीं। PDF भेजें या मेनू से नंबर चुनें।",
    "send_pdf_first": "📄 पहले टेंडर PDF भेजें — 3 मिनट में पूरी रिपोर्ट दूँगा!",
    "pdf_received_analyzing": "📄 टेंडर मिल गया!\n⏳ एनालाइज़ कर रहा हूँ — 3 मिनट में रिपोर्ट भेजूँगा।",
    "pdf_too_large": "⚠️ PDF बहुत बड़ा है (>50MB).\nकम्प्रेस करके भेजें।",
    "documents_checklist_prompt": "जब तक मैं एनालाइज़ करता हूँ —\nये कागज़ात तैयार हैं?\n\n□ ITR (3 साल)\n□ CA बैलेंस शीट\n□ रजिस्ट्रेशन सर्टिफिकेट\n□ GST सर्टिफिकेट\n□ पिछले काम के कम्प्लीशन सर्टिफिकेट\n□ सॉल्वेंसी सर्टिफिकेट",
    "pref_location_prompt": "📍 *आप कहाँ काम करते हैं?*\n(नंबर लिखें, जैसे: 2, 4):\n\n1️⃣ पूरा भारत 🇮🇳\n2️⃣ महाराष्ट्र 🏙️\n3️⃣ दिल्ली NCR 🏛️\n4️⃣ पंजाब और हरियाणा 🌾\n5️⃣ J&K और लद्दाख ⛰️\n6️⃣ उत्तर प्रदेश 🕌\n7️⃣ कर्नाटक 🏢\n8️⃣ गुजरात 🏭",
    "pref_location_error": "❓ समझा नहीं। 1 से 8 तक कोई नंबर भेजें।",
    "pref_location_noted": "✅ लोकेशन नोट: {names}{ladakh_note}",
    "pref_ladakh_note": "\n\n⛰️ लद्दाख — BRO, NHIDCL, MES, LAHDC टेंडर भी ट्रैक होंगे!",
    "pref_work_type_prompt": "🔨 *कौनसा काम करते हैं?*\n\n1️⃣ सड़क / हाईवे 🛣️\n2️⃣ बिल्डिंग / सिविल 🏗️\n3️⃣ इलेक्ट्रिकल ⚡\n4️⃣ पानी सप्लाई 💧\n5️⃣ पुल / फ्लाईओवर 🌉\n6️⃣ सोलर ☀️",
    "pref_work_type_noted": "✅ वर्क टाइप: {work_types}",
    "pref_value_range_prompt": "💰 *कितनी वैल्यू के टेंडर?*\n\n1️⃣ 50 लाख तक\n2️⃣ 50 लाख - 5 करोड़\n3️⃣ 5 करोड़ - 20 करोड़\n4️⃣ 20 करोड़ - 100 करोड़\n5️⃣ सभी",
    "pref_value_range_noted": "✅ वैल्यू रेंज: {min_disp} से {max_disp}",
    "pref_departments_prompt": "🏢 *कौनसे विभाग?*\n\n1️⃣ सभी सरकारी 🏛️\n2️⃣ PWD / CPWD / नगर निगम 🏢\n3️⃣ हाईवे (NHAI, BRO) 🛣️\n4️⃣ रेलवे / मेट्रो 🚂\n5️⃣ जल बोर्ड 💧\n6️⃣ रक्षा / MES 🛡️",
    "pref_departments_noted": "✅ विभाग: {departments}",
    "pref_alert_freq_prompt": "⏰ *कितनी बार अलर्ट?*\n\n1️⃣ तुरंत 🚀\n2️⃣ रोज़ सुबह ☀️\n3️⃣ हफ्ते में एक बार 📅",
    "pref_summary": "✅ प्राथमिकताएं सेव!\n\n📍 लोकेशन: {state_names}\n🔨 काम: {work_types}\n💰 वैल्यू: {min_value} — {max_value}\n🏢 विभाग: {departments}\n⏰ अलर्ट: {alerts}\n📡 {num_portals} पोर्टल ट्रैक\n\nमैचिंग टेंडर मिलेंगे!\nबदलने के लिए \"preference update\" लिखें।",
    "freq_instant": "तुरंत 🚀",
    "freq_daily": "रोज़ सुबह 8 बजे ☀️",
    "freq_weekly": "हर सोमवार 📅",
    "plan_options": "⭐ *TenderBot प्लान:*\n\n1️⃣ *1 रिपोर्ट (₹99)* — 48 घंटे\n2️⃣ *5 रिपोर्ट (₹399)* 🔥 — 60 दिन\n3️⃣ *अनलिमिटेड (₹799/महीना)* 🚀 — 30 रिपोर्ट + अलर्ट\n\n👉 *नंबर रिप्लाई करें!*",
    "single_plan_msg": "📄 *₹99 — एक एनालिसिस*\n1 पूरी रिपोर्ट। 48 घंटे।",
    "pack_plan_msg": "⭐ *₹399 — 5 एनालिसिस पैक*\n5 रिपोर्ट। 60 दिन।",
    "monthly_plan_msg": "🚀 *₹799 — मंथली प्रो*\n30 रिपोर्ट + AI अलर्ट।",
    "payment_link_message": "💳 पेमेंट लिंक:\n{link}\n\nभुगतान होते ही अनलॉक। 🔓",
    "free_analysis_used": "✅ फ्री एनालिसिस इस्तेमाल हो गया।",
    "payment_options_prompt": "अगले टेंडर के लिए:\n\n1️⃣ ₹99 — 1 📄\n2️⃣ ₹399 — 5 पैक ⭐\n3️⃣ ₹799 — मंथली 🚀\n\n👉 *₹99 का लिंक:*\n{link_99}\n\n👉 *2 या 3 का नंबर रिप्लाई करें!*",
    "plan_free": "फ्री",
    "plan_single": "₹99 सिंगल",
    "plan_pack": "₹399 पैक",
    "plan_monthly": "₹799 मंथली",
    "balance_expiry": "\n📅 एक्सपायरी: {expiry_date} ({days_left} दिन बाकी)",
    "balance_details": "📊 आपका अकाउंट:\n\nप्लान: {plan_name}\nक्रेडिट: {credits}\nफ्री एनालिसिस: {free_analysis_status}\nकुल एनालिसिस: {total_analyses}{expiry_info}\n\nअपग्रेड के लिए \"प्लान\" लिखें",
    "used": "इस्तेमाल हो गया ✓",
    "available": "उपलब्ध ✅",
    "alerts_paused": "✅ अलर्ट 7 दिन के लिए बंद।\nशुरू करने के लिए \"अलर्ट शुरू\" लिखें।",
    "alerts_resumed": "✅ अलर्ट फिर शुरू! 🔔",
    "no_past_analysis": "📋 कोई पिछला एनालिसिस नहीं। PDF भेजें!",
    "recent_analyses_header": "📋 आपके हाल के एनालिसिस:",
    "total_analyses_done": "\nकुल: {total} एनालिसिस किए।",
}

_MARATHI = {
    "welcome_new": "👋 *TenderBot* मध्ये स्वागत!\n\nमी कोणतीही सरकारी टेंडर PDF ३ मिनिटांत एनालाइज़ करतो:\n✅ पात्रता तपासणी\n✅ छुपे धोके\n✅ BOQ रेट्स आणि नफा अंदाज\n\nकृपया भाषा निवडा:",
    "lang_menu": "🌐 *भाषा निवडा:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (डिफॉल्ट)\n4️⃣ Marathi (मराठी)\n\n👉 *१, २, ३, किंवा ४ टाईप करा!*",
    "lang_set_success": "✅ भाषा *मराठी* सेट झाली.\n\nआता टेंडर *PDF फाईल* पाठवा! 📄",
    "welcome_message": "👋 TenderBot मध्ये परत स्वागत!\n\n📄 टेंडर PDF पाठवा.\n⚙️ \"अलर्ट\" टाईप करा.\n💰 \"प्लान\" टाईप करा.\n🌐 \"भाषा\" टाईप करा.",
    "menu_title": "📊 *टेंडर ऍनालिसिस मेनू*",
    "menu_opt_1": "1️⃣ पात्रता तपासा",
    "menu_opt_2": "2️⃣ छुपे धोके",
    "menu_opt_3": "3️⃣ BOQ रेट्स आणि बिड",
    "menu_opt_4": "4️⃣ आवश्यक कागदपत्रे",
    "menu_opt_5": "5️⃣ किती पैसे लागतील?",
    "menu_opt_6": "6️⃣ नफा आणि खर्च",
    "menu_opt_7": "7️⃣ संपूर्ण अहवाल",
    "menu_opt_8": "8️⃣ PDF डाउनलोड ⬇️",
    "menu_opt_9": "9️⃣ शेअर करा, फ्री क्रेडिट मिळवा 🎁",
    "menu_footer": "👉 *फक्त 1, 2, 3... टाईप करा!*",
    "analyzing_wait": "⏳ टेंडर तपासले जात आहे... २-३ मिनिटे थांबा.",
    "still_analyzing": "अजून तपासत आहे... जवळजवळ झाले ⏳",
    "error_generic": "❌ क्षमस्व, चूक झाली. नंतर प्रयत्न करा.",
    "unrecognized": "❓ समजले नाही. PDF पाठवा किंवा मेनूमधून निवडा.",
    "send_pdf_first": "📄 आधी टेंडर PDF पाठवा — ३ मिनिटांत रिपोर्ट!",
    "pdf_received_analyzing": "📄 टेंडर मिळाले!\n⏳ एनालाइज़ करत आहे — ३ मिनिटांत रिपोर्ट.",
    "pdf_too_large": "⚠️ PDF खूप मोठी आहे (>50MB).\nकम्प्रेस करून पाठवा.",
    "documents_checklist_prompt": "मी एनालाइज़ करतो तोपर्यंत —\nहे कागदपत्रे तयार आहेत का?\n\n□ ITR (३ वर्षे)\n□ CA बॅलन्स शीट\n□ रजिस्ट्रेशन\n□ GST\n□ कामाचे प्रमाणपत्र\n□ सॉल्व्हन्सी",
    "pref_location_prompt": "📍 *तुम्ही कुठे काम करता?*\n\n1️⃣ संपूर्ण भारत 🇮🇳\n2️⃣ महाराष्ट्र 🏙️\n3️⃣ दिल्ली 🏛️\n4️⃣ पंजाब/हरियाणा 🌾\n5️⃣ J&K/लडाख ⛰️\n6️⃣ उत्तर प्रदेश 🕌\n7️⃣ कर्नाटक 🏢\n8️⃣ गुजरात 🏭",
    "pref_location_error": "❓ समजले नाही. १ ते ८ नंबर पाठवा.",
    "pref_location_noted": "✅ लोकेशन: {names}{ladakh_note}",
    "pref_ladakh_note": "\n\n⛰️ लडाख — BRO, NHIDCL, MES ट्रॅक होतील!",
    "pref_work_type_prompt": "🔨 *कोणते काम करता?*\n\n1️⃣ रस्ते 🛣️\n2️⃣ बांधकाम 🏗️\n3️⃣ इलेक्ट्रिकल ⚡\n4️⃣ पाणी पुरवठा 💧\n5️⃣ पूल 🌉\n6️⃣ सोलर ☀️",
    "pref_work_type_noted": "✅ वर्क टाइप: {work_types}",
    "pref_value_range_prompt": "💰 *किती किमतीचे टेंडर?*\n\n1️⃣ ५० लाखांपर्यंत\n2️⃣ ५० लाख - ५ कोटी\n3️⃣ ५ - २० कोटी\n4️⃣ २० - १०० कोटी\n5️⃣ सर्व",
    "pref_value_range_noted": "✅ व्हॅल्यू रेंज: {min_disp} ते {max_disp}",
    "pref_departments_prompt": "🏢 *कोणते विभाग?*\n\n1️⃣ सर्व सरकारी 🏛️\n2️⃣ PWD / नगरपालिका 🏢\n3️⃣ हायवे 🛣️\n4️⃣ रेल्वे / मेट्रो 🚂\n5️⃣ जल बोर्ड 💧\n6️⃣ संरक्षण / MES 🛡️",
    "pref_departments_noted": "✅ विभाग: {departments}",
    "pref_alert_freq_prompt": "⏰ *अलर्ट किती वेळा?*\n\n1️⃣ लगेच 🚀\n2️⃣ रोज सकाळी ☀️\n3️⃣ आठवड्यातून एकदा 📅",
    "pref_summary": "✅ प्राधान्ये सेव्ह!\n\n📍 {state_names}\n🔨 {work_types}\n💰 {min_value} — {max_value}\n🏢 {departments}\n⏰ {alerts}\n📡 {num_portals} पोर्टल\n\nमॅचिंग टेंडर मिळतील!",
    "freq_instant": "लगेच 🚀",
    "freq_daily": "रोज सकाळी ☀️",
    "freq_weekly": "दर सोमवारी 📅",
    "plan_options": "⭐ *TenderBot प्लान:*\n\n1️⃣ *१ रिपोर्ट (₹99)*\n2️⃣ *५ रिपोर्ट (₹399)* 🔥\n3️⃣ *अनलिमिटेड (₹799/महिना)* 🚀\n\n👉 *नंबर पाठवा!*",
    "single_plan_msg": "📄 *₹99 — एक ऍनालिसिस*",
    "pack_plan_msg": "⭐ *₹399 — ५ ऍनालिसिस पॅक*",
    "monthly_plan_msg": "🚀 *₹799 — मंथली प्रो*",
    "payment_link_message": "💳 पेमेंट लिंक:\n{link}\n\nपेमेंट झाल्यावर लगेच अनलॉक. 🔓",
    "free_analysis_used": "✅ फ्री ऍनालिसिस वापरले.",
    "payment_options_prompt": "पुढच्या टेंडरसाठी:\n\n1️⃣ ₹99 📄\n2️⃣ ₹399 पॅक ⭐\n3️⃣ ₹799 मंथली 🚀\n\n👉 *₹99:*\n{link_99}\n\n👉 *२ किंवा ३ साठी नंबर पाठवा!*",
    "plan_free": "फ्री",
    "plan_single": "₹99",
    "plan_pack": "₹399 पॅक",
    "plan_monthly": "₹799 मंथली",
    "balance_expiry": "\n📅 एक्स्पायरी: {expiry_date} ({days_left} दिवस बाकी)",
    "balance_details": "📊 तुमचे अकाउंट:\n\nप्लान: {plan_name}\nक्रेडिट: {credits}\nफ्री: {free_analysis_status}\nएकूण: {total_analyses}{expiry_info}\n\nअपग्रेड — \"प्लान\" टाईप करा",
    "used": "वापरले ✓",
    "available": "उपलब्ध ✅",
    "alerts_paused": "✅ अलर्ट ७ दिवसांसाठी बंद.\nचालू करण्यासाठी \"अलर्ट चालू\" टाईप करा.",
    "alerts_resumed": "✅ अलर्ट पुन्हा चालू! 🔔",
    "no_past_analysis": "📋 मागील ऍनालिसिस नाही. PDF पाठवा!",
    "recent_analyses_header": "📋 तुमचे अलीकडील ऍनालिसिस:",
    "total_analyses_done": "\nएकूण: {total} ऍनालिसिस.",
}

_GUJARATI = {
    # Onboarding
    "welcome_new": "👋 TenderBot માં તમારું સ્વાગત છે!\n\nહું કોઈપણ સરકારી ટેન્ડર PDF ને ૩ મિનિટમાં વાંચીને જણાવી શકું છું:\n✅ શું તમે ક્વોલિફાય કરો છો?\n✅ છુપાયેલા જોખમો અને સમસ્યાઓ\n✅ BOQ દરો અને નફાનો અંદાજ\n\nશરૂ કરવા માટે, તમારી ભાષા પસંદ કરો:",
    "lang_menu": "🌐 *ભાષા પસંદ કરો:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (Default)\n4️⃣ Marathi (મરાઠી)\n5️⃣ Gujarati (ગુજરાતી)\n\n👉 *ફક્ત નંબર ટાઈપ કરો!*",
    "lang_set_success": "✅ ભાષા *Gujarati* સેટ થઈ ગઈ છે.\n\nહવે, મને કોઈપણ ટેન્ડરની *PDF ફાઇલ* અથવા લિંક મોકલો, અને હું તરત જ વિશ્લેષણ કરી આપીશ! 📄",
    "welcome_message": "👋 TenderBot માં ફરી સ્વાગત છે!\n\n📄 ટેન્ડર PDF મોકલો — ૩ મિનિટમાં સંપૂર્ણ રિપોર્ટ.\n⚙️ \"Alert chahiye\" લખો પસંદગીઓ સેટ કરવા માટે.\n💰 \"Plan\" લખો પ્લાન જોવા માટે.\n🌐 \"Language\" લખો ભાષા બદલવા માટે.",

    # Analysis Menu
    "menu_title": "📊 *ટેન્ડર વિશ્લેષણ મેનુ*",
    "menu_opt_1": "1️⃣ પાત્રતા તપાસ (શું તમે ક્વોલિફાય છો?)",
    "menu_opt_2": "2️⃣ છુપાયેલા જોખમો અને સમસ્યાઓ",
    "menu_opt_3": "3️⃣ BOQ દરો અને બિડ રકમ",
    "menu_opt_4": "4️⃣ જરૂરી દસ્તાવેજો",
    "menu_opt_5": "5️⃣ રોકડ પ્રવાહની જરૂરિયાત",
    "menu_opt_6": "6️⃣ નફા અને ખર્ચનો અંદાજ જુઓ",
    "menu_opt_7": "7️⃣ સંપૂર્ણ રિપોર્ટ (બધું એકસાથે)",
    "menu_opt_8": "8️⃣ PDF ડાઉનલોડ કરો ⬇️",
    "menu_opt_9": "9️⃣ શેર કરો અને મેળવો (ફ્રી ક્રેડિટ્સ) 🎁",
    "menu_footer": "👉 *ફક્ત 1, 2, 3... ટાઈપ કરીને મોકલો!*",

    # Status Messages
    "analyzing_wait": "⏳ તમારું ટેન્ડર અત્યારે એનાલાઈઝ થઈ રહ્યું છે... થોડી રાહ જુઓ (૨-૩ મિનિટ).",
    "still_analyzing": "હજુ એનાલાઈઝ થઈ રહ્યું છે... લગભગ પૂર્ણ ⏳",
    "error_generic": "❌ માફ કરશો, કંઈક ભૂલ થઈ છે. થોડી વાર પછી ફરી પ્રયાસ કરો.",

    # Verdict
    "verdict_header": "━━━━━━━━━━━━━━━━━━━━━━━━\n📋 {department} — {work}\n💰 કિંમત: ₹{value}\n📅 અંતિમ તારીખ: {deadline} ({days} દિવસ બાકી)\n\n⚡ ચુકાદો: {verdict} — {score}/10\n\n🔴 {critical} ગંભીર જોખમો\n🟡 {warnings} ચેતવણીઓ\n💡 ભલામણ કરેલ બિડ: ₹{bid}\n💰 અંદાજિત નફો: ₹{profit}\n━━━━━━━━━━━━━━━━━━━━━━━━",
    "verdict_menu": "\nતમે શું જોવા માંગો છો?\n(ફક્ત *નંબર* મોકલો!)\n\n1️⃣ Eligibility\n2️⃣ Risks\n3️⃣ BOQ Rates\n4️⃣ Documents\n5️⃣ Cash Flow\n6️⃣ Profit/Cost\n7️⃣ Full Report\n8️⃣ Download PDF\n9️⃣ Share & Earn\n\n👉 *ફક્ત 1, 2, 3... ટાઈપ કરો!*",
    "monthly_report_template": "📊 *તમારો માસિક રિપોર્ટ*\n━━━━━━━━━━━━━━━━━━━━━━\n\nઆ મહિનાનું વિશ્લેષણ: {analysis_count}/30\nએલર્ટ મળ્યા: {alert_count}\nએલર્ટ વિશ્લેષણ: {free_alert_analyses} (ફ્રી)\n\nકન્સલ્ટન્ટ સામે બચત:\n{analysis_count} વિશ્લેષણ × ₹10,000 = ₹{savings:,}\nતમે ચૂકવ્યા: ₹{paid}\nતમે બચાવ્યા: ₹{total_savings:,}\n━━━━━━━━━━━━━━━━━━━━━━\nતમારો પ્લાન {days_left} દિવસમાં પૂરો થઈ જશે.\nરિન્યુ કરો — કોઈ ટેન્ડર મિસ ન થાય.\nટાઈપ કરો: \"renew\"",
}

_TAMIL = {
    "welcome_new": "வணக்கம்! 🙏 நான் TenderBot.\nஅரசு டெண்டர் முழு பகுப்பாய்வு 3 நிமிடத்தில் செய்வேன்.\n✅ நீங்கள் தகுதியுடையவரா?\n✅ மறைக்கப்பட்ட அபாயங்கள்\n✅ BOQ விகிதங்கள்\n\nதொடங்குவதற்கு, உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்:",
    "lang_menu": "🌐 *மொழியைத் தேர்ந்தெடுக்கவும்:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (Default)\n4️⃣ Marathi (மராઠી)\n5️⃣ Gujarati (ગુજરાતી)\n6️⃣ Tamil (தமிழ்)\n7️⃣ Telugu (తెలుగు)\n\n👉 *எண்ணை மட்டும் தட்டச்சு செய்யவும்!*",
    "lang_set_success": "✅ மொழி *தமிழ்* அமைக்கப்பட்டது.\nஇப்போது, டெண்டர் PDF ஐ அனுப்பவும்! 📄",
    "welcome_message": "👋 TenderBot-க்கு மீண்டும் வருக!\n📄 டெண்டர் PDF அனுப்பவும் - 3 நிமிடங்களில் அறிக்கை.\n💰 \"Plan\" - திட்டங்களைக் காண.\n🌐 \"Language\" - மொழியை மாற்ற.",
    "menu_title": "📊 *டெண்டர் பகுப்பாய்வு மெனு*",
    "menu_opt_1": "1️⃣ தகுதி சரிபார்ப்பு",
    "menu_opt_2": "2️⃣ மறைக்கப்பட்ட அபாயங்கள்",
    "menu_opt_3": "3️⃣ BOQ விகிதங்கள் & ஏலத் தொகை",
    "menu_opt_4": "4️⃣ தேவையான ஆவணங்கள்",
    "menu_opt_5": "5️⃣ பணப்புழக்கத் தேவை",
    "menu_opt_6": "6️⃣ லாபம் மற்றும் செலவு மதிப்பீடு",
    "menu_opt_7": "7️⃣ முழு அறிக்கை",
    "menu_opt_8": "8️⃣ PDF பதிவிறக்கம் ⬇️",
    "menu_opt_9": "9️⃣ பகிரவும் மற்றும் சம்பாதிக்கவும் 🎁",
    "menu_footer": "👉 *1, 2, 3... என பதில் அளிக்கவும்!*",
    "analyzing_wait": "⏳ உங்கள் டெண்டர் பகுப்பாய்வு செய்யப்படுகிறது... தயவுசெய்து காத்திருக்கவும் (2-3 நிமிடம்).",
    "verdict_header": "━━━━━━━━━━━━━━━━━━━━━━━━\n📋 {department} — {work}\n💰 மதிப்பு: ₹{value}\n📅 காலக்கெடு: {deadline} ({days} நாட்கள் மீதமுள்ளன)\n\n⚡ தீர்ப்பு: {verdict} — {score}/10\n━━━━━━━━━━━━━━━━━━━━━━━━",
    "ocr_failed_manual_download": "இந்த PDF ஸ்கேன் செய்யப்பட்ட படம், உரையை பிரித்தெடுக்க முடியவில்லை. தயவுசெய்து அசல் PDF-ஐ பதிவிறக்கம் செய்து அனுப்பவும்.",
}

_TELUGU = {
    "welcome_new": "నమస్కారం! 🙏 నేను TenderBot.\nప్రభుత్వ టెண்டర్ పూర్తి విશ્લેషణ 3 నిమిషాల్లో చేస్తాను.\n✅ మీరు అర్హులా?\n✅ దాగి ఉన్న ప్రమాదాలు\n✅ BOQ రేట్లు\n\nప్రారంభించడానికి, మీ భాషను ఎంచుకోండి:",
    "lang_menu": "🌐 *భాషను ఎంచుకోండి:*\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Hinglish (Default)\n4️⃣ Marathi (మరాઠી)\n5️⃣ Gujarati (ગુજરાતી)\n6️⃣ Tamil (தமிழ்)\n7️⃣ Telugu (తెలుగు)\n\n👉 *కేవలం నంబర్‌ను టైప్ చేయండి!*",
    "lang_set_success": "✅ భాష *తెలుగు* సెట్ చేయబడింది.\nఇప్పుడు, టెండర్ PDF ని పంపండి! 📄",
    "welcome_message": "👋 TenderBot కి స్వాగతం!\n📄 టెండర్ PDF పంపండి - 3 నిమిషాల్లో నివేదిక.\n💰 \"Plan\" - ప్లాన్‌ల కోసం.\n🌐 \"Language\" - భాష మార్చడానికి.",
    "menu_title": "📊 *టెండర్ విశ్લેషణ మెనూ*",
    "menu_opt_1": "1️⃣ అర్హత తనిఖీ",
    "menu_opt_2": "2️⃣ దాగి ఉన్న ప్రమాదాలు",
    "menu_opt_3": "3️⃣ BOQ రేట్లు & బిడ్ మొత్తం",
    "menu_opt_4": "4️⃣ అవసరమైన పత్రాలు",
    "menu_opt_5": "5️⃣ నగదు ప్రవాహ అవసరం",
    "menu_opt_6": "6️⃣ లాభం మరియు ఖర్చు అంచనా",
    "menu_opt_7": "7️⃣ పూర్తి నివేదిక",
    "menu_opt_8": "8️⃣ PDF డౌన్‌లోడ్ ⬇️",
    "menu_opt_9": "9️⃣ షేర్ చేయండి & సంపాదించండి 🎁",
    "menu_footer": "👉 *1, 2, 3... అని రిప్లై ఇవ్వండి!*",
    "analyzing_wait": "⏳ మీ టెండర్ విశ్లేషించబడుతోంది... దయచేసి వేచి ఉండండి (2-3 నిమిషాలు).",
    "verdict_header": "━━━━━━━━━━━━━━━━━━━━━━━━\n📋 {department} — {work}\n💰 విలువ: ₹{value}\n📅 గడువు: {deadline} ({days} రోజులు మిగిలి ఉన్నాయి)\n\n⚡ తీర్పు: {verdict} — {score}/10\n━━━━━━━━━━━━━━━━━━━━━━━━",
    "ocr_failed_manual_download": "ఈ PDF స్కాన్ చేసిన చిత్రం, టెక్స్ట్‌ని సేకరించడం సాధ్యం కాలేదు. దయచేసి అసలు PDF ని డౌన్‌లోడ్ చేసి పంపండి.",
}

MESSAGES = {
    "hinglish": _HINGLISH,
    "en": _ENGLISH,
    "hi": _HINDI,
    "mr": _MARATHI,
    "gu": _GUJARATI,
    "ta": _TAMIL,
    "te": _TELUGU,
}

def get_string(lang_code: str, key: str) -> str:
    """Safely retrieves a translated string, falling back to Hinglish if missing."""
    lang = lang_code.lower() if lang_code else "hinglish"

    # Map common aliases
    alias_map = {
        "hindi": "hi", "english": "en", "en_us": "en", 
        "marathi": "mr", "gujarati": "gu", 
        "tamil": "ta", "telugu": "te"
    }
    lang = alias_map.get(lang, lang)
    if lang not in MESSAGES:
        lang = "hinglish"

    result = MESSAGES[lang].get(key)
    if not result:
        result = _HINGLISH.get(key, "")
    return result

def build_menu(lang_code: str) -> str:
    """Dynamically builds the 1-9 analysis menu based on the user's language."""
    parts = [
        get_string(lang_code, "menu_title"),
        "",
        get_string(lang_code, "menu_opt_1"),
        get_string(lang_code, "menu_opt_2"),
        get_string(lang_code, "menu_opt_3"),
        get_string(lang_code, "menu_opt_4"),
        get_string(lang_code, "menu_opt_5"),
        get_string(lang_code, "menu_opt_6"),
        get_string(lang_code, "menu_opt_7"),
        get_string(lang_code, "menu_opt_8"),
        get_string(lang_code, "menu_opt_9"),
        "",
        get_string(lang_code, "menu_footer")
    ]
    return "\n".join(parts)
