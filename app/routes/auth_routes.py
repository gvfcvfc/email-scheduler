from app.schemas.auth_schema import ResetPasswordRequest, ResendVerificationEmailRequest, GenericMessageResponse, ForgotPasswordRequest, VerifyEmailRequest
from app.services.password_reset_service import send_password_reset_link, reset_password
from app.services.email_verification_service import send_verification_link, verify_email_token
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.schemas.user import UserResponse, UserDashboardResponse
from app.models import User, EmailRecord, FileUpload
from app.utils.JWT import get_current_user

router = APIRouter()

@router.post("/auth/forgot-password", response_model=GenericMessageResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return send_password_reset_link(db, data.email)

@router.post("/auth/reset-password", response_model=GenericMessageResponse)
def reset_password_route(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return reset_password(db, data.token, data.new_password)

@router.post("/auth/resend-verification-email", response_model=GenericMessageResponse)
def resned_verification(data: ResendVerificationEmailRequest, db: Session = Depends(get_db)):
    return send_verification_link(db, data.email)

@router.post("/auth/verify-email", response_model=GenericMessageResponse)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    return verify_email_token(db, data.token)

@router.get("/users/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user

@router.get("/users/dashboard", response_model=UserDashboardResponse)
def get_user_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scheduled_email_count = db.query(EmailRecord).filter(EmailRecord.user_id == user.id).count()
    pending_email_count = db.query(EmailRecord).filter(EmailRecord.user_id == user.id, EmailRecord.status == "pending").count()
    sent_email_count = db.query(EmailRecord).filter(EmailRecord.user_id == user.id, EmailRecord.status == "sent").count()
    cancelled_email_count = db.query(EmailRecord).filter(EmailRecord.user_id == user.id, EmailRecord.status == "cancelled").count()
    attachment_count = db.query(FileUpload).filter(FileUpload.user_id == user.id).count()
    attachment_storage_bytes = db.query(func.coalesce(func.sum(FileUpload.size_bytes), 0)).filter(FileUpload.user_id == user.id).scalar() or 0

    return {
        "id": user.id,
        "email": user.email,
        "plan": user.plan,
        "subscription_status": user.subscription_status,
        "email_verified": user.email_verified,
        "scheduled_email_count": scheduled_email_count,
        "pending_email_count": pending_email_count,
        "sent_email_count": sent_email_count,
        "cancelled_email_count": cancelled_email_count,
        "attachment_count": attachment_count,
        "attachment_storage_bytes": attachment_storage_bytes,
    } 

    