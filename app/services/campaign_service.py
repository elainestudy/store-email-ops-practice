from uuid import UUID

from sqlmodel import select

from app.core.config import Settings
from app.db import get_session
from app.messaging.factory import get_event_bus
from app.models import AuditLog, Campaign, DeliveryAttempt, Recipient
from app.schemas.campaigns import CampaignCreateRequest, DeliveryResultItem
from app.services.email_sender import FakeEmailSender


class CampaignService:
    def __init__(self) -> None:
        self.settings = Settings()
        self.event_bus = get_event_bus()
        self.email_sender = FakeEmailSender()

    def list_campaigns(self) -> list[Campaign]:
        with get_session() as session:
            statement = select(Campaign)
            return list(session.exec(statement).all())

    def create_campaign(self, request: CampaignCreateRequest) -> Campaign:
        campaign = Campaign(**request.model_dump(exclude={"recipients"}))
        recipients = [
            Recipient(
                campaign_id=campaign.id,
                email=recipient.email,
                first_name=recipient.first_name,
            )
            for recipient in request.recipients
        ]
        audit_log = AuditLog(
            campaign_id=campaign.id,
            event_type="campaign_created",
            message=f"Campaign {campaign.name} created with {len(recipients)} recipients",
        )

        with get_session() as session:
            session.add(campaign)
            for recipient in recipients:
                session.add(recipient)
            session.add(audit_log)
            session.commit()
            session.refresh(campaign)
            return campaign

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            return None

        with get_session() as session:
            statement = select(Campaign).where(Campaign.id == campaign_uuid)
            return session.exec(statement).first()

    def enqueue_campaign_send(self, campaign_id: str) -> Campaign | None:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        recipients = self.list_recipients(campaign_id)

        campaign.status = "queued"
        audit_log = AuditLog(
            campaign_id=campaign.id,
            event_type="campaign_queued",
            message="Campaign queued for asynchronous sending",
        )

        with get_session() as session:
            session.add(campaign)
            session.add(audit_log)
            session.commit()
            session.refresh(campaign)

        self.event_bus.publish_send_requested(
            {
                "event_type": "campaign_send_requested",
                "campaign_id": str(campaign.id),
                "subject": campaign.subject,
                "body": campaign.body,
                "recipients": [
                    {
                        "recipient_id": str(recipient.id),
                        "email": recipient.email,
                        "first_name": recipient.first_name,
                    }
                    for recipient in recipients
                ],
            }
        )
        return campaign

    def process_delivery_job(self, payload: dict) -> Campaign | None:
        campaign_id = payload["campaign_id"]
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        recipients = payload.get("recipients", [])
        if not recipients:
            with get_session() as session:
                campaign.status = "failed"
                session.add(campaign)
                session.add(
                    AuditLog(
                        campaign_id=campaign.id,
                        event_type="campaign_failed",
                        message="Campaign has no recipients to send",
                    )
                )
                session.commit()
                session.refresh(campaign)
                return campaign

        results: list[DeliveryResultItem] = []
        for recipient in recipients:
            send_result = self.email_sender.send_email(
                recipient_email=recipient["email"],
                subject=payload["subject"],
                body=payload["body"],
            )
            results.append(
                DeliveryResultItem(
                    recipient_id=recipient["recipient_id"],
                    status=send_result.status,
                    provider_message=send_result.provider_message,
                )
            )

        return self.record_delivery_results(campaign_id, results)

    def record_delivery_results(
        self, campaign_id: str, results: list[DeliveryResultItem]
    ) -> Campaign | None:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        any_failures = False
        with get_session() as session:
            for result in results:
                try:
                    recipient_uuid = UUID(result.recipient_id)
                except ValueError:
                    continue

                recipient = session.exec(
                    select(Recipient).where(Recipient.id == recipient_uuid)
                ).first()
                if recipient is None:
                    continue

                recipient.status = result.status
                if result.status != "sent":
                    any_failures = True

                session.add(
                    DeliveryAttempt(
                        campaign_id=campaign.id,
                        recipient_id=recipient.id,
                        status=result.status,
                        provider_message=result.provider_message,
                    )
                )
                session.add(recipient)

            campaign.status = "partially_failed" if any_failures else "sent"
            session.add(campaign)
            session.add(
                AuditLog(
                    campaign_id=campaign.id,
                    event_type="campaign_processed",
                    message=f"Campaign processed asynchronously with status {campaign.status}",
                )
            )
            session.commit()
            session.refresh(campaign)
            return campaign

    def list_delivery_attempts(self, campaign_id: str) -> list[DeliveryAttempt]:
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            return []

        with get_session() as session:
            statement = select(DeliveryAttempt).where(DeliveryAttempt.campaign_id == campaign_uuid)
            return list(session.exec(statement).all())

    def list_recipients(self, campaign_id: str) -> list[Recipient]:
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            return []

        with get_session() as session:
            statement = select(Recipient).where(Recipient.campaign_id == campaign_uuid)
            return list(session.exec(statement).all())

    def list_audit_logs(self, campaign_id: str) -> list[AuditLog]:
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            return []

        with get_session() as session:
            statement = select(AuditLog).where(AuditLog.campaign_id == campaign_uuid)
            return list(session.exec(statement).all())
