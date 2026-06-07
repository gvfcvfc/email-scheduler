from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TemplateCreateRequest(BaseModel):
    name: str
    subject: str
    body: str

class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
