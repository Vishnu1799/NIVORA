"""
Mock ML Provider for local development and testing before Google Colab connection.
"""
from typing import List
from models.risk import MLRiskRequest, MLRiskResponse
from models.enums import RiskLevel
from ml.ml_provider import MLProvider


class MockMLProvider(MLProvider):
    """
    Mock ML Provider that computes realistic risk, duplicate, and failure scores
    from payment telemetry and context.
    """

    def _compute_analysis(self, request: MLRiskRequest) -> MLRiskResponse:
        anomaly_score = 0.05
        duplicate_risk = 0.05
        failure_risk = 0.05
        signals: List[str] = []

        gw_status = (request.gateway_status or "").upper()

        # Check for previous success on same order
        if request.same_order_previous_success:
            duplicate_risk = 1.0
            anomaly_score = max(anomaly_score, 0.95)
            signals.append("CRITICAL: Prior attempt on this order already succeeded; duplicate payment imminent.")

        # Check for customer debited condition
        if request.customer_debited is True and gw_status != "SUCCESS":
            if request.merchant_status in ["PENDING", "UNKNOWN", "FAILED"]:
                anomaly_score = max(anomaly_score, 0.88)
                duplicate_risk = max(duplicate_risk, 0.92)
                signals.append("HIGH_ANOMALY: Customer bank debited but merchant uncredited.")

        # Check gateway status
        if gw_status in ["TIMEOUT", "UNKNOWN"]:
            anomaly_score = max(anomaly_score, 0.75)
            duplicate_risk = max(duplicate_risk, 0.80)
            failure_risk = max(failure_risk, 0.60)
            signals.append("GATEWAY_TIMEOUT: Response interrupted; settlement outcome uncertain.")
        elif gw_status == "FAILED":
            failure_risk = 0.90
            signals.append("GATEWAY_FAILED: Gateway returned explicit failure.")
        elif gw_status == "SUCCESS":
            failure_risk = 0.02
            duplicate_risk = 0.02
            anomaly_score = 0.02
            signals.append("GATEWAY_SUCCESS: Gateway confirmed successful capture.")

        # Server latency / health anomalies
        if request.server_latency > 2000.0 or request.gateway_response_time > 5000.0:
            anomaly_score = max(anomaly_score, 0.65)
            signals.append("HIGH_LATENCY: High server or gateway response time observed.")

        if request.server_error_rate > 0.30:
            anomaly_score = max(anomaly_score, 0.80)
            signals.append("HIGH_ERROR_RATE: Elevated server error rate detected.")

        if request.webhook_delay > 10000.0 and not request.webhook_received and gw_status != "SUCCESS":
            anomaly_score = max(anomaly_score, 0.60)
            signals.append("WEBHOOK_DELAY: Webhook confirmation overdue.")

        if request.previous_attempts >= 2 and gw_status != "SUCCESS":
            duplicate_risk = max(duplicate_risk, 0.70)
            signals.append(f"MULTIPLE_ATTEMPTS: Attempt count is {request.previous_attempts + 1}.")

        # Assign Risk Level
        max_score = max(anomaly_score, duplicate_risk, failure_risk)
        if max_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
        elif max_score >= 0.60:
            risk_level = RiskLevel.HIGH
        elif max_score >= 0.30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return MLRiskResponse(
            payment_id=request.payment_id,
            anomaly_score=round(anomaly_score, 3),
            duplicate_risk=round(duplicate_risk, 3),
            failure_risk=round(failure_risk, 3),
            risk_level=risk_level,
            signals=signals
        )

    def analyze_payment(self, request: MLRiskRequest) -> MLRiskResponse:
        return self._compute_analysis(request)

    async def analyze_payment_async(self, request: MLRiskRequest) -> MLRiskResponse:
        return self._compute_analysis(request)
