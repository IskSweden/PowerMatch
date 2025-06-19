<template>
  <div class="game-container">
    <div class="status-bar">
      <h1>⚡ PowerMatch</h1>
      <div class="status-info">
        <span>Zeit: {{ timeLeft }}s</span>
        <span>Punkte: {{ score.toFixed(1) }}</span>
      </div>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'

const timeLeft = ref(30)
const score = ref(0)
const chartCanvas = ref(null)
let chart

onMounted(() => {
  chart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Live Power (W)',
          borderColor: 'green',
          data: [],
          fill: false
        },
        {
          label: 'Target Power (W)',
          borderColor: 'orange',
          data: [],
          fill: false
        },
        {
          label: 'Upper Tolerance',
          borderColor: 'rgba(0,0,0,0.4)',
          borderDash: [4, 4],
          data: [],
          fill: false,
          pointRadius: 0
        },
        {
          label: 'Lower Tolerance',
          borderColor: 'rgba(0,0,0,0.4)',
          borderDash: [4, 4],
          data: [],
          fill: false,
          pointRadius: 0
        }
      ]
    },
    options: {
      animation: false,
      scales: {
        x: { title: { display: true, text: 'Time (s)' } },
        y: { title: { display: true, text: 'Watts' }, min: 0, max: 300 }
      }
    }
  })

  const ws = new WebSocket("ws://localhost:8000/ws/game")

  ws.onopen = () => {
    const name = sessionStorage.getItem("playerName") || "Unknown"
    const difficulty = sessionStorage.getItem("difficulty") || "Medium"
    console.log("Sending config to backend:", { name, difficulty })
    ws.send(JSON.stringify({ name, difficulty }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.gameTick) {
      const { second, actual, target, tolerance, tickScore, totalScore } = data.gameTick
      timeLeft.value = 30 - second
      score.value = totalScore

      chart.data.labels.push(second)
      // Limit to last 10 ticks
      if (chart.data.labels.length > 10) {
      chart.data.labels.shift()
      chart.data.datasets.forEach(dataset => dataset.data.shift())
      }
      chart.data.datasets[0].data.push(actual || 0)
      chart.data.datasets[1].data.push(target || 0)
      chart.data.datasets[2].data.push((target || 0) + (tolerance || 0)) // upper band
      chart.data.datasets[3].data.push((target || 0) - (tolerance || 0)) // lower band

      chart.update()
    }

    if (data.gameEnd) {
      console.log("Game Over. Score:", data.gameEnd.totalScore)
      sessionStorage.setItem("finalScore", data.gameEnd.totalScore)
      window.location.href = "/end"
    }
  }
})
</script>

<style scoped>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  background-color: #000000;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}

.game-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1rem;
  font-family: sans-serif;
  color: rgb(170, 169, 169);
  background-color: #fffdfd;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.status-bar h1 {
  margin: 0;
  font-size: 1.5rem;
}

.status-info {
  display: flex;
  gap: 1.5rem;
  font-size: 1.2rem;
}
</style>