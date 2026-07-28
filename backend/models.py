from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="normal") # normal, alert, verifying
    last_active = Column(DateTime, default=datetime.utcnow)
    hashed_password = Column(String, nullable=True)  # for auth

class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(Float)
    anomaly_type = Column(String)
    evidence_image_url = Column(String, nullable=True)  # URL to snapshot image
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String) # verification_requested, user_verified, alert_triggered
