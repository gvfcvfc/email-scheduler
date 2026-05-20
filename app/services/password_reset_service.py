import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import PasswordResetToken, RefreshToken, User
from app.config import settings
from app.utils.JWT import hash_password
from app.services.email_service import send_password_reset_email

RESET_TOKEN_EXPIRATION_HOURS = 1

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_password_reset_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRATION_HOURS)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return raw_token

def send_password_reset_link(db: Session, email: str) -> dict:
    user = db.query(User).filter(User.email ==email).first()

    if not user:
        return {"message": " If the email exists, a reset link has been sent."}
    
    raw_token = create_password_reset_token(db, user)
    reset_link = f"{settings.FRONTEND_URL}/reset_password?token={raw_token}"
    send_password_reset_email(user.email, reset_link)
    return {"message": "If the email exists, a reset link has been sent."}

def verify_password_reset_token(db: Session, raw_token: str) -> PasswordResetToken:
    token_hash = hash_reset_token(raw_token)

    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash,
                 PasswordResetToken.used == False,
                 PasswordResetToken.expires_at > datetime.now(timezone.utc)).first()

        )
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return reset_token

def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    for token in tokens:
        token.revoked = True
        db.add(token)
    db.commit()

def reset_password(db: Session, raw_token: str, new_password: str) -> dict:
    reset_token = verify_password_reset_token(db, raw_token)
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    user.hashed_password = hash_password(new_password)
    reset_token.used = True
    db.add(user)
    db.add(reset_token)
    db.commit()
    db.refresh(user)

    revoke_all_user_refresh_tokens(db, user.id)

    return {"message": "Password has been reset successfully."}
