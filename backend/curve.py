import random

class TargetCurve:
    def __init__(self, duration=30, seed=None, difficulty="Medium"):
        self.duration = duration
        self.seed = seed or random.randint(1000, 9999)
        self.difficulty = difficulty
        self.values = []

    def generate(self):
        random.seed(self.seed)
        self.values = []

        # Difficulty-specific volatility ranges
        delta_ranges = {
            "Easy":   (6, 12),
            "Medium": (8, 15),
            "Hard":   (10, 20)
        }
        min_delta, max_delta = delta_ranges.get(self.difficulty, (8, 15))

        # Starting value
        current = int(random.uniform(20, 40))
        self.values.append(current)
        tick = 1

        while tick < self.duration:
            cluster_length = min(random.choices([2, 3, 4, 5], weights=[1, 2, 2, 1])[0], self.duration - tick)
            progress = tick / (self.duration - 1)
            current_max_delta = min_delta + (max_delta - min_delta) * progress

            # Force high jump every ~8 ticks
            if tick % 8 == 0 and random.random() < 0.6:
                current_max_delta *= random.uniform(1.5, 2.0)

            step = random.choice([-1, 1]) * random.uniform(min_delta, current_max_delta)

            if abs(step) < 2:
                step = 2.0 * (1 if step > 0 else -1)

            new_value = max(0, min(135, current + step))
            new_value = int(round(new_value))

            for _ in range(cluster_length):
                self.values.append(new_value)
                tick += 1
                if tick >= self.duration:
                    break

            current = new_value

        # Force range coverage
        self._enforce_range_requirements()

    def _enforce_range_requirements(self):
        has_low = any(val <= 20 for val in self.values)
        has_high = any(val >= 120 for val in self.values)

        indices = list(range(len(self.values)))

        if not has_low:
            insert_at = random.choice(indices[:10])  # early in the curve
            self.values[insert_at] = random.randint(0, 15)

        if not has_high:
            insert_at = random.choice(indices[-10:])  # later in the curve
            self.values[insert_at] = random.randint(125, 135)

    def get(self, second: int):
        if 0 <= second < len(self.values):
            return self.values[second]
        return None
