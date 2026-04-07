from pydantic import BaseModel, Field


class RecipientCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    first_name: str = Field(min_length=1, max_length=100)


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    subject: str = Field(min_length=3, max_length=150)
    body: str = Field(min_length=5, max_length=5000)
    store_id: str = Field(min_length=2, max_length=50)
    recipients: list[RecipientCreateRequest] = Field(default_factory=list)


class DeliveryResultItem(BaseModel):
    recipient_id: str
    status: str = Field(min_length=4, max_length=32)
    provider_message: str = Field(min_length=1, max_length=255)


class CampaignDeliveryResultsRequest(BaseModel):
    results: list[DeliveryResultItem] = Field(default_factory=list)
