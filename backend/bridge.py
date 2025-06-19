import asyncio
import json
from collections import deque
from backend.mqtt import MQTTReceiver
from backend.websocket_manager import WebSocketManager
from backend.engine import GameEngine

class PowerDataBridge:
    def __init__(self, mqtt_topic: str, ws_manager: WebSocketManager, loop=None):
        self.ws_manager = ws_manager
        self.loop = loop or asyncio.get_event_loop()
        self.engine = GameEngine(ws_manager, loop=self.loop)

        # MQTT setup
        self.mqtt = MQTTReceiver(topic=mqtt_topic)
        self.mqtt.set_callback(self._handle_mqtt_message)

        # Buffer of recent MQTT wattage values
        self.input_buffer = deque(maxlen=5)  # configurable: 3–5 values

    def start(self):
        self.mqtt.start()

    def start_game(self):
        self.engine.start()

    def _handle_mqtt_message(self, message: str):
        try:
            data = json.loads(message)
            for item in data.get("reader_data", []):
                if "1-0:1.7.0.255" in item:
                    value = item["1-0:1.7.0.255"]
                    if isinstance(value, (int, float)):
                        self._process_input(value)
                    break
        except Exception as e:
            print(f"❌ Failed to parse MQTT message: {e}")

    def _process_input(self, value: float):
        # Clamp to valid range
        value = max(0.0, min(135.0, value))

        # Add to buffer
        self.input_buffer.append(value)

        # Compute short-term average
        smoothed = round(sum(self.input_buffer) / len(self.input_buffer), 2)

        # Forward to engine
        self.engine.register_wattage(smoothed)
