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
        curve = []
        current = random.uniform(30, 100)

        for i in range(30):
            if self.difficulty == "Easy":
                step_duration = random.randint(3, 5)
                delta = random.uniform(-10, 10)
            elif self.difficulty == "Medium":
                step_duration = random.randint(2, 4)
                delta = random.uniform(-20, 20)
            else:  # Hard
                step_duration = random.randint(1, 3)
                delta = random.uniform(-40, 40)

            if i % step_duration == 0:
                current += delta

            current = max(10, min(135, current))
            curve.append(round(current, 1))

        # Force low + high coverage
        curve[random.randint(0, 5)] = round(random.uniform(10, 20), 1)
        curve[random.randint(24, 29)] = round(random.uniform(120, 135), 1)

        return curve

    def generate_tolerance(self):
        if self.difficulty == "Easy":
            return [15 for _ in range(30)]
        elif self.difficulty == "Medium":
            return [10 for _ in range(30)]
        else:  # Hard
            return [6 for _ in range(30)]

    def get_curve_preview(self):
        return self.target_curve, self.tolerance_curve

    def compute_tick_score(self, actual, target, tolerance):
        if actual is None or target is None or tolerance is None:
            return 0.0

        distance = abs(actual - target)
        if distance <= tolerance:
            base_score = 100 * (1 - (distance / tolerance))
            multiplier = {
                "Easy": 1.0,
                "Medium": 1.25,
                "Hard": 1.5
            }.get(self.difficulty, 1.0)
            return round(base_score * multiplier, 1)
        else:
            return 0.0

    async def run(self):
        last_known = 0.0

        for t in range(30):
            try:
                actual = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
                last_known = actual
            except asyncio.TimeoutError:
                actual = last_known

            target = self.target_curve[t]
            tolerance = self.tolerance_curve[t]
            tick_score = self.compute_tick_score(actual, target, tolerance)
            self.total_score += tick_score

            yield {
                "type": "tick",
                "actual": actual,
                "target": target,
                "tolerance": tolerance,
                "tickScore": tick_score,
                "totalScore": round(self.total_score, 1)
            }

        yield {
            "type": "end",
            "score": round(self.total_score, 1),
            "seed": self.seed,
            "difficulty": self.difficulty
        }
