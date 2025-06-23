import random
import asyncio
from ..mqtt_input import input_queue

class GameEngine:
    def __init__(self, name, difficulty, input_source=None):
        self.name = name
        self.difficulty = difficulty
        self.seed = random.randint(1000, 9999)
        self.target_curve = self.generate_curve()
        self.tolerance_curve = self.generate_tolerance()
        self.total_score = 0
        self.input_queue = input_source or input_queue

    def generate_curve(self):
        random.seed(self.seed)
        return [random.randint(10, 125) for _ in range(30)]

    def generate_tolerance(self):
        return [10 for _ in range(30)]

    def get_curve_preview(self):
        return self.target_curve, self.tolerance_curve

    async def run(self):
        last_known = 0.0

        for t in range(30):
            try:
                actual = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
                last_known = actual
            except asyncio.TimeoutError:
                actual = last_known

            tick_score = max(0, 100 - abs(self.target_curve[t] - actual))
            self.total_score += tick_score

            yield {
                "actual": actual,
                "tickScore": tick_score,
                "totalScore": self.total_score
            }
