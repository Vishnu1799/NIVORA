"""
AUREV AI Tool Definitions
These are the ONLY ways AUREV AI can interact with the payment system.
Each tool is a controlled, logged action.
"""
import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def check_bank_health() -> dict:
    """Check current bank/payment gateway health status."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.bank_simulator_url}/health")
            data = response.json()
            return {
                "status": data.get("status", "UNKNOWN"),
                "latency_ms": data.get("latency_ms", 0),
                "success": True,
            }
    except Exception as e:
        logger.error(f"Bank health check failed: {e}")
        return {"status": "UNKNOWN", "latency_ms": 0, "success": False, "error": str(e)}


async def get_payment_status(transaction_id: str) -> dict:
    """Query payment status from bank simulator."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.bank_simulator_url}/payments/{transaction_id}")
            if response.status_code == 200:
                return {"found": True, **response.json()}
            return {"found": False, "status": "NOT_FOUND"}
    except Exception as e:
        logger.error(f"Get payment status failed: {e}")
        return {"found": False, "status": "ERROR", "error": str(e)}


async def verify_transaction(transaction_id: str) -> dict:
    """
    Verify transaction — check if money actually moved.
    Returns money_debited status from bank.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.bank_simulator_url}/payments/{transaction_id}/verify")
            if response.status_code == 200:
                data = response.json()
                return {
                    "verified": True,
                    "money_debited": data.get("money_debited"),
                    "merchant_credited": data.get("merchant_credited", False),
                    "bank_status": data.get("status"),
                }
            return {"verified": False, "money_debited": None}
    except Exception as e:
        logger.error(f"Transaction verification failed: {e}")
        return {"verified": False, "money_debited": None, "error": str(e)}


async def submit_payment_to_bank(
    transaction_id: str, amount: float, payment_method: str, idempotency_key: str
) -> dict:
    """Submit payment request to bank simulator."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.bank_simulator_url}/payments",
                json={
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "payment_method": payment_method,
                    "idempotency_key": idempotency_key,
                },
                timeout=15.0,
            )
            data = response.json()
            return {
                "success": data.get("status") == "SUCCESS",
                "status": data.get("status"),
                "bank_transaction_id": data.get("bank_transaction_id"),
                "money_debited": data.get("money_debited", False),
                "response_time_ms": data.get("response_time_ms", 0),
                "error_code": data.get("error_code"),
                "error_message": data.get("error_message"),
            }
    except httpx.TimeoutException:
        return {
            "success": False,
            "status": "TIMEOUT",
            "error_code": "TIMEOUT",
            "money_debited": None,
            "response_time_ms": 15000,
        }
    except Exception as e:
        logger.error(f"Payment submission failed: {e}")
        return {"success": False, "status": "ERROR", "error_code": "NETWORK_ERROR", "money_debited": None}
