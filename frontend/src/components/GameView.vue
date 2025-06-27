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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, LineElement, PointElement, LinearScale, Title,
  CategoryScale, Filler, Tooltip, Legend
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

// Register Chart.js components
ChartJS.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip, Legend, annotationPlugin)
const LineChart = Line

// Game State & Data
const route = useRoute()
const router = useRouter()
const name = route.query.name || 'Player'
const difficulty = route.query.difficulty || 'Medium'

const targetCurve = ref([])
const actualValues = ref(Array(30 * 60).fill(null)) // Store actual inputs at FPS resolution
const lastActual = ref(0)
const tolerance = 10
const score = ref(0)

const gameState = ref('loading')
const countdown = ref(3)
const startTime = ref(null)
const elapsed = ref(0)
const timeLeft = computed(() => Math.max(0, 30 - elapsed.value))

const chartRef = ref(null)
const fps = 60
let animationFrameId = null

const chartWindowDuration = 10; // seconds the chart window spans
const inputMarkerOffset = 3; // seconds from left edge where input marker usually sits
const GAME_TOTAL_DURATION = 30; // total duration of the game in seconds

// --- X-Axis Scrolling Logic ---
const xMin = computed(() => {
  const scrollFreezePoint = GAME_TOTAL_DURATION - chartWindowDuration;
  const currentDynamicXMin = elapsed.value - inputMarkerOffset;
  // Cap xMin at 0 and at the scroll freeze point
  return Math.max(0, Math.min(currentDynamicXMin, scrollFreezePoint));
});

const xMax = computed(() => xMin.value + chartWindowDuration);

// --- Input Marker Position Logic ---
const inputX = computed(() => {
  // Time point when the chart stops scrolling and marker starts absolute movement
  const markerStartsAbsoluteMovementAt = GAME_TOTAL_DURATION - chartWindowDuration + inputMarkerOffset;

  if (elapsed.value < inputMarkerOffset) {
    // Initial ramp-up: marker follows elapsed time until it reaches the offset
    return elapsed.value;
  } else if (elapsed.value < markerStartsAbsoluteMovementAt) {
    // Scrolling phase: marker stays fixed relative to the window (at inputMarkerOffset from xMin)
    return xMin.value + inputMarkerOffset;
  } else {
    // Frozen phase: marker tracks elapsed.value directly to move into the goal
    return elapsed.value;
  }
});


// Function to generate dense, stepped {x,y} points for a curve
function getSteppedCurveWithXY(arr, durationSeconds, framesPerSecond) {
  const result = [];
  const totalFrames = durationSeconds * framesPerSecond;

  for (let i = 0; i < totalFrames; i++) {
    // Determine which original targetCurve index this frame corresponds to
    // Use Math.min to ensure we don't go out of bounds if i/framesPerSecond exceeds arr.length
    const targetCurveIndex = Math.min(Math.floor(i / framesPerSecond), arr.length - 1);
    const yVal = arr[targetCurveIndex];
    const x = i / framesPerSecond; // Current time in seconds

    if (typeof yVal === 'number' && !isNaN(yVal)) {
      result.push({ x: parseFloat(x.toFixed(2)), y: parseFloat(yVal.toFixed(2)) });
    }
  }
  // Ensure the very last point is precisely at GAME_TOTAL_DURATION with its corresponding value
  const lastX = parseFloat(GAME_TOTAL_DURATION.toFixed(2));
  const lastY = arr[arr.length - 1]; // Last value from the original targetCurve
  if (typeof lastY === 'number' && !isNaN(lastY)) {
      // Add the final point if it's not already there or to ensure its Y value is correct
      if (result.length === 0 || result[result.length - 1].x !== lastX) {
          result.push({ x: lastX, y: parseFloat(lastY.toFixed(2)) });
      } else {
          result[result.length - 1].y = parseFloat(lastY.toFixed(2));
      }
  }
  return result;
}

const fullSteppedTargetXY = ref([]); // Stores the pre-calculated full target curve

// --- Chart Data Definition ---
const chartData = computed(() => {
  // Filter target curve points for the visible window
  const visibleTargetXY = fullSteppedTargetXY.value.filter(point =>
    point.x >= xMin.value && point.x <= xMax.value
  );

  // Calculate tolerance lines for the visible window
  const toleranceUpper = visibleTargetXY.map(p => ({ x: p.x, y: p.y != null ? Math.min(p.y + tolerance, 135) : null }));
  const toleranceLower = visibleTargetXY.map(p => ({ x: p.x, y: p.y != null ? Math.max(p.y - tolerance, 0) : null }));

  // Filter actual input values for the visible window
  const visibleActualXY = [];
  const startIdx = Math.floor(xMin.value * fps);
  const endIdx = Math.floor(xMax.value * fps);

  for (let i = startIdx; i < endIdx; i++) {
    const y = actualValues.value[i];
    if (typeof y === 'number' && !isNaN(y)) {
      const x = i / fps;
      visibleActualXY.push({ x: parseFloat(x.toFixed(2)), y: parseFloat(y.toFixed(2)) });
    }
  }

  return {
    labels: [], // Not used with linear scales and x,y data
    datasets: [
      // Dataset for the lower boundary of the tolerance band
      // It must have an ID to be targeted by the fill property of the upper band.
      // Its line is transparent, but its data is crucial for the fill area.
      {
        id: 'toleranceLowerLine', // Unique ID for targeting
        data: toleranceLower,
        borderColor: 'transparent', // Make the line invisible
        borderWidth: 0,
        pointRadius: 0,
        fill: false, // This dataset itself does not fill
        stepped: 'before', // Crucial for correct stepped rendering
        tension: 0,
        order: 3, // Draw this furthest back
      },
      // Dataset for the upper boundary of the tolerance band
      // This is the dataset that will perform the fill down to the 'toleranceLowerLine'.
      {
        label: 'Tolerance', // This label will appear in the legend
        data: toleranceUpper,
        backgroundColor: 'rgba(255, 200, 0, 0.2)', // Fill color
        borderColor: 'transparent', // No line for the upper boundary itself (just the fill)
        borderWidth: 0,
        pointRadius: 0,
        fill: {
            target: 'toleranceLowerLine', // Fill down to the dataset with this ID
            above: 'rgba(255, 200, 0, 0.2)', // Ensure color is applied consistently
            below: 'rgba(255, 200, 0, 0.2)'
        },
        stepped: 'before', // Crucial for correct stepped rendering of the fill
        tension: 0,
        order: 2, // Drawn in front of toleranceLowerLine, but behind Target and Input
      },
      // Target Line
      {
        label: 'Target',
        data: visibleTargetXY,
        borderColor: 'orange',
        borderDash: [4, 4],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        stepped: 'before',
        tension: 0,
        order: 1, // Drawn in front of the tolerance fill
      },
      // Input Line
      {
        label: 'Input',
        data: visibleActualXY,
        borderColor: 'limegreen',
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0.1, // Keep smooth for user input
        order: 0, // Drawn on top of everything else
      }
    ]
  }
})

// --- Chart Options ---
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 0 // Disable animation for real-time updates
  },
  parsing: false, // Required when providing {x,y} data directly
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
      type: 'linear', // Use linear scale for continuous time
      ticks: {
        color: 'black',
        callback: function(value, index, ticks) {
            // Display whole seconds
            const step = 1;
            if (value % step === 0) {
              return `${Math.floor(value)}s`;
            }
            return null;
        },
        maxTicksLimit: chartWindowDuration + 1, // Control number of visible ticks
      },
      grid: { color: 'rgba(0,0,0,0.05)' }
    }
  },
  plugins: {
    legend: {
      labels: {
        color: 'black',
        // Filter out the 'toleranceLowerLine' from the legend as it's just a boundary
        filter: item => ['Input', 'Target', 'Tolerance'].includes(item.text)
      }
    },
    annotation: {
      annotations: {
        inputMarker: {
          type: 'line',
          xMin: inputX.value,
          xMax: inputX.value + 0.001, // A very thin line
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

// --- Game Loop ---
function runGameLoop() {
  function loop() {
    if (gameState.value !== 'playing') return

    elapsed.value = (performance.now() - startTime.value) / 1000

    const currentFrameIndex = Math.floor(elapsed.value * fps);
    if (currentFrameIndex < actualValues.value.length) {
      actualValues.value[currentFrameIndex] = lastActual.value;

      // Simple linear interpolation to fill gaps in actualValues for smooth rendering
      if (currentFrameIndex > 0) {
          let prevNonNullIndex = currentFrameIndex - 1;
          while (prevNonNullIndex >= 0 && actualValues.value[prevNonNullIndex] === null) {
              prevNonNullIndex--;
          }
          if (prevNonNullIndex >= 0 && actualValues.value[currentFrameIndex] !== null) {
            const startValue = actualValues.value[prevNonNullIndex];
            const endValue = actualValues.value[currentFrameIndex];
            for (let i = prevNonNullIndex + 1; i < currentFrameIndex; i++) {
                const fraction = (i - prevNonNullIndex) / (currentFrameIndex - prevNonNullIndex);
                actualValues.value[i] = startValue + (endValue - startValue) * fraction;
            }
          }
      }
    }

    // Request chart update
    if (chartRef.value?.chart) {
      chartRef.value.chart.update('none'); // 'none' for no animation
    }

    // Game end condition
    if (elapsed.value >= GAME_TOTAL_DURATION) {
      gameState.value = 'ended'
      cancelAnimationFrame(animationFrameId)
      router.push({ path: '/end', query: { score: score.value, name, difficulty } })
      return
    }

    animationFrameId = requestAnimationFrame(loop)
  }

  requestAnimationFrame(loop)
}

// --- WebSocket Setup ---
function connectWebSocket() {
  // Determine WebSocket URL based on development or production environment
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = import.meta.env.DEV ? 'localhost:8000' : location.host;
  const socket = new WebSocket(`${wsProtocol}//${wsHost}/ws/game`);

  socket.onopen = () => socket.send(JSON.stringify({ name, difficulty }));

  socket.onmessage = event => {
    const data = JSON.parse(event.data);
    if (data.type === 'init') {
      targetCurve.value = data.targetCurve;
      // Pre-calculate full stepped target curve once on init
      fullSteppedTargetXY.value = getSteppedCurveWithXY(targetCurve.value, GAME_TOTAL_DURATION, fps);

      gameState.value = 'countdown';
      const countdownTimer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) {
          clearInterval(countdownTimer);
          startTime.value = performance.now();
          gameState.value = 'playing';
          runGameLoop();
        }
      }, 1000);
    }
    if (data.type === 'tick') {
      if (typeof data.actual === 'number') lastActual.value = data.actual;
      if (typeof data.totalScore === 'number') score.value = data.totalScore;
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
    // TODO: User feedback for connection errors
  };

  socket.onclose = (event) => {
    console.warn("WebSocket Closed:", event);
    // TODO: User feedback for disconnected state
  };
}

onMounted(() => {
  connectWebSocket();
});

// Watch elapsed time to trigger chart updates
watch(elapsed, () => {
    if (gameState.value === 'playing' && chartRef.value?.chart) {
        chartRef.value.chart.update('none');
    }
});
</script>

<style scoped>
/* Scoped styles for the component */
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