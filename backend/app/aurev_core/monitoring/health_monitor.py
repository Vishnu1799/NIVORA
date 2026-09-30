"""
System and Gateway Health Monitor.
Tracks gateway error rates, server latency, and deterministically triggers Financial Safety Mode.
"""
from typing import List, Tuple
from config.settings import settings
from models.decisions import SystemHealthState
from models.enums import GatewayStatus, ServerStatus, EventType
from tools.observation_tools import _system_health, set_system_health
from memory.event_timeline import timeline_store


class HealthMonitor:
    @classmethod
    def evaluate_health(
        cls,
        error_rate: float,
        latency_ms: float,
        gateway_status: GatewayStatus = GatewayStatus.HEALTHY
    ) -> Tuple[bool, SystemHealthState, List[str]]:
        issues: List[str] = []
        should_enter_safety_mode = False

        if error_rate >= settings.GATEWAY_ERROR_RATE_THRESHOLD:
            issues.append(f"Gateway error rate ({error_rate:.1%}) exceeds safety threshold ({settings.GATEWAY_ERROR_RATE_THRESHOLD:.1%}).")
            should_enter_safety_mode = True

        if latency_ms >= settings.SERVER_LATENCY_THRESHOLD_MS:
            issues.append(f"Server latency ({latency_ms:.0f}ms) exceeds safety threshold ({settings.SERVER_LATENCY_THRESHOLD_MS:.0f}ms).")
            should_enter_safety_mode = True

        if gateway_status == GatewayStatus.DOWN:
            issues.append("Gateway is reporting DOWN.")
            should_enter_safety_mode = True

        prev_safety_mode = _system_health.is_safety_mode_active

        updated_health = set_system_health(
            gateway_status=gateway_status,
            error_rate=error_rate,
            avg_latency_ms=latency_ms,
            is_safety_mode_active=should_enter_safety_mode,
            active_issues=issues
        )

        # Log timeline events upon mode transitions
        if should_enter_safety_mode and not prev_safety_mode:
            timeline_store.record_event(
                payment_id="SYSTEM",
                order_id="SYSTEM_HEALTH",
                event_type=EventType.SAFETY_MODE_ENTERED,
                source="health_monitor",
                status="FINANCIAL_SAFETY_MODE_ACTIVE",
                metadata={"issues": issues}
            )
        elif not should_enter_safety_mode and prev_safety_mode:
            timeline_store.record_event(
                payment_id="SYSTEM",
                order_id="SYSTEM_HEALTH",
                event_type=EventType.SAFETY_MODE_EXITED,
                source="health_monitor",
                status="FINANCIAL_SAFETY_MODE_CLEARED",
                metadata={"status": "All systems operational"}
            )

        return should_enter_safety_mode, updated_health, issues
