from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.utils.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CostSnapshot(Base):
    """Daily cost snapshots cached from AWS Cost Explorer."""
    __tablename__ = "cost_snapshots"

    id = Column(String, primary_key=True)  # date:service
    date = Column(String, nullable=False, index=True)
    service = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    region = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """Stored chat history for context."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    session_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IdleResource(Base):
    """Cached idle resource scan results."""
    __tablename__ = "idle_resources"

    id = Column(String, primary_key=True)
    resource_type = Column(String, nullable=False)  # ebs_volume | elastic_ip | ec2_stopped
    resource_id = Column(String, nullable=False)
    region = Column(String, nullable=False)
    estimated_monthly_cost = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(String, default="false")


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
