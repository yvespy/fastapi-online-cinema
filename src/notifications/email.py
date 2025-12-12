import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import aiosmtplib
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")  # login
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # password
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@example.com")
USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

logger.debug("Email config: server=%s port=%s from=%s use_tls=%s",
             SMTP_SERVER, SMTP_PORT, MAIL_FROM, USE_TLS)

ACTIVATION_HTML = """\
<p>Hello,</p>
<p>Thank you for registering. Please activate your account by clicking the link below:</p>
<a href="{activation_link}">{activation_link}</a>
<p>This link is valid for 24 hours.</p>
"""

PASSWORD_RESET_HTML = """\
<p>Hello,</p>
<p>You requested a password reset. Please click the link below:</p>
<a href="{reset_link}">{reset_link}</a>
<p>This link is valid for 1 hour.</p>
"""

PASSWORD_RESET_COMPLETE_HTML = """\
<p>Hello,</p>
<p>Your password has been successfully reset.</p>
<p>You can log in using the link below:</p>
<a href="{login_link}">{login_link}</a>
"""


async def _send_email(recipient_email: str, subject: str, html_body: str) -> None:
    message = MIMEMultipart()
    message["From"] = MAIL_FROM
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            use_tls=False,
            start_tls=True
        )

        await smtp.connect()
        await smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        await smtp.sendmail(MAIL_FROM, [recipient_email], message.as_string())
        await smtp.quit()

    except Exception as e:
        logger.exception("Failed to send email: %s", e)


async def send_activation_email(recipient_email: str, activation_link: str) -> None:
    html = ACTIVATION_HTML.format(activation_link=activation_link)
    await _send_email(recipient_email, "Activate your account", html)


async def send_password_reset_email(recipient_email: str, reset_link: str) -> None:
    html = PASSWORD_RESET_HTML.format(reset_link=reset_link)
    await _send_email(recipient_email, "Password reset request", html)


async def send_password_reset_complete_email(recipient_email: str, login_link: str) -> None:
    html = PASSWORD_RESET_COMPLETE_HTML.format(login_link=login_link)
    await _send_email(recipient_email, "Your password has been reset", html)
