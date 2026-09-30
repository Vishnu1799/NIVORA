"""
Payment memory repository for AUREV.
Maintains payment sessions, attempts, recovery permits, and audit logs.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading
from models.payment import PaymentAttempt, PaymentSession
from models.enums import (
    BankStatus,
    FinalityState,
    MerchantStatus,
    PaymentStatus,
    ReconciliationState,
    AurevDecision,
)
from models.decisions import AurevAuditRecord, RecoveryPermit


class PaymentMemoryRepository:
    def __init__(self):
        self._sessions: Dict[str, PaymentSession] = {}  # keyed by order_id
        self._payment_to_order: Dict[str, str] = {}  # payment_id -> order_id
        self._permits: Dict[str, RecoveryPermit] = {}  # permit_id -> RecoveryPermit
        self._audit_records: List[AurevAuditRecord] = []
        self._lock = threading.RLock()
        self._init_default_test_data()

    def _init_default_test_data(self):
        """Pre-populate classic test payments: PAY001, PAY002, PAY003, PAY004."""
        # PAY001 = UNKNOWN (e.g. Gateway Timeout)
        self.create_session(
            order_id="ORD-001",
            payment_id="PAY001",
            amount=2000.0,
            gateway_status="UNKNOWN",
            bank_status=BankStatus.UNKNOWN,
            merchant_status=MerchantStatus.UNKNOWN,
            customer_debited=None,
            merchant_credited=None,
            finality_state=FinalityState.UNKNOWN,
            decision=AurevDecision.WAIT
        )

        # PAY002 = SUCCESS
        self.create_session(
            order_id="ORD-002",
            payment_id="PAY002",
            amount=550.0,
            gateway_status="SUCCESS",
            bank_status=BankStatus.DEBITED,
            merchant_status=MerchantStatus.CONFIRMED,
            customer_debited=True,
            merchant_credited=True,
            finality_state=FinalityState.FINAL_SUCCESS,
            decision=AurevDecision.STOP
        )

        # PAY003 = FAILED
        self.create_session(
            order_id="ORD-003",
            payment_id="PAY003",
            amount=1200.0,
            gateway_status="FAILED",
            bank_status=BankStatus.NOT_DEBITED,
            merchant_status=MerchantStatus.FAILED,
            customer_debited=False,
            merchant_credited=False,
            finality_state=FinalityState.FINAL_FAILURE,
            decision=AurevDecision.RETRY
        )

        # PAY004 = PROCESSING
        self.create_session(
            order_id="ORD-004",
            payment_id="PAY004",
            amount=340.0,
            gateway_status="PROCESSING",
            bank_status=BankStatus.PENDING,
            merchant_status=MerchantStatus.PENDING,
            customer_debited=None,
            merchant_credited=None,
            finality_state=FinalityState.NON_FINAL,
            decision=AurevDecision.WAIT
        )

    def create_session(
        self,
        order_id: str,
        payment_id: str,
        amount: float,
        currency: str = "INR",
        user_id: str = "CUST-001",
        device_id: str = "DEV-001",
        session_id: str = "SESS-001",
        gateway_status: str = "UNKNOWN",
        bank_status: BankStatus = BankStatus.UNKNOWN,
        merchant_status: MerchantStatus = MerchantStatus.UNKNOWN,
        customer_debited: Optional[bool] = None,
        merchant_credited: Optional[bool] = None,
        webhook_received: bool = False,
        finality_state: FinalityState = FinalityState.UNKNOWN,
        decision: AurevDecision = AurevDecision.WAIT,
        is_pay_again_blocked: bool = False,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> PaymentSession:
        with self._lock:
            attempt = PaymentAttempt(
                attempt_number=1,
                payment_id=payment_id,
                transaction_id=f"TXN-{payment_id}",
                amount=amount,
                currency=currency,
                gateway="RAZORPAY",
                gateway_status=gateway_status,
                bank_status=bank_status,
                merchant_status=merchant_status,
                customer_debited=customer_debited,
                merchant_credited=merchant_credited,
                webhook_received=webhook_received,
                error_code=error_code,
                error_message=error_message
            )
            session = PaymentSession(
                order_id=order_id,
                user_id=user_id,
                device_id=device_id,
                session_id=session_id,
                amount=amount,
                currency=currency,
                current_payment_id=payment_id,
                attempts=[attempt],
                finality_state=finality_state,
                current_decision=decision,
                is_pay_again_blocked=is_pay_again_blocked
            )
            self._sessions[order_id] = session
            self._payment_to_order[payment_id] = order_id
            return session

    def get_session_by_order_id(self, order_id: str) -> Optional[PaymentSession]:
        with self._lock:
            return self._sessions.get(order_id)

    def get_session_by_payment_id(self, payment_id: str) -> Optional[PaymentSession]:
        with self._lock:
            order_id = self._payment_to_order.get(payment_id)
            if not order_id:
                # Check directly in sessions
                for s in self._sessions.values():
                    if s.get_attempt(payment_id):
                        return s
                return None
            return self._sessions.get(order_id)

    def get_attempt(self, payment_id: str) -> Optional[PaymentAttempt]:
        with self._lock:
            session = self.get_session_by_payment_id(payment_id)
            if session:
                return session.get_attempt(payment_id)
            return None

    def add_attempt_to_session(
        self,
        order_id: str,
        payment_id: str,
        amount: float,
        gateway: str = "RAZORPAY",
        payment_method: str = "UPI"
    ) -> Optional[PaymentAttempt]:
        with self._lock:
            session = self._sessions.get(order_id)
            if not session:
                return None
            attempt_num = len(session.attempts) + 1
            attempt = PaymentAttempt(
                attempt_number=attempt_num,
                payment_id=payment_id,
                transaction_id=f"TXN-{payment_id}",
                amount=amount,
                currency=session.currency,
                payment_method=payment_method,
                gateway=gateway,
                gateway_status="INITIATED",
                bank_status=BankStatus.UNKNOWN,
                merchant_status=MerchantStatus.UNKNOWN,
                customer_debited=None,
                merchant_credited=None,
                webhook_received=False
            )
            session.attempts.append(attempt)
            session.current_payment_id = payment_id
            session.updated_at = datetime.now(timezone.utc)
            self._payment_to_order[payment_id] = order_id
            return attempt

    def save_session(self, session: PaymentSession):
        with self._lock:
            session.updated_at = datetime.now(timezone.utc)
            self._sessions[session.order_id] = session
            for att in session.attempts:
                self._payment_to_order[att.payment_id] = session.order_id

    def store_permit(self, permit: RecoveryPermit):
        with self._lock:
            self._permits[permit.permit_id] = permit

    def get_permit(self, permit_id: str) -> Optional[RecoveryPermit]:
        with self._lock:
            return self._permits.get(permit_id)

    def record_audit(self, audit: AurevAuditRecord):
        with self._lock:
            self._audit_records.append(audit)

    def get_audit_records(self, payment_id: Optional[str] = None) -> List[AurevAuditRecord]:
        with self._lock:
            if payment_id:
                return [a for a in self._audit_records if a.payment_id == payment_id]
            return list(self._audit_records)

    def reset_to_defaults(self):
        with self._lock:
            self._sessions.clear()
            self._payment_to_order.clear()
            self._permits.clear()
            self._audit_records.clear()
            self._init_default_test_data()


# Global in-memory memory repository
payment_memory = PaymentMemoryRepository()
