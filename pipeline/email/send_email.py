import smtplib
import logging
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")

SMTP_PORT = os.getenv("SMTP_PORT")

SMTP_USERNAME = os.getenv("SMTP_USERNAME")

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FROM_EMAIL = os.getenv("FROM_EMAIL")


def validate_email_config():

    missing = []

    if not SMTP_SERVER:
        missing.append("SMTP_SERVER")

    if not SMTP_PORT:
        missing.append("SMTP_PORT")

    if not SMTP_USERNAME:
        missing.append("SMTP_USERNAME")

    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")

    if not FROM_EMAIL:
        missing.append("FROM_EMAIL")

    if missing:

        logger.error(
            f"Missing environment variables: {', '.join(missing)}"
        )

        return False

    return True


def send_email(
    recipient_email: str,
    subject: str,
    body: str
) -> bool:

    if not validate_email_config():

        return False

    try:

        port = int(SMTP_PORT)

        logger.info(
            f"Connecting to SMTP server {SMTP_SERVER}:{port}"
        )

        server = smtplib.SMTP(
            SMTP_SERVER,
            port
        )

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        message = MIMEMultipart()

        message["From"] = FROM_EMAIL
        message["To"] = recipient_email
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain")
        )

        server.send_message(
            message
        )

        server.quit()

        logger.info(
            f"Email successfully sent to {recipient_email}"
        )

        return True

    except Exception as e:

        logger.error(
            f"Email sending failed: {str(e)}"
        )

        return False
