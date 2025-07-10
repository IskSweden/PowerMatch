# backend/services/game_runner.py
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from . engine import GameEngine
from . db import SessionLocal
from . score import Score
from datetime import datetime, timezone
import traceback
from . mqtt_input import input_queue # Import the shared queue

class GameRunner:
    def __init__(self, name, difficulty, websocket, ws_manager):
        self.name = name
        self.difficulty = difficulty
        self.websocket = websocket
        self.ws_manager = ws_manager
        print(f"[GAME_RUNNER_INIT] GameRunner initialized for {name} ({difficulty})") # Added debug

    async def run_game_session(self):
        print(f"[GAME_SESSION_START] Starting game session for {self.name}") # Added debug
        engine = GameEngine(name=self.name, difficulty=self.difficulty, input_source=input_queue)
        target, tolerance = engine.get_curve_preview()
        start_time = datetime.now(timezone.utc).timestamp()
        print("[WS] Sending INIT to frontend")

        await self.websocket.send_json({
            "type": "init",
            "targetCurve": target,
            "toleranceCurve": tolerance,
            "difficulty": self.difficulty,
            "seed": engine.seed,
            "duration": len(target),
            #"start_time": start_time frontend sets this
        })

        print("[WS] Waiting for 'start' signal from frontend...")
        start_received = False
        while not start_received:
            try:
                message = await self.websocket.receive_json()
                if message.get("type") == "start":
                    print("[WS] Received 'start' signal. Commencing game ticks.")
                    start_received = True
                else:
                    print(f"[WS] Received unexpected message type during wait for start: {message.get('type')}. Ignoring.")
            except WebSocketDisconnect:
                print(f"[WS_DISCONNECT] WebSocket disconnected while waiting for 'start' for {self.name}.")
                return # Exit the session if disconnected
            except Exception as e:
                print(f"[WS_ERROR] Error receiving message while waiting for 'start': {e}")
                traceback.print_exc()
                return # Exit the session on error

        print("[WS] Started game loop (expecting ticks...)") # Added debug

        try: # Wrap the game loop in a try-except to catch errors within it
            async for tick in engine.run():
                print(f"[GAME_RUNNER_RECEIVED] Received tick from engine: {tick}") # DEBUG

                await self.websocket.send_json({
                    "type": "tick",
                    "tickNumber": tick["tickNumber"],
                    "actual": tick["actual"],
                    "totalScore": tick["totalScore"]
                })
        except Exception as e:
            print(f"[GAME_LOOP_ERROR] An error occurred during the game loop: {e}")
            traceback.print_exc()
            # Decide how to handle this - perhaps send an error message to frontend
        
        print("[GAME_SESSION_END] Game loop finished or interrupted. Attempting to send END message.") # Added debug
        await self.websocket.send_json({"type": "end", "score": engine.total_score})
        print(f"[GAME_SESSION_END] END message sent. Final score: {engine.total_score}") # Added debug


        # Debugging output for DB save flow
        print(f"[DB_FLOW] Game session for {self.name} ended. Proceeding to save score.")
        print(f"[DB_FLOW] Final calculated score: {engine.total_score}") # Ensure score is not zero

        # Save result to DB
        db = SessionLocal()
        try:
            print("[DB_FLOW] Database session created.")
            score_entry = Score(
                name=self.name,
                score=engine.total_score,
                difficulty=self.difficulty,
                seed=engine.seed,
                # timestamp will be set automatically by SQLAlchemy if not provided,
                # or ensure your model handles it
            )
            db.add(score_entry)
            print("[DB_FLOW] Score entry added to session.")
            db.commit()
            print("[DB_SAVE_STATUS] Successfully saved score to database!") # Clear success message
        except Exception as e:
            db.rollback() # Important: rollback the session on error
            print(f"[DB_SAVE_STATUS] DB SAVE FAILED for {self.name}: {e}") # Clear failure message
            print(f"[DB_SAVE_STATUS] Full traceback for the DB error:")
            traceback.print_exc() # Print full traceback for precise error
        finally:
            db.close()
            print("[DB_FLOW] Database session closed.")
            print("[GAME_RUNNER_EXIT] GameRunner run_game_session completed.") # Added debug