from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class DraftRecord(Base):
    __tablename__ = "email_drafts"
    id = Column(Integer, primary_key=True)
    to = Column(String, index=True, nullable=True)
    subject = Column(String, nullable=True)
    body = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
