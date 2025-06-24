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
        import random
        random.seed(self.seed)
        curve = []

        # Wattage zones
        low = lambda: random.uniform(10, 30)
        mid = lambda: random.uniform(45, 90)
        high = lambda: random.uniform(100, 135)
        zones = [low, mid, high]

        i = 0
        prev_zone = None

        while i < 30:
            duration = random.randint(2, 4)
            duration = min(duration, 30 - i)  # Don't overflow

            next_zone = random.choice([z for z in zones if z != prev_zone])
            prev_zone = next_zone
            value = round(next_zone(), 1)

            curve.extend([value] * duration)
            i += duration

        # Pad to exactly 30 ticks if undershot
        while len(curve) < 30:
            curve.append(curve[-1])

        # Force low and high values at least once
        curve[random.randint(0, 5)] = round(low(), 1)
        curve[random.randint(24, 29)] = round(high(), 1)

        print(f"Generated curve: {curve} with seed {self.seed}")
        print(f"Curve length: {len(curve)} → {curve}")
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
