import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email_via_sendgrid(to_email, subject, html_content):
    message = Mail(
        from_email=os.environ["FROM_EMAIL"],
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    sg.send(message)
