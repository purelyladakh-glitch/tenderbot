import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    rzp_client = None

def generate_payment_link(amount_in_inr: int, user_phone: str, reference_id: str, description: str) -> str:
    """Generates a Razorpay payment link for the given package."""
    if not rzp_client:
        return "https://razorpay.com/fake-link-for-local-testing"
        
    payment_data = {
        "amount": amount_in_inr * 100, # paise
        "currency": "INR",
        "description": description,
        "customer": {
            "contact": user_phone
        },
        "notify": {
            "sms": False,
            "email": False
        },
        "reminder_enable": False,
        "reference_id": str(reference_id)
    }
    
    try:
        payment_link = rzp_client.payment_link.create(payment_data)
        return payment_link['short_url']
    except Exception as e:
        print(f"Error creating payment link: {e}")
        return ""

def verify_webhook_signature(payload_body: bytes, webhook_signature: str) -> bool:
    """Verifies the integrity of the Razorpay Webhook."""
    if not rzp_client:
         return True # Mocking for local
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_KEY_SECRET)
    try:
        rzp_client.utility.verify_webhook_signature(payload_body.decode('utf-8'), webhook_signature, secret)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
