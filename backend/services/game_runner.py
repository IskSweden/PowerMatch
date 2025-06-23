import asyncio
from ..core.engine import GameEngine
from ..db import SessionLocal
from ..models.score import Score
from datetime import datetime, timezone

class GameRunner:
    def __init__(self, name, difficulty, websocket, ws_manager):
        self.name = name
        self.difficulty = difficulty
        self.websocket = websocket
        self.ws_manager = ws_manager

    async def run_game_session(self):
        engine = GameEngine(name=self.name, difficulty=self.difficulty)
        target, tolerance = engine.get_curve_preview()
        start_time = datetime.now(timezone.utc).timestamp()

        await self.websocket.send_json({
            "type": "init",
            "targetCurve": target,
            "toleranceCurve": tolerance,
            "difficulty": self.difficulty,
            "seed": engine.seed,
            "duration": len(target),
            "start_time": start_time
        })

        async for tick in engine.run():
            await asyncio.sleep(1)
            await self.websocket.send_json({
                "type": "tick",
                "actual": tick["actual"],
                "totalScore": tick["totalScore"]
            })

        await self.websocket.send_json({"type": "end", "score": engine.total_score})

        # Save result to DB
        db = SessionLocal()
        score_entry = Score(
            name=self.name,
            score=engine.total_score,
            difficulty=self.difficulty,
            seed=engine.seed
        )
        db.add(score_entry)
        db.commit()
        db.close()
