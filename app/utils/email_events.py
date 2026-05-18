import json
import redis
from app.config import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2, decode_responses=True)
CHANNEL_NAME = "email_events"

def publish_public_email_event(payload: dict):
    redis_client.publish("email_events:public", json.dumps(payload))

def publish_private_email_event(user_id: int, payload: dict):
    redis_client.publish(f"email_events:user:{user_id}", json.dumps(payload))


    











    