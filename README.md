# ⚡ PowerMatch

**PowerMatch** is a real-time, precision-based energy game where players try to match their live power output to a dynamically shifting target curve. Built with a FastAPI backend and Vue 3 frontend, the game leverages MQTT for real-world wattage input and provides responsive gameplay with live scoring.

---

## Game Concept

Over a 30-second session, the player’s real-time power input (e.g., from a connected Raspberry Pi device via MQTT) is compared every second to a target curve. Scoring is based on how closely the player's input matches the curve, with:

- **Increasing difficulty** over time (tighter tolerance, more volatility)
- **Seed-based reproducible curves** for fairness
- **No manual input required** during gameplay – just real-world power

---

## Tech Stack

- **Backend:** FastAPI + WebSockets
- **Frontend:** Vue 3 + Vite
- **Realtime Input:** MQTT
- **Database:** SQLite (score logging)
- **UI/UX:** Clean, responsive game view with a start screen and leaderboard integration (coming soon)

---

## Project Structure

```
PowerMatch/
├── backend/
│   ├── bridge.py
│   ├── curve.py
│   ├── db.py
│   ├── engine.py
│   ├── main.py
│   ├── mqtt.py
│   └── websocket_manager.py
├── frontend/
│   ├── public/
│   │   └── vite.svg
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── views/
│   │   │   ├── EndScreen.vue
│   │   │   ├── PowerCurveGame.vue
│   │   │   └── StartGame.vue
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── router.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── scores.db              # Local SQLite database for score logging
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r ../requirements.txt
uvicorn main:app --reload
```

> ✅ `requirements.txt` includes:
> - `fastapi`
> - `uvicorn`
> - `paho-mqtt`
> - `python-dotenv`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## MQTT Setup (Mosquitto Broker)

To simulate or receive real-time power data, this project uses a local [Mosquitto MQTT broker](https://mosquitto.org/).

### Install Mosquitto (Windows)

1. Download from: https://mosquitto.org/download/
2. Run the installer using default settings.
3. Note the path to `mosquitto.exe` and `mosquitto.conf`.

### Quick-Start Script (Windows Batch)

To launch everything in one go (MQTT broker + FastAPI server), use this `start_game.bat` script:

```bat
@echo off
:: Move to project root
cd /d C:\Users\skoog\Documents\PowerMatch

echo.
echo Starting Mosquitto broker...
start "" "C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Program Files\mosquitto\mosquitto.conf"

echo.
echo Starting FastAPI game server...
"C:\Users\skoog\Documents\PowerMatch\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload

pause
```

📌 This script assumes:
- Mosquitto is installed at `C:\Program Files\mosquitto\`
- Your Python virtual environment is in `.venv\`
- FastAPI runs from `backend/main.py`

---

## Gameplay Logic

- **Duration:** 30 seconds
- **Scoring:** Per-second proximity to the target curve
- **Difficulty:** Affects tolerance, volatility, and score multiplier
- **Target Curve:** Generated based on a random seed (for replayability and fairness)
- **Leaderboard:** Stores score, player ID, timestamp, seed, and difficulty

---

## Future Plans

- 🎯 Leaderboard UI
- 📊 Score analytics

---

## Author

Made by [Isak Skoog](https://github.com/IskSweden)  
Feel free to fork, contribute, or reach out!

---

## License

MIT License – free to use, modify, and distribute.