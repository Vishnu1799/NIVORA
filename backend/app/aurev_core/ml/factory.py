"""
Factory for creating the appropriate ML Provider instance based on configuration.
"""
from config.settings import settings
from ml.ml_provider import MLProvider
from ml.mock_provider import MockMLProvider
from ml.http_provider import HTTPMLProvider


def get_ml_provider() -> MLProvider:
    if settings.ML_PROVIDER.lower() == "http":
        return HTTPMLProvider(
            service_url=settings.ML_SERVICE_URL,
            timeout_seconds=settings.ML_TIMEOUT_SECONDS,
            fallback_on_error=True
        )
    return MockMLProvider()
