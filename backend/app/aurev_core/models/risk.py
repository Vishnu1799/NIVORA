"""
Risk assessment models for ML integration and risk signals.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from models.enums import RiskLevel, BankStatus, MerchantStatus, PaymentStatus


class MLRiskRequest(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    payment_method: str = "UPI"
    gateway: str = "RAZORPAY"
    attempt_number: int = 1
    gateway_response_time: float = 0.0  # in ms
    gateway_status: str = "UNKNOWN"
    http_status: int = 200
    server_latency: float = 50.0  # in ms
    server_error_rate: float = 0.0  # fraction 0.0-1.0
    webhook_delay: float = 0.0  # in ms
    webhook_received: bool = False
    bank_status: str = "UNKNOWN"
    merchant_status: str = "UNKNOWN"
    customer_debited: Optional[bool] = None
    payment_state: str = "UNKNOWN"
    previous_attempts: int = 0
    time_since_previous_attempt: float = 0.0  # in seconds
    same_order_previous_success: bool = False
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_risk_score: float = 0.0
    transaction_velocity: int = 1


class MLRiskResponse(BaseModel):
    payment_id: str
    anomaly_score: float = Field(ge=0.0, le=1.0, description="Anomaly score between 0.0 and 1.0")
    duplicate_risk: float = Field(ge=0.0, le=1.0, description="Risk of duplicate charge between 0.0 and 1.0")
    failure_risk: float = Field(ge=0.0, le=1.0, description="Risk of final failure between 0.0 and 1.0")
    risk_level: RiskLevel = RiskLevel.LOW
    signals: List[str] = Field(default_factory=list)
