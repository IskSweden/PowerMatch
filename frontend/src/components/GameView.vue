<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip,
  Legend
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Filler,
  Tooltip,
  Legend,
  annotationPlugin
)

const LineChart = Line

const route = useRoute()
const router = useRouter()
const name = route.query.name || 'Player'
const difficulty = route.query.difficulty || 'Medium'

const score = ref(0)
const timeLeft = ref(30)
const loading = ref(true)
const initialized = ref(false)

const actualData = ref([])
const targetCurve = ref([])
const toleranceCurve = ref([])
const interpolatedActual = ref([])
const interpolatedTarget = ref([])
const displayWindow = 10
const startTime = ref(Date.now() / 1000)
const roundedScore = computed(() => score.value.toFixed(1))

const chartReady = computed(
  () => actualData.value.length > 0 && targetCurve.value.length > 0 && toleranceCurve.value.length > 0,

  console.log(targetCurve.value.length),    // should be 30
  console.log(interpolatedTarget.value.length)


)

const chartData = computed(() => {
  const currentLen = interpolatedTarget.value.length
  const start = Math.max(0, currentLen - displayWindow * 30)
  const end = currentLen

  // Label timeline: 30fps window from gameTime
  const now = Date.now() / 1000
  const gameTime = now - startTime.value

  const labels = Array.from({ length: end - start }, (_, i) =>
    ((i - (end - start)) / 30 + gameTime).toFixed(1)
  )

  return {
    labels,
    datasets: [
      {
        label: 'Actual',
        data: interpolatedActual.value.slice(start, end),
        borderColor: 'rgba(255, 99, 132, 0.8)',
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 0,
        fill: false
      },
      {
        type: 'line',
        label: 'Target',
        data: interpolatedTarget.value.slice(start, end),
        borderColor: 'rgba(54, 162, 235, 0.7)',
        borderDash: [5, 5],
        borderWidth: 2,
        tension: 0,
        stepped: true,
        pointRadius: 0,
        fill: false
      }
    ]
  }
})




const chartOptions = {
  responsive: true,
  animation: false,
  maintainAspectRatio: false,
  scales: {
    y: {
      min: 0,
      max: 135,
      ticks: { color: 'black' },
      grid: { color: 'rgba(0, 0, 0, 0.1)' }
    },
    x: {
      ticks: { color: 'black' },
      grid: { color: 'rgba(0, 0, 0, 0.05)' }
    }
  },
  plugins: {
    legend: {
      labels: { color: 'black' }
    },
    tooltip: { enabled: true },
    annotation: {
      annotations: {
        inputLine: {
          type: 'line',
          xMin: 3,
          xMax: 3,
          borderColor: 'rgb(0, 54, 69)',
          borderWidth: 2,
          borderDash: [4, 4],
          label: {
            display: true,
            content: 'You are here',
            color: 'black',
            backgroundColor: 'rgb(139, 191, 128)',
            position: 'start'
          }
        }
      }
    }
  }
}

let lastTick = -1
let lastTarget = 0
let lastActual = 0

const interpolate = () => {
  requestAnimationFrame(interpolate)

  if (!initialized.value || targetCurve.value.length === 0) return

  const now = Date.now() / 1000
  const gameTime = now - startTime.value
  const tick = Math.floor(gameTime)

  if (tick >= 30) {
    router.push({
      path: '/end',
      query: {
        score: score.value,
        name,
        difficulty
      }
    })
    return
  }

  // Only update tick-based values once per second
  if (tick !== lastTick) {
    lastTick = tick
    if (actualData.value.length > tick) {
      lastActual = actualData.value[tick]
    }

    lastTarget = targetCurve.value[tick] ?? lastTarget
  }

  // Push last known values at 60fps
  interpolatedActual.value.push(lastActual)
  interpolatedTarget.value.push(lastTarget)
}







const connectSocket = () => {
  const socket = new WebSocket(
    import.meta.env.DEV ? 'ws://localhost:8000/ws/game' : `ws://${location.host}/ws/game`
  )

  socket.onopen = () => {
    socket.send(JSON.stringify({ name, difficulty }))
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'init' && !initialized.value) {
      targetCurve.value = data.targetCurve || []
      toleranceCurve.value = data.toleranceCurve || []
      initialized.value = true
      loading.value = false

      startTime.value = Date.now() / 1000

      console.log("Game initialized")
      console.log("targetCurve:", data.targetCurve)
      console.log("length:", data.targetCurve?.length)

    }

    if (data.type === 'tick') {
      if (typeof data.actual === 'number') {
        actualData.value.push(data.actual)
      }
      score.value = data.totalScore
      timeLeft.value = Math.max(0, 30 - actualData.value.length)
    }

    if (data.type === 'end') {
      router.push({
        path: '/end',
        query: {
          score: data.score,
          name,
          difficulty
        }
      })
    }
  }

  socket.onerror = (e) => console.error('WebSocket error', e)
  socket.onclose = () => console.log('WebSocket closed')
}

onMounted(() => {
  connectSocket()
  // Don't start interpolate() yet — wait until initialized
})

watch(initialized, (ready) => {
  if (ready) interpolate()
})

</script>

<template>
  <div class="game-wrapper">
    <div v-if="loading" class="loading-overlay">
      <h1>Loading PowerMatch...</h1>
    </div>

    <div v-else>
      <div class="info-bar">
        <div>⏱ {{ timeLeft }}s</div>
        <h1>PowerMatch</h1>
        <div>⭐ {{ roundedScore }}</div>
      </div>

      <div class="chart-container">
        <LineChart
          v-if="chartReady && chartData.labels.length > 0"
          :data="chartData"
          :options="chartOptions"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

* {
  font-family: 'Poppins', sans-serif;
  box-sizing: border-box;
}

body {
  margin: 0;
  background: rgb(0, 117, 130);
}

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
}

.chart-container {
  flex-grow: 1;
  width: 100%;
  padding: 1rem;
  display: flex;
}

canvas {
  width: 100% !important;
  height: 100% !important;
  background: white;
  border-radius: 1rem;
  color: black !important;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0, 54, 69);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  z-index: 1000;
}
</style>
