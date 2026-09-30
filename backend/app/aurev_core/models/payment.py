"""
Payment data structures, attempt records, and session models.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from models.enums import (
    BankStatus,
    FinalityState,
    GatewayStatus,
    MerchantStatus,
    PaymentStatus,
    ReconciliationState,
    AurevDecision,
)
from models.decisions import RecoveryPermit


class PaymentAttempt(BaseModel):
    attempt_number: int = 1
    payment_id: str
    transaction_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_method: str = "UPI"
    gateway: str = "RAZORPAY"
    gateway_status: str = "UNKNOWN"
    bank_status: BankStatus = BankStatus.UNKNOWN
    merchant_status: MerchantStatus = MerchantStatus.UNKNOWN
    customer_debited: Optional[bool] = None
    merchant_credited: Optional[bool] = None
    webhook_received: bool = False
    webhook_delay_ms: float = 0.0
    gateway_latency_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_terminal: bool = False


class PaymentSession(BaseModel):
    order_id: str
    user_id: str = "CUST-DEFAULT"
    device_id: Optional[str] = "DEV-001"
    session_id: Optional[str] = "SESS-001"
    amount: float
    currency: str = "INR"
    current_payment_id: str
    attempts: List[PaymentAttempt] = Field(default_factory=list)
    finality_state: FinalityState = FinalityState.UNKNOWN
    current_decision: AurevDecision = AurevDecision.WAIT
    is_pay_again_blocked: bool = False
    reconciliation_state: ReconciliationState = ReconciliationState.NOT_NEEDED
    active_recovery_permit: Optional[RecoveryPermit] = None
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_attempt(self, payment_id: str) -> Optional[PaymentAttempt]:
        for att in self.attempts:
            if att.payment_id == payment_id:
                return att
        return None

    def get_latest_attempt(self) -> Optional[PaymentAttempt]:
        if not self.attempts:
            return None
        return self.attempts[-1]

    def has_successful_attempt(self) -> bool:
        for att in self.attempts:
            if att.gateway_status == "SUCCESS" or (att.customer_debited and att.merchant_credited):
                return True
        return False

    def has_debited_attempt(self) -> bool:
        for att in self.attempts:
            if att.customer_debited is True or att.bank_status == BankStatus.DEBITED:
                return True
        return False
