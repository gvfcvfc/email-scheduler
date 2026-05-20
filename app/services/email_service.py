from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import EmailRecord
from app.utils.smtp_client import send_email_smtp
from datetime import datetime, timezone
from app.utils.email_events import publish_private_email_event,publish_public_email_event


@celery_app.task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_job(email_id):
    db = SessionLocal()

    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()

    if not email:
        db.close()
        return

    try:
        send_email_smtp(email.to, email.subject, email.body )
        
        email.status = "sent"
        email.send_at = datetime.now(timezone.utc)
        db.commit()
        
        payload = {"email_id": email.id, "status": "sent", "subject": email.subject}

        publish_public_email_event(payload)
        publish_private_email_event(email.user_id, payload)
      
    except Exception as e:
        db.rollback()
        email.status = "failed"
        email.error_message = str(e)
        db.commit()
        raise e
    
    finally:
        db.close()

def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Password Reset Request"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\n the link expires in 1 hour.\nIf you did not request this, please ignore this email."
    
    send_email_smtp(to_email, subject, body)