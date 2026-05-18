from celery import Celery

celery_app = Celery(
    "email_scheduler",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    include=["app.services.scheduler_service"]
)

celery_app.conf.beat_schedule = {
    "check-email-every-10-seconds": {
        "task": "app.services.scheduler_service.check_and_send_scheduled_emails",
        "schedule": 10.0,
    }
}
