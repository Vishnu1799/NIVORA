import uuid
import logging
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.payment import Payment, PaymentEvent, RecoveryAction, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderStatus
from app.aurev import tools
from app.config.settings import settings
from app.database.connection import SessionLocal

logger = logging.getLogger(__name__)


def generate_transaction_id() -> str:
    return f"TXN_{uuid.uuid4().hex[:16].upper()}"


async def log_event(db: Session, payment_id: str, event_type: str, message: str, data: dict = None):
    """Log a payment event and broadcast via WebSocket."""
    try:
        event = PaymentEvent(
            payment_id=payment_id,
            event_type=event_type,
            message=message,
            data=data or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        from app.api.websockets import broadcast_payment_event
        await broadcast_payment_event(str(payment_id), {
            "event": event_type,
            "message": message,
            "data": data or {},
            "timestamp": event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
        })
        return event
    except Exception as e:
        logger.error(f"Error logging event {event_type}: {e}")
        return None


async def initiate_payment(db: Session, order_id: str, amount: float,
                           payment_method: str, idempotency_key: str, user_id: str) -> Payment:
    """
    Main payment initiation flow.
    State machine: INITIATED → BANK_CHECK → PROCESSING/DECLINED → SUCCESS/FAILED
    """
    existing = db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
    if existing:
        logger.info(f"Idempotency key hit: {idempotency_key}")
        return existing

    transaction_id = generate_transaction_id()

    payment = Payment(
        order_id=order_id,
        transaction_id=transaction_id,
        idempotency_key=idempotency_key,
        amount=amount,
        payment_method=PaymentMethod(payment_method) if payment_method in [m.value for m in PaymentMethod] else PaymentMethod.UPI,
        status=PaymentStatus.INITIATED,
        money_debited=False,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    await log_event(db, payment.id, "payment_started", f"Payment initiated: ₹{amount}", {"transaction_id": transaction_id})

    # Step 1: Bank health check
    payment.status = PaymentStatus.BANK_CHECK
    db.commit()

    import time
    start = time.time()
    bank_health = await tools.check_bank_health()
    latency = int((time.time() - start) * 1000)
    bank_status = bank_health.get("status", "UNKNOWN")

    await log_event(db, payment.id, "bank_health_checked", f"Bank status: {bank_status}", {"status": bank_status, "latency_ms": latency})

    # Step 2: If bank is DOWN, decline immediately
    if bank_status == "DOWN":
        payment.status = PaymentStatus.DECLINED
        payment.failure_code = "BANK_UNAVAILABLE"
        payment.failure_reason = "Bank service is currently unavailable"
        payment.money_debited = False
        db.commit()
        await log_event(db, payment.id, "payment_declined", "Bank unavailable — payment not attempted", {"bank_status": bank_status})
        return payment

    # Step 3: Submit payment to bank
    payment.status = PaymentStatus.PROCESSING
    payment.attempt_count += 1
    db.commit()

    await log_event(db, payment.id, "payment_submitted", "Submitting payment to bank", {})

    result = await tools.submit_payment_to_bank(
        transaction_id=transaction_id,
        amount=amount,
        payment_method=payment.payment_method.value,
        idempotency_key=idempotency_key,
    )

    bank_result_status = result.get("status")
    payment.bank_transaction_id = result.get("bank_transaction_id")
    payment.money_debited = result.get("money_debited", False)

    await log_event(
        db, payment.id, "bank_response_received",
        f"Bank response: {bank_result_status}",
        {"status": bank_result_status, "money_debited": payment.money_debited},
    )

    if bank_result_status == "SUCCESS":
        payment.status = PaymentStatus.SUCCESS
        payment.merchant_credited = True
        db.commit()
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus.CONFIRMED
            db.commit()
        await log_event(db, payment.id, "payment_succeeded", "Payment completed successfully", {})

    elif bank_result_status in ["FAILED", "TIMEOUT", "UNKNOWN", "PROCESSING"]:
        payment.status = PaymentStatus.FAILED
        payment.failure_code = result.get("error_code", "UNKNOWN")
        payment.failure_reason = result.get("error_message", "Payment failed")
        db.commit()
        await log_event(
            db, payment.id, "payment_failed",
            f"Payment failed: {payment.failure_code}",
            {"error_code": payment.failure_code, "bank_status": bank_result_status},
        )
        await log_event(db, payment.id, "aurev_triggered", "AUREV AI recovery initiated", {})
        asyncio.create_task(run_recovery_task(payment.id))

    else:
        payment.status = PaymentStatus.UNKNOWN
        payment.failure_code = "UNKNOWN"
        db.commit()
        await log_event(db, payment.id, "payment_unknown", "Unknown payment state", {})
        asyncio.create_task(run_recovery_task(payment.id))

    return payment


async def run_recovery_task(payment_id: str):
    """Background task with its own database session."""
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            await trigger_recovery(db, payment)
    except Exception as e:
        logger.error(f"Error in background recovery task: {e}")
    finally:
        db.close()


async def trigger_recovery(db: Session, payment: Payment):
    """Trigger AUREV AI recovery workflow."""
    try:
        from app.aurev.agent import aurev_agent

        async def event_logger(p_id, event_type, message, data):
            await log_event(db, str(p_id), event_type, message, data)

        decision = await aurev_agent.diagnose_and_recover(payment, db, event_logger)
        action = decision["action"]

        payment.recovery_attempt_count += 1
        db.commit()

        recovery = RecoveryAction(
            payment_id=payment.id,
            action_type=action,
            reason=decision.get("reasoning", ""),
            attempt_number=payment.recovery_attempt_count,
        )
        db.add(recovery)
        db.commit()

        if action == "RETRY":
            await execute_retry(db, payment)
        elif action == "RECONCILE":
            await execute_reconcile(db, payment)
        elif action == "DECLINE":
            payment.status = PaymentStatus.DECLINED
            db.commit()
            await log_event(db, payment.id, "payment_declined", "Payment declined by safety policy", {})
        elif action in ["ESCALATE", "WAIT_AND_VERIFY"]:
            payment.status = PaymentStatus.ESCALATED
            db.commit()
            await log_event(db, payment.id, "payment_escalated", "Payment escalated for manual review", {})

        recovery.result = payment.status.value
        db.commit()

    except Exception as e:
        logger.error(f"Recovery failed for {payment.transaction_id}: {e}")
        payment.status = PaymentStatus.ESCALATED
        db.commit()


async def execute_retry(db: Session, payment: Payment):
    """Execute a safe retry through payment orchestrator."""
    await log_event(db, payment.id, "retry_requested", "Safe retry authorized — retrying payment", {})

    result = await tools.submit_payment_to_bank(
        transaction_id=payment.transaction_id,
        amount=payment.amount,
        payment_method=payment.payment_method.value,
        idempotency_key=f"{payment.idempotency_key}_retry_{payment.recovery_attempt_count}",
    )

    payment.attempt_count += 1
    bank_status = result.get("status")
    payment.money_debited = result.get("money_debited", payment.money_debited)

    if bank_status == "SUCCESS":
        payment.status = PaymentStatus.SUCCESS
        payment.merchant_credited = True
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = OrderStatus.CONFIRMED
        db.commit()
        await log_event(db, payment.id, "payment_recovered", "Payment recovered successfully via retry", {})
    else:
        payment.status = PaymentStatus.FAILED
        payment.failure_code = result.get("error_code", payment.failure_code)
        db.commit()
        await log_event(db, payment.id, "retry_failed", f"Retry failed: {bank_status}", {"bank_status": bank_status})
        if payment.recovery_attempt_count < settings.max_recovery_attempts:
            await trigger_recovery(db, payment)
        else:
            payment.status = PaymentStatus.ESCALATED
            db.commit()
            await log_event(db, payment.id, "payment_escalated", "Max recovery attempts reached. Escalated.", {})


async def execute_reconcile(db: Session, payment: Payment):
    """Reconcile payment — money debited but status unclear."""
    await log_event(db, payment.id, "reconcile_started", "Reconciling payment — verifying customer bank debit", {})
    payment.status = PaymentStatus.RECONCILING
    db.commit()

    verification = await tools.verify_transaction(payment.transaction_id)
    money_debited = verification.get("money_debited")
    merchant_credited = verification.get("merchant_credited")

    # If money was debited from customer account, AUREV credits merchant & confirms order instantly
    if money_debited is True or merchant_credited is True:
        payment.status = PaymentStatus.SUCCESS
        payment.money_debited = True
        payment.merchant_credited = True
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = OrderStatus.CONFIRMED
        db.commit()
        await log_event(db, payment.id, "payment_reconciled", "Reconciliation: customer debit confirmed. Merchant credited & Order confirmed.", {
            "money_debited": True,
            "merchant_credited": True,
            "bank_transaction_id": verification.get("bank_transaction_id"),
        })
    else:
        payment.status = PaymentStatus.ESCALATED
        db.commit()
        await log_event(db, payment.id, "payment_escalated", "Reconciliation inconclusive. Escalated for manual review.", {})
