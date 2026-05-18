from app.services.email_service import send_email_job
from app.models import EmailRecord
from app.database import SessionLocal
from datetime import datetime, timezone
from app.celery_app import celery_app

@celery_app.task()
def check_and_send_scheduled_emails():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    emails = db.query(EmailRecord).filter(
        EmailRecord.status == "pending",
        EmailRecord.send_at <= now).all()
    
    for email in emails:
        email.status = "processing"
        db.commit()
        send_email_job.delay(email.id)

    db.close()
