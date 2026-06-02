from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Attachment, EmailRecord, FileUpload
from app.utils.smtp_client import send_email_smtp
from datetime import datetime, timezone
from app.utils.email_events import publish_private_email_event,publish_public_email_event
from app.utils.mino import download_object_bytes

def build_email_attachments(db, email_id: int) -> list[dict]:
    files = (
        db.query(FileUpload)
        .join(Attachment, Attachment.file_id == FileUpload.id)
        .filter(Attachment.email_id == email_id)
        .all()
    )

    return [
        {
            "filename": file.original_filename,
            "mime_type": file.mime_type,
            "content": download_object_bytes(file.storage_key),
        }
        for file in files
    ]

def publish_email_status(email: EmailRecord) -> None:
    payload = {"email_id": email.id, "status": email.status, "subject": email.subject}
    try:
        publish_public_email_event(payload)
        publish_private_email_event(email.user_id, payload)
    except Exception as exc:
        print(f"failed to publish email status event: {exc}")


@celery_app.task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_job(email_id):
    db = SessionLocal()

    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()

    if not email:
        db.close()
        return

    try:
        if email.status in ("cancelled", "sent"):
            return

        attachments = build_email_attachments(db, email.id)
        send_email_smtp(email.to, email.subject, email.body, attachments)
        
        email.status = "sent"
        email.sent_at = datetime.now(timezone.utc)
        email.error_message = None
        db.commit()
        publish_email_status(email)
      
    except Exception as e:
        db.rollback()

        email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
        if email:
            email.status = "failed"
            email.error_message = str(e)
            db.commit()
            publish_email_status(email)

        raise e
    
    finally:
        db.close()

def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Password Reset Request"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\n the link expires in 1 hour.\nIf you did not request this, please ignore this email."
    
    send_email_smtp(to_email, subject, body)
