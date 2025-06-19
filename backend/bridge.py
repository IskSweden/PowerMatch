import asyncio
import json
from backend.mqtt import MQTTReceiver
from backend.websocket_manager import WebSocketManager
from backend.engine import GameEngine

class PowerDataBridge:
    from backend.db import Score, SessionLocal
    def __init__(self, mqtt_topic: str, ws_manager: WebSocketManager, loop=None):
        self.ws_manager = ws_manager
        self.loop = loop or asyncio.get_event_loop()
        self.engine = GameEngine(ws_manager, loop=self.loop)
        self.mqtt = MQTTReceiver(topic=mqtt_topic)
        self.mqtt.set_callback(self._handle_mqtt_message)

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
                    self.engine.register_wattage(value)
                    break
        except Exception as e:
            print(f"Failed to parse MQTT message: {e}")

