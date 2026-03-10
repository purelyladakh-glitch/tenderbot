from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tenderbot.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
