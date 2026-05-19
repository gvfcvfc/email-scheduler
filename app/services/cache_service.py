import redis.asyncio as redis
import json
from app.config import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

async def set_cache(key: str, value: dict, expire: int = 300):
    await redis_client.set(key, json.dumps(value), ex=expire)

async def get_cache(key: str):
    data = await redis_client.get(key)

    if not data:
        return None
    return json.loads(data)

async def delete_cache(key:str):
    await redis_client.delete(key)