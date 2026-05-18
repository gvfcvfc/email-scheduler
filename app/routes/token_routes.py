from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from app.utils.JWT import verify_password,hash_password, get_current_user
from app.database import get_db
from app.schemas.user import UserResponse, UserCreate
from app.models import RefreshToken, User
from datetime import datetime, timezone
from app.utils.oauth import oauth
from app.utils.set_auth_cookies import set_auth_cookies

router = APIRouter()

ALGORITHM = "HS256"
@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.post("/token")
def login(response:Response,request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host 
    

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    response = JSONResponse(content={"message": "login successful"})
    return set_auth_cookies(response, db, user, user_agent=user_agent, ip_address=ip_address)

@router.post("/logout")
def logout(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response.delete_cookie(key="access_token",path="/")
    response.delete_cookie(key="refresh_token",path="/")
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked":True})
    return {"message": "logout successful"}

@router.post("/refresh")
def refresh_token(response: Response,request: Request,db:Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    if not refresh_token or refresh_token.revoked or refresh_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    refresh_token.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    response = JSONResponse(content={"message": "token refreshed"})
    return set_auth_cookies(response, db, user)
    
   
@router.get("/sessions")
def get_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    sessions = db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked == False).all()
    return sessions

@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(RefreshToken).filter(RefreshToken.id == session_id, RefreshToken.user_id == user.id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.revoked = True
    db.commit()
    return {"message": "Session revoked"}

@router.get("/auth/github/login")
async def github_login(request: Request):
    redirect_uri = str(request.url_for("github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/auth/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        print("GitHub auth error", repr(e))
        raise HTTPException(status_code=400, detail=f"GitHub authorization failed: {e}")
    
    email_resp = await oauth.github.get("user/emails", token=token)
    email_resp.raise_for_status()
    emails = email_resp.json()

    email = next(
        (
            item["email"] for item in emails
            if item.get("primary") and item.get("verified")
        ),
        None,
    )

    if not email:
        raise HTTPException(status_code=400, detail="No verified primary email found in GitHub account")
    
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email, hashed_password=None)
        db.add(user)
        db.commit()
        db.refresh(user)

    response = RedirectResponse(url="http://localhost:8000", status_code=302)

    return set_auth_cookies(response, db, user)

