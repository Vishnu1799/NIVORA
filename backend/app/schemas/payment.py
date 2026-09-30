from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    payment_method: PaymentMethod = PaymentMethod.UPI
    idempotency_key: Optional[str] = None


class PaymentResponse(BaseModel):
    transaction_id: str
    status: str
    amount: float
    currency: str
    message: str
    ml_classification: Optional[str] = None
    ml_confidence: Optional[float] = None
    aurev_action: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    transaction_id: str
    status: str
    amount: float
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    money_debited: Optional[bool] = None
    attempt_count: int
    recovery_attempt_count: int
    ml_classification: Optional[str] = None
    ml_confidence: Optional[float] = None
    aurev_action: Optional[str] = None
    aurev_reasoning: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentEventResponse(BaseModel):
    event_type: str
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
