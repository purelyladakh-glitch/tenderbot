from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tenderbot.db")

# Fix for Heroku/Railway PostgreSQL URLs which starts with 'postgres://' 
# but SQLAlchemy requires 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False, PostgreSQL does not.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- TABLES ---

class WebhookLog(Base):
    """Logs all incoming webhooks from Twilio and Razorpay for reliability."""
    __tablename__ = "webhook_logs"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)  # 'twilio' or 'razorpay'
    payload = Column(String) # JSON string
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class User(Base):
    __tablename__ = "users"

    phone_number = Column(String, primary_key=True, index=True)
    language_preference = Column(String, default="Hinglish")
    conversation_state = Column(String, default="new")
    referred_by = Column(String, nullable=True)  # Phone number of the referrer
    # new | awaiting_location | awaiting_work_type | awaiting_value_range |
    # awaiting_departments | awaiting_alert_freq | ready | analyzing | menu

    # Subscription
    subscription_type = Column(String, default="free")  # free / single / pack / monthly
    alert_tier = Column(String, default="free")  # free / basic / full
    paid_credits_remaining = Column(Integer, default=0)
    free_analyses_used = Column(Integer, default=0)  # max 1
    total_analyses_done = Column(Integer, default=0)
    subscription_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContractorPreference(Base):
    __tablename__ = "contractor_preferences"

    phone_number = Column(String, primary_key=True, index=True)
    states_list = Column(Text, default="[]")        # JSON list
    districts_list = Column(Text, default="[]")      # JSON list
    work_types = Column(Text, default="[]")          # JSON list
    departments = Column(Text, default="[]")         # JSON list
    min_value = Column(Integer, default=0)           # in rupees
    max_value = Column(Integer, default=500000000)   # 50 crore default
    alert_frequency = Column(String, default="daily")  # instant / daily / weekly
    alerts_paused = Column(Boolean, default=False)
    pause_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    tender_summary = Column(String)
    analysis_result = Column(Text)  # JSON text
    deadline_date = Column(DateTime, nullable=True) # Extracted deadline
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    razorpay_order_id = Column(String, unique=True, index=True)
    amount = Column(Integer)
    status = Column(String, default="created")  # created / paid / failed
    plan_type = Column(String)  # single / pack / monthly
    created_at = Column(DateTime, default=datetime.utcnow)


class TenderAlertLog(Base):
    __tablename__ = "tender_alerts_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    tender_id = Column(String)
    alert_type = Column(String)  # free / brief / full
    sent_at = Column(DateTime, default=datetime.utcnow)
    user_response = Column(String, default="ignored")  # yes / no / later / ignored
    followed_up = Column(Boolean, default=False)


class ReminderLog(Base):
    __tablename__ = "reminder_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    tender_id = Column(String, index=True)
    analysis_id = Column(Integer, index=True)
    deadline = Column(DateTime)
    reminders_sent = Column(Text, default="[]") # JSON list: ["7d", "2d", "1d", "0d"]
    created_at = Column(DateTime, default=datetime.utcnow)


class TenderRecord(Base):
    __tablename__ = "tender_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String, unique=True, index=True) # e.g., eprocure ID
    title = Column(String)
    department = Column(String)
    state = Column(String)
    value_inr = Column(Integer, default=0)
    published_date = Column(DateTime)
    closing_date = Column(DateTime)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
