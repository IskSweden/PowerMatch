import os
import asyncio
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import APIRouter
from backend.bridge import PowerDataBridge
from backend.websocket_manager import WebSocketManager
from backend.db import init_db
from backend.db import Score, SessionLocal
from datetime import datetime, timedelta, timezone

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

from datetime import datetime

# ...existing code...

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

        # Generate preview BEFORE starting game
        target, tolerance = bridge.engine.get_curve_preview()

        # Add start_time (UTC timestamp)
        start_time = datetime.now(timezone.utc).timestamp()

        await websocket.send_json({
            "type": "init",
            "targetCurve": target,
            "toleranceCurve": tolerance,
            "difficulty": difficulty,
            "seed": bridge.engine.seed,
            "duration": len(target),
            "start_time": start_time   # <-- add this line
        })

        bridge.engine.start()

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# ✅ These frontend paths should always return index.html
@app.get("/")
@app.get("/game")
@app.get("/end")
async def vue_routes():
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

# API router for scores
@app.get("/api/highscores")
def get_highscores():
    db = SessionLocal()
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    alltime = db.query(Score).order_by(Score.score.desc()).limit(5).all()
    recent = db.query(Score).filter(Score.timestamp >= day_ago).order_by(Score.score.desc()).limit(5).all()

    def to_dict(score):
        return {
            "name": score.name,
            "score": int(score.score)
        }

    return {
        "alltime": [to_dict(s) for s in alltime],
        "recent": [to_dict(s) for s in recent]
    }



# ✅ Mount the frontend build (must come last)
app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")


