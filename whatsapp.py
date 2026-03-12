import httpx
import os
from dotenv import load_dotenv

load_dotenv()

AISENSY_API_KEY = os.getenv("AISENSY_API_KEY")
AISENSY_BASE_URL = "https://backend.aisensy.com"

async def send_text_message(to: str, text: str):
    """Send plain text message via AiSensy"""
    # Remove + and spaces, keep digits
    phone = to.replace("+", "").replace(" ", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AISENSY_BASE_URL}/campaign/t1/api/v2",
            headers={"Content-Type": "application/json"},
            json={
                "apiKey": AISENSY_API_KEY,
                "campaignName": "direct_message",
                "destination": phone,
                "userName": "TenderBot",
                "templateParams": [text],
                "source": "bot",
                "media": {},
                "buttons": [],
                "carouselCards": [],
                "location": {}
            },
            timeout=10.0
        )
        return response.json()

async def send_template(to: str, 
                         template_name: str,
                         params: list):
    """Send approved template message"""
    phone = to.replace("+", "").replace(" ", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AISENSY_BASE_URL}/campaign/t1/api/v2",
            headers={"Content-Type": "application/json"},
            json={
                "apiKey": AISENSY_API_KEY,
                "campaignName": template_name,
                "destination": phone,
                "userName": "TenderBot",
                "templateParams": params,
                "source": "bot",
                "media": {},
                "buttons": [],
                "carouselCards": [],
                "location": {}
            },
            timeout=10.0
        )
        return response.json()

async def send_document(to: str,
                         doc_url: str,
                         filename: str,
                         caption: str):
    """Send PDF document"""
    phone = to.replace("+", "").replace(" ", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AISENSY_BASE_URL}/campaign/t1/api/v2",
            headers={"Content-Type": "application/json"},
            json={
                "apiKey": AISENSY_API_KEY,
                "campaignName": "send_document",
                "destination": phone,
                "userName": "TenderBot",
                "templateParams": [caption],
                "source": "bot",
                "media": {
                    "url": doc_url,
                    "filename": filename
                },
                "buttons": [],
                "carouselCards": [],
                "location": {}
            },
            timeout=10.0
        )
        return response.json()
