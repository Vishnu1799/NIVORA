"""
Payment event timeline store.
Tracks every granular event in the lifecycle of a payment session.
"""
from typing import Dict, List, Optional
import threading
from models.events import PaymentTimelineEvent
from models.enums import EventType


class EventTimelineStore:
    def __init__(self):
        self._events: List[PaymentTimelineEvent] = []
        self._lock = threading.RLock()

    def record_event(
        self,
        payment_id: str,
        order_id: str,
        event_type: EventType,
        source: str,
        status: Optional[str] = None,
        transaction_id: Optional[str] = None,
        attempt_number: int = 1,
        metadata: Optional[dict] = None
    ) -> PaymentTimelineEvent:
        event = PaymentTimelineEvent(
            payment_id=payment_id,
            order_id=order_id,
            transaction_id=transaction_id,
            event_type=event_type,
            source=source,
            status=status,
            attempt_number=attempt_number,
            metadata=metadata or {}
        )
        with self._lock:
            self._events.append(event)
        return event

    def get_events_for_payment(self, payment_id: str) -> List[PaymentTimelineEvent]:
        with self._lock:
            return [e for e in self._events if e.payment_id == payment_id]

    def get_events_for_order(self, order_id: str) -> List[PaymentTimelineEvent]:
        with self._lock:
            return [e for e in self._events if e.order_id == order_id]

    def get_all_events(self) -> List[PaymentTimelineEvent]:
        with self._lock:
            return list(self._events)

    def clear(self):
        with self._lock:
            self._events.clear()


# Global in-memory timeline store
timeline_store = EventTimelineStore()
