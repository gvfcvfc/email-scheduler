from fastapi import Response
from app.utils.JWT import create_access_token, create_refresh_token

def set_auth_cookies(response: Response, db, user, user_agent=None, ip_address=None):
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(db, user.id, user_agent=user_agent, ip_address=ip_address)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800,
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/"
    )

    return response
