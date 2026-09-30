"""
Recovery Permit Manager.
Provides cryptographically secure single-use authorization tokens for payment retries.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from config.settings import settings
from memory.payment_memory import payment_memory
from models.decisions import RecoveryPermit
from models.enums import PermitStatus, EventType
from memory.event_timeline import timeline_store


class RecoveryPermitManager:
    @staticmethod
    def create_permit(payment_id: str, order_id: str, amount: float, reason: str) -> RecoveryPermit:
        now = datetime.now(timezone.utc)
        permit = RecoveryPermit(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            reason=reason,
            created_at=now,
            expires_at=now + timedelta(seconds=settings.RECOVERY_PERMIT_TTL_SECONDS),
            single_use=True,
            status=PermitStatus.ACTIVE
        )
        payment_memory.store_permit(permit)
        timeline_store.record_event(
            payment_id=payment_id,
            order_id=order_id,
            event_type=EventType.RECOVERY_PERMIT_ISSUED,
            source="recovery_permit_manager",
            status="ISSUED",
            metadata={"permit_id": permit.permit_id, "expires_at": permit.expires_at.isoformat()}
        )
        return permit

    @staticmethod
    def validate_and_consume(
        permit_id: str,
        payment_id: str,
        order_id: str,
        amount: float
    ) -> Tuple[bool, str]:
        permit = payment_memory.get_permit(permit_id)
        if not permit:
            return False, f"Permit '{permit_id}' not found."

        if permit.status == PermitStatus.USED:
            return False, f"Permit '{permit_id}' has already been consumed (single-use violated)."

        if permit.status == PermitStatus.REVOKED:
            return False, f"Permit '{permit_id}' was revoked due to conflicting evidence."

        now = datetime.now(timezone.utc)
        exp = permit.expires_at if permit.expires_at.tzinfo else permit.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            permit.status = PermitStatus.EXPIRED
            return False, f"Permit '{permit_id}' has expired."

        if permit.order_id != order_id or abs(permit.amount - amount) > 0.01:
            return False, f"Permit '{permit_id}' does not match order '{order_id}' or amount '{amount}'."

        # Mark as used
        permit.status = PermitStatus.USED
        permit.used_at = now
        timeline_store.record_event(
            payment_id=payment_id,
            order_id=order_id,
            event_type=EventType.RECOVERY_PERMIT_USED,
            source="recovery_permit_manager",
            status="CONSUMED",
            metadata={"permit_id": permit.permit_id}
        )
        return True, "Permit successfully validated and consumed."

    @staticmethod
    def revoke_permit(permit_id: str, reason: str):
        permit = payment_memory.get_permit(permit_id)
        if permit and permit.status == PermitStatus.ACTIVE:
            permit.status = PermitStatus.REVOKED
            timeline_store.record_event(
                payment_id=permit.payment_id,
                order_id=permit.order_id,
                event_type=EventType.RECOVERY_PERMIT_REVOKED,
                source="recovery_permit_manager",
                status="REVOKED",
                metadata={"permit_id": permit.permit_id, "reason": reason}
            )
