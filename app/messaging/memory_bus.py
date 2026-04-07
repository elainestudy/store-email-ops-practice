from collections import deque
from typing import Any

_queue: deque[dict[str, Any]] = deque()


class MemoryEventBus:
    def publish_send_requested(self, payload: dict) -> None:
        _queue.append(payload)

    def pop_next_event(self) -> dict[str, Any] | None:
        if not _queue:
            return None

        return _queue.popleft()

    def reset(self) -> None:
        _queue.clear()
