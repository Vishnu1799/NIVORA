"""
Global mutable state for the bank simulator.
Controls service behavior for demo scenarios.
"""
import random
from typing import Optional
from datetime import datetime

class BankState:
    def __init__(self):
        self.service_state = "UP"  # UP, DOWN, TIMEOUT, DEGRADED, INSUFFICIENT_FUNDS, INVALID_DETAILS, UNKNOWN
        self.failure_rate = 0.0    # 0.0 to 1.0 — random failure rate when UP
        self.force_outcome = None  # Persistent or forced outcome
        self.response_delay_ms = 0 # Additional delay in ms
        self.transactions: dict = {}  # transaction_id -> transaction record
        self.state_changed_at = datetime.utcnow()

    def set_state(self, state: str, failure_rate: float = 0.0,
                  force_outcome: Optional[str] = None, response_delay_ms: int = 0):
        self.service_state = state
        self.failure_rate = failure_rate
        self.force_outcome = force_outcome
        self.response_delay_ms = response_delay_ms
        self.state_changed_at = datetime.utcnow()

    def should_fail_randomly(self) -> bool:
        return random.random() < self.failure_rate

    def get_latency_ms(self) -> int:
        base = {
            "UP": random.randint(80, 250),
            "DEGRADED": random.randint(2000, 3500),
            "TIMEOUT": random.randint(5000, 7000),
            "DOWN": 0,
            "INSUFFICIENT_FUNDS": random.randint(100, 300),
            "INVALID_DETAILS": random.randint(100, 300),
            "UNKNOWN": random.randint(500, 1500),
        }.get(self.service_state, 200)
        return base + self.response_delay_ms


bank_state = BankState()
