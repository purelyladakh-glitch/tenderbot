from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
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
    language_preference = Column(String, default="English")
    preferred_states = Column(String, default="")  # comma-separated state keys e.g. "7,8"
    conversation_state = Column(String, default="new")  # new, awaiting_location, ready, analyzing, menu
    free_analyses_used = Column(Integer, default=0) # max 1
    paid_credits_remaining = Column(Integer, default=0)
    subscription_type = Column(String, default="none") # none/single/pack/monthly
    subscription_expiry = Column(DateTime, nullable=True)
    total_analyses_done = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    tender_summary = Column(String)
    analysis_result = Column(String) # Storing JSON text
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String, index=True)
    razorpay_order_id = Column(String, unique=True, index=True)
    amount = Column(Integer)
    status = Column(String, default="created") # created, paid, failed, signature_verified
    plan_type = Column(String) # single, pack, monthly
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
