from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class EmailRecord(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True)
    to = Column(String, index=True, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String)
    send_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="pending", nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


