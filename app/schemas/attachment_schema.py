from datetime import datetime
from uuid import UUID
from pydantic import BaseModel 

class AttachmentOut(BaseModel):
    id: UUID
    email_id: int
    file_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class AttachmentCreate(BaseModel):
    file_id: UUID 
    