from app.schemas.auth_schema import ResetPasswordRequest, ResendVerificationEmailRequest, GenericMessageResponse, ForgotPasswordRequest
from app.services.password_reset_service import send_password_reset_link, reset_password
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