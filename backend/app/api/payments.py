from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.core.security import get_current_user
from app.models.user import User
from app.services.payment_service import initiate_payment, inject_payment_signal, verify_and_confirm_success
import uuid

router = APIRouter(prefix="/api/payments", tags=["payments"])


class SignalRequest(BaseModel):
    signal: str  # INSTANT_SUCCESS, ERROR_SIGNAL, TIMEOUT
    transaction_id: Optional[str] = None


@router.post("", response_model=PaymentResponse)
async def create_payment(
    req: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    idempotency_key = req.idempotency_key or f"{req.order_id}_{uuid.uuid4().hex[:8]}"
    payment = await initiate_payment(
        db=db,
        order_id=req.order_id,
        amount=req.amount,
        payment_method=req.payment_method.value,
        idempotency_key=idempotency_key,
        user_id=str(current_user.id),
    )
    messages = {
        PaymentStatus.SUCCESS: "Payment completed successfully",
        PaymentStatus.UNDER_VERIFICATION: "Payment is under verification by AUREV AI. Do not make another payment.",
        PaymentStatus.SAFE_RETURN: "Payment could not be confirmed. ₹0 was debited.",
        PaymentStatus.DECLINED: f"Payment declined: {payment.failure_reason or 'Bank unavailable'}",
        PaymentStatus.FAILED: "Payment failed — verification completed safely",
        PaymentStatus.RECOVERING: "Payment recovering — AUREV AI is working",
        PaymentStatus.ESCALATED: "Payment escalated for manual review",
        PaymentStatus.UNKNOWN: "Payment status unknown — investigating",
    }
    return PaymentResponse(
        transaction_id=payment.transaction_id,
        status=payment.status.value,
        amount=payment.amount,
        currency=payment.currency,
        message=messages.get(payment.status, "Processing"),
        ml_classification=payment.ml_classification,
        ml_confidence=payment.ml_confidence,
        aurev_action=payment.aurev_action,
    )


@router.post("/signal")
async def receive_payment_signal(req: SignalRequest, db: Session = Depends(get_db)):
    """
    Demo Control Endpoint:
    Receives external test signals (INSTANT_SUCCESS, ERROR_SIGNAL, TIMEOUT).
    When INSTANT_SUCCESS arrives while a transaction is UNDER_VERIFICATION,
    AUREV AI immediately verifies identity, amount, order, and confirms payment.
    """
    signal = req.signal.upper()
    inject_payment_signal(signal, req.transaction_id)

    # If INSTANT_SUCCESS, immediately resolve active UNDER_VERIFICATION payment
    if signal == "INSTANT_SUCCESS":
        query = db.query(Payment).filter(Payment.status == PaymentStatus.UNDER_VERIFICATION)
        if req.transaction_id:
            query = query.filter(Payment.transaction_id == req.transaction_id)
        active_payment = query.order_by(Payment.created_at.desc()).first()

        if active_payment:
            await verify_and_confirm_success(db, active_payment)
            return {
                "success": True,
                "signal": signal,
                "transaction_id": active_payment.transaction_id,
                "status": "SUCCESS",
                "message": "Payment verified and confirmed by AUREV AI"
            }

    return {
        "success": True,
        "signal": signal,
        "message": f"Signal {signal} registered for verification loop"
    }


@router.get("/{transaction_id}/status")
def get_payment_status(transaction_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "transaction_id": payment.transaction_id,
        "status": payment.status.value,
        "amount": payment.amount,
        "failure_code": payment.failure_code,
        "failure_reason": payment.failure_reason,
        "money_debited": payment.money_debited,
        "attempt_count": payment.attempt_count,
        "recovery_attempt_count": payment.recovery_attempt_count,
        "ml_classification": payment.ml_classification,
        "ml_confidence": payment.ml_confidence,
        "aurev_action": payment.aurev_action,
        "aurev_reasoning": payment.aurev_reasoning,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


@router.get("/{transaction_id}/events")
def get_payment_events(transaction_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return [
        {
            "event_type": e.event_type,
            "message": e.message,
            "data": e.data,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in payment.events
    ]
