from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database.connection import Base


class PaymentStatus(str, enum.Enum):
    IDLE = "IDLE"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    BANK_CHECK = "BANK_CHECK"
    PROCESSING = "PROCESSING"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SAFE_RETURN = "SAFE_RETURN"
    DECLINED = "DECLINED"
    UNKNOWN = "UNKNOWN"
    RECOVERING = "RECOVERING"
    RECONCILING = "RECONCILING"
    ESCALATED = "ESCALATED"



class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CARD = "CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    COD = "COD"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False, index=True)
    idempotency_key = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.UPI)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.INITIATED)
    failure_code = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    bank_transaction_id = Column(String, nullable=True)
    attempt_count = Column(Integer, default=0)
    recovery_attempt_count = Column(Integer, default=0)
    money_debited = Column(Boolean, nullable=True)
    merchant_credited = Column(Boolean, default=False)
    ml_classification = Column(String, nullable=True)
    ml_confidence = Column(Float, nullable=True)
    aurev_action = Column(String, nullable=True)
    aurev_reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order = relationship("Order", back_populates="payments")
    events = relationship("PaymentEvent", back_populates="payment")
    recovery_actions = relationship("RecoveryAction", back_populates="payment")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="events")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    action_type = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    result = Column(String, nullable=True)
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="recovery_actions")
