import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.bridge import PowerDataBridge
from backend.websocket_manager import WebSocketManager
from backend.db import init_db

# Initialize the database
init_db()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend build output
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

# WebSocket + game engine setup
ws_manager = WebSocketManager()
loop = asyncio.get_event_loop()
bridge = PowerDataBridge("/eniwa/energy/device/1091A8AAAA28/status/evt", ws_manager, loop=loop)
bridge.start()

@app.websocket("/ws/game")
async def game_socket(websocket: WebSocket):
    print("WebSocket connected at /ws/game")
    await ws_manager.connect(websocket)
    try:
        message = await websocket.receive_text()
        data = json.loads(message)
        name = data.get("name", "Unknown")
        difficulty = data.get("difficulty", "Medium")
        bridge.engine.set_player_context(name, difficulty)
        bridge.engine.start()
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# ✅ These frontend paths should always return index.html
@app.get("/")
@app.get("/game")
@app.get("/end")
async def vue_routes():
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

# ✅ Mount the frontend build (must come last)
app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
