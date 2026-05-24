from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class FileUpload(Base):
    __tablename__ = "file_uploads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False, unique=True, index=True)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
