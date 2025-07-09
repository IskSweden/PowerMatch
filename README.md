# PowerMatch

PowerMatch is a real-time energy game where players try to match their live power output to a shifting target curve. It can run entirely on a Raspberry Pi, with a FastAPI backend and a Vue 3 frontend served directly by the backend.

---

## Summary

- 30-second game session
- Realtime power input via MQTT
- FastAPI backend with WebSocket updates
- Vue 3 frontend (auto-served)
- Works on Raspberry Pi and other micro-pc environments with HDMI output

---

## Requirements

- Python 3.11+
- pip
- virtualenv
- Git
- (Optional) MQTT broker like Mosquitto
- Node.js + npm (only if developing frontend)


---

## Installation of the Package

### 1. Quick install without code download

```bash
python3 -m venv powermatch-venv
source powermatch-venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir git+https://github.com/IskSweden/PowerMatch.git@v1.0.0
```

### 2. Download and Install the Package from Github

```bash
git clone https://github.com/IskSweden/PowerMatch.git
cd PowerMatch
python3 -m venv powermatch-venv
source powermatch-venv/bin/activate
pip install --upgrade pip
pip install .

```

### 3. Run the game server with served frontend

```bash
powermatch
```

Then open http://localhost:8000 to play the game.

---

## MQTT broker

This game requires input via MQTT Wattage readings. If you already have a MQTT Broker somewhere, configure it correctly: [MQTT broker and topic configuration](#mqtt-topic--broker-config)

### Install Mosquitto (Optional)

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

To run it:
```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Test its working:
```bash
sudo systemctl status mosquitto
mosquitto_pub -t {your/topic} -m 50
```

For more check out:
[mosquitto.org](https://mosquitto.org/)


### MQTT Topic & Broker config

The MQTT Topic and broker connection details are configured in
```bash
#file
powermatch/mqtt_input.py

#Configs:
self.broker = "raspberrypi.local"                               # Change to correct MQTT broker address
self.topic = "/eniwa/energy/device/1091A8AB9138/status/evt"     # Change to correct MQTT topic
```

---

## File structure 
<pre>
PowerMatch/
├── powermatch/
│   ├── app.py          # FastAPI app + static serving
│   ├── cli.py          # CLI entry point
│   ├── db.py           # Score database logic
│   ├── engine.py       # Game engine
│   ├── mqtt_input.py   # MQTT listener
│   ├── ws.py           # WebSocket endpoint
│   ├── highscores.py   # Highscore API route
│   ├── score.py        # Score model
│   └── frontend/
│       └── dist/       # Built Vue frontend (index.html + assets/)
├── frontend/           # Vue 3 app (source for dev)
├── setup.py            # Pip install config
├── MANIFEST.in         # Package static files
└── README.md           # This file
</pre>
---

## Author

Made by Isak Skoog.
Contact:
[skoog.isak@gmail.com](mailto:skoog.isak@gmail.com)

## License

MIT LICENSE - free to use, modify and share