from fastapi import APIRouter, Depends, HTTPException
from app.models import EmailRecord
from app.schemas.email_schema import EmailCreateRequest, EmailResponse
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import timezone, datetime
from app.utils.JWT import get_current_user

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Welcome to the Email Scheduler API!"}

@router.post("/emails", response_model=EmailResponse)
def create_email(
    email: EmailCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if email.send_at is None:
        send_at = datetime.now(timezone.utc)
    elif email.send_at.tzinfo is None:
        send_at = email.send_at.replace(tzinfo=timezone.utc)
    else:
        send_at = email.send_at.astimezone(timezone.utc)
    
    record = EmailRecord(
        to=email.to,
        subject=email.subject,
        body=email.body,
        send_at=send_at,
        status="pending",
        user_id=current_user.id
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record



@router.get("/scheduled-emails", response_model=list[EmailResponse])
def get_scheduled_emails(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    emails = db.query(EmailRecord).filter(EmailRecord.user_id == current_user.id).all()
    return emails
 
@router.delete("/cancel-email/{email_id}")
def cancel_scheduled_email(email_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    email = db.query(EmailRecord).filter(
        EmailRecord.id ==email_id,
        EmailRecord.user_id == current_user.id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if email.status != "pending":
        return {"error": "Already processed"}
    
    email.status = "cancelled"
    db.commit()
    return {"message": "Scheduled email cancelled successfully!",
            "email_id": email.id}
