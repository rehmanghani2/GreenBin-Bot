from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./greenbin_triage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TriageItem(Base):
    __tablename__ = "triage_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    user_query = Column(Text)
    image_url = Column(String, nullable=True)
    status = Column(String, default="NEEDS_REVIEW") # NEEDS_REVIEW or RESOLVED
    agent_notes = Column(Text, nullable=True)
    admin_resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
