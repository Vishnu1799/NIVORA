import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from state import bank_state
from datetime import datetime

router = APIRouter(tags=["payments"])


class PaymentRequest(BaseModel):
    transaction_id: str
    amount: float
    payment_method: str
    idempotency_key: str


@router.post("/payments")
async def process_payment(req: PaymentRequest):
    """
    Process a payment.
    Behavior strictly follows bank state set via /admin/service-state
    """
    # Idempotency — same key returns same cached result
    if req.idempotency_key in bank_state.transactions:
        return bank_state.transactions[req.idempotency_key]

    # Simulate response delay
    delay_ms = bank_state.get_latency_ms()
    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)

    # 1. Bank is DOWN
    if bank_state.service_state == "DOWN":
        result = {
            "bank_transaction_id": None,
            "transaction_id": req.transaction_id,
            "status": "FAILED",
            "money_debited": False,
            "merchant_credited": False,
            "error_code": "BANK_UNAVAILABLE",
            "error_message": "503 Service Unavailable: Core banking system offline",
            "response_time_ms": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
        bank_state.transactions[req.idempotency_key] = result
        return result

    # 2. Bank is TIMEOUT / NO_RESPONSE
    if bank_state.service_state in ["TIMEOUT", "NO_RESPONSE"] or bank_state.force_outcome in ["TIMEOUT", "NO_RESPONSE"]:
        if bank_state.force_outcome in ["TIMEOUT", "NO_RESPONSE"]:
            bank_state.force_outcome = None
        elif bank_state.service_state in ["TIMEOUT", "NO_RESPONSE"]:
            bank_state.service_state = "UP"
        raise HTTPException(status_code=504, detail="504 Gateway Timeout: Bank switch dropped handshake")

    # 2b. Bank is ERROR_SIGNAL (Connection Reset / Uncertain State)
    if bank_state.service_state == "ERROR_SIGNAL" or bank_state.force_outcome == "ERROR_SIGNAL":
        if bank_state.force_outcome == "ERROR_SIGNAL":
            bank_state.force_outcome = None
        elif bank_state.service_state == "ERROR_SIGNAL":
            bank_state.service_state = "UP"
        raise HTTPException(status_code=500, detail="500 Internal Server Error: Signal lost during payment capture")


    # 3. Persistent Insufficient Balance
    if bank_state.service_state == "INSUFFICIENT_FUNDS" or bank_state.force_outcome in ["INSUFFICIENT_FUNDS", "FAILED"]:
        if bank_state.force_outcome in ["INSUFFICIENT_FUNDS", "FAILED"]:
            bank_state.force_outcome = None
        result = {
            "bank_transaction_id": None,
            "transaction_id": req.transaction_id,
            "status": "FAILED",
            "money_debited": False,
            "merchant_credited": False,
            "error_code": "INSUFFICIENT_FUNDS",
            "error_message": "Decline Code 51: Insufficient funds in customer account",
            "response_time_ms": delay_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        bank_state.transactions[req.idempotency_key] = result
        return result

    # 4. Persistent Invalid Credentials / PIN
    if bank_state.service_state == "INVALID_DETAILS" or bank_state.force_outcome in ["INVALID_DETAILS", "INVALID_PIN"]:
        if bank_state.force_outcome in ["INVALID_DETAILS", "INVALID_PIN"]:
            bank_state.force_outcome = None
        result = {
            "bank_transaction_id": None,
            "transaction_id": req.transaction_id,
            "status": "FAILED",
            "money_debited": False,
            "merchant_credited": False,
            "error_code": "INVALID_DETAILS",
            "error_message": "Decline Code 55: Incorrect UPI PIN or card credentials",
            "response_time_ms": delay_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        bank_state.transactions[req.idempotency_key] = result
        return result

    # 5. Indeterminate / Money Debited Conflict
    if bank_state.service_state == "UNKNOWN" or bank_state.force_outcome == "UNKNOWN":
        if bank_state.force_outcome == "UNKNOWN":
            bank_state.force_outcome = None
        bank_transaction_id = f"BANK_{uuid.uuid4().hex[:12].upper()}"
        result = {
            "bank_transaction_id": bank_transaction_id,
            "transaction_id": req.transaction_id,
            "status": "UNKNOWN",
            "money_debited": True,  # Customer account debited
            "merchant_credited": False,
            "error_code": "PENDING_RECONCILIATION",
            "error_message": "Beneficiary bank processing pending: Customer ledger debited",
            "response_time_ms": delay_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        bank_state.transactions[req.idempotency_key] = result
        return result

    # 6. Degraded Random Failure
    if bank_state.service_state == "DEGRADED" and bank_state.should_fail_randomly():
        raise HTTPException(status_code=504, detail="504 Gateway Timeout: Latency threshold exceeded")

    if bank_state.should_fail_randomly():
        result = {
            "bank_transaction_id": None,
            "transaction_id": req.transaction_id,
            "status": "FAILED",
            "money_debited": False,
            "merchant_credited": False,
            "error_code": "INSUFFICIENT_FUNDS",
            "error_message": "Decline Code 51: Insufficient funds in customer account",
            "response_time_ms": delay_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        bank_state.transactions[req.idempotency_key] = result
        return result

    # 7. Normal Success (200 OK)
    bank_transaction_id = f"BANK_{uuid.uuid4().hex[:12].upper()}"
    result = {
        "bank_transaction_id": bank_transaction_id,
        "transaction_id": req.transaction_id,
        "status": "SUCCESS",
        "money_debited": True,
        "merchant_credited": True,
        "error_code": None,
        "error_message": None,
        "response_time_ms": delay_ms,
        "timestamp": datetime.utcnow().isoformat(),
    }
    bank_state.transactions[req.idempotency_key] = result
    return result


@router.get("/payments/{transaction_id}")
def get_payment(transaction_id: str):
    """Get payment status by transaction ID."""
    for txn in bank_state.transactions.values():
        if txn.get("transaction_id") == transaction_id:
            return txn
    raise HTTPException(status_code=404, detail="Transaction not found")


@router.get("/payments/{transaction_id}/verify")
def verify_payment(transaction_id: str):
    """Verify whether money was debited for a transaction."""
    for txn in bank_state.transactions.values():
        if txn.get("transaction_id") == transaction_id:
            return {
                "transaction_id": transaction_id,
                "status": txn.get("status"),
                "money_debited": txn.get("money_debited"),
                "merchant_credited": txn.get("merchant_credited"),
                "bank_transaction_id": txn.get("bank_transaction_id"),
                "verified_at": datetime.utcnow().isoformat(),
            }
    return {
        "transaction_id": transaction_id,
        "status": "NOT_FOUND",
        "money_debited": None,
        "merchant_credited": None,
        "verified_at": datetime.utcnow().isoformat(),
    }
