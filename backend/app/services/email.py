import logging,smtplib
from email.message import EmailMessage
from app.core.config import settings
log=logging.getLogger(__name__)
def send_email(to:str,subject:str,body:str)->bool:
    required=[settings.email_smtp_host,settings.email_smtp_user,settings.email_smtp_password,settings.email_from]
    if not all(required):
        log.info("Email provider not configured; skipped delivery to %s",to)
        return False
    msg=EmailMessage();msg["Subject"]=subject;msg["From"]=settings.email_from;msg["To"]=to;msg.set_content(body)
    try:
        with smtplib.SMTP(settings.email_smtp_host,settings.email_smtp_port,timeout=10) as server:
            server.starttls();server.login(settings.email_smtp_user,settings.email_smtp_password);server.send_message(msg)
        return True
    except Exception:
        log.exception("Email delivery failed")
        return False
