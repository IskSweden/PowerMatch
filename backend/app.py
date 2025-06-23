import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .db import init_db
from .routes import game_ws, highscores
from .mqtt_input import MQTTInputHandler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init database
    init_db()

    # Start MQTT
    loop = asyncio.get_event_loop()
    mqtt = MQTTInputHandler(loop)
    mqtt.start()

    print("🚀 App startup complete")
    yield
    print("👋 App shutdown")

def create_app():
    app = FastAPI(lifespan=lifespan)

    # Routers
    app.include_router(game_ws.router)
    app.include_router(highscores.router)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Frontend build
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

    return app
