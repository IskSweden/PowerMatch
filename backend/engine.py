import asyncio
from backend.curve import TargetCurve
from backend.db import Score, SessionLocal
import random

class GameEngine:
    def __init__(self, ws_manager, duration=30, loop=None):
        self.ws_manager = ws_manager
        self.duration = duration
        self.loop = loop or asyncio.get_event_loop()
        self.actual_values = [None] * duration
        self.scores = [0] * duration
        self.total_score = 0
        self.start_time = None
        self.is_running = False
        self.player_name = "Unknown"
        self.difficulty = "Medium"
        self.seed = random.randint(1000, 9999)
        self.curve = None

    def set_player_context(self, name: str, difficulty: str):
        print(f"Setting player context: {name}, Difficulty: {difficulty}")
        self.player_name = name
        self.difficulty = difficulty

    def start(self):
        if self.is_running:
            print("Game already running.")
            return

        self.seed = random.randint(1000, 9999)
        self.curve = TargetCurve(seed=self.seed, difficulty=self.difficulty)
        self.curve.generate()

        print(f"Generated curve for seed {self.seed}:")
        print(self.curve.values)
        print("-" * 60)

        print(f"Game started for {self.player_name} on {self.difficulty} (seed {self.seed})")

        self.start_time = self.loop.time()
        self.is_running = True
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

            tolerance = self._get_tolerance(second)
            score = self._calculate_score(actual, target, tolerance)

            self.scores[second] = score
            self.total_score += score

            await self.ws_manager.broadcast({
                "gameTick": {
                    "second": second,
                    "actual": actual,
                    "target": target,
                    "tolerance": tolerance,
                    "tickScore": score,
                    "totalScore": round(self.total_score, 1)
                }
            })

        await self.ws_manager.broadcast({
            "gameEnd": {
                "totalScore": round(self.total_score, 1),
                "actual": self.actual_values,
                "targetCurve": self.curve.values,
                "seed": self.seed,
                "difficulty": self.difficulty,
                "player": self.player_name
            }
        })
        self._save_score()


    def _calculate_score(self, actual, target, tolerance):
        if actual is None or target is None:
            return 0.0

        error = abs(actual - target)

        # ✅ Allow perfect score when both are zero
        if error == 0:
            multiplier = {
                "Easy": 1.0,
                "Medium": 1.5,
                "Hard": 2.0
            }.get(self.difficulty, 1.5)
            return round(1.0 * multiplier, 1)

        if error > tolerance or tolerance <= 0:
            return 0.0

        base_score = 1.0 - (error / tolerance)
        multiplier = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.0
        }.get(self.difficulty, 1.5)
        print(f"[TICK SCORE] Actual={actual}, Target={target}, Tolerance={tolerance} → Score={base_score * multiplier}")
        return round(base_score * multiplier, 1)


    def _get_tolerance(self, tick):
        tolerance_range = {
            "Easy": (12, 8),
            "Medium": (10, 6),
            "Hard": (8, 5)
        }
        start_tol, end_tol = tolerance_range.get(self.difficulty, (10, 6))
        progress = tick / (self.duration - 1)
        return round(start_tol + (end_tol - start_tol) * progress, 2)

    def get_curve_preview(self):
        if not self.curve:
            self.seed = random.randint(1000, 9999)
            self.curve = TargetCurve(seed=self.seed, difficulty=self.difficulty)
            self.curve.generate()

        target = self.curve.values
        tolerance = [self._get_tolerance(tick) for tick in range(self.duration)]
        return target, tolerance


    def _save_score(self):
        db = SessionLocal()
        print(f"Saving score for {self.player_name}: {round(self.total_score, 1)} ({self.difficulty}, seed {self.seed})")
        db_score = Score(
            name=self.player_name,
            difficulty=self.difficulty,
            score=round(self.total_score, 1),
            seed=self.seed
        )
        db.add(db_score)
        db.commit()
        db.close()
