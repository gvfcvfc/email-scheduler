from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class EmailCreateRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    send_at: Optional[datetime] = None

class EmailResponse(BaseModel):
    id: int
    to: EmailStr
    subject: str
    body: str
    send_at: datetime
    status: str

    class Config:
        from_attributes = True
        