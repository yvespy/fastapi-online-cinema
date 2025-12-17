import os
from fastapi import Depends

from src.config.settings import Settings, TestSettings
from src.notifications.email import (
    send_activation_email,
    send_password_reset_email,
    send_password_reset_complete_email,
)
from src.notifications.interface import EmailSenderInterface
from src.tests.stubs.email_stub import StubEmailSender


def get_settings():
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "testing":
        return TestSettings()

    return Settings()


class EmailSenderAdapter(EmailSenderInterface):
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        await send_activation_email(email, activation_link)

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        await send_password_reset_email(email, reset_link)

    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        await send_password_reset_complete_email(email, login_link)


def get_email_sender(settings=Depends(get_settings)) -> EmailSenderInterface:
    """
    Return email sender:
    - for testing -> StubEmailSender
    - for real case -> real email sender
    """
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "testing":
        return StubEmailSender()

    return EmailSenderAdapter()
