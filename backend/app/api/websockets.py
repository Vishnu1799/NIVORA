from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # payment-specific connections: transaction_id -> list of websockets
        self.payment_connections: Dict[str, List[WebSocket]] = {}
        # AUREV dashboard connections
        self.aurev_connections: List[WebSocket] = []

    async def connect_payment(self, websocket: WebSocket, transaction_id: str):
        await websocket.accept()
        if transaction_id not in self.payment_connections:
            self.payment_connections[transaction_id] = []
        self.payment_connections[transaction_id].append(websocket)

    async def connect_aurev(self, websocket: WebSocket):
        await websocket.accept()
        self.aurev_connections.append(websocket)

    def disconnect_payment(self, websocket: WebSocket, transaction_id: str):
        if transaction_id in self.payment_connections:
            try:
                self.payment_connections[transaction_id].remove(websocket)
            except ValueError:
                pass

    def disconnect_aurev(self, websocket: WebSocket):
        try:
            self.aurev_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast_to_payment(self, transaction_id: str, data: dict):
        connections = self.payment_connections.get(transaction_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_payment(ws, transaction_id)

    async def broadcast_to_aurev(self, data: dict):
        dead = []
        for ws in self.aurev_connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_aurev(ws)


manager = ConnectionManager()


async def broadcast_payment_event(transaction_id: str, event: dict):
    """Called by payment service to broadcast events to all listeners."""
    await manager.broadcast_to_payment(transaction_id, event)
    await manager.broadcast_to_aurev({"transaction_id": transaction_id, **event})
