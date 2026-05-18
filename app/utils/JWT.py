from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from app.config import settings
from sqlalchemy.orm import Session
from app.database import get_db
import secrets
from app.models import RefreshToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(password: str, hashed:str) -> bool:
    return pwd_context.verify(password, hashed)

ALGORITHM = "HS256"

def create_access_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {"sub": str(user_id),"type":"access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(db: Session, user_id, user_agent=None, ip_address=None):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token, 
        expires_at=expires_at,
        revoked=False,
        user_agent=user_agent,
        ip_address=ip_address

    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return token 

def get_current_user(request: Request, db: Session = Depends(get_db)):

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
def get_user_from_access_token(token: str, db: Session):
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")

        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        print("user", user)

        return user
    except JWTError:
        return None 
