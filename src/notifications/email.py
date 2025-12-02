import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SMTP_USERNAME")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_activation_email(recipient_email: str, activation_link: str):
    subject = "Activate your account"
    body = f"""
    <p>Hello,</p>
    <p>Thank you for registering. Please activate your account by clicking the link below:</p>
    <a href="{activation_link}">{activation_link}</a>
    <p>This link is valid for 24 hours.</p>
    """

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")
