from typing import List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        print("WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)
        print("WebSocket disconnected")

    async def broadcast(self, message: str):
        for conn in self.connections:
            await conn.send_text(message)
