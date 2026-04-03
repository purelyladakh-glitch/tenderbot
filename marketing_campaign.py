import os
import time
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, MarketingLead, MarketingTemplate
from bot import send_whatsapp_message
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DAILY_LIMIT = 20

def seed_marketing_templates(db: Session):
    if db.query(MarketingTemplate).count() == 0:
        templates = [
            MarketingTemplate(
                template_name="profit_focus",
                message_body="Hi {name} from {company} 👋\n\nWe noticed you bid on civil projects. We built an AI that instantly reads 50-page NIT/BOQ PDFs to calculate realistic L1 Profit margins.\n\n🎁 *I have 5 Free Analyses reserved for you.*\n\nReply with a Tender PDF to test it!\n🌐 https://web-production-b925d.up.railway.app/"
            ),
            MarketingTemplate(
                template_name="time_focus",
                message_body="Hi {name} from {company} ⏱️\n\nTired of spending hours reading Tender PDFs? We built a WhatsApp AI that instantly reads the entire BOQ and summarizes it for you right here.\n\n🎁 *5 Free Analyses reserved.*\n\nReply with a Tender PDF to instantly test it out.\n🌐 https://web-production-b925d.up.railway.app/"
            ),
            MarketingTemplate(
                template_name="risk_focus",
                message_body="Hi {name} 🚨\n\nDid you know 40% of contractors lose money because they miss hidden clauses in heavy Tender PDFs?\n\nOur AI reads 50-page BOQs in 2 seconds and flags hidden eligibility risks.\n\n🎁 *Check your next 5 PDFs for Free.*\n\nJust reply to this message with any Tender PDF!\n🌐 https://web-production-b925d.up.railway.app/"
            )
        ]
        db.add_all(templates)
        db.commit()

def select_darwin_template(templates):
    """Epsilon-Greedy AI selection algorithm for A/B testing ad copy."""
    total_sent = sum([t.sent_count for t in templates])
    if total_sent < 60:
        # Exploration Phase: Test all templates equally until statistically significant
        return random.choice(templates)
    
    # Exploitation Phase: Find the template with highest mathematical win rate
    best_template = max(templates, key=lambda t: (t.reply_count / t.sent_count) if t.sent_count > 0 else 0)
    
    # 80% chance to use the proven winner, 20% chance to keep experimenting
    if random.random() < 0.8:
        return best_template
    else:
        return random.choice(templates)

def run_campaign():
    logger.info("🚀 Booting Up Darwin Marketing Engine...")
    db = SessionLocal()
    seed_marketing_templates(db)
    
    try:
        new_leads = db.query(MarketingLead).filter(MarketingLead.status == "new").limit(DAILY_LIMIT).all()
        logger.info(f"Preparing to blast {len(new_leads)} new leads.")
        
        active_templates = db.query(MarketingTemplate).filter(MarketingTemplate.is_active == True).all()
        
        for lead in new_leads:
            try:
                chosen_template = select_darwin_template(active_templates)
                first_touch_msg = chosen_template.message_body.format(
                    name=lead.name or "Contractor",
                    company=lead.company or "Your Company"
                )
                
                # Use our robust Meta API wrapper
                send_whatsapp_message(lead.phone_number, first_touch_msg)
                # Securely log the Darwin algorithm choice
                chosen_template.sent_count += 1
                lead.template_used = chosen_template.template_name
                
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
