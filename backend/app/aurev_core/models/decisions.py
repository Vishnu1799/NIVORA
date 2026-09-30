"""
Decision, Audit, Permit and System Health models for AUREV.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from models.enums import (
    AurevDecision,
    FinalityState,
    GatewayStatus,
    PermitStatus,
    RiskLevel,
    ServerStatus,
)


class RecoveryPermit(BaseModel):
    permit_id: str = Field(default_factory=lambda: f"PERMIT-{uuid.uuid4().hex[:8].upper()}")
    payment_id: str
    order_id: str
    amount: float
    currency: str = "INR"
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=300)
    )
    single_use: bool = True
    status: PermitStatus = PermitStatus.ACTIVE
    used_at: Optional[datetime] = None

    def is_valid_for(self, payment_id: str, order_id: str, amount: float) -> bool:
        now = datetime.now(timezone.utc)
        if self.status != PermitStatus.ACTIVE:
            return False
        # Normalize timezone if necessary
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            return False
        if self.order_id != order_id or abs(self.amount - amount) > 0.01:
            return False
        return True


class AurevReasoningResult(BaseModel):
    """
    Structured reasoning output produced by Gemini or fallback AI reasoning layer.
    Conforms to AUREV_REASONING_RESULT contract.
    """
    agent_status: str = "AI_AVAILABLE"  # AI_AVAILABLE | AI_UNAVAILABLE | COMPLETED
    observed_evidence: List[str] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    risk_assessment: str = ""
    relevant_events: List[str] = Field(default_factory=list)
    requested_tools: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_decision: AurevDecision = AurevDecision.WAIT
    proposed_action: str = ""
    reason_summary: str = ""
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    next_monitoring_step: Optional[str] = None
    agent_trace: List[str] = Field(default_factory=list)

    def to_legacy_dict(self) -> Dict[str, Any]:
        return {
            "known": self.observed_evidence,
            "uncertain": self.evidence_gaps,
            "verify_next": [self.next_monitoring_step] if self.next_monitoring_step else [],
            "recommendation": self.proposed_decision.value,
            "explanation": self.reason_summary,
            "agent_status": self.agent_status,
            "proposed_action": self.proposed_action,
            "risk_assessment": self.risk_assessment,
            "requested_tools": self.requested_tools,
            "confidence": self.confidence,
            "agent_trace": self.agent_trace,
        }


class AurevAnalysisResult(BaseModel):
    payment_id: str
    order_id: str
    finality_state: FinalityState
    decision: AurevDecision
    risk_level: RiskLevel = RiskLevel.LOW
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    known_evidence: List[str] = Field(default_factory=list)
    uncertain_evidence: List[str] = Field(default_factory=list)
    verification_needed: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)
    reason: str
    next_check_at: Optional[str] = None
    audit_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    permit: Optional[RecoveryPermit] = None
    agent_trace: List[str] = Field(default_factory=list)
    reasoning_result: Optional[AurevReasoningResult] = None


class AurevAuditRecord(BaseModel):
    audit_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_id: str
    order_id: str
    observed_evidence: Dict[str, Any] = Field(default_factory=dict)
    ml_signals: List[str] = Field(default_factory=list)
    aurev_reasoning: str
    policy_result: Dict[str, Any] = Field(default_factory=dict)
    decision: AurevDecision
    actions_taken: List[str] = Field(default_factory=list)
    verification_result: Optional[str] = None
    financial_safety_mode: bool = False
    agent_trace: List[str] = Field(default_factory=list)
    reasoning_result: Optional[Dict[str, Any]] = None


class SystemHealthState(BaseModel):
    gateway_status: GatewayStatus = GatewayStatus.HEALTHY
    server_status: ServerStatus = ServerStatus.HEALTHY
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=45.0, ge=0.0)
    is_safety_mode_active: bool = False
    active_issues: List[str] = Field(default_factory=list)
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
