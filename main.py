from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import os
import httpx
from pathlib import Path
import sentry_sdk

from database import get_db, init_db, User, ContractorPreference, Analysis, Payment, WebhookLog
from migrate_db import run_migrations
from bot import handle_incoming_message, handle_payment_success, send_whatsapp_message
from payments import verify_webhook_signature
from utils import PLANS

# Create all tables in sqlite DB automatically
# Base.metadata.create_all(bind=engine) # This line is removed as init_db() will handle it

app = FastAPI(title="TenderBot")

# Optional Sentry Monitoring for Error Tracking
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

@app.on_event("startup")
async def startup_event():
    # Initialize database tables and run migrations for existing tables
    init_db()
    run_migrations()
    print("🚀 TenderBot API starting up...")
    
    # --- CONNECTIVITY AUDIT LOGS ---
    print("🔍 --- CONNECTIVITY AUDIT ---")
    
    meta_token = os.getenv("META_ACCESS_TOKEN", "")
    whatsapp_token = os.getenv("WHATSAPP_TOKEN", "")
    phone_id = os.getenv("META_PHONE_NUMBER_ID", "")
    verify_token_meta = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    verify_token_generic = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
    
    print(f"META_ACCESS_TOKEN: {meta_token[:10]}..." if meta_token else "META_ACCESS_TOKEN: MISSING")
    print(f"WHATSAPP_TOKEN: {whatsapp_token[:10]}..." if whatsapp_token else "WHATSAPP_TOKEN: MISSING")
    print(f"META_PHONE_NUMBER_ID: {phone_id}" if phone_id else "META_PHONE_NUMBER_ID: MISSING")
    print(f"META_WEBHOOK_VERIFY_TOKEN: {verify_token_meta}" if verify_token_meta else "META_WEBHOOK_VERIFY_TOKEN: MISSING")
    print(f"WEBHOOK_VERIFY_TOKEN: {verify_token_generic}" if verify_token_generic else "WEBHOOK_VERIFY_TOKEN: MISSING")
    
    print("Webhook URL: /webhook")
    print(f"Verify token configured: {'YES' if verify_token_meta or verify_token_generic else 'NO'}")
    print(f"Phone Number ID: {phone_id}")
    print("🔍 ---------------------------")
    
    # One-time fix: Credit payment for order_SUetgAmPkc3DpL (Razorpay confirmed paid but webhook missed)
    try:
        from database import SessionLocal, User
        db = SessionLocal()
        user = db.query(User).filter(User.phone_number == "+916006788068").first()
        if user and getattr(user, 'paid_credits_remaining', 0) < 1:
            user.paid_credits_remaining = (user.paid_credits_remaining or 0) + 1
            db.commit()
            print("✅ One-time fix: Credited 1 analysis to +916006788068 (missed Razorpay webhook)")
        db.close()
    except Exception as e:
        print(f"One-time credit fix skipped: {e}")

    print("💰 Razorpay webhook should be configured at: https://web-production-b925d.up.railway.app/payment-webhook")

    import threading
    import httpx as httpx_sync

    def keep_alive_ping():
        """Pings the health endpoint every 4 minutes to prevent Railway sleep."""
        import time as _time
        port = int(os.environ.get("PORT", 8000))
        while True:
            _time.sleep(240)  # 4 minutes
            try:
                import urllib.request
                urllib.request.urlopen(f"http://0.0.0.0:{port}/health", timeout=5)
            except Exception:
                pass

    threading.Thread(target=keep_alive_ping, daemon=True).start()
    print("✅ Keep-alive ping thread started (every 4 minutes)")

    # --- Deadline Reminder Scheduler ---
    def deadline_reminder_loop():
        """Checks for upcoming tender deadlines and sends reminders every 6 hours."""
        import time as _time
        _time.sleep(60)  # Wait 1 minute after startup before first check
        
        while True:
            try:
                from database import SessionLocal, Analysis, ReminderLog, User
                import json
                from datetime import datetime, timedelta
                
                db = SessionLocal()
                now = datetime.utcnow()
                
                # Find analyses with upcoming deadlines
                analyses = db.query(Analysis).filter(
                    Analysis.deadline_date != None,
                    Analysis.deadline_date > now,
                    Analysis.deadline_date < now + timedelta(days=8)
                ).all()
                
                for analysis in analyses:
                    days_left = (analysis.deadline_date - now).days
                    
                    # Determine which reminder to send
                    reminder_key = None
                    if days_left == 7:
                        reminder_key = "7d"
                    elif days_left == 2:
                        reminder_key = "2d"
                    elif days_left == 1:
                        reminder_key = "1d"
                    elif days_left == 0:
                        reminder_key = "0d"
                    
                    if not reminder_key:
                        continue
                    
                    # Check if this reminder was already sent
                    existing = db.query(ReminderLog).filter(
                        ReminderLog.analysis_id == analysis.id,
                        ReminderLog.user_phone == analysis.user_phone
                    ).first()
                    
                    if existing:
                        sent_list = json.loads(existing.reminders_sent or "[]")
                        if reminder_key in sent_list:
                            continue
                        sent_list.append(reminder_key)
                        existing.reminders_sent = json.dumps(sent_list)
                    else:
                        existing = ReminderLog(
                            user_phone=analysis.user_phone,
                            tender_id=str(analysis.id),
                            analysis_id=analysis.id,
                            deadline=analysis.deadline_date,
                            reminders_sent=json.dumps([reminder_key])
                        )
                        db.add(existing)
                    
                    # Send the reminder
                    result = json.loads(analysis.analysis_result) if analysis.analysis_result else {}
                    dept = result.get("department", "Unknown")
                    work = result.get("work_description", "Tender")
                    
                    reminder_messages = {
                        "7d": f"⏰ REMINDER: 7 din baaki!\n\n📋 {dept}\n🔨 {work[:50]}...\n📅 Deadline: {analysis.deadline_date.strftime('%d %b %Y')}\n\nDocuments ready hain? EMD deposit kiya?",
                        "2d": f"🔴 URGENT: Sirf 2 din baaki!\n\n📋 {dept}\n🔨 {work[:50]}...\n📅 Deadline: {analysis.deadline_date.strftime('%d %b %Y')}\n\nAaj submission complete karo!",
                        "1d": f"🚨 LAST DAY TOMORROW!\n\n📋 {dept}\n🔨 {work[:50]}...\n📅 Deadline: KAL - {analysis.deadline_date.strftime('%d %b %Y')}\n\nSab kuch ready hai? Final check karo!",
                        "0d": f"🚨🚨 TODAY IS THE DEADLINE!\n\n📋 {dept}\n🔨 {work[:50]}...\n📅 Deadline: AAJ - {analysis.deadline_date.strftime('%d %b %Y')}\n\nAbhi submit karo! ⏰"
                    }
                    
                    msg = reminder_messages.get(reminder_key, "")
                    if msg:
                        from bot import send_whatsapp_message
                        send_whatsapp_message(analysis.user_phone, msg)
                        print(f"📨 Sent {reminder_key} reminder to {analysis.user_phone} for analysis #{analysis.id}")
                    
                    db.commit()
                
                db.close()
            except Exception as e:
                print(f"⚠️ Reminder loop error: {e}")
            
            _time.sleep(21600)  # Run every 6 hours

    threading.Thread(target=deadline_reminder_loop, daemon=True).start()
    print("✅ Deadline reminder scheduler started (every 6 hours)")

    if meta_token.startswith("EAA") and len(meta_token) < 250:
        print("⚠️ WARNING: META_ACCESS_TOKEN may be temporary.")
        print("⚠️ Generate a permanent System User token. See README for instructions.")
        
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Database connection verified.")
        db.close()
    except Exception as e:
        print(f"❌ CRITICAL DATABASE ERROR ON STARTUP: {e}")
        
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 TenderBot API gracefully shutting down...")


# Ensure static directory exists for serving PDFs
Path("static/pdfs").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    import os
    from fastapi.responses import HTMLResponse
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"status": "ok", "app": "BidMaster AI - WhatsApp Tender Analysis Bot"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/admin/stats")
async def admin_stats(key: str = "", db: Session = Depends(get_db)):
    """Simple admin stats dashboard. Protected by a secret key."""
    admin_key = os.getenv("ADMIN_SECRET_KEY", "tenderbot_admin_2026")
    if key != admin_key:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.created_at > datetime.utcnow() - timedelta(days=1)
    ).count()
    total_analyses = db.query(Analysis).count()
    total_payments = db.query(Payment).filter(Payment.status == "paid").count()
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "paid").scalar() or 0
    
    # Recent webhook activity
    recent_webhooks = db.query(WebhookLog).filter(
        WebhookLog.created_at > datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        "status": "ok",
        "stats": {
            "total_users": total_users,
            "new_users_24h": active_today,
            "total_analyses": total_analyses,
            "total_paid_orders": total_payments,
            "total_revenue_inr": total_revenue,
            "webhooks_24h": recent_webhooks,
        },
        "health": {
            "database": "connected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing",
            "whatsapp": "configured" if os.getenv("META_ACCESS_TOKEN") else "missing",
            "razorpay": "configured" if os.getenv("RAZORPAY_KEY_ID") else "missing",
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/privacy")
async def privacy_policy():
    """Returns a simple HTML privacy policy page for TenderBot."""
    from fastapi.responses import HTMLResponse
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy - TenderBot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 40px 20px; background-color: #f9f9f9; }
            .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            h1 { color: #1a73e8; border-bottom: 2px solid #eef2f7; padding-bottom: 10px; margin-top: 0; }
            h2 { color: #2c3e50; margin-top: 30px; }
            p, ul { color: #555; }
            .footer { margin-top: 50px; font-size: 0.9em; color: #888; text-align: center; }
            .highlight { color: #1a73e8; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Privacy Policy for TenderBot</h1>
            <p>Last updated: March 2026</p>
            
            <p>At <span class="highlight">TenderBot</span>, your privacy is our priority. This policy explains how we handle your information.</p>

            <h2>1. What Data We Collect</h2>
            <ul>
                <li><strong>Phone Number:</strong> We collect your WhatsApp phone number to identify you and send analysis results.</li>
                <li><strong>Tender PDFs:</strong> We temporarily process the tender documents you send to perform AI analysis.</li>
                <li><strong>Usage Data:</strong> We track the number of analyses performed and your subscription status.</li>
            </ul>

            <h2>2. How We Use Your Data</h2>
            <p>We use the collected information solely to:</p>
            <ul>
                <li>Provide accurate 9-part tender analysis.</li>
                <li>Manage your subscription and credits.</li>
                <li>Communicate with you via WhatsApp regarding your requests.</li>
            </ul>

            <h2>3. Data Protection & Sharing</h2>
            <p>We do <span class="highlight">NOT sell or share</span> your personal data or tender documents with third parties. Your data is used exclusively to power the bot's features.</p>

            <h2>4. Contact Us</h2>
            <p>If you have any questions or concerns about your data, please contact us at:</p>
            <p class="highlight">purelyladakh@gmail.com</p>

            <div class="footer">
                &copy; 2026 TenderBot - All Rights Reserved.
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/webhook")
async def verify_meta_webhook(request: Request):
    """Meta Webhook Verification (Handshake)"""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == os.getenv("META_WEBHOOK_VERIFY_TOKEN"):
        print("WEBHOOK_VERIFIED")
        from fastapi.responses import Response
        return Response(content=challenge, media_type="text/plain")
    
    return JSONResponse({"status": "error", "message": "Verification failed"}, status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Receives incoming messages/media from Meta WhatsApp Cloud API"""
    try:
        data = await request.json()
        print(f"📥 Received Webhook JSON: {json.dumps(data)}")
    except Exception as e:
        print(f"❌ Webhook JSON Parse Error: {e}")
        return JSONResponse({"status": "error", "message": "Invalid JSON"}, status_code=400)
    
    # Meta webhook payload structure is nested: entry[] -> changes[] -> value
    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    
    if "messages" not in value:
        # Likely a status update (delivered, read, etc.)
        return {"status": "ok", "detail": "not a message"}

    message = value.get("messages", [{}])[0]
    msg_id = message.get("id") # The unique WAMID
    
    # Check for idempotency (duplicate prevention)
    existing_log = db.query(WebhookLog).filter(WebhookLog.message_id == msg_id).first()
    if existing_log and msg_id:
        return {"status": "ok", "detail": "already processed"}

    # Log the webhook for reliability
    log = WebhookLog(source="meta", message_id=msg_id, payload=json.dumps(data))
    db.add(log)
    db.commit()

    wa_id = message.get("from")
    phone = f"+{wa_id}"
    msg_type = message.get("type")
    
    text = None
    pdf_bytes = None
    from whatsapp import get_media_url, download_media

    if msg_type == "text":
        text = message.get("text", {}).get("body")
    
    elif msg_type == "document":
        doc = message.get("document", {})
        if doc.get("mime_type") == "application/pdf":
            media_id = doc.get("id")
            media_url = await get_media_url(media_id)
            if media_url:
                pdf_bytes = await download_media(media_url)
    
    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "button_reply":
            text = interactive.get("button_reply", {}).get("id")
        elif interactive.get("type") == "list_reply":
            text = interactive.get("list_reply", {}).get("id")

    elif msg_type in ["image", "audio", "video"]:
        send_whatsapp_message(phone, "Sorry, I can only analyze PDF documents. Please send a tender PDF.")
        log.processed = True
        db.commit()
        return {"status": "ok", "detail": "unsupported media type"}
        
    elif msg_type in ["location", "sticker", "reaction", "contacts", "button"]:
        # Gracefully ignore or respond simply
        if msg_type not in ["reaction", "status"]:
            send_whatsapp_message(phone, "I didn't understand that. Please send a tender PDF or type 'Menu'.")
        log.processed = True
        db.commit()
        return {"status": "ok", "detail": "ignored type"}

    if text or pdf_bytes:
        # Hand off to bot logic
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
    
    try:
        data = json.loads(payload_body)
    except Exception as e:
        return JSONResponse({"status": "error", "message": "Invalid JSON"}, status_code=400)

    # Check for duplicate webhook
    payment_id = data.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "")
    if payment_id:
        existing = db.query(WebhookLog).filter(WebhookLog.message_id == payment_id).first()
        if existing:
            return JSONResponse({"status": "ok", "detail": "already processed"})

    # Log the webhook for reliability
    log = WebhookLog(source="razorpay", message_id=payment_id, payload=payload_body.decode('utf-8'))
    db.add(log)
    db.commit()
    
    try:
        
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
