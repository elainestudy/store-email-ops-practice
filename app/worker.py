from app.messaging.factory import get_event_bus
from app.services.campaign_service import CampaignService


def process_next_send_request() -> bool:
    event_bus = get_event_bus()
    event = getattr(event_bus, "pop_next_event", lambda: None)()
    if event is None:
        return False

    if event.get("event_type") != "campaign_send_requested":
        return False

    CampaignService().process_delivery_job(event)
    return True
