import time
from fastapi import FastAPI, Request, HTTPException
from app.routes.email_routes import router
from app.routes.token_routes import router as token_router
from app.routes.ws_routes import router as ws_router
from app.routes.stripe_routes import router as st_router
from app.routes.auth_routes import router as auth_router
from app.config import settings
from starlette.middleware.sessions import SessionMiddleware
from app.utils.rate_limit import check_rate_limit
from fastapi.responses import JSONResponse

def create_app():

    app = FastAPI()

    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        ip = request.client.host
        try:
            check_rate_limit(key=f"global:{ip}", limit=100, window_seconds=60)
        except HTTPException:
            return JSONResponse(
                status_code=429,
                content={"detail": "too many requests. Please try again later."}
            )

        return await call_next(request)

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):


        start_time = time.time()
        
        response =  await call_next(request)
        duration = time.time() - start_time
        print("response took", duration)
        print("request method",request.method)
        
        return response
    
    app.include_router(router)
    app.include_router(token_router)
    app.include_router(ws_router)
    app.include_router(st_router)
    app.include_router(auth_router)
    return app
app = create_app()
