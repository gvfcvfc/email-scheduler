from fastapi import APIRouter, Depends, Request
from app.services.stripe_service import create_checkout_session, verify_and_construct_event, handle_stripe_event,create_portal_session
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
from app.utils.JWT import get_current_user

router = APIRouter()

@router.post("/billing/checkout-session")
async def checkout_session(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_checkout_session(user, db)
    
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):

    event = await verify_and_construct_event(request)
    return await handle_stripe_event(event,db)

@router.post("/billing/portal")
async def portal_session(db: Session =Depends(get_db), user: User = Depends(get_current_user)):
    return await create_portal_session(user,db)
    

@router.get("/billing/status")
def billing_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return{
        "plan": user.plan,
        "subscription_status":  user.subscription_status,
        "stripe_customer_id": user.stripe_customer_id,
        "stripe_subscription_id": user.stripe_subscription_id
    }

@router.get("/billing/success")
def billing_success():
    return {"message": "Payment successful. Your subscription will update shortly."}

@router.get("/billing/cancel")
def billing_cancel():
    return {"message": "Checkout canceled."}

@router.get("/settings/billing")
def setting_billing():
    return{"plan_management": True}
