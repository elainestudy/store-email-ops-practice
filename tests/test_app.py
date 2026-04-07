import pytest

from app import create_app
from app.db import reset_db
from app.messaging.factory import get_event_bus
from app.worker import process_next_send_request


def reset_event_bus() -> None:
    event_bus = get_event_bus()
    reset = getattr(event_bus, "reset", None)
    if callable(reset):
        reset()


@pytest.fixture(autouse=True)
def clear_campaigns():
    reset_db()
    reset_event_bus()
    yield
    reset_db()
    reset_event_bus()


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def make_campaign_payload(**overrides):
    payload = {
        "name": "Spring Member Event",
        "subject": "New arrivals for members",
        "body": "Join us this weekend for a new product preview.",
        "store_id": "store-101",
        "recipients": [],
    }
    payload.update(overrides)
    return payload


def create_campaign(client, **overrides):
    response = client.post("/campaigns", json=make_campaign_payload(**overrides))
    assert response.status_code == 201
    return response.get_json()


def test_scenario_healthcheck_returns_ok(client):
    # Given the API is running

    # When the operator checks the service health
    response = client.get("/health")

    # Then the API reports that it is healthy
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_scenario_create_campaign_saves_a_draft(client):
    # Given a valid campaign request from a store operator
    payload = make_campaign_payload()

    # When the operator creates the campaign
    response = client.post("/campaigns", json=payload)
    body = response.get_json()

    # Then the API stores the campaign as a draft
    assert response.status_code == 201
    assert body["name"] == payload["name"]
    assert body["subject"] == payload["subject"]
    assert body["status"] == "draft"


def test_scenario_get_campaign_returns_existing_campaign(client):
    # Given a campaign already exists
    created_campaign = create_campaign(client)

    # When the operator requests the campaign details
    response = client.get(f"/campaigns/{created_campaign['id']}")
    body = response.get_json()

    # Then the API returns the stored campaign
    assert response.status_code == 200
    assert body["id"] == created_campaign["id"]
    assert body["name"] == created_campaign["name"]
    assert body["status"] == "draft"


def test_scenario_get_campaign_returns_404_when_missing(client):
    # Given the requested campaign does not exist

    # When the operator requests that campaign
    response = client.get("/campaigns/not-a-real-id")

    # Then the API reports that the campaign was not found
    assert response.status_code == 404
    assert response.get_json() == {"error": "Campaign not found"}


def test_scenario_list_campaigns_returns_all_created_campaigns(client):
    # Given multiple campaigns already exist
    first_campaign = create_campaign(client, name="Spring Member Event")
    second_campaign = create_campaign(
        client,
        name="Summer VIP Preview",
        subject="Exclusive early access",
        body="Preview this season's new collection before the public launch.",
        store_id="store-102",
    )

    # When the operator lists campaigns
    response = client.get("/campaigns")
    body = response.get_json()

    # Then the API returns both campaigns
    assert response.status_code == 200
    assert len(body) == 2
    assert body[0]["id"] == first_campaign["id"]
    assert body[1]["id"] == second_campaign["id"]


def test_scenario_create_campaign_rejects_invalid_payload(client):
    # Given the operator submits an invalid campaign request
    invalid_payload = {
        "name": "A",
        "subject": "Hi",
        "body": "1234",
        "store_id": "s",
    }

    # When the operator creates the campaign
    response = client.post("/campaigns", json=invalid_payload)
    body = response.get_json()

    # Then the API returns validation details
    assert response.status_code == 400
    assert body["error"] == "Validation failed"
    assert len(body["details"]) == 4
    assert body["details"][0]["field"] == "name"


def test_scenario_send_campaign_records_delivery_results_and_audit_logs(client):
    # Given a campaign exists with send recipients
    created_campaign = create_campaign(
        client,
        name="Member Event",
        recipients=[
            {"email": "alex@example.com", "first_name": "Alex"},
            {"email": "jamie@invalid.test", "first_name": "Jamie"},
        ],
    )

    # When the operator sends the campaign and the async worker processes the request
    enqueue_response = client.post(f"/campaigns/{created_campaign['id']}/send")
    enqueue_body = enqueue_response.get_json()
    assert process_next_send_request() is True

    campaign_response = client.get(f"/campaigns/{created_campaign['id']}")
    attempts_response = client.get(
        f"/campaigns/{created_campaign['id']}/delivery-attempts"
    )
    audit_logs_response = client.get(f"/campaigns/{created_campaign['id']}/audit-logs")

    campaign_body = campaign_response.get_json()
    attempts_body = attempts_response.get_json()
    audit_logs_body = audit_logs_response.get_json()

    # Then the campaign reflects the async outcome and keeps an audit trail
    assert enqueue_response.status_code == 202
    assert enqueue_body["status"] == "queued"
    assert campaign_body["status"] == "partially_failed"
    assert len(attempts_body) == 2
    assert any(attempt["status"] == "sent" for attempt in attempts_body)
    assert any(attempt["status"] == "failed" for attempt in attempts_body)
    assert len(audit_logs_body) == 3
