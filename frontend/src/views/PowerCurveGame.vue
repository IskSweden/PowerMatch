<template>
  <div class="game-container">
    <h1>⚡ Power Curve</h1>
    <div class="status-bar">
      <span>⏱ Time Left: {{ timeLeft }}s</span>
      <span>📊 Score: {{ score }}</span>
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
          borderColor: 'blue',
          data: [],
          fill: false
        },
        {
          label: 'Target Power (W)',
          borderColor: 'orange',
          data: [],
          fill: false
        }
      ]
    },
    options: {
      animation: false,
      scales: {
        x: { title: { display: true, text: 'Time (s)' } },
        y: { title: { display: true, text: 'Watts' }, min: 0, max: 3000 }
      }
    }
  })

  const ws = new WebSocket("ws://localhost:8000/ws/game")

  ws.onopen = () => {
    const name = sessionStorage.getItem("playerName") || "Unknown"
    const difficulty = sessionStorage.getItem("difficulty") || "Medium"
    console.log("📤 Sending config to backend:", { name, difficulty })
    ws.send(JSON.stringify({ name, difficulty }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.gameTick) {
      const { second, actual, target, tickScore, totalScore } = data.gameTick
      timeLeft.value = 30 - second
      score.value = totalScore

      chart.data.labels.push(second)
      chart.data.datasets[0].data.push(actual || 0)
      chart.data.datasets[1].data.push(target || 0)
      chart.update()
    }

    if (data.gameEnd) {
      console.log("🎯 Game Over. Score:", data.gameEnd.totalScore)
      sessionStorage.setItem("finalScore", data.gameEnd.totalScore)
      window.location.href = "/end"
    }
  }
})
</script>

<style scoped>
.game-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: sans-serif;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}
</style>
