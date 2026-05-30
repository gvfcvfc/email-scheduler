from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Attachment, EmailRecord
from app.schemas.attachment_schema import AttachmentCreate, AttachmentOut

router = APIRouter(prefix="/attachments")

@router.post("/emails/{email_id}", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def  create_attachment(email_id: int, payload: AttachmentCreate, db: Session = Depends(get_db)):

    file_id = payload.file_id
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()

    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    
    existing = (db.query(Attachment).filter(Attachment.email_id == email_id, Attachment.file_id ==file_id).first())
    if existing:
        return {
            "id": str(existing.id),
            "email_id": existing.email_id,
            "file_id": existing.file_id,
            "created_at": existing.created_at.isoformat()
        }
    
    attachment = Attachment(email_id=email_id, file_id=file_id)
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return {
        "id": str(attachment.id),
        "email_id": attachment.email_id,
        "file_id": attachment.file_id,
        "created_at": attachment.created_at.isoformat()
    }

@router.get("/{attachment_id}", response_model=dict)
def get_attachment(attachment_id: UUID, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return {
        "id": str(attachment.id),
        "email_id": attachment.email_id,
        "file_id": attachment.file_id,
        "created_at": attachment.created_at.isoformat()
    }

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(attachment_id: UUID, db:Session = Depends(get_db)):
    attachment = (db.query(Attachment).filter(Attachment.id == attachment_id).first())
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Attachment not found")
    db.delete(attachment)
    db.commit()
    return None