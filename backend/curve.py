import math
import random

class TargetCurve:
    def __init__(self, duration):
        self.duration = duration
        self.values = []

    def generate(self, base=1000, amplitude=500, noise=50, seed=None):
        seed = seed or random.randint(0, 9999)
        random.seed(seed)
        self.values = []
        for t in range(self.duration):
            x = 2 * math.pi * t / self.duration
            value = base + amplitude * math.sin(x * 2)
            value += random.uniform(-noise, noise)
            self.values.append(round(value, 2))

    def get(self, second):
        if 0 <= second < self.duration:
            return self.values[second]
        return None
