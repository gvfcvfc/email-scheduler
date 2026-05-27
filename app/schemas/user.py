from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class UserDashboardResponse(BaseModel):
    id: int
    email: EmailStr
    plan: str
    subscription_status: str
    email_verified: bool
    scheduled_email_count: int
    pending_email_count: int
    sent_email_count: int
    cancelled_email_count: int
    attachment_count: int
    attachment_storage_bytes: int

    class Config:
        from_attributes = True
