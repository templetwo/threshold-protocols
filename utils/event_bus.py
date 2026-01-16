"""
Event Bus - Inter-layer Communication

Simple pub/sub event bus for communication between layers.
Detection publishes, Simulation and Deliberation subscribe.

Design Philosophy:
- Simple over complex: Python stdlib only
- Synchronous by default: Async adds complexity we don't need yet
- Logged: All events are recorded for audit

Alternatives Considered:
- Redis pub/sub: External dependency, overkill for single-process
- asyncio queues: Adds async complexity throughout
- Direct function calls: Tight coupling between layers
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("event_bus")


@dataclass
class Event:
    """A single event on the bus."""
    topic: str
    payload: Any
    source: str
    timestamp: str = ""
    event_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.event_id:
            self.event_id = self._generate_id()

    def _generate_id(self) -> str:
        content = f"{self.topic}:{self.source}:{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "payload": self.payload if isinstance(self.payload, dict) else str(self.payload),
            "source": self.source,
            "timestamp": self.timestamp,
            "event_id": self.event_id
        }


class EventBus:
    """
    Simple synchronous event bus for inter-layer communication.

    Usage:
        bus = EventBus()

        # Subscribe
        def on_threshold(event):
            print(f"Threshold: {event.payload}")

        bus.subscribe("threshold.crossed", on_threshold)

        # Publish
        bus.publish("threshold.crossed", {"metric": "file_count", "value": 100})
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._event_log: List[Event] = []
        self._wildcards: List[Callable[[Event], None]] = []

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to events on a topic.

        Args:
            topic: Topic pattern (e.g., "threshold.crossed", "simulation.*")
            callback: Function to call when event is published
        """
        if topic == "*":
            self._wildcards.append(callback)
        else:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)

        logger.debug(f"Subscribed to: {topic}")

    def unsubscribe(
        self,
        topic: str,
        callback: Callable[[Event], None]
    ) -> bool:
        """
        Unsubscribe from a topic.

        Returns:
            True if callback was found and removed
        """
        if topic == "*":
            if callback in self._wildcards:
                self._wildcards.remove(callback)
                return True
            return False

        if topic in self._subscribers:
            if callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
                return True
        return False

    def publish(
        self,
        topic: str,
        payload: Any,
        source: str = "unknown"
    ) -> Event:
        """
        Publish an event to the bus.

        Args:
            topic: Event topic
            payload: Event data
            source: Identifier for the publisher

        Returns:
            The published Event object
        """
        event = Event(topic=topic, payload=payload, source=source)
        self._event_log.append(event)

        # Notify exact subscribers
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Subscriber error for {topic}: {e}")

        # Notify wildcard subscribers
        for callback in self._wildcards:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Wildcard subscriber error: {e}")

        # Notify prefix subscribers (e.g., "threshold.*" matches "threshold.crossed")
        prefix = topic.rsplit(".", 1)[0] + ".*" if "." in topic else None
        if prefix and prefix in self._subscribers:
            for callback in self._subscribers[prefix]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Prefix subscriber error for {prefix}: {e}")

        logger.debug(f"Published: {topic} from {source}")
        return event

    def get_event_log(self) -> List[Event]:
        """Return all published events."""
        return self._event_log.copy()

    def export_log(self, output_path: str) -> None:
        """Export event log to JSON file."""
        events = [e.to_dict() for e in self._event_log]
        with open(output_path, "w") as f:
            json.dump(events, f, indent=2)

    def clear(self) -> None:
        """Clear all subscribers and event log."""
        self._subscribers.clear()
        self._wildcards.clear()
        self._event_log.clear()


# Global bus instance (optional pattern)
_global_bus: Optional[EventBus] = None


def get_bus() -> EventBus:
    """Get or create the global event bus."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus
