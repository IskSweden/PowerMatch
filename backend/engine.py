import asyncio
from backend.curve import TargetCurve
from backend.db import Score, SessionLocal

class GameEngine:
    def __init__(self, ws_manager, duration=30, loop=None):
        self.ws_manager = ws_manager
        self.duration = duration
        self.loop = loop or asyncio.get_event_loop()
        self.curve = TargetCurve(duration)
        self.actual_values = [None] * duration
        self.scores = [0] * duration
        self.total_score = 0
        self.start_time = None
        self.is_running = False
        self.player_name = "Unknown"
        self.difficulty = "Medium"

    def set_player_context(self, name: str, difficulty: str):
        print(f"Setting player context: {name}, Difficulty: {difficulty}") # Debug log
        self.player_name = name
        self.difficulty = difficulty

    def start(self):
        if self.is_running:
            print("⚠️ Game already running.")
            return
        print(f"✅ Game started for {self.player_name} on {self.difficulty}")
        self.start_time = self.loop.time()
        self.is_running = True
        self.curve.generate()
        self.actual_values = [None] * self.duration
        self.scores = [0] * self.duration
        self.total_score = 0
        asyncio.create_task(self._game_loop())

    def register_wattage(self, value: float):
        if not self.is_running:
            return
        elapsed = int(self.loop.time() - self.start_time)
        if 0 <= elapsed < self.duration:
            self.actual_values[elapsed] = value

    async def _game_loop(self):
        for second in range(self.duration):
            await asyncio.sleep(1)
            actual = self.actual_values[second]
            target = self.curve.get(second)

            if actual is not None:
                score = max(0, 100 - abs(actual - target))
                self.scores[second] = round(score, 1)
                self.total_score += score

            await self.ws_manager.broadcast({
                "gameTick": {
                    "second": second,
                    "actual": actual,
                    "target": target,
                    "tickScore": self.scores[second],
                    "totalScore": round(self.total_score, 1)
                }
            })

        await self.ws_manager.broadcast({
            "gameEnd": {
                "totalScore": round(self.total_score, 1),
                "actual": self.actual_values,
                "targetCurve": self.curve.values
            }
        })

        self._save_score()
        self.is_running = False
        print("✅ Game ended and score saved.")

    def _save_score(self):
        db = SessionLocal()
        db_score = Score(
            name=self.player_name,
            difficulty=self.difficulty,
            score=self.total_score
        )
        db.add(db_score)
        db.commit()
        db.close()
