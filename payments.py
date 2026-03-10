import os
import requests
import hmac
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

def generate_payment_link(amount_in_inr: int, user_phone: str, reference_id: str, description: str) -> str:
    """Generates a Razorpay payment link using direct HTTP API (bypassing SDK)."""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return "https://razorpay.com/fake-link-for-local-testing"
        
    url = "https://api.razorpay.com/v1/payment_links"
    
    payment_data = {
        "amount": int(amount_in_inr * 100), # paise
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "contact": user_phone
        },
        "notify": {
            "sms": False,
            "email": False
        },
        "reminder_enable": False,
        "reference_id": str(reference_id),
        "notes": {
            "user_phone": user_phone
        }
    }
    
    try:
        response = requests.post(
            url, 
            json=payment_data, 
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get('short_url', '')
    except Exception as e:
        print(f"Error creating payment link via HTTP: {e}")
        if 'response' in locals():
            print(f"Response: {response.text}")
        return ""

def verify_webhook_signature(payload_body: bytes, webhook_signature: str) -> bool:
    """Verifies the integrity of the Razorpay Webhook using HMAC SHA256 (bypassing SDK)."""
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_KEY_SECRET)
    if not secret:
        return True # Fallback if secret not configured
        
    try:
        # Expected signature is HMAC-SHA256 using the webhook secret
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, webhook_signature)
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False
