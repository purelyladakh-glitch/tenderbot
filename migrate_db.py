from sqlalchemy import text, inspect
from database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Checks for missing columns and applies ALTER TABLE statements."""
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 1. Check users table
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'referred_by' not in columns:
            logger.info("Adding referred_by column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN referred_by VARCHAR;"))
            conn.commit()
            
        if 'subscription_expiry' not in columns:
            logger.info("Adding subscription_expiry column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_expiry TIMESTAMP;"))
            conn.commit()

        if 'updated_at' not in columns:
            logger.info("Adding updated_at column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            conn.commit()

        if 'source' not in columns:
            logger.info("Adding source column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN source VARCHAR DEFAULT 'organic';"))
            conn.commit()

        if 'upsell_sent' not in columns:
            logger.info("Adding upsell_sent tracking flag...")
            conn.execute(text("ALTER TABLE users ADD COLUMN upsell_sent BOOLEAN DEFAULT FALSE;"))
            conn.commit()

        # 2. Check webhook_logs table
        columns = [col['name'] for col in inspector.get_columns('webhook_logs')]
        if 'message_id' not in columns:
            logger.info("Adding message_id column to webhook_logs...")
            conn.execute(text("ALTER TABLE webhook_logs ADD COLUMN message_id VARCHAR;"))
            conn.commit()

        # 3. Check analyses table
        columns = [col['name'] for col in inspector.get_columns('analyses')]
        if 'deadline_date' not in columns:
            logger.info("Adding deadline_date to analyses...")
            conn.execute(text("ALTER TABLE analyses ADD COLUMN deadline_date TIMESTAMP;"))
            conn.commit()

        # 4. Check marketing_leads table
        columns = [col['name'] for col in inspector.get_columns('marketing_leads')]
        if 'template_used' not in columns:
            logger.info("Adding template_used to marketing_leads...")
            conn.execute(text("ALTER TABLE marketing_leads ADD COLUMN template_used VARCHAR;"))
            conn.commit()

        logger.info("Database migration check complete.")

if __name__ == "__main__":
    run_migrations()
