from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from .db import init_db
from .routes import game_ws, highscores
from .mqtt_input import MQTTInputHandler
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    loop = asyncio.get_event_loop()
    mqtt = MQTTInputHandler(loop)
    mqtt.start()
    yield

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

    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    assets_dir = os.path.join(dist_dir, "assets")

    # ✅ Mount only static /assets
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # ✅ Catch all unmatched routes and serve index.html manually
    @app.get("/{path_name:path}")
    async def catch_all(path_name: str):
        file_path = os.path.join(dist_dir, "index.html")
        return FileResponse(file_path)

    return app
