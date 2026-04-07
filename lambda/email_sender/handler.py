import json
import os
import urllib.request

import boto3

ses = boto3.client("sesv2")


def send_email(recipient_email: str, subject: str, body: str) -> dict:
    if recipient_email.endswith("@invalid.test"):
        return {
            "status": "failed",
            "provider_message": "provider_rejected_address",
        }

    response = ses.send_email(
        FromEmailAddress=os.environ["SES_FROM_EMAIL"],
        Destination={"ToAddresses": [recipient_email]},
        Content={
            "Simple": {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            }
        },
    )
    return {
        "status": "sent",
        "provider_message": response["MessageId"],
    }


def post_delivery_results(campaign_id: str, results: list[dict]) -> None:
    backend_base_url = os.environ.get("BACKEND_BASE_URL", "").rstrip("/")
    internal_api_token = os.environ.get("INTERNAL_API_TOKEN", "")
    if not backend_base_url or not internal_api_token:
        return

    payload = json.dumps({"results": results}).encode("utf-8")
    request = urllib.request.Request(
        url=f"{backend_base_url}/internal/campaigns/{campaign_id}/delivery-results",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Internal-Token": internal_api_token,
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15):
        pass


def handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        campaign_id = body["campaign_id"]
        subject = body["subject"]
        email_body = body["body"]
        recipients = body.get("recipients", [])

        results = []
        for recipient in recipients:
            send_result = send_email(
                recipient_email=recipient["email"],
                subject=subject,
                body=email_body,
            )
            results.append(
                {
                    "recipient_id": recipient["recipient_id"],
                    "status": send_result["status"],
                    "provider_message": send_result["provider_message"],
                }
            )

        post_delivery_results(campaign_id, results)

    return {"statusCode": 200, "body": "ok"}
