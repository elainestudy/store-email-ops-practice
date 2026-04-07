# Lambda Email Sender

This Lambda function consumes queued campaign send jobs, sends emails through Amazon SES, and posts delivery results back to the Flask API internal endpoint.

Expected SQS message body:

```json
{
  "event_type": "campaign_send_requested",
  "campaign_id": "uuid",
  "subject": "Campaign subject",
  "body": "Campaign email body",
  "recipients": [
    {
      "recipient_id": "uuid",
      "email": "alex@example.com",
      "first_name": "Alex"
    }
  ]
}
```
