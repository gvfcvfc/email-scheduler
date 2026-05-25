import asyncio
import json
import redis.asyncio as redis_async
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.config import settings
from app.database import SessionLocal
from app.utils.permissions import require_pro_user_ws
from app.models import User

router = APIRouter()

@router.websocket("/ws/emails/public")
async def email_updates(websocket: WebSocket):


    await websocket.accept()

    redis_client = redis_async.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("email_events:public")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = json.loads(message["data"])
                await websocket.send_json(data)

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("email_events:public")
        await pubsub.close()
        await redis_client.close()

@router.websocket("/ws/emails/me")
async def private_email_updates(websocket: WebSocket, user: User = Depends(require_pro_user_ws)):

    await websocket.accept()
    db = SessionLocal()
    redis_client = redis_async.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2, decode_responses=True)
    pubsub = redis_client.pubsub()


    try:
        channel_name = f"email_events:user:{user.id}"
        await pubsub.subscribe(channel_name)
        
        while True:

            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message:
                data = json.loads(message["data"])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass

    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        await redis_client.close()
        db.close()