import random
import asyncio
import time
import json
import os
from . mqtt_input import input_queue

class GameEngine:
    def __init__(self, name, difficulty, input_source=None):
        self.name = name
        self.difficulty = difficulty
        self.seed = random.randint(1000, 9999)
        self.target_curve = self.load_precomputed_curve()
        self.tolerance_curve = self.generate_tolerance()
        self.total_score = 0
        self.input_queue = input_source or input_queue

    def load_precomputed_curve(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # → powermatch/
            json_path = os.path.join(base_dir, "data", "normalized_curves.json")

            with open(json_path, "r", encoding="utf-8") as f:
                all_curves = json.load(f)

            key = self.difficulty.lower()
            curve = all_curves.get(key, {}).get("curve", [])

            if not curve or len(curve) != 30:
                raise ValueError(f"Curve for '{self.difficulty}' not valid or missing.")

            print(f"Loaded curve from JSON for difficulty {self.difficulty}: {curve}")
            return curve

        except Exception as e:
            print(f"[ERROR] Could not load precomputed curve: {e}")
            return [0.0] * 30



    def generate_tolerance(self):
        if self.difficulty == "Easy":
            return [15 for _ in range(30)]
        elif self.difficulty == "Medium":
            return [10 for _ in range(30)]
        else:  # Hard
            return [6 for _ in range(30)]

        

    def get_curve_preview(self):

        print(f"Generated tolerance: {self.tolerance_curve} for difficulty {self.difficulty}")

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

            tick_start_time = time.monotonic()


            try:
                actual = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
                last_known = actual
            except asyncio.TimeoutError:
                actual = last_known

            target = self.target_curve[t]
            tolerance = self.tolerance_curve[t]
            tick_score = self.compute_tick_score(actual, target, tolerance)
            self.total_score += tick_score

            tick_data_to_yield = {
                "type": "tick",
                "tickNumber": t,
                "actual": actual,
                "target": target,
                "tolerance": tolerance,
                "tickScore": tick_score,
                "totalScore": round(self.total_score, 1)
            }
            print(f"[ENGINE_YIEALD_DEBUG] Yielding: {tick_data_to_yield}")  # Debug print
            yield tick_data_to_yield

            elapsed_time = time.monotonic() - tick_start_time
            sleep_time = 1.0 - elapsed_time # Calculate how much time is left to sleep
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
