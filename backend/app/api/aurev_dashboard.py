from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.payment import Payment, PaymentStatus, PaymentEvent
from app.api.websockets import manager
import httpx
from app.config.settings import settings

router = APIRouter(prefix="/api/aurev", tags=["aurev"])


@router.get("/metrics")
async def aurev_metrics(db: Session = Depends(get_db)):
    total = db.query(Payment).count()
    successful = db.query(Payment).filter(Payment.status == PaymentStatus.SUCCESS).count()
    recovered = db.query(Payment).filter(
        Payment.status == PaymentStatus.SUCCESS,
        Payment.recovery_attempt_count > 0,
    ).count()
    escalated = db.query(Payment).filter(Payment.status == PaymentStatus.ESCALATED).count()
    declined = db.query(Payment).filter(Payment.status == PaymentStatus.DECLINED).count()
    active = db.query(Payment).filter(
        Payment.status.in_([
            PaymentStatus.INITIATED,
            PaymentStatus.PROCESSING,
            PaymentStatus.BANK_CHECK,
            PaymentStatus.RECOVERING,
        ])
    ).count()

    # Bank health
    bank_status = "UNKNOWN"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.bank_simulator_url}/health")
            bank_status = resp.json().get("status", "UNKNOWN")
    except Exception:
        pass

    return {
        "bank_status": bank_status,
        "gateway_status": "ONLINE",
        "total_payments": total,
        "successful_payments": successful,
        "auto_recovered": recovered,
        "escalated": escalated,
        "declined": declined,
        "active_payments": active,
    }


@router.get("/events")
def aurev_events(db: Session = Depends(get_db)):
    events = db.query(PaymentEvent).order_by(PaymentEvent.created_at.desc()).limit(100).all()
    return [
        {
            "event_type": e.event_type,
            "message": e.message,
            "data": e.data,
            "payment_id": str(e.payment_id),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.websocket("/ws")
async def aurev_ws(websocket: WebSocket):
    await manager.connect_aurev(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_aurev(websocket)
