import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

async def send_text_message(to: str, text: str):
    """Send plain text message via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=10.0)
        return response.json()

async def send_document(to: str, doc_url: str, filename: str, caption: str):
    """Send PDF document via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {
            "link": doc_url,
            "filename": filename,
            "caption": caption
        },
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=10.0)
        return response.json()

async def send_interactive_buttons(to: str, body: str, buttons: list):
    """Send interactive buttons via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Meta supports up to 3 buttons for 'reply' type
    formatted_buttons = []
    for i, btn in enumerate(buttons[:3]):
        formatted_buttons.append({
            "type": "reply",
            "reply": {
                "id": btn.get("id", f"btn_{i}"),
                "title": btn.get("title")[:20]  # Meta has 20 char limit for button titles
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": formatted_buttons
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=10.0)
        return response.json()

async def send_interactive_list(to: str, body: str, button_text: str, sections: list):
    """Send interactive list via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Format sections for Meta API
    formatted_sections = []
    for section in sections:
        rows = []
        for row in section.get("rows", []):
            rows.append({
                "id": row.get("id"),
                "title": row.get("title")[:24],  # 24 char limit
                "description": row.get("description", "")[:72] if row.get("description") else ""
            })
        formatted_sections.append({
            "title": section.get("title", "")[:24],
            "rows": rows
        })

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_text[:20],
                "sections": formatted_sections
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=10.0)
        return response.json()

async def get_media_url(media_id: str):
    """Retrieve media URL from Meta media ID"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }
    url = f"https://graph.facebook.com/v22.0/{media_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10.0)
        data = response.json()
        return data.get("url")

async def download_media(media_url: str):
    """Download media from the provided URL (requires Auth header for Meta)"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, headers=headers, timeout=30.0)
        if response.status_code == 200:
            return response.content
    return None
