from fastapi import FastAPI, WebSocket, WebSocketDisconnect # <--- ADDED WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from pathlib import Path
from . import game_ws
from .db import init_db
from . import highscores
from .mqtt_input import MQTTInputHandler
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing database...") # Debug print
    init_db()
    print("Database initialized.") # Debug print
    loop = asyncio.get_event_loop()
    mqtt = MQTTInputHandler(loop)
    mqtt.start()
    print("MQTT handler started.") # Debug print
    yield
    # You might want to add mqtt.stop() here if your MQTTInputHandler has one
    print("Application shutdown complete.") # Debug print

def create_app():
    app = FastAPI(lifespan=lifespan)

    app.include_router(game_ws.router)
    app.include_router(highscores.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Fixed: resolve path relative to this file (inside installed powermatch package)
    base_dir = Path(__file__).parent
    dist_dir = base_dir / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    index_file = dist_dir / "index.html"

    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path_name:path}")
    async def catch_all(path_name: str):
        return FileResponse(index_file)

    return app