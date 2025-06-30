import paho.mqtt.client as mqtt
import asyncio
import json

# Shared queue for real-time power input
input_queue = asyncio.Queue()

class MQTTInputHandler:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.broker = "raspberrypi.local"  # Change to correct MQTT broker address
        self.topic = "/eniwa/energy/device/1091A8AB9138/status/evt" # Change to correct MQTT topic
        self.client = mqtt.Client()
        self.loop = loop  # store loop explicitly

    def start(self):
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.broker, 1883, 60)
        self.client.loop_start()
        print(f"MQTT connecting to {self.broker} and subscribing to {self.topic}")

    def _on_connect(self, client, userdata, flags, rc):
        print("✅ MQTT connected")
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        #print(f"[MQTT] Received message on topic {msg.topic}: {msg.payload.decode()}") debugging

        try:
            payload = json.loads(msg.payload.decode())
            reader_data = payload.get("reader_data", [])
            watt_value = None
            for item in reader_data:
                if "1-0:1.7.0.255" in item:
                    watt_value = float(item["1-0:1.7.0.255"])
                    watt_value = watt_value * 1000 # kw to W
                    break

            if watt_value is not None:
                self.loop.call_soon_threadsafe(
                    asyncio.create_task, input_queue.put(watt_value)
                )
                print(f"[MQTT] Queued power: {watt_value}W")
            else:
                print("[MQTT] ⚠️ Wattage key not found in reader_data.")

        except Exception as e:
            print(f"[MQTT] Failed to parse message: {e}")
