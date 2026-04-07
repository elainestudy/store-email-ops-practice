import pytest
from pytest_bdd import given, parsers, scenario, then, when

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
def clear_state():
    reset_db()
    reset_event_bus()
    yield
    reset_db()
    reset_event_bus()


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


@scenario(
    "features/campaign_sending.feature",
    "Creating a campaign stores it as a draft",
)
def test_create_campaign_bdd():
    pass


@scenario(
    "features/campaign_sending.feature",
    "Sending a campaign records delivery attempts and audit logs",
)
def test_send_campaign_bdd():
    pass


@given("a valid campaign creation request", target_fixture="campaign_request")
def valid_campaign_creation_request():
    return {
        "name": "Spring Member Event",
        "subject": "New arrivals for members",
        "body": "Join us this weekend for a new product preview.",
        "store_id": "store-101",
        "recipients": [],
    }


@when("the operator creates the campaign", target_fixture="create_campaign_result")
def create_campaign(client, campaign_request):
    response = client.post("/campaigns", json=campaign_request)

    return {
        "response": response,
        "body": response.get_json(),
    }


@given(
    "an existing campaign with valid and invalid recipients",
    target_fixture="campaign_context",
)
def existing_campaign_with_recipients(client):
    response = client.post(
        "/campaigns",
        json={
            "name": "Member Event",
            "subject": "New arrivals for members",
            "body": "Join us this weekend for a new product preview.",
            "store_id": "store-101",
            "recipients": [
                {"email": "alex@example.com", "first_name": "Alex"},
                {"email": "jamie@invalid.test", "first_name": "Jamie"},
            ],
        },
    )

    assert response.status_code == 201
    created_campaign = response.get_json()
    return {"campaign_id": created_campaign["id"]}


@when("the operator sends the campaign", target_fixture="campaign_context")
def send_campaign(client, campaign_context):
    campaign_id = campaign_context["campaign_id"]
    enqueue_response = client.post(f"/campaigns/{campaign_id}/send")

    assert enqueue_response.status_code == 202
    campaign_context["enqueue_response"] = enqueue_response.get_json()
    return campaign_context


@when(
    "the async worker processes the queued send request",
    target_fixture="campaign_context",
)
def process_queued_send_request(client, campaign_context):
    campaign_id = campaign_context["campaign_id"]

    assert process_next_send_request() is True

    campaign_context["campaign"] = client.get(f"/campaigns/{campaign_id}").get_json()
    campaign_context["delivery_attempts"] = client.get(
        f"/campaigns/{campaign_id}/delivery-attempts"
    ).get_json()
    campaign_context["audit_logs"] = client.get(
        f"/campaigns/{campaign_id}/audit-logs"
    ).get_json()
    return campaign_context


@then(parsers.parse("the response status code is {expected_status_code:d}"))
def check_response_status_code(create_campaign_result, expected_status_code):
    assert create_campaign_result["response"].status_code == expected_status_code


@then(parsers.parse('the created campaign status is "{expected_status}"'))
def check_created_campaign_status(create_campaign_result, expected_status):
    assert create_campaign_result["body"]["status"] == expected_status


@then(parsers.parse('the created campaign name is "{expected_name}"'))
def check_created_campaign_name(create_campaign_result, expected_name):
    assert create_campaign_result["body"]["name"] == expected_name


@then(parsers.parse('the campaign status becomes "{expected_status}"'))
def check_campaign_status(campaign_context, expected_status):
    assert campaign_context["campaign"]["status"] == expected_status


@then(parsers.parse("{expected_count:d} delivery attempts are recorded"))
def check_delivery_attempt_count(campaign_context, expected_count):
    assert len(campaign_context["delivery_attempts"]) == expected_count


@then(parsers.parse("the audit log contains {expected_count:d} entries"))
def check_audit_log_count(campaign_context, expected_count):
    assert len(campaign_context["audit_logs"]) == expected_count


@then(parsers.parse('at least {minimum_count:d} delivery attempt has status "{status}"'))
def check_delivery_attempt_status(campaign_context, minimum_count, status):
    matching_attempts = [
        attempt
        for attempt in campaign_context["delivery_attempts"]
        if attempt["status"] == status
    ]
    assert len(matching_attempts) >= minimum_count
