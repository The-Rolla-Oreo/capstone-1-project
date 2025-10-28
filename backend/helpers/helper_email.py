import smtplib
import ssl
from email.message import EmailMessage

from backend.settings import get_settings


settings = get_settings()


def send_email(receiver_email: str, subject: str, body: str):
    # Config values
    SMTP_HOST = settings.SMTP_HOST
    PORT = settings.SMTP_PORT
    SENDER_EMAIL = settings.SMTP_USERNAME
    PASSWORD = settings.SMTP_PASSWORD
    RECEIVER_EMAIL = receiver_email
    SUBJECT = subject
    BODY = body

    # Create the email object
    msg = EmailMessage()
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(BODY)

    # Sending email
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(SMTP_HOST, PORT) as server:
            # Identify yourself to the ESMTP server
            server.ehlo()

            # Secure the connection using TLS
            server.starttls(context=context)
            server.ehlo()

            # Log in to the server
            server.login(SENDER_EMAIL, PASSWORD)

            # Send the email
            server.send_message(msg)

        # TODO: Use logging instead of printing
        print(f"Email successfully sent to {RECEIVER_EMAIL}!")
    except Exception as e:
        print(f"An error occurred: {e}")
