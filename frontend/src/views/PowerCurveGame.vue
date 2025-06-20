<template>
  <div v-if="loading" class="loading">Loading game...</div>
  <div v-else class="game-container">
    <div class="status-bar">
      <h1>⚡ PowerMatch</h1>
      <div class="status-info">
        <span>⏱ {{ Math.max(0, Math.ceil(duration - gameTime)).toString().padStart(2, '0') }}s</span>
        <span>🏆 {{ score.toFixed(1) }}</span>
      </div>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'
import { useRouter } from 'vue-router'

Chart.register(annotationPlugin)

const router = useRouter()
const chartCanvas = ref(null)

const duration = 30
const scrollWindow = 10
const score = ref(0)
const gameTime = ref(0)
const loading = ref(true)

let chart
let isRunning = false
let targetCurve = []
let toleranceCurve = []
let currentActual = 0

let interpolatedTarget = []
let interpolatedLower = []
let interpolatedUpper = []
let backendStartTime = null
let ws = null

function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val))
}

function interpolateCurve(raw, stepsPerSecond = 60) {
  const interpolated = []
  for (let i = 0; i < raw.length - 1; i++) {
    const y0 = raw[i]
    const y1 = raw[i + 1]
    for (let j = 0; j < stepsPerSecond; j++) {
      const t = j / stepsPerSecond
      interpolated.push((1 - t) * y0 + t * y1)
    }
  }

  // Patch: add tail for smoother rendering at the end
  const lastY = raw[raw.length - 1]
  for (let j = 1; j <= 5; j++) {
    interpolated.push(lastY)
  }

  return interpolated
}

onMounted(() => {
  const name = sessionStorage.getItem("playerName")
  const difficulty = sessionStorage.getItem("difficulty")

  if (!name || !difficulty) {
    router.push('/start')
    return
  }

  if (ws) {
    ws.close()
    ws = null
  }

  ws = new WebSocket("ws://localhost:8000/ws/game")

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: "start", name, difficulty }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === "init") {
      targetCurve = data.targetCurve
      toleranceCurve = data.toleranceCurve
      backendStartTime = data.start_time

      interpolatedTarget = interpolateCurve(targetCurve)
      interpolatedLower = interpolateCurve(targetCurve.map((v, i) => Math.max(0, v - toleranceCurve[i])))
      interpolatedUpper = interpolateCurve(targetCurve.map((v, i) => v + toleranceCurve[i]))

      isRunning = true
      loading.value = false
      nextTick(() => {
        setupChart()
        requestAnimationFrame(renderLoop)
      })
    }

    if (data.gameTick) {
      currentActual = data.gameTick.actual ?? 0
      score.value = data.gameTick.totalScore
    }

    if (data.gameEnd) {
      isRunning = false
      sessionStorage.setItem("finalScore", data.gameEnd.totalScore)
      setTimeout(() => router.push('/end'), 1500)
    }
  }

  ws.onerror = () => {
    loading.value = false
    alert("WebSocket error. Please refresh.")
  }
})

onBeforeUnmount(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})

function getSyncedGameTime() {
  if (!backendStartTime) return 0
  const now = Date.now() / 1000
  return clamp(now - backendStartTime, 0, duration)
}

function setupChart() {
  chart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      datasets: [
        {
          label: 'Input',
          borderColor: 'limegreen',
          data: [],
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0.3
        },
        {
          label: 'Target',
          borderColor: 'orange',
          data: [],
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0.3
        },
        {
          label: 'Lower Tolerance',
          borderColor: 'rgba(0,0,0,0)',
          data: [],
          fill: false,
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0.3
        },
        {
          label: 'Upper Tolerance',
          backgroundColor: 'rgba(255,165,0,0.25)',
          borderColor: 'rgba(0,0,0,0)',
          data: [],
          fill: '-1',
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0.3
        }
      ]
    },
    options: {
      animation: false,
      scales: {
        x: {
          type: 'linear',
          title: { display: true, text: 'Time (s)' },
          ticks: { color: 'green' }
        },
        y: {
          min: 0,
          max: 135,
          title: { display: true, text: 'Watts' },
          ticks: { color: 'green' }
        }
      },
      plugins: {
        legend: { labels: { color: 'green' } },
        annotation: { annotations: {} }
      }
    }
  })
}

function renderLoop() {
  if (!isRunning) return

  const now = getSyncedGameTime()
  gameTime.value = now

  const windowStart = clamp(now, 0, duration - scrollWindow)
  const windowEnd = windowStart + scrollWindow

  // Scroll chart window with real time
  chart.options.scales.x.min = windowStart
  chart.options.scales.x.max = windowEnd

  // Input line at 3s from left
  const inputX = windowStart + 3
  chart.data.datasets[0].data = [
    { x: inputX, y: 0 },
    { x: inputX, y: currentActual }
  ]

  // Smooth target and tolerance slices
  const stepTime = 1 / 60
  const visibleTarget = []
  const visibleLower = []
  const visibleUpper = []

  let minY = Infinity
  let maxY = -Infinity

  for (let i = 0; i < interpolatedTarget.length; i++) {
    const t = i * stepTime
    if (t >= windowStart && t <= windowEnd) {
      const yT = interpolatedTarget[i]
      const yL = interpolatedLower[i]
      const yU = interpolatedUpper[i]

      visibleTarget.push({ x: t, y: yT })
      visibleLower.push({ x: t, y: yL })
      visibleUpper.push({ x: t, y: yU })

      minY = Math.min(minY, yL)
      maxY = Math.max(maxY, yU)
    }
  }

  chart.data.datasets[1].data = visibleTarget
  chart.data.datasets[2].data = visibleLower
  chart.data.datasets[3].data = visibleUpper

  // Adaptive Y-axis
  const padding = 5
  const rangeMin = clamp(minY - padding, 0, 135)
  const rangeMax = clamp(maxY + padding, rangeMin + 10, 135)
  chart.options.scales.y.min = rangeMin
  chart.options.scales.y.max = rangeMax

  // Game end
  if (now >= duration) {
    isRunning = false
    chart.options.plugins.annotation.annotations.goalLine = {
      type: 'line',
      xMin: duration,
      xMax: duration,
      borderColor: '#ff4444',
      borderWidth: 2,
      borderDash: [6, 4],
      label: {
        display: true,
        content: 'Goal',
        position: 'start',
        color: '#ff4444',
        font: { weight: 'bold' }
      }
    }
    chart.update()
    return
  }

  chart.update()
  requestAnimationFrame(renderLoop)
}
</script>

<style scoped>
.loading {
  font-size: 2rem;
  text-align: center;
  margin-top: 4rem;
}

.game-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1rem;
  font-family: sans-serif;
  color: #148114;
  background-color: #ffffff;
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

canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
