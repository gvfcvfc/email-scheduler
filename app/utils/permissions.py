from fastapi import Depends, HTTPException, WebSocketException, status
from app.utils.JWT import get_current_user, get_current_user_ws
from app.models import User

def require_pro_user(user: User = Depends(get_current_user)):
    if not user.plan != "pro" or user.subscription_status != "active":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    return user

def require_pro_user_ws(user: User = Depends(get_current_user_ws)):

    if not user:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Not authenticated")
    if user.plan != "pro" or user.subscription_status != "active":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Pro subscription required")
    
    return user
