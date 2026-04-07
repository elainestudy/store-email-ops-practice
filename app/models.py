from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CampaignBase(SQLModel):
    name: str
    subject: str
    body: str
    store_id: str


class Campaign(CampaignBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class RecipientBase(SQLModel):
    email: str
    first_name: str


class Recipient(RecipientBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaign.id", index=True)
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class DeliveryAttempt(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaign.id", index=True)
    recipient_id: UUID = Field(foreign_key="recipient.id", index=True)
    status: str
    provider_message: str
    retry_count: int = 0
    attempted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class AuditLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: Optional[UUID] = Field(default=None, foreign_key="campaign.id", index=True)
    event_type: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
