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

        delta_ranges = {
            "Easy": (15, 30),
            "Medium": (25, 45),
            "Hard": (35, 60)
        }
        min_delta, max_delta = delta_ranges.get(self.difficulty, (25, 45))

        # Start with a stable 3-tick flat segment
        stable_value = int(round(random.uniform(20, 60) / 5.0) * 5)
        self.values.extend([stable_value] * 3)
        current = stable_value
        tick = 3

        while tick < self.duration:
            cluster_length = min(random.choice([2, 3]), self.duration - tick)
            progress = tick / (self.duration - 1)
            max_step = min_delta + (max_delta - min_delta) * progress

            for _ in range(10):  # ensure a meaningful jump
                step = random.choice([-1, 1]) * random.uniform(min_delta, max_step)
                new_value = int(round(max(0, min(135, current + step)) / 5.0) * 5)
                if abs(new_value - current) >= min_delta:
                    break

            for _ in range(cluster_length):
                self.values.append(new_value)
                tick += 1
                if tick >= self.duration:
                    break

            current = new_value

        self._enforce_range_requirements()




    def _enforce_range_requirements(self):
        has_low = any(val <= 20 for val in self.values)
        has_high = any(val >= 120 for val in self.values)

        indices = list(range(len(self.values)))

        if not has_low:
            for _ in range(2):
                insert_at = random.choice(indices[:10])  # early in the curve
                self.values[insert_at] = random.randint(5, 20)

        if not has_high:
            for _ in range(2):
                insert_at = random.choice(indices[-10:])  # later in the curve
                self.values[insert_at] = random.randint(120, 135)

    def get(self, second: int):
        if 0 <= second < len(self.values):
            return self.values[second]
        return None
