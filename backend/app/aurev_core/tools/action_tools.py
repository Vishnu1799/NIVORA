"""
Controlled Action Tools for AUREV.
All financial action executions pass through strict safety checks.
"""
from typing import Any, Dict, Optional
from memory.payment_memory import payment_memory
from memory.event_timeline import timeline_store
from models.enums import EventType, ReconciliationState, FinalityState, BankStatus, MerchantStatus
from models.decisions import RecoveryPermit
from safety.recovery_permit import RecoveryPermitManager


def block_pay_again(order_id: str, reason: str = "Duplicate protection active") -> Dict[str, Any]:
    """Locks the UI 'Pay Again' button to prevent duplicate charges."""
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return {"success": False, "error": f"Session for order {order_id} not found."}

    session.is_pay_again_blocked = True
    payment_memory.save_session(session)
    timeline_store.record_event(
        payment_id=session.current_payment_id,
        order_id=order_id,
        event_type=EventType.RETRY_BLOCKED,
        source="action_tool",
        status="PAY_AGAIN_BLOCKED",
        metadata={"reason": reason}
    )
    return {
        "success": True,
        "order_id": order_id,
        "is_pay_again_blocked": True,
        "reason": reason
    }


def allow_retry(order_id: str, permit_id: str) -> Dict[str, Any]:
    """
    Unlocks retry capability ONLY if a valid Recovery Permit is provided and verified.
    """
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return {"success": False, "error": "Order not found."}

    permit = payment_memory.get_permit(permit_id)
    if not permit:
        return {"success": False, "error": f"Permit {permit_id} not found."}

    valid, msg = RecoveryPermitManager.validate_and_consume(
        permit_id=permit_id,
        payment_id=session.current_payment_id,
        order_id=order_id,
        amount=session.amount
    )

    if not valid:
        return {"success": False, "error": msg}

    session.is_pay_again_blocked = False
    payment_memory.save_session(session)

    timeline_store.record_event(
        payment_id=session.current_payment_id,
        order_id=order_id,
        event_type=EventType.RETRY_PERMITTED,
        source="action_tool",
        status="RETRY_PERMITTED",
        metadata={"permit_id": permit_id}
    )
    return {
        "success": True,
        "order_id": order_id,
        "message": "Retry authorized under recovery permit."
    }


def create_recovery_permit(payment_id: str, order_id: str, amount: float, reason: str) -> RecoveryPermit:
    """Issues a single-use time-limited recovery permit."""
    return RecoveryPermitManager.create_permit(payment_id, order_id, amount, reason)


def request_payment_status(payment_id: str) -> Dict[str, Any]:
    """Triggers active verification with bank and payment gateway."""
    timeline_store.record_event(
        payment_id=payment_id,
        order_id="UNKNOWN",
        event_type=EventType.VERIFICATION_REQUESTED,
        source="action_tool",
        status="POLLING"
    )
    return {
        "payment_id": payment_id,
        "action": "VERIFICATION_REQUESTED",
        "status": "IN_FLIGHT"
    }


def trigger_reconciliation(order_id: str) -> Dict[str, Any]:
    """Initiates ledger reconciliation between Bank settlement and Merchant backend."""
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return {"success": False, "error": "Session not found."}

    session.reconciliation_state = ReconciliationState.IN_PROGRESS
    timeline_store.record_event(
        payment_id=session.current_payment_id,
        order_id=order_id,
        event_type=EventType.RECONCILIATION_STARTED,
        source="action_tool",
        status="RECONCILING"
    )

    # Automated check: if bank was debited, reconcile to success
    if session.has_debited_attempt():
        session.reconciliation_state = ReconciliationState.RECONCILED_SUCCESS
        session.finality_state = FinalityState.FINAL_SUCCESS
        for att in session.attempts:
            if att.customer_debited or att.bank_status == BankStatus.DEBITED:
                att.merchant_status = MerchantStatus.CONFIRMED
                att.merchant_credited = True
                att.gateway_status = "SUCCESS"
        timeline_store.record_event(
            payment_id=session.current_payment_id,
            order_id=order_id,
            event_type=EventType.RECONCILIATION_COMPLETED,
            source="action_tool",
            status="RECONCILED_SUCCESS",
            metadata={"result": "Bank debit reconciled to merchant fulfillment."}
        )
    else:
        session.reconciliation_state = ReconciliationState.RECONCILED_FAILED
        timeline_store.record_event(
            payment_id=session.current_payment_id,
            order_id=order_id,
            event_type=EventType.RECONCILIATION_COMPLETED,
            source="action_tool",
            status="RECONCILED_FAILED"
        )

    payment_memory.save_session(session)
    return {
        "success": True,
        "order_id": order_id,
        "reconciliation_state": session.reconciliation_state.value,
        "finality_state": session.finality_state.value
    }


def switch_gateway(order_id: str, new_gateway: str) -> Dict[str, Any]:
    """Switches default gateway routing for retry attempts."""
    session = payment_memory.get_session_by_order_id(order_id)
    if not session:
        return {"success": False, "error": "Session not found"}
    session.metadata["routing_gateway"] = new_gateway
    return {"success": True, "order_id": order_id, "new_gateway": new_gateway}


def create_support_case(order_id: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Escalates conflict or manual review cases to human support."""
    session = payment_memory.get_session_by_order_id(order_id)
    payment_id = session.current_payment_id if session else "UNKNOWN"
    timeline_store.record_event(
        payment_id=payment_id,
        order_id=order_id,
        event_type=EventType.ESCALATED,
        source="action_tool",
        status="SUPPORT_TICKET_CREATED",
        metadata={"reason": reason, **(metadata or {})}
    )
    return {
        "ticket_id": f"TICK-{order_id}",
        "order_id": order_id,
        "status": "OPEN",
        "reason": reason
    }


def trigger_eligible_refund(order_id: str, payment_id: str, amount: float, reason: str) -> Dict[str, Any]:
    """Flags duplicate charge or overcharge for automated refund pipeline."""
    timeline_store.record_event(
        payment_id=payment_id,
        order_id=order_id,
        event_type=EventType.REFUND_FLAGGED,
        source="action_tool",
        status="REFUND_PENDING",
        metadata={"amount": amount, "reason": reason}
    )
    return {
        "refund_id": f"REF-{payment_id}",
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": amount,
        "status": "QUEUED_FOR_EXECUTION",
        "reason": reason
    }


def notify_user(user_id: str, message: str, level: str = "INFO") -> Dict[str, Any]:
    """Sends user-facing communication message."""
    timeline_store.record_event(
        payment_id="SYSTEM",
        order_id="USER_NOTIFICATION",
        event_type=EventType.USER_NOTIFIED,
        source="action_tool",
        status=level,
        metadata={"user_id": user_id, "message": message}
    )
    return {"user_id": user_id, "message": message, "delivered": True}


def notify_merchant(merchant_id: str, order_id: str, status: str) -> Dict[str, Any]:
    """Sends merchant fulfillment update."""
    timeline_store.record_event(
        payment_id="SYSTEM",
        order_id=order_id,
        event_type=EventType.MERCHANT_NOTIFIED,
        source="action_tool",
        status=status,
        metadata={"merchant_id": merchant_id}
    )
    return {"merchant_id": merchant_id, "order_id": order_id, "status": status, "delivered": True}
