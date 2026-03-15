import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_API_VERSION = os.getenv("META_API_VERSION", "v22.0")
API_URL = f"https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/messages"
print(f"WhatsApp API URL configured: {API_URL}")
print(f"WhatsApp token length: {len(META_ACCESS_TOKEN) if META_ACCESS_TOKEN else 0}")

async def send_text_message(to: str, text: str):
    """Send plain text message via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
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

async def upload_media(file_bytes: bytes, mime_type: str, filename: str) -> str:
    """Uploads media direct to Meta and returns the media_id"""
    url = f"https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}"
    }
    data = {
        "messaging_product": "whatsapp"
    }
    files = {
        "file": (filename, file_bytes, mime_type)
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data, files=files, timeout=30.0)
        res_json = response.json()
        if "id" in res_json:
            return res_json["id"]
        else:
            raise Exception(f"Failed to upload media: {res_json}")

async def send_document(to: str, doc_url_or_id: str, filename: str, caption: str, is_id: bool = False):
    """Send PDF document via Meta Cloud API using either Media ID or Link"""
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    document_obj = {
        "filename": filename,
        "caption": caption
    }
    
    if is_id:
        document_obj["id"] = doc_url_or_id
    else:
        document_obj["link"] = doc_url_or_id
        
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": document_obj,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=10.0)
        return response.json()

async def send_interactive_buttons(to: str, body: str, buttons: list):
    """Send interactive buttons via Meta Cloud API"""
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
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
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
    }
    url = f"https://graph.facebook.com/{META_API_VERSION}/{media_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10.0)
        data = response.json()
        return data.get("url")

async def download_media(media_url: str):
    """Download media from the provided URL (requires Auth header for Meta)"""
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, headers=headers, timeout=30.0)
        if response.status_code == 200:
            return response.content
    return None
