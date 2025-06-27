# backend/routes/game_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.game_runner import GameRunner
from ..managers.ws import WebSocketManager
import json

router = APIRouter()
ws_manager = WebSocketManager()

# Define the WebSocket path to include name and difficulty as path parameters
@router.websocket("/ws/game/{name}/{difficulty}")
async def game_websocket(websocket: WebSocket, name: str, difficulty: str): # <--- name and difficulty are parameters
    await ws_manager.connect(websocket)
    try:

        runner = GameRunner(name=name, difficulty=difficulty, websocket=websocket, ws_manager=ws_manager)
        await runner.run_game_session()

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {name} ({difficulty}).") # Added debug print
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error for {name} ({difficulty}): {e}") # Added debug print
        ws_manager.disconnect(websocket)

