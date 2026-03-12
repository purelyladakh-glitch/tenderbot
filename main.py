from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import json
import os
import httpx
from pathlib import Path

from database import engine, get_db, Base, Payment, User, WebhookLog
from bot import handle_incoming_message, handle_payment_success
from payments import verify_webhook_signature
from utils import PLANS

# Create all tables in sqlite DB automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TenderBot")

# Ensure static directory exists for serving PDFs
Path("static/pdfs").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "ok", "app": "TenderBot - WhatsApp Tender Analysis Bot"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Receives incoming messages/media from AiSensy"""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON"}, status_code=400)
    
    # Log the webhook for reliability
    log = WebhookLog(source="aisensy", payload=json.dumps(data))
    db.add(log)
    db.commit()
    
    wa_id = data.get("waId", "")
    phone = f"+{wa_id}"
    msg_type = data.get("type", "")
    
    text = None
    pdf_bytes = None
    
    if msg_type == "text":
        text = data.get("text", "")
    
    elif msg_type == "document":
        doc_url = data.get("document", {}).get("url")
        if doc_url:
            # Download PDF from URL
            async with httpx.AsyncClient() as client:
                pdf_response = await client.get(doc_url, timeout=30.0)
                if pdf_response.status_code == 200:
                    pdf_bytes = pdf_response.content
    
    elif msg_type == "interactive":
        text = data.get("selectedId", "")

    if text or pdf_bytes:
        handle_incoming_message(phone, text, pdf_bytes, db, background_tasks)
    
    log.processed = True
    db.commit()
    
    return {"status": "ok"}

@app.post("/payment-webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives event updates from Razorpay"""
    payload_body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    
    if not verify_webhook_signature(payload_body, signature):
        return JSONResponse({"status": "error", "message": "Invalid signature"}, status_code=400)
    
    # Log the webhook for reliability
    log = WebhookLog(source="razorpay", payload=payload_body.decode('utf-8'))
    db.add(log)
    db.commit()
    
    try:
        data = json.loads(payload_body)
        
        if data.get("event") == "payment.captured":
            payment_entity = data["payload"]["payment"]["entity"]
            
            # Get user phone from notes
            notes = payment_entity.get("notes", {})
            phone = notes.get("user_phone")
            amount_paid = payment_entity.get("amount", 0) / 100  # paise to rupees
            
            user = db.query(User).filter(User.phone_number == phone).first() if phone else None
            
            if user:
                # Match with our internal Payment record
                razorpay_order_id = payment_entity.get("order_id") or payment_entity.get("id")
                
                payment_record = db.query(Payment).filter(
                    Payment.razorpay_order_id == razorpay_order_id
                ).first()
                
                if not payment_record:
                    # Fallback to user phone + status if order_id is missing or different
                    payment_record = db.query(Payment).filter(
                        Payment.user_phone == phone,
                        Payment.status == "created"
                    ).order_by(Payment.id.desc()).first()

                if payment_record and payment_record.status == "created":
                    # Use plan_type from our record, or infer from amount if record missing
                    plan_type = payment_record.plan_type
                    
                    # Use the bot's handler for clean subscription logic
                    handle_payment_success(user, int(amount_paid), plan_type, db)
                    
                    payment_record.status = "paid"
                    payment_record.razorpay_order_id = payment_entity.get("id", razorpay_order_id)
                    db.commit()
                elif user:
                    # Emergency fallback if no record found but user exists
                    # Determine plan type from amount using PLANS config
                    plan_type = "single"
                    for p_key, p_val in PLANS.items():
                        if amount_paid == p_val["price"]:
                            plan_type = p_key
                            break
                    handle_payment_success(user, int(amount_paid), plan_type, db)
        
        # Mark as processed
        log.processed = True
        db.commit()
        
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
