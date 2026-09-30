def build_features(payment, bank_health: str, gateway_health: str, response_time_ms: int, error_code: str = "NONE") -> dict:
    """Build feature dict for ML predictor from payment context."""
    actual_latency = response_time_ms
    if error_code == "TIMEOUT" or payment.failure_code == "TIMEOUT":
        actual_latency = max(actual_latency, 6500)
    
    network_status = "UNSTABLE" if actual_latency >= 3000 else "STABLE"

    return {
        "amount": float(payment.amount),
        "payment_method": payment.payment_method.value if hasattr(payment.payment_method, "value") else str(payment.payment_method),
        "bank_health": bank_health,
        "gateway_health": gateway_health,
        "network_status": network_status,
        "response_time_ms": actual_latency,
        "money_debited": payment.money_debited,
        "retry_count": payment.attempt_count,
        "error_code": error_code if error_code != "NONE" else (payment.failure_code or "NONE"),
    }
