from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Attachment, EmailRecord, DraftRecord, TemplateRecord
from app.schemas.attachment_schema import AttachmentOut
from app.schemas.email_schema import (
    EmailCreateRequest,
    EmailFromDraftRequest,
    EmailFromTemplateRequest,
    EmailResponse,
    EmailUpdateRequest,
)
from app.schemas.draft_schema import (
    DraftCreateRequest,
    DraftResponse,
    DraftUpdateRequest,
)
from app.schemas.template_schema import (
    TemplateCreateRequest,
    TemplateResponse,
    TemplateUpdateRequest,
)
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


def get_user_draft_or_404(draft_id: int, user_id: int, db: Session) -> DraftRecord:
    draft = (
        db.query(DraftRecord)
        .filter(DraftRecord.id == draft_id, DraftRecord.user_id == user_id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


def get_user_template_or_404(template_id: int, user_id: int, db: Session) -> TemplateRecord:
    template = (
        db.query(TemplateRecord)
        .filter(TemplateRecord.id == template_id, TemplateRecord.user_id == user_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template

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

@router.get("/emails/drafts", response_model=list[DraftResponse])
def list_drafts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(DraftRecord).filter(DraftRecord.user_id == current_user.id).all()

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

@router.post("/emails/from-draft/{draft_id}", response_model=EmailResponse)
def create_email_from_draft(
    draft_id: int,
    payload: EmailFromDraftRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    draft = get_user_draft_or_404(draft_id, current_user.id, db)
    if not (draft.to and draft.subject and draft.body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft must include recipient, subject, and body to create an email",
        )
    send_at = normalize_send_at(payload.send_at)
    email = EmailRecord(
        to=draft.to,
        subject=draft.subject,
        body=draft.body,
        send_at=send_at,
        status="pending",
        user_id=current_user.id,
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

@router.post("/emails/from-template/{template_id}", response_model=EmailResponse)
def create_email_from_template(
    template_id: int,
    payload: EmailFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    template = get_user_template_or_404(template_id, current_user.id, db)
    send_at = normalize_send_at(payload.send_at)
    email = EmailRecord(
        to=payload.to,
        subject=payload.subject or template.subject,
        body=payload.body or template.body,
        send_at=send_at,
        status="pending",
        user_id=current_user.id,
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

@router.post("/emails/draft", response_model=DraftResponse)
def create_draft(
    payload: DraftCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    draft = DraftRecord(
        to=payload.to,
        subject=payload.subject,
        body=payload.body,
        created_at=now,
        updated_at=now,
        user_id=current_user.id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

@router.patch("/emails/draft/{draft_id}", response_model=DraftResponse)
def update_draft(
    draft_id: int,
    payload: DraftUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    draft = get_user_draft_or_404(draft_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        for field, value in updates.items():
            setattr(draft, field, value)
        draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft

@router.delete("/emails/draft/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    draft = get_user_draft_or_404(draft_id, current_user.id, db)
    db.delete(draft)
    db.commit()
    return None

@router.post("/templates", response_model=TemplateResponse)
def create_template(
    payload: TemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    template = TemplateRecord(
        name=payload.name,
        subject=payload.subject,
        body=payload.body,
        created_at=now,
        updated_at=now,
        user_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.get("/templates", response_model=list[TemplateResponse])
def list_templates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(TemplateRecord).filter(TemplateRecord.user_id == current_user.id).all()

@router.patch("/templates/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    payload: TemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    template = get_user_template_or_404(template_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        for field, value in updates.items():
            setattr(template, field, value)
        template.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    template = get_user_template_or_404(template_id, current_user.id, db)
    db.delete(template)
    db.commit()
    return None

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
