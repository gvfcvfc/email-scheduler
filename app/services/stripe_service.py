import stripe
from app.services.cache_service import get_cache, set_cache, delete_cache
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User

def get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="stripe secret key is not configured")
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe

async def create_or_get_customer(user, db: Session):
        stripe_client = get_stripe_client()

        cached_customer_id = await get_cache(f"stripe_customer:{user.id}")
        if cached_customer_id:
            return cached_customer_id

        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        if not user.email:
            raise HTTPException(status_code=400, detail="User does not have an email address")
        
        customer = stripe_client.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id)})
        
        user.stripe_customer_id = customer["id"]
        db.add(user)
        db.commit()
        db.refresh(user)
        
        await set_cache(f"stripe_customer:{user.id}", customer["id"], expire=3600)
        return customer["id"]

def create_checkout_session(user, db: Session):

    stripe_client = get_stripe_client()
    customer_id = create_or_get_customer(user, db)

    try:
        checkout_session = stripe_client.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{settings.APP_URL}/billing/success",
            cancel_url=f"{settings.APP_URL}/billing/cancel",
            metadata={"user_id": str(user.id)}
        )
        return {"checkout_url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def verify_and_construct_event(request):

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="stripe webhook secret is not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature header")
    secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=secret)
        return event
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="invalid stripe signature")
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid payload")
    
async def sync_user_subscription_from_stripe(user: User, subscription:dict, db: Session):

        status = subscription.get("status", "inactive")

        user.stripe_subscription_id = subscription.get("id", user.stripe_customer_id)
        user.stripe_customer_id = subscription.get("customer", user.stripe_customer_id)

        if status in {"active", "trialing"}:
            user.plan = "pro"
            user.subscription_status = "active"

        elif status == "past_due":
            user.plan = "pro"
            user.subscription_status = "past_due"
        elif status == "canceled":
            user.plan = "free"
            user.subscription_status = "canceled"
        else:
            user.subscription_status = status
            if not subscription.get("cancel_at_period_end", False):
                user.plan = "free"

        db.add(user)
        db.commit()
        db.refresh(user)

        await delete_cache(f"billing:{user.id}")
        return user

def handle_stripe_event(event: dict, db: Session):

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = obj.get("metadata",{}).get("user_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")

        if not user_id:
            return {"recieved": True}
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return {"recieved": True}
        
        user.stripe_customer_id = customer_id or user.stripe_customer_id
        user.stripe_subscription_id = subscription_id
        user.plan = "pro"
        user.subscription_status = "active"

        db.add(user)
        db.commit()
        db.refresh(user)
        return {"received": True}
    
    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        subscription_id = obj.get("id")
        customer_id = obj.get("customer")

        user = (db.query(User).filter(User.stripe_subscription_id == subscription_id).first())

        if not user and customer_id:
            user = (db.query(User).filter(User.stripe_customer_id == customer_id).first())
        
        if user:
            sync_user_subscription_from_stripe(user, obj, db)
        return {"received": True}
    
    if event_type == "customer.subscription.deleted":
        subscription_id = obj.get("id")
        user = (db.query(User).filter(User.stripe_subscription_id ==subscription_id).first())

        if user:
            user.stripe_subscription_id = None
            user.plan = "free"
            user.subscription_status = "canceled"
            db.add(user)
            db.commit()
            db.refresh(user)

        return {"received": True}
    
    if event_type == "invoice.payment_failed":
        subscription_id = obj.get("subscription")
        if subscription_id:
            user = (db.query(User).filter(User.stripe_subscrition_id == subscription_id).first())
            if user:
                user.subscription_status = "past_due"
                db.add(user)
                db.commit()
                db.refresh(user)
            
            return {"received": True}
        return {"received": True}
    
def create_portal_session(user, db: Session):

    stripe_client = get_stripe_client()
    customer_id = create_or_get_customer(user, db)

    try:
        session = stripe_client.billing_portal.Session.create(
            customer=customer_id,
            return_url = f"{settings.APP_URL}/settings/billing"
        )
        return{"portal_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
