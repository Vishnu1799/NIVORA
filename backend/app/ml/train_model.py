"""
NIVORA ML Training Pipeline — Enhanced Real-World Failure Predictor
Problem Statement: FI-04 Payment Failure Recovery System
Platform: NIVORA Grocery & Instant Commerce
"""
import os
import random
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

CLASSES = [
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

CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

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

BANK_MAP = {"UP": 1, "DEGRADED": 2, "TIMEOUT": 3, "DOWN": 4}
GATEWAY_MAP = {"UP": 1, "DEGRADED": 2, "DOWN": 3}
NET_MAP = {"STABLE": 1, "UNSTABLE": 2}
METHOD_MAP = {"UPI": 1, "CARD": 2, "NET_BANKING": 3, "WALLET": 4}
ERROR_MAP = {
    "NONE": 0,
    "TIMEOUT": 1,
    "NETWORK_ERROR": 2,
    "GATEWAY_ERROR": 3,
    "BANK_ERROR": 4,
    "INSUFFICIENT_FUNDS": 5,
    "INVALID_DETAILS": 6,
    "UNKNOWN": 7,
}


def generate_enhanced_dataset(n_samples: int = 30000) -> pd.DataFrame:
    """
    Generates realistic, telemetry-rich synthetic payment failure dataset
    mirroring real-world NPCI/UPI & payment gateway telemetry in India.
    """
    records = []
    methods = ["UPI", "CARD", "NET_BANKING", "WALLET"]
    method_weights = [0.65, 0.20, 0.10, 0.05]

    for _ in range(n_samples):
        scenario = random.choices(
            CLASSES,
            weights=[38, 12, 10, 10, 7, 8, 5, 5, 5],
            k=1
        )[0]

        method = random.choices(methods, weights=method_weights, k=1)[0]
        retry_count = random.choices([0, 1, 2], weights=[0.75, 0.18, 0.07], k=1)[0]

        # Realistic Indian grocery basket pricing (₹20 to ₹5000)
        if method == "UPI":
            amount = round(random.uniform(25.0, 1500.0), 2)
        elif method == "CARD":
            amount = round(random.uniform(200.0, 4800.0), 2)
        else:
            amount = round(random.uniform(50.0, 3000.0), 2)

        if scenario == "SUCCESS":
            bank_health = "UP"
            gateway_health = "UP"
            network_status = "STABLE"
            response_time_ms = random.randint(70, 750)
            money_debited = 1
            error_code = "NONE"

        elif scenario == "NETWORK_TIMEOUT":
            bank_health = random.choice(["UP", "DEGRADED", "TIMEOUT"])
            gateway_health = "UP"
            network_status = "UNSTABLE"
            response_time_ms = random.randint(4800, 12500)
            money_debited = 0
            error_code = "TIMEOUT"

        elif scenario == "GATEWAY_TIMEOUT":
            bank_health = "UP"
            gateway_health = random.choice(["DEGRADED", "DOWN"])
            network_status = random.choice(["STABLE", "UNSTABLE"])
            response_time_ms = random.randint(5200, 15000)
            money_debited = 0
            error_code = "GATEWAY_ERROR"

        elif scenario == "TEMPORARY_BANK_ERROR":
            bank_health = "DEGRADED"
            gateway_health = "UP"
            network_status = "STABLE"
            response_time_ms = random.randint(1100, 3900)
            money_debited = 0
            error_code = "BANK_ERROR"

        elif scenario == "BANK_SERVER_DOWN":
            bank_health = "DOWN"
            gateway_health = random.choice(["UP", "DEGRADED"])
            network_status = "STABLE"
            response_time_ms = random.randint(15, 250)
            money_debited = 0
            error_code = "BANK_ERROR"

        elif scenario == "INSUFFICIENT_FUNDS":
            bank_health = "UP"
            gateway_health = "UP"
            network_status = "STABLE"
            response_time_ms = random.randint(150, 850)
            money_debited = 0
            error_code = "INSUFFICIENT_FUNDS"

        elif scenario == "INVALID_PAYMENT_DETAILS":
            bank_health = "UP"
            gateway_health = "UP"
            network_status = "STABLE"
            response_time_ms = random.randint(90, 550)
            money_debited = 0
            error_code = "INVALID_DETAILS"

        elif scenario == "DUPLICATE_RISK":
            bank_health = random.choice(["UP", "DEGRADED"])
            gateway_health = "UP"
            network_status = "UNSTABLE"
            response_time_ms = random.randint(2200, 6800)
            money_debited = 1
            error_code = random.choice(["TIMEOUT", "UNKNOWN", "NONE"])

        else:  # UNKNOWN_STATUS
            bank_health = random.choice(["DEGRADED", "TIMEOUT"])
            gateway_health = random.choice(["DEGRADED", "UP"])
            network_status = "UNSTABLE"
            response_time_ms = random.randint(3100, 9500)
            money_debited = -1
            error_code = "UNKNOWN"

        records.append({
            "amount": amount,
            "payment_method": method,
            "bank_health": bank_health,
            "gateway_health": gateway_health,
            "network_status": network_status,
            "response_time_ms": response_time_ms,
            "money_debited": money_debited,
            "retry_count": retry_count,
            "error_code": error_code,
            "failure_category": scenario,
            "recommended_action": ACTION_MAP[scenario],
        })

    return pd.DataFrame(records)


def encode_features(df: pd.DataFrame) -> np.ndarray:
    return np.array([
        [
            float(row["amount"]),
            METHOD_MAP.get(row["payment_method"], 1),
            BANK_MAP.get(row["bank_health"], 1),
            GATEWAY_MAP.get(row["gateway_health"], 1),
            NET_MAP.get(row["network_status"], 1),
            float(row["response_time_ms"]),
            int(row["money_debited"]),
            int(row["retry_count"]),
            ERROR_MAP.get(row["error_code"], 0),
        ]
        for _, row in df.iterrows()
    ])


def main():
    print("[NIVORA ML] Generating 30,000 enhanced real-time payment telemetry samples...", flush=True)
    df = generate_enhanced_dataset(n_samples=30000)
    dataset_path = os.path.join(os.path.dirname(__file__), "payment_ml_dataset.csv")
    df.to_csv(dataset_path, index=False)
    print(f"[NIVORA ML] Dataset saved ({len(df)} rows) -> {dataset_path}", flush=True)

    X = encode_features(df)
    y = np.array([CLASS_TO_IDX[c] for c in df["failure_category"]])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[NIVORA ML] Training production RandomForestClassifier on {len(X_train)} samples...", flush=True)

    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=16,
        min_samples_split=3,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n=======================================================", flush=True)
    print(f" [NIVORA ML] Enhanced Model Accuracy: {acc * 100:.2f}%", flush=True)
    print(f"=======================================================\n", flush=True)
    print(classification_report(y_test, y_pred, target_names=CLASSES), flush=True)

    # Calculate Feature Importances
    feature_names = [
        "amount", "payment_method", "bank_health", "gateway_health",
        "network_status", "response_time_ms", "money_debited", "retry_count", "error_code"
    ]
    importances = sorted(zip(feature_names, clf.feature_importances_), key=lambda x: x[1], reverse=True)
    print("--- Top Predictive Telemetry Signals ---")
    for feat, score in importances:
        print(f"  • {feat:20s}: {score * 100:.2f}%")

    model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
    bundle = {
        "model": clf,
        "classes": CLASSES,
        "action_map": ACTION_MAP,
        "feature_order": feature_names,
    }
    joblib.dump(bundle, model_path)
    print(f"\n[NIVORA ML] Production model bundle saved -> {model_path}", flush=True)


if __name__ == "__main__":
    main()
