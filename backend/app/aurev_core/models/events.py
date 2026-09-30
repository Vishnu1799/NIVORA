"""
Event models for payment timeline tracking and auditing.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from models.enums import EventType, PaymentStatus


class PaymentTimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_id: str
    order_id: str
    transaction_id: Optional[str] = None
    event_type: EventType
    source: str = Field(description="Source of event, e.g., 'gateway', 'bank', 'webhook', 'aurev_policy', 'reconciliation'")
    status: Optional[str] = None
    attempt_number: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
