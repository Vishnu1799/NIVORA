from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websockets import manager

router = APIRouter()


@router.websocket("/ws/payments/{transaction_id}")
async def payment_ws(websocket: WebSocket, transaction_id: str):
    await manager.connect_payment(websocket, transaction_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_payment(websocket, transaction_id)
