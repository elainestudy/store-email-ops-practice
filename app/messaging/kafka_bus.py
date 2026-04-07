import json


class KafkaEventBus:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic

    def publish_send_requested(self, payload: dict) -> None:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        producer.send(self.topic, payload)
        producer.flush()
        producer.close()
