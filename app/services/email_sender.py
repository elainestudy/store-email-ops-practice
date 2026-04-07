from dataclasses import dataclass
from uuid import uuid4


@dataclass
class EmailSendResult:
    status: str
    provider_message: str


class FakeEmailSender:
    def send_email(self, recipient_email: str, subject: str, body: str) -> EmailSendResult:
        if recipient_email.endswith("@invalid.test"):
            return EmailSendResult(
                status="failed",
                provider_message="provider_rejected_address",
            )

        return EmailSendResult(
            status="sent",
            provider_message=f"message-{uuid4()}",
        )
