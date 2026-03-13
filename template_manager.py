"""
Meta WhatsApp Business API - Message Templates Manager

Meta requires pre-approved templates for ANY message the bot sends outside the 
standard 24-hour customer service window (like alerts, reminders, expiry notices).

Instructions to submit these templates in Meta Business Manager:
1. Go to business.facebook.com
2. Navigate to WhatsApp Manager -> Message Templates
3. Click "Create Template"
4. Select "Utility" category
5. Give the EXACT name listed below
6. Select language (Hindi or English)
7. Copy paste the Body exactly as shown
8. Submit for review (usually approved in minutes)
"""

TEMPLATES = [
    {
        "name": "tender_alert_hindi",
        "category": "UTILITY",
        "language": "hi",
        "body": "🔔 नया टेंडर!\\n{{1}}\\nValue: ₹{{2}}\\nDeadline: {{3}} दिन\\nAnalyze: YES reply करें"
    },
    {
        "name": "tender_alert_english",
        "category": "UTILITY",
        "language": "en",
        "body": "🔔 New Tender!\\n{{1}}\\nValue: ₹{{2}}\\nDeadline: {{3}} days\\nReply YES to analyze"
    },
    {
        "name": "deadline_reminder_hindi",
        "category": "UTILITY",
        "language": "hi",
        "body": "⚠️ Reminder: {{1}}\\nDeadline {{2}} दिन बाकी!\\nDocuments ready हैं?"
    },
    {
        "name": "deadline_reminder_english",
        "category": "UTILITY",
        "language": "en",
        "body": "⚠️ Reminder: {{1}}\\n{{2}} days to deadline!\\nDocuments ready?"
    },
    {
        "name": "payment_request_hindi",
        "category": "UTILITY",
        "language": "hi",
        "body": "आपका free analysis use हो गया।\\n💳 ₹99 / ₹399 / ₹799\\nPayment: {{1}}"
    },
    {
        "name": "subscription_expiry_hindi",
        "category": "UTILITY",
        "language": "hi",
        "body": "⏰ आपका plan {{1}} दिन में expire होगा।\\nRenew: {{2}}"
    },
    {
        "name": "welcome_back_hindi",
        "category": "UTILITY",
        "language": "hi",
        "body": "नमस्ते {{1}}! TenderBot में वापस स्वागत है।\\nTender PDF भेजिए। 📄"
    }
]

def get_template(name: str) -> dict:
    for t in TEMPLATES:
        if t["name"] == name:
            return t
    return None

if __name__ == "__main__":
    print(f"Total templates to register in Meta: {len(TEMPLATES)}")
    for t in TEMPLATES:
        print(f"- {t['name']} ({t['language']})")
