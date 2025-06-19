from typing import List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        print("🌐 WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
            print("❌ WebSocket disconnected")

    async def broadcast(self, message: dict):
        for conn in self.connections:
            try:
                await conn.send_json(message)
            except Exception as e:
                print(f"WebSocket error: {e}")
