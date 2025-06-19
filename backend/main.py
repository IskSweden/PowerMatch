import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.bridge import PowerDataBridge
from backend.websocket_manager import WebSocketManager

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded absolute path to frontend build
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

# Setup game engine + MQTT
ws_manager = WebSocketManager()
loop = asyncio.get_event_loop()
bridge = PowerDataBridge("/eniwa/energy/device/1091A8AAAA28/status/evt", ws_manager, loop=loop)
bridge.start()

@app.websocket("/ws/game")
async def game_socket(websocket: WebSocket):
    print("🔌 WebSocket connected at /ws/game")
    await ws_manager.connect(websocket)
    bridge.start_game()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Mount static assets at /
app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")


# Catch-all: send index.html for Vue router paths like /game
@app.get("/{full_path:path}")
async def serve_vue(full_path: str):
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

