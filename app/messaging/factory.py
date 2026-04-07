from app.core.config import Settings
from app.messaging.kafka_bus import KafkaEventBus
from app.messaging.memory_bus import MemoryEventBus
from app.messaging.sqs_bus import SQSEventBus

settings = Settings()
_memory_bus = MemoryEventBus()


def get_event_bus():
    if settings.message_bus_backend == "sqs":
        return SQSEventBus(queue_url=settings.sqs_queue_url)

    if settings.message_bus_backend == "kafka":
        return KafkaEventBus(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            topic=settings.kafka_topic,
        )

    return _memory_bus
