from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class EmailCreateRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    send_at: Optional[datetime] = None

class EmailUpdateRequest(BaseModel):
    to: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    send_at: Optional[datetime] = None

class EmailResponse(BaseModel):
    id: int
    to: EmailStr
    subject: str
    body: Optional[str] = None
    send_at: datetime
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
