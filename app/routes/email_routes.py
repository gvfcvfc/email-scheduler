from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Attachment, EmailRecord
from app.schemas.attachment_schema import AttachmentOut
from app.schemas.email_schema import EmailCreateRequest, EmailResponse, EmailUpdateRequest
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import timezone, datetime
from app.utils.JWT import get_current_user
from app.services.email_service import publish_email_status
from typing import Optional
router = APIRouter()

def normalize_send_at(send_at:Optional[datetime]) -> datetime:
    if send_at is None:
        return datetime.now(timezone.utc)
    if send_at.tzinfo is None:
        return send_at.replace(tzinfo=timezone.utc)
    return send_at.astimezone(timezone.utc)

def get_user_email_or_404(email_id: int, user_id: int, db: Session) -> EmailRecord:
    email = (
        db.query(EmailRecord)
        .filter(EmailRecord.id == email_id, EmailRecord.user_id == user_id)
        .first()
    )
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return email

@router.get("/")
def home():
    return {"message": "Welcome to the Email Scheduler API!"}

@router.post("/emails", response_model=EmailResponse)
def create_email(
    email: EmailCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    send_at = normalize_send_at(email.send_at)
    
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

@router.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(email_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return get_user_email_or_404(email_id, current_user.id, db)

@router.patch("/emails/{email_id}", response_model=EmailResponse)
def update_email(
    email_id: int,
    payload: EmailUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    email = get_user_email_or_404(email_id, current_user.id, db)

    if email.status not in ("pending", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending, failed, or cancelled emails can be updated",
        )

    updates = payload.model_dump(exclude_unset=True)
    if "send_at" in updates:
        updates["send_at"] = normalize_send_at(updates["send_at"])

    for field, value in updates.items():
        setattr(email, field, value)

    if email.status in ("failed", "cancelled"):
        email.status = "pending"
        email.error_message = None

    db.commit()
    db.refresh(email)
    return email

@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(email_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    email = get_user_email_or_404(email_id, current_user.id, db)

    if email.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Processing emails cannot be deleted",
        )

    db.delete(email)
    db.commit()
    return None

@router.get("/emails/{email_id}/attachments", response_model=list[AttachmentOut])
def get_email_attachments(
    email_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    get_user_email_or_404(email_id, current_user.id, db)
    return db.query(Attachment).filter(Attachment.email_id == email_id).all()

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
    publish_email_status(email)
    return {"message": "Scheduled email cancelled successfully!",
            "email_id": email.id}
