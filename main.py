from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from mqtt_receiver import MQTTReceiver
import asyncio
from asyncio import get_event_loop

app = FastAPI()
loop = asyncio.get_event_loop()
clients = []

html = """
<!DOCTYPE html>
<html>
<head>
  <title>MQTT WebSocket Chart</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<h2>Live MQTT Data</h2>
<canvas id="chart" width="600" height="400"></canvas>
<script>
  const ctx = document.getElementById('chart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'MQTT Data',
        data: [],
        borderColor: 'blue',
        fill: false
      }]
    },
    options: {
      animation: false,
      scales: {
        x: { display: true },
        y: { display: true }
      }
    }
  });

  const ws = new WebSocket("ws://localhost:8000/ws");
  ws.onmessage = function(event) {
    const value = parseFloat(event.data);
    const time = new Date().toLocaleTimeString();
    chart.data.labels.push(time);
    chart.data.datasets[0].data.push(value);
    if (chart.data.labels.length > 20) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }
    chart.update();
  };
</script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)

async def broadcast_message(message: str):
    for ws in clients:
        try:
            await ws.send_text(message)
        except:
            pass  # in production, handle disconnected clients

# MQTT Handler
mqtt = MQTTReceiver(topic="your/topic")

def mqtt_callback(msg: str):
    asyncio.run_coroutine_threadsafe(broadcast_message(msg), loop)

mqtt.set_callback(mqtt_callback)
mqtt.start()
