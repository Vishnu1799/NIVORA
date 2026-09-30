"""
Continuous Payment Session Monitor.
Monitors non-final payments, polls downstream state, and advances payment lifecycle until resolution.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from memory.payment_memory import payment_memory
from memory.event_timeline import timeline_store
from models.enums import FinalityState, EventType, BankStatus, MerchantStatus
from agent.aurev_agent import aurev_agent
from models.decisions import AurevAnalysisResult

logger = logging.getLogger("aurev.monitoring")


class PaymentMonitor:
    def __init__(self):
        self._monitored_payments: Dict[str, bool] = {}

    def is_monitoring(self, payment_id: str) -> bool:
        return self._monitored_payments.get(payment_id, False)

    def attach(self, payment_id: str):
        self._monitored_payments[payment_id] = True

    def detach(self, payment_id: str):
        self._monitored_payments.pop(payment_id, None)

    async def monitor_step(self, payment_id: str) -> AurevAnalysisResult:
        """Runs a single monitoring tick for a payment."""
        analysis = aurev_agent.process_payment_session(payment_id)
        if analysis.finality_state in [FinalityState.FINAL_SUCCESS, FinalityState.FINAL_FAILURE]:
            self.detach(payment_id)
        return analysis

    async def run_until_terminal(
        self,
        payment_id: str,
        max_ticks: int = 5,
        tick_interval_seconds: float = 0.1
    ) -> AurevAnalysisResult:
        """
        Actively monitors a payment across ticks until a terminal state is reached
        or max_ticks is exhausted.
        """
        self.attach(payment_id)
        last_result = None

        for _ in range(max_ticks):
            last_result = await self.monitor_step(payment_id)
            if not self.is_monitoring(payment_id):
                break
            await asyncio.sleep(tick_interval_seconds)

        return last_result or aurev_agent.process_payment_session(payment_id)


payment_monitor = PaymentMonitor()
