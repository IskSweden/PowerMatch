from fastapi import FastAPI, WebSocket, WebSocketDisconnect # <--- ADDED WebSocket, WebSocketDisconnect
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
        allow_origins=["*"], # Your original setting, kept as requested
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    assets_dir = os.path.join(dist_dir, "assets")

    # ✅ Mount only static /assets
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # --- START: Debugging WebSocket Endpoint Addition ---
    # This is a temporary endpoint to test general WebSocket connectivity.
    @app.websocket("/ws_test")
    async def websocket_test(websocket: WebSocket):
        print("[DEBUG] /ws_test connected!") # Server-side debug print
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                print(f"[DEBUG] Received on /ws_test: {data}") # Server-side debug print
                await websocket.send_text(f"Echo from /ws_test: {data}")
        except WebSocketDisconnect: # Catch a normal disconnect
            print("[DEBUG] /ws_test disconnected.") # Server-side debug print
        except Exception as e: # Catch any other errors
            print(f"[DEBUG] /ws_test error: {e}") # Server-side debug print
    # --- END: Debugging WebSocket Endpoint Addition ---

    # ✅ Catch all unmatched routes and serve index.html manually
    @app.get("/{path_name:path}")
    async def catch_all(path_name: str):
        file_path = os.path.join(dist_dir, "index.html")
        return FileResponse(file_path)

    return app