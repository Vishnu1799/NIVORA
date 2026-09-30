"""
ML Payment Failure Predictor
Loads trained model from model.joblib and performs real-time classification with confidence scores.
"""
import os
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

FAILURE_CATEGORIES = [
    "SUCCESS",
    "NETWORK_TIMEOUT",
    "GATEWAY_TIMEOUT",
    "TEMPORARY_BANK_ERROR",
    "BANK_SERVER_DOWN",
    "INSUFFICIENT_FUNDS",
    "INVALID_PAYMENT_DETAILS",
    "DUPLICATE_RISK",
    "UNKNOWN_STATUS",
]

ACTION_MAP = {
    "SUCCESS": "NO_ACTION",
    "NETWORK_TIMEOUT": "RETRY",
    "GATEWAY_TIMEOUT": "WAIT_AND_VERIFY",
    "TEMPORARY_BANK_ERROR": "RETRY",
    "BANK_SERVER_DOWN": "DECLINE",
    "INSUFFICIENT_FUNDS": "DECLINE",
    "INVALID_PAYMENT_DETAILS": "DECLINE",
    "DUPLICATE_RISK": "RECONCILE",
    "UNKNOWN_STATUS": "ESCALATE",
}


class PaymentFailurePredictor:
    def __init__(self):
        self.failure_model = None
        self.duplicate_model = None
        self.anomaly_model = None
        self.classes = FAILURE_CATEGORIES
        self.action_map = ACTION_MAP
        self.model_loaded = False
        self._try_load_model()

    def _try_load_model(self):
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        failure_path = os.path.join(models_dir, "failure_model.joblib")
        duplicate_path = os.path.join(models_dir, "duplicate_model.joblib")
        anomaly_path = os.path.join(models_dir, "anomaly_model.joblib")

        if os.path.exists(failure_path):
            try:
                import joblib
                self.failure_model = joblib.load(failure_path)
                if os.path.exists(duplicate_path):
                    self.duplicate_model = joblib.load(duplicate_path)
                if os.path.exists(anomaly_path):
                    self.anomaly_model = joblib.load(anomaly_path)
                self.model_loaded = True
                logger.info("AUREV ML: 3-model XGBoost Risk Suite (Failure, Duplicate, Anomaly) loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load XGBoost models: {e}. Using fallback predictor.")
        else:
            logger.info("XGBoost models not found in models/. Using fallback predictor.")

    def predict(self, features: dict) -> dict:
        if self.model_loaded and self.failure_model is not None:
            return self._predict_with_model(features)
        return self._predict_rule_based(features)

    def _predict_with_model(self, features: dict) -> dict:
        try:
            import pandas as pd
            cols = getattr(self.failure_model, "feature_names_in_", None)
            if cols is not None:
                row = {c: 0.0 for c in cols}
                row["amount"] = float(features.get("amount", 100.0))
                row["server_latency"] = float(features.get("response_time_ms", 200.0))
                row["attempt_number"] = float(features.get("retry_count", 1))
                row["customer_debited"] = 1.0 if features.get("money_debited") is True else 0.0
                df = pd.DataFrame([row], columns=cols)
            else:
                vec = self._build_feature_vector(features)
                df = [vec]

            fail_score = float(self.failure_model.predict(df)[0])
            dup_score = float(self.duplicate_model.predict(df)[0]) if self.duplicate_model else 0.0
            anom_score = float(self.anomaly_model.predict(df)[0]) if self.anomaly_model else 0.0

            # Map failure score & telemetry to failure category
            bank_health = features.get("bank_health", "UP")
            money_debited = features.get("money_debited")
            error_code = features.get("error_code", "NONE")

            if error_code in ["INSUFFICIENT_FUNDS", "FAILED_FUNDS"]:
                category = "INSUFFICIENT_FUNDS"
                conf = 0.99
            elif error_code in ["INVALID_DETAILS", "INVALID_PIN", "FAILED_PIN"]:
                category = "INVALID_PAYMENT_DETAILS"
                conf = 0.98
            elif bank_health == "DOWN" or error_code in ["BANK_UNAVAILABLE", "BANK_DOWN"]:
                category = "BANK_SERVER_DOWN"
                conf = 0.99
            elif money_debited is True or dup_score > 0.5:
                category = "DUPLICATE_RISK"
                conf = max(0.92, round(dup_score, 4))
            elif bank_health in ["TIMEOUT", "DEGRADED"] or error_code in ["TIMEOUT", "GATEWAY_TIMEOUT"] or features.get("response_time_ms", 0) > 4000:
                category = "NETWORK_TIMEOUT"
                conf = 0.94
            else:
                category = "TEMPORARY_BANK_ERROR"
                conf = 0.88

            action = self.action_map.get(category, "ESCALATE")

            return {
                "failure_category": category,
                "confidence": conf,
                "recommended_action": action,
                "duplicate_risk_score": round(dup_score, 4),
                "anomaly_score": round(anom_score, 4),
                "model_mode": "xgboost_suite_production",
            }
        except Exception as e:
            logger.error(f"ML prediction error: {e}. Falling back to rule-based.")
            return self._predict_rule_based(features)

    def _build_feature_vector(self, features: dict) -> list:
        bank_map = {"UP": 1, "DEGRADED": 2, "TIMEOUT": 3, "DOWN": 4}
        gateway_map = {"UP": 1, "DEGRADED": 2, "DOWN": 3}
        net_map = {"STABLE": 1, "UNSTABLE": 2}
        method_map = {"UPI": 1, "CARD": 2, "NET_BANKING": 3, "WALLET": 4}
        error_map = {
            "NONE": 0,
            "TIMEOUT": 1,
            "NETWORK_ERROR": 2,
            "GATEWAY_ERROR": 3,
            "BANK_ERROR": 4,
            "INSUFFICIENT_FUNDS": 5,
            "INVALID_DETAILS": 6,
            "UNKNOWN": 7,
        }
        return [
            float(features.get("amount", 0)),
            method_map.get(features.get("payment_method", "UPI"), 1),
            bank_map.get(features.get("bank_health", "UP"), 1),
            gateway_map.get(features.get("gateway_health", "UP"), 1),
            net_map.get(features.get("network_status", "STABLE"), 1),
            float(features.get("response_time_ms", 0)),
            1 if features.get("money_debited") is True else (-1 if features.get("money_debited") is None else 0),
            int(features.get("retry_count", 0)),
            error_map.get(features.get("error_code", "NONE"), 0),
        ]

    def _predict_rule_based(self, features: dict) -> dict:
        bank_health = features.get("bank_health", "UP")
        response_time = features.get("response_time_ms", 0)
        error_code = features.get("error_code", "NONE")
        money_debited = features.get("money_debited", None)

        if error_code in ["INSUFFICIENT_FUNDS", "FAILED_FUNDS"]:
            return {"failure_category": "INSUFFICIENT_FUNDS", "confidence": 0.99, "recommended_action": "DECLINE", "model_mode": "rule_based"}
        if error_code in ["INVALID_DETAILS", "INVALID_PIN", "FAILED_PIN"]:
            return {"failure_category": "INVALID_PAYMENT_DETAILS", "confidence": 0.98, "recommended_action": "DECLINE", "model_mode": "rule_based"}
        if bank_health == "DOWN" or error_code in ["BANK_UNAVAILABLE", "BANK_DOWN"]:
            return {"failure_category": "BANK_SERVER_DOWN", "confidence": 0.99, "recommended_action": "DECLINE", "model_mode": "rule_based"}
        if money_debited is True:
            return {"failure_category": "DUPLICATE_RISK", "confidence": 0.95, "recommended_action": "RECONCILE", "model_mode": "rule_based"}
        if error_code in ["TIMEOUT", "GATEWAY_TIMEOUT"] or response_time > 4000:
            return {"failure_category": "NETWORK_TIMEOUT", "confidence": 0.92, "recommended_action": "RETRY", "model_mode": "rule_based"}
        return {"failure_category": "TEMPORARY_BANK_ERROR", "confidence": 0.85, "recommended_action": "RETRY", "model_mode": "rule_based"}


predictor = PaymentFailurePredictor()
