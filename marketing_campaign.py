import os
import time
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, MarketingLead
from bot import send_whatsapp_message  # Standardizing outgoing messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conservative limit to prevent Meta spam detection
DAILY_LIMIT = 20

def run_campaign():
    logger.info("🚀 Booting Up Advanced Marketing Engine...")
    db = SessionLocal()
    
    try:
        # 1. FIRST TOUCH OUTREACH
        # Find completely new leads that haven't been messaged yet
        new_leads = db.query(MarketingLead).filter(MarketingLead.status == "new").limit(DAILY_LIMIT).all()
        logger.info(f"Preparing to blast {len(new_leads)} new leads.")
        
        for lead in new_leads:
            try:
                # Highly Personalized Template
                first_touch_msg = (
                    f"Hi {lead.name} from {lead.company} 👋\n\n"
                    "We noticed you bid on government infrastructure projects and wanted to share an internal tool with you.\n\n"
                    "We built an AI that instantly reads 50-page NIT/BOQ PDFs. It will check your eligibility, flag hidden financial risks, and calculate a realistic L1 Profit margin directly here in WhatsApp.\n\n"
                    "🎁 *I have 5 Free Analyses reserved for you.*\n\n"
                    "To try it right now, simply reply to this message with any Tender PDF!\n\n"
                    "🌐 See demo: https://web-production-b925d.up.railway.app/"
                )
                
                # Use our robust Meta API wrapper
                send_whatsapp_message(lead.phone_number, first_touch_msg)
                
                # Securely mark as contacted to prevent duplicate sending
                lead.status = "contacted"
                lead.last_contacted_at = datetime.utcnow()
                db.commit()
                time.sleep(2) # Artificial delay to mimic human speed and respect rate limits
                logger.info(f"✅ Success: First Touch sent to {lead.phone_number}")
                
            except Exception as e:
                logger.error(f"❌ Failed to reach {lead.phone_number}: {e}")
                db.rollback()


        # 2. THE 3-DAY FOLLOW-UP DRIP
        # Find leads contacted over 3 days ago who never replied
        follow_up_threshold = datetime.utcnow() - timedelta(days=3)
        drip_leads = db.query(MarketingLead).filter(
            MarketingLead.status == "contacted",
            MarketingLead.last_contacted_at <= follow_up_threshold,
            MarketingLead.follow_up_count == 0
        ).limit(DAILY_LIMIT).all()
        
        logger.info(f"Preparing to drip follow-up to {len(drip_leads)} cold leads.")
        
        for lead in drip_leads:
            try:
                drip_msg = (
                    f"Hi {lead.name}! Just checking if you caught my last message.\n\n"
                    "The 5 free BOQ profit estimates are still active on your account.\n\n"
                    "If you're bidding on anything this week, just reply to this chat with your PDF and the AI will analyze it instantly. (Reply STOP if not interested)."
                )
                
                send_whatsapp_message(lead.phone_number, drip_msg)
                
                lead.follow_up_count += 1
                lead.last_contacted_at = datetime.utcnow()
                db.commit()
                time.sleep(2)
                logger.info(f"🔄 Success: Follow-up Drip sent to {lead.phone_number}")
                
            except Exception as e:
                logger.error(f"❌ Failed to run drip to {lead.phone_number}: {e}")
                db.rollback()

    finally:
        db.close()
        logger.info("🛑 Marketing Campaign cycle complete.")

if __name__ == "__main__":
    run_campaign()
