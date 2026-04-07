import json


class SQSEventBus:
    def __init__(self, queue_url: str) -> None:
        self.queue_url = queue_url

    def publish_send_requested(self, payload: dict) -> None:
        import boto3

        client = boto3.client("sqs")
        client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(payload),
        )
