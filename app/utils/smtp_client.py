import smtplib
from email.message import EmailMessage
from app.config import settings

def send_email_smtp(to, subject, body):
    msg = EmailMessage()
    msg["to"] = to
    msg["from"] = settings.EMAIL_USER
    msg["subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_SERVER,settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
    