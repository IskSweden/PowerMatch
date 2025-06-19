import asyncio
from backend.curve import TargetCurve

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

    def start(self):
        if self.is_running:
            print("Game already running.")
            return
        print("✅ Game started.")
        self.start_time = self.loop.time()
        self.is_running = True
        self.curve.generate()  # new curve each round
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

        self.is_running = False
        print("Game ended.")
