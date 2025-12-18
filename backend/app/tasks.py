import logging

import emails  

from app.core.config import settings
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self,
    email_to: str,
    subject: str,
    html_content: str,
) -> dict:
    try:
        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        
        smtp_options: dict = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD
        
        response = message.send(to=email_to, smtp=smtp_options)
        logger.info(f"Email sent to {email_to}: {response}")
        
        return {
            "status": "sent",
            "email_to": email_to,
            "subject": subject,
        }
    except Exception as exc:
        logger.error(f"Failed to send email to {email_to}: {exc}")
        raise self.retry(exc=exc)
