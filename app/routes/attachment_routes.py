from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Attachment, EmailRecord, FileUpload
from app.schemas.attachment_schema import AttachmentCreate, AttachmentOut
from app.utils.JWT import get_current_user

router = APIRouter(prefix="/attachments")

@router.post("/emails/{email_id}", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def create_attachment(
    email_id: int,
    payload: AttachmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):

    file_id = payload.file_id
    email = (
        db.query(EmailRecord)
        .filter(EmailRecord.id == email_id, EmailRecord.user_id == current_user.id)
        .first()
    )

    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    file_record = (
        db.query(FileUpload)
        .filter(FileUpload.id == file_id, FileUpload.user_id == current_user.id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    existing = (
        db.query(Attachment)
        .filter(Attachment.email_id == email_id, Attachment.file_id == file_id)
        .first()
    )
    if existing:
        return existing
    
    attachment = Attachment(email_id=email_id, file_id=file_id)
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

@router.get("/{attachment_id}", response_model=AttachmentOut)
def get_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    attachment = (
        db.query(Attachment)
        .join(EmailRecord, Attachment.email_id == EmailRecord.id)
        .filter(Attachment.id == attachment_id, EmailRecord.user_id == current_user.id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return attachment

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    attachment = (
        db.query(Attachment)
        .join(EmailRecord, Attachment.email_id == EmailRecord.id)
        .filter(Attachment.id == attachment_id, EmailRecord.user_id == current_user.id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    db.delete(attachment)
    db.commit()
    return None
