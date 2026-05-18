from fastapi import HTTPException
from redis import Redis
from app.config import settings

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2, decode_responses=True)

def check_rate_limit(key: str, limit: int, window_seconds: int):
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, window_seconds)
    if count > limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")