import smtplib
from email.message import EmailMessage
from app.config import settings
from typing import Optional

def split_mime_type(mime_type: Optional[str]):
    if not mime_type or "/" not in mime_type:
        return "application", "octet-stream"
    maintype, subtype = mime_type.split("/", 1)
    return maintype, subtype

def send_email_smtp(to, subject, body, attachments=None):
    msg = EmailMessage()
    msg["To"] = to
    msg["From"] = settings.EMAIL_USER
    msg["Subject"] = subject
    if body is None:
        raise ValueError("Email body cannot be None")
    msg.set_content(body)

    for attachment in attachments or []:
        maintype, subtype = split_mime_type(attachment.get("mime_type"))
        msg.add_attachment(
            attachment["content"],
            maintype=maintype,
            subtype=subtype,
            filename=attachment["filename"],
        )

    with smtplib.SMTP(settings.SMTP_SERVER,settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
