"""
HTTP ML Provider for communicating with external ML Risk API (e.g., Google Colab / FastAPI ML Service).
"""
import logging
from typing import Optional
import httpx
from models.risk import MLRiskRequest, MLRiskResponse
from models.enums import RiskLevel
from ml.ml_provider import MLProvider
from ml.mock_provider import MockMLProvider

logger = logging.getLogger("aurev.ml.http")


class HTTPMLProvider(MLProvider):
    """
    Connects to external ML Service endpoint: POST /ml/analyze-payment.
    Falls back gracefully if external service is unreachable.
    """

    def __init__(self, service_url: str, timeout_seconds: float = 3.0, fallback_on_error: bool = True):
        self.service_url = service_url.rstrip("/")
        self.endpoint = f"{self.service_url}/ml/analyze-payment"
        self.timeout_seconds = timeout_seconds
        self.fallback_on_error = fallback_on_error
        self._fallback_provider = MockMLProvider()

    def analyze_payment(self, request: MLRiskRequest) -> MLRiskResponse:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(self.endpoint, json=request.model_dump())
                if resp.status_code == 200:
                    data = resp.json()
                    return MLRiskResponse.model_validate(data)
                else:
                    logger.warning(f"ML service returned status {resp.status_code}: {resp.text}")
                    if self.fallback_on_error:
                        return self._fallback_provider.analyze_payment(request)
                    resp.raise_for_status()
        except Exception as exc:
            logger.error(f"Failed to connect to ML service at {self.endpoint}: {exc}")
            if self.fallback_on_error:
                fallback_res = self._fallback_provider.analyze_payment(request)
                fallback_res.signals.append(f"FALLBACK_TRIGGERED: External ML service unreachable ({exc}).")
                return fallback_res
            return MLRiskResponse(
                payment_id=request.payment_id,
                anomaly_score=0.5,
                duplicate_risk=0.5,
                failure_risk=0.5,
                risk_level=RiskLevel.MEDIUM,
                signals=["ML_UNAVAILABLE: External ML service unreachable. Relying on deterministic safety logic."]
            )

    async def analyze_payment_async(self, request: MLRiskRequest) -> MLRiskResponse:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(self.endpoint, json=request.model_dump())
                if resp.status_code == 200:
                    data = resp.json()
                    return MLRiskResponse.model_validate(data)
                else:
                    logger.warning(f"ML service returned status {resp.status_code}: {resp.text}")
                    if self.fallback_on_error:
                        return await self._fallback_provider.analyze_payment_async(request)
                    return MLRiskResponse(
                        payment_id=request.payment_id,
                        anomaly_score=0.5,
                        duplicate_risk=0.5,
                        failure_risk=0.5,
                        risk_level=RiskLevel.MEDIUM,
                        signals=[f"ML_UNAVAILABLE: Service returned {resp.status_code}."]
                    )
        except Exception as exc:
            logger.error(f"Failed to connect to ML service async at {self.endpoint}: {exc}")
            if self.fallback_on_error:
                fallback_res = await self._fallback_provider.analyze_payment_async(request)
                fallback_res.signals.append(f"FALLBACK_TRIGGERED: External ML service unreachable ({exc}).")
                return fallback_res
            return MLRiskResponse(
                payment_id=request.payment_id,
                anomaly_score=0.5,
                duplicate_risk=0.5,
                failure_risk=0.5,
                risk_level=RiskLevel.MEDIUM,
                signals=["ML_UNAVAILABLE: External ML service unreachable. Relying on deterministic safety logic."]
            )
