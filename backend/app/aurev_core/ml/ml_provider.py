"""
Abstract Base Class for ML Risk and Anomaly Analysis Providers.
"""
from abc import ABC, abstractmethod
from models.risk import MLRiskRequest, MLRiskResponse


class MLProvider(ABC):
    @abstractmethod
    async def analyze_payment_async(self, request: MLRiskRequest) -> MLRiskResponse:
        """Asynchronously analyze payment parameters for risk and anomaly signals."""
        pass

    @abstractmethod
    def analyze_payment(self, request: MLRiskRequest) -> MLRiskResponse:
        """Synchronously analyze payment parameters for risk and anomaly signals."""
        pass
