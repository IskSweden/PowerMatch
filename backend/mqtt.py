import paho.mqtt.client as mqtt

class MQTTReceiver:
    def __init__(self, topic="/eniwa/energy/device/1091A8AAAA28/status/evt"):
        self.topic = topic
        self.callback = None

    def set_callback(self, callback_func):
        self.callback = callback_func

    def on_connect(self, client, userdata, flags, rc):
        print("✅ Connected to MQTT broker")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"MQTT message received: {payload}...")  # print preview
        if self.callback:
            self.callback(payload)

    def start(self):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect("powerbuddy.duckdns.org", 1883, 60)
        client.loop_start()
