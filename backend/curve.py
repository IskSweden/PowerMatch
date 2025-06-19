import random

class TargetCurve:
    def __init__(self, duration=30, seed=None, difficulty="Medium"):
        self.duration = duration
        self.seed = seed or random.randint(1000, 9999)
        self.difficulty = difficulty
        self.values = []

    def generate(self):
        random.seed(self.seed)

        # Initial base value: ~30W with ±5 jitter
        base = random.uniform(25, 35)
        self.values = [round(base, 1)]

        # Difficulty volatility scaling
        volatility_map = {
            "Easy": (5, 10),
            "Medium": (10, 15),
            "Hard": (15, 20)
        }
        min_delta, max_delta = volatility_map.get(self.difficulty, (10, 15))

        for t in range(1, self.duration):
            # Linearly ramp up volatility
            progress = t / (self.duration - 1)
            max_step = min_delta + (max_delta - min_delta) * progress

            # Random walk: small positive/negative drift
            last = self.values[-1]
            delta = random.uniform(-max_step, max_step)

            next_val = max(10, min(2000, last + delta))  # clamp between 10W and 2000W
            self.values.append(round(next_val, 1))

    def get(self, second: int):
        if 0 <= second < len(self.values):
            return self.values[second]
        return None
