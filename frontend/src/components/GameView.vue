<template>
  <div class="game-wrapper">
    <div v-if="gameState === 'loading'" class="loading-overlay">
      <h1>Loading PowerMatch…</h1>
    </div>

    <div v-else-if="gameState === 'countdown'" class="loading-overlay">
      <h1>Starting in {{ countdown }}…</h1>
    </div>

    <div v-else>
      <div class="info-bar">
        <div>⏱ {{ Math.ceil(timeLeft) }}s</div>
        <h1>PowerMatch</h1>
        <div>⭐ {{ score.toFixed(1) }}</div>
      </div>

      <div class="chart-container">
        <LineChart ref="chartRef" :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, LineElement, PointElement, LinearScale, Title,
  CategoryScale, Filler, Tooltip, Legend
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

ChartJS.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip, Legend, annotationPlugin)
const LineChart = Line

const route = useRoute()
const router = useRouter()
const name = route.query.name || 'Player'
const difficulty = route.query.difficulty || 'Medium'

const targetCurve = ref([])
const actualValues = ref(Array(30).fill(null))
const interpolatedActual = ref([])
const tolerance = 10
const score = ref(0)
const lastActual = ref(0)

const gameState = ref('loading')
const countdown = ref(3)
const startTime = ref(null)
const elapsed = ref(0)
const timeLeft = computed(() => Math.max(0, 30 - elapsed.value))
const chartRef = ref(null)

const fps = 60
let animationFrameId = null
let frameSkip = 0

const inputX = computed(() => elapsed.value < 3 ? elapsed.value : elapsed.value < 20 ? xMin.value + 3 : elapsed.value);

const chartData = computed(() => {
  const labels = Array.from({ length: fps * 10 }, (_, i) => (xMin.value + i / fps).toFixed(2))

  const steppedTargetFull = getSteppedCurve(targetCurve.value)
  const steppedTarget = steppedTargetFull

  const toleranceUpper = steppedTarget.map(v => v != null ? Math.min(v + tolerance, 135) : null)
  const toleranceLower = steppedTarget.map(v => v != null ? Math.max(v - tolerance, 0) : null)

  const visibleActual = interpolatedActual.value.map((val, i) => {
    const time = i / fps
    return time <= elapsed.value ? val : null
  })
  const steppedActual = visibleActual
  return {
    labels,
    datasets: [
      {
        label: 'Input',
        data: steppedActual,
        borderColor: 'limegreen',
        borderWidth: 3,
        tension: 0,
        pointRadius: 0,
        stepped: false,
        fill: false
      },
      {
        label: 'Target',
        data: steppedTarget.slice(startIndex.value, endIndex.value),
        borderColor: 'orange',
        borderDash: [4, 4],
        borderWidth: 2,
        pointRadius: 0,
        stepped: true,
        fill: false
      },
      {
        data: toleranceUpper.slice(startIndex.value, endIndex.value),
        backgroundColor: 'rgba(255, 200, 0, 0.2)',
        stepped: true,
        borderWidth: 0,
        fill: '-1'
      },
      {
        data: toleranceLower.slice(startIndex.value, endIndex.value),
        backgroundColor: 'rgba(255, 200, 0, 0.2)',
        stepped: true,
        borderWidth: 0,
        fill: '-1'
      }
    ]
  }
})

const xMin = computed(() => elapsed.value < 3 ? 0 : elapsed.value < 20 ? elapsed.value - 3 : 20)
const xMax = computed(() => xMin.value + 10)
const startIndex = computed(() => Math.floor(xMin.value * fps))
const endIndex = computed(() => Math.ceil(xMax.value * fps))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  scales: {
    y: {
      min: 0,
      max: 135,
      ticks: { color: 'black' },
      grid: { color: 'rgba(0,0,0,0.1)' }
    },
    x: {
      min: xMin.value,
      max: xMax.value,
      ticks: {
        color: 'black',
        callback: val => `${Math.floor(val)}s`
      },
      grid: { color: 'rgba(0,0,0,0.05)' }
    }
  },
  plugins: {
    legend: {
      labels: {
        color: 'black',
        filter: item => ['Input', 'Target'].includes(item.text)
      }
    },
    annotation: {
      annotations: {
        inputMarker: {
          type: 'line',
          xMin: inputX.value,
      xMax: inputX.value + 0.001,
          borderColor: 'rgb(0, 54, 69)',
          borderDash: [4, 4],
          borderWidth: 2,
          label: {
            display: true,
            content: 'You are here',
            color: 'white',
            backgroundColor: 'rgb(0, 54, 69)',
            font: { weight: 'bold' },
            position: 'start'
          }
        }
      }
    }
  }
}))



function getSteppedCurve(arr) {
  return arr.flatMap(val => Array(fps).fill(val ?? null))
}

function interpolateActuals(rawValues) {
  const result = []
  for (let i = 0; i < 29; i++) {
    const v1 = rawValues[i]
    const v2 = rawValues[i + 1] ?? v1
    for (let j = 0; j < fps; j++) {
      result.push(v1 !== null && v2 !== null ? v1 + (v2 - v1) * (j / fps) : v1)
    }
  }
  const last = rawValues[29] ?? rawValues.findLast(v => v !== null) ?? 0
  result.push(...Array(fps).fill(last))
  return result
}

function connectWebSocket() {
  const socket = new WebSocket(import.meta.env.DEV ? 'ws://localhost:8000/ws/game' : `ws://${location.host}/ws/game`)
  socket.onopen = () => socket.send(JSON.stringify({ name, difficulty }))

  socket.onmessage = event => {
    const data = JSON.parse(event.data)
    if (data.type === 'init') {
      targetCurve.value = data.targetCurve
      gameState.value = 'countdown'
      const countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(countdownTimer)
          startTime.value = performance.now()
          gameState.value = 'playing'
          runGameLoop()
        }
      }, 1000)
    }
    if (data.type === 'tick') {
      if (typeof data.actual === 'number') lastActual.value = data.actual
      if (typeof data.totalScore === 'number') score.value = data.totalScore
    }
  }
}

function runGameLoop() {
  function loop() {
    if (gameState.value !== 'playing') return
    elapsed.value = (performance.now() - startTime.value) / 1000

    const t = Math.floor(elapsed.value)
    if (t < 30) actualValues.value[t] = lastActual.value

    interpolatedActual.value = interpolateActuals(actualValues.value)

    if (++frameSkip % 3 === 0 && chartRef.value?.chart) chartRef.value.chart.update('none')

    if (elapsed.value >= 30) {
      gameState.value = 'ended'
      cancelAnimationFrame(animationFrameId)
      router.push({ path: '/end', query: { score: score.value, name, difficulty } })
      return
    }
    animationFrameId = requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)
}

onMounted(() => {
  connectWebSocket()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

* { font-family: 'Poppins', sans-serif; box-sizing: border-box; }
body { margin: 0; background: rgb(0, 117, 130); }
.game-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: rgb(0, 117, 130);
  color: white;
  padding: 1rem;
}
.info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.2rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 54, 69, 0.8);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}
.info-bar h1 {
  margin: 0;
  font-size: 1.5rem;
}
.chart-container {
  flex-grow: 1;
  width: 100%;
  height: 70vh;
  padding: 1rem;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0, 54, 69);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 3rem;
  z-index: 1000;
}
</style>
