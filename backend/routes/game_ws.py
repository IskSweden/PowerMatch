from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.game_runner import GameRunner
from ..managers.ws import WebSocketManager
import json

router = APIRouter()
ws_manager = WebSocketManager()

@router.websocket("/ws/game")
async def game_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        message = await websocket.receive_text()
        data = json.loads(message)
        name = data.get("name", "Unknown")
        difficulty = data.get("difficulty", "Medium")

        runner = GameRunner(name=name, difficulty=difficulty, websocket=websocket, ws_manager=ws_manager)
        await runner.run_game_session()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
