import paho.mqtt.client as mqtt
import asyncio
import json

# Shared queue for real-time power input
input_queue = asyncio.Queue()

class MQTTInputHandler:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.broker = "raspberrypi.local"  # Change to correct MQTT broker address
        self.topic = "/Strommessung_PowerMatch/events/rpc" # Change to correct MQTT topic
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
            params = payload.get("params", {})
            em_data = params.get("em:0", {})
            watt_value = em_data.get("c_aprt_power")

            if watt_value is not None:
                self.loop.call_soon_threadsafe(
                    asyncio.create_task, input_queue.put(watt_value)
                )
                print(f"[MQTT] Queued power: {watt_value}W")
            else:
                print("[MQTT] Wattage key not found in reader_data.")

        except Exception as e:
            print(f"[MQTT] Failed to parse message: {e}")



async def clear_input_queue():
    cleared = 0
    while not input_queue.empty():
        try:
            input_queue.get_nowait()
            cleared += 1
        except asyncio.QueueEmpty:
            break
    print(f"[MQTT] Cleared {cleared} old input(s) from queue.")
