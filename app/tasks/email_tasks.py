from app import celery
from app.email_sendgrid import send_email_via_sendgrid

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to_email, subject, html_content):
    try:
        send_email_via_sendgrid(to_email, subject, html_content)
    except Exception as exc:
        raise self.retry(exc=exc)
