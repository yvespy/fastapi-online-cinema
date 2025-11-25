import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 587
SENDER_EMAIL = "8a308993f64669"
SENDER_PASSWORD = "3f7911d441bcf0"

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
