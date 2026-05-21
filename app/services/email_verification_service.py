import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import EmailVerificationToken, User
from app.config import settings
from app.utils.smtp_client import send_email_smtp

VERIFICATION_EXPIRATION_HOURS = 24

def hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def send_verification_email(to_email: str, verification_link: str) -> None:
    subject = "verify your email"
    body = f"Please verify by clicking the link:\n {verification_link}\n\nThis link expires in {VERIFICATION_EXPIRATION_HOURS} hours."

    send_email_smtp(to_email, subject, body)

def create_email_verification(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_verification_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRATION_HOURS)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db.add(verification_token)
    db.commit()
    db.refresh(verification_token)
    return raw_token

def send_verification_link(db: Session, email: str) -> dict:
    
    user = db.query(User).filter(User.email == email).first()
    if not user: 
        return {"message": "If an account with that email exists, a verification email has been sent."}
    if (user, "email_verified", False):
    
        raw_token = create_email_verification(db, user)
        verification_link = f"{settings.FRONTEND_URL}/verify_email?token={raw_token}"
        send_verification_email(user.email, verification_link)
    return {"message": "If an account with that email exists, a verification email has been sent."}

def verify_email_token(db: Session, raw_token: str) -> dict:
    token_hash = hash_verification_token(raw_token)

    verification_token = (db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.used ==False,
        EmailVerificationToken.expires_at > datetime.now(timezone.utc)
    ).first())

    if not verification_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.id == verification_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if (user, "email_verified"):
        user.email_verified = True
    else:
        raise HTTPException(status_code=500, detail=" User model has no verification field")
    
    verification_token.used = True
    db.add(user)
    db.add(verification_token)
    db.commit()
    return {"message": "Email verified successfully."}



