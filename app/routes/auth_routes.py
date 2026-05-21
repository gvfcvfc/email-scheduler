from app.schemas.auth_schema import ResetPasswordRequest, ResendVerificationEmailRequest, GenericMessageResponse, ForgotPasswordRequest, VerifyEmailRequest
from app.services.password_reset_service import send_password_reset_link, reset_password
from app.services.email_verification_service import send_verification_link, verify_email_token
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

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