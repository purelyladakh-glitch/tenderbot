from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import json
import os
from pathlib import Path

from database import engine, get_db, Base, Payment, User
from bot import handle_incoming_message, send_whatsapp_message
from payments import verify_webhook_signature

# Create all tables in sqlite DB automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TenderBot")

# Ensure static directory exists for serving PDFs
Path("static/pdfs").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "ok", "app": "TenderBot - WhatsApp API Handler"}

@app.post("/webhook")
async def twilio_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Receives incoming messages/media from Twilio"""
    form_data = await request.form()
    
    phone_number = form_data.get("From", "")
    text = form_data.get("Body", "").strip()
    media_url = form_data.get("MediaUrl0") # Exists if PDF sent
    
    # Process message or send directly to bot state machine
    handle_incoming_message(phone_number, text, media_url, db, background_tasks)
    
    # Twilio expects valid XML for the webhook response, sending empty response because we reply async
    return PlainTextResponse("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>", media_type="text/xml")

@app.post("/payment-webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives event updates from Razorpay"""
    payload_body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    
    if not verify_webhook_signature(payload_body, signature):
         return JSONResponse({"status": "error", "message": "Invalid webhook signature"}, status_code=400)
    
    try:
        data = json.loads(payload_body)
        
        # Check if payment was successfully captured
        if data.get("event") == "payment.captured":
            payment_entity = data["payload"]["payment"]["entity"]
            
            # Extract phone directly from notes passed during payment link creation
            notes = payment_entity.get("notes", {})
            phone = notes.get("user_phone")
            
            user = db.query(User).filter(User.phone_number == phone).first() if phone else None
            
            if user:
                 amount_paid = payment_entity.get("amount", 0) / 100
                 
                 # Adding credits
                 if amount_paid == 99:
                     user.paid_credits_remaining += 1
                 elif amount_paid == 399:
                     user.paid_credits_remaining += 5
                 elif amount_paid == 799:
                     user.subscription_type = "monthly"
                 
                 db.commit()
                 
                 unlock_msg = f"Payment received! ✅\n{user.paid_credits_remaining} analyses unlock ho gaye.\n\nAgla tender bhejo — main ready hoon! 📄"
                 send_whatsapp_message(user.phone_number, unlock_msg)

        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
