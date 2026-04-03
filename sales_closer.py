import os
import time
from datetime import datetime, timedelta
from database import SessionLocal, User
from bot import send_whatsapp_message

def run_sales_closer():
    """
    Hunts for high-intent users who exhausted their limits 24 hours ago
    and sends them an aggressive automated upsell offer.
    """
    print("💰 Booting up Aggressive AI Sales Closer...")
    db = SessionLocal()
    
    try:
        # Find exhausted free-tier users over 24h old who haven't been upsold
        # Specifically targeting those who hit 0 free limits, have 0 paid credits
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        exhausted_users = db.query(User).filter(
            User.free_analyses_used >= 1,
            User.paid_credits_remaining == 0,
            User.subscription_type == "free",
            User.upsell_sent == False,
            User.created_at <= cutoff_time
        ).all()
        
        if not exhausted_users:
            print("   [~] No exhausted users ready for upselling today.")
            return

        print(f"🎯 Target Acquired: {len(exhausted_users)} hot leads.")
        
        for user in exhausted_users:
            try:
                from bot import send_whatsapp_template
                
                # Trigger pre-approved Meta Template (bypasses 24h block)
                send_whatsapp_template(user.phone_number, "vip_discount_upsell")
                
                # Mark as upsold
                user.upsell_sent = True
                db.commit()
                
                print(f"   [+] Sent aggressive priority upsell to {user.phone_number}")
                time.sleep(2) # Respect meta rate limits
                
            except Exception as e:
                print(f"   [!] Failed to upsell {user.phone_number}: {e}")
                db.rollback()
                
    except Exception as e:
        print(f"❌ Sales Closer failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_sales_closer()
