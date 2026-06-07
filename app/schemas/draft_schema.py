from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DraftCreateRequest(BaseModel):
    to: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None

class DraftUpdateRequest(BaseModel):
    to: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None

class DraftResponse(BaseModel):
    id: int
    to: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
