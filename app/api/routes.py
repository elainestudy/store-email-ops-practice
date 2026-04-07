from http import HTTPStatus

from flask import Blueprint, jsonify, request

from app.core.config import Settings
from app.schemas.campaigns import CampaignCreateRequest, CampaignDeliveryResultsRequest
from app.services.campaign_service import CampaignService

api_bp = Blueprint("api", __name__)
campaign_service = CampaignService()
settings = Settings()


@api_bp.get("/health")
def healthcheck():
    return jsonify({"status": "ok"}), HTTPStatus.OK


@api_bp.get("/campaigns")
def list_campaigns():
    campaigns = campaign_service.list_campaigns()
    return jsonify([campaign.model_dump() for campaign in campaigns]), HTTPStatus.OK


@api_bp.post("/campaigns")
def create_campaign():
    payload = request.get_json(silent=True) or {}
    validated = CampaignCreateRequest.model_validate(payload)
    campaign = campaign_service.create_campaign(validated)
    return jsonify(campaign.model_dump()), HTTPStatus.CREATED


@api_bp.get("/campaigns/<campaign_id>")
def get_campaign(campaign_id):
    campaign = campaign_service.get_campaign(campaign_id)
    if campaign:
        return jsonify(campaign.model_dump()), HTTPStatus.OK
    else:
        return jsonify({"error": "Campaign not found"}), HTTPStatus.NOT_FOUND


@api_bp.post("/campaigns/<campaign_id>/send")
def send_campaign(campaign_id):
    campaign = campaign_service.enqueue_campaign_send(campaign_id)
    if campaign is None:
        return jsonify({"error": "Campaign not found"}), HTTPStatus.NOT_FOUND

    return (
        jsonify(
            {
                "campaign_id": str(campaign.id),
                "status": campaign.status,
                "message": "Campaign queued for asynchronous sending",
            }
        ),
        HTTPStatus.ACCEPTED,
    )


@api_bp.get("/campaigns/<campaign_id>/delivery-attempts")
def list_delivery_attempts(campaign_id):
    attempts = campaign_service.list_delivery_attempts(campaign_id)
    return jsonify([attempt.model_dump() for attempt in attempts]), HTTPStatus.OK


@api_bp.get("/campaigns/<campaign_id>/recipients")
def list_recipients(campaign_id):
    recipients = campaign_service.list_recipients(campaign_id)
    return jsonify([recipient.model_dump() for recipient in recipients]), HTTPStatus.OK


@api_bp.get("/campaigns/<campaign_id>/audit-logs")
def list_audit_logs(campaign_id):
    audit_logs = campaign_service.list_audit_logs(campaign_id)
    return jsonify([audit_log.model_dump() for audit_log in audit_logs]), HTTPStatus.OK


@api_bp.post("/internal/campaigns/<campaign_id>/delivery-results")
def record_delivery_results(campaign_id):
    token = request.headers.get("X-Internal-Token", "")
    if token != settings.internal_api_token:
        return jsonify({"error": "Unauthorized"}), HTTPStatus.UNAUTHORIZED

    payload = request.get_json(silent=True) or {}
    validated = CampaignDeliveryResultsRequest.model_validate(payload)
    campaign = campaign_service.record_delivery_results(campaign_id, validated.results)
    if campaign is None:
        return jsonify({"error": "Campaign not found"}), HTTPStatus.NOT_FOUND

    return jsonify(campaign.model_dump()), HTTPStatus.OK
