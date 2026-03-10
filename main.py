from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import json
import os
from pathlib import Path

from database import engine, get_db, Base, Payment, User
from bot import handle_incoming_message, send_whatsapp_message, handle_payment_success
from payments import verify_webhook_signature

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
async def twilio_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Receives incoming messages/media from Twilio"""
    form_data = await request.form()
    
    phone_number = form_data.get("From", "")
    text = form_data.get("Body", "").strip()
    media_url = form_data.get("MediaUrl0")  # Exists if PDF sent
    
    handle_incoming_message(phone_number, text, media_url, db, background_tasks)
    
    return PlainTextResponse(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>",
        media_type="text/xml"
    )

@app.post("/payment-webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives event updates from Razorpay"""
    payload_body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    
    if not verify_webhook_signature(payload_body, signature):
        return JSONResponse({"status": "error", "message": "Invalid signature"}, status_code=400)
    
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
                # Determine plan type from amount
                if amount_paid == 99:
                    plan_type = "single"
                elif amount_paid == 399:
                    plan_type = "pack"
                elif amount_paid == 799:
                    plan_type = "monthly"
                else:
                    plan_type = "single"
                
                # Use the bot's handler for clean subscription logic
                handle_payment_success(user, int(amount_paid), plan_type, db)
                
                # Update payment record
                razorpay_id = payment_entity.get("id", "")
                payment_record = db.query(Payment).filter(
                    Payment.user_phone == phone,
                    Payment.status == "created"
                ).order_by(Payment.id.desc()).first()
                
                if payment_record:
                    payment_record.status = "paid"
                    payment_record.razorpay_order_id = razorpay_id
                    db.commit()
        
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
