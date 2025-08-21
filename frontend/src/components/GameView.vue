<template>
  <div class="game-wrapper">
    <div v-if="gameState === 'loading'" class="loading-overlay">
      <h1>Loading PowerMatch…</h1>
    </div>

    <div v-else>
      <div v-if="gameState === 'countdown'" class="countdown-overlay">
        <h1>Starting in {{ countdown }}…</h1>
      </div>

      <div class="info-bar">
        <div>{{ remainingTime }}s</div>
        <h1>PowerMatch</h1>
        <div>{{ Math.round(score) }}</div>
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

// Chart.js registrations
ChartJS.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip, Legend, annotationPlugin)
const LineChart = Line

// Vue Router setup
const route = useRoute()
const router = useRouter()
const name = ref(route.query.name || 'Player')
const difficulty = ref(route.query.difficulty || 'Medium')

// --- CORE GAME STATE AND DATA REFS ---
const targetCurve = ref([])
const lastActual = ref(0) // Last received actual Y value from backend

// MODIFICATION 1: Change 'tolerance' from a constant to a reactive ref
const dynamicTolerance = ref(10) // Initialize with a default, will be updated by backend

const score = ref(0)

// This array will hold the actual points to render for the input line,
// including all the interpolated visual frames. This is the source of truth for the green line's history.
const inputLineInterpolatedPoints = ref([]);

const gameState = ref('loading')
const countdown = ref(3)

const gameTotalTicks = ref(30); // Total ticks from backend (raw duration, e.g., 30)

const chartRef = ref(null)
const fps = 60
let animationFrameId = null

const chartWindowDuration = 10; // How many seconds are visible on the chart at once
const inputMarkerOffset = 3; // Position of the "You are here" marker from the left of the visible window

// For smooth visual time progression - completely independent of backend timing
let gameStartTime = null; // When the game actually started (after countdown)
const visualCurrentTick = ref(0); // Always starts at 0, progresses smoothly based on real time

// Track if we should ignore ticks during countdown
const gameActuallyStarted = ref(false);

// --- COMPUTED PROPERTIES FOR CHART SCALING AND MARKER POSITION ---
const xMin = computed(() => {
  // Calculate the game's actual duration (always use gameTotalTicks as effective duration)
  const effectiveGameDuration = gameTotalTicks.value;
  // Point at which the chart starts scrolling (marker hits inputMarkerOffset from right edge)
  const scrollFreezePoint = Math.max(0, effectiveGameDuration - chartWindowDuration);

  // The dynamic minimum X based on current visual time and marker offset
  const currentDynamicXMin = visualCurrentTick.value - inputMarkerOffset;
  // The calculated X minimum ensures it doesn't go below 0 and respects the scroll freeze point
  const calculatedXMin = Math.max(0, Math.min(currentDynamicXMin, scrollFreezePoint));
  return calculatedXMin;
});

const xMax = computed(() => {
  const newXMax = xMin.value + chartWindowDuration;
  const effectiveGameDuration = gameTotalTicks.value;
  // Ensure X-max doesn't exceed the game's effective duration
  return Math.min(newXMax, effectiveGameDuration);
});

const inputX = computed(() => {
  const effectiveGameDuration = gameTotalTicks.value;
  // The absolute time at which the "You are here" marker stops moving relative to the left edge
  const markerStartsAbsoluteMovementAt = effectiveGameDuration - chartWindowDuration + inputMarkerOffset;

  let calculatedInputX;

  // If visualCurrentTick is before the marker's fixed position, it moves with visualCurrentTick
  if (visualCurrentTick.value < inputMarkerOffset) {
    calculatedInputX = visualCurrentTick.value;
  }
  // If visualCurrentTick is between the fixed marker position and the scroll freeze point, marker stays fixed
  else if (visualCurrentTick.value < markerStartsAbsoluteMovementAt) {
    calculatedInputX = xMin.value + inputMarkerOffset;
  }
  // If visualCurrentTick is past the scroll freeze point, marker moves with visualCurrentTick again
  else {
    calculatedInputX = visualCurrentTick.value;
  }
  return calculatedInputX;
});

const remainingTime = computed(() => {
  const total = gameTotalTicks.value;
  const current = visualCurrentTick.value;

  // Add console logs to see the values right before the calculation
  console.log(`[TIMER_DEBUG] Calculating remaining time: total=${total}, current=${current}`);

  // Optional: Add more specific checks if needed
  if (typeof total !== 'number' || isNaN(total)) {
    console.error(`[TIMER_DEBUG] gameTotalTicks.value is invalid:`, total);
    return NaN; // This will ensure NaN is propagated if it's the source
  }
  if (typeof current !== 'number' || isNaN(current)) {
    console.error(`[TIMER_DEBUG] visualCurrentTick.value is invalid:`, current);
    return NaN; // This will ensure NaN is propagated if it's the source
  }

  const timeRemaining = total - current;
  return Math.max(0, Math.ceil(timeRemaining));
});


// --- UTILITY FUNCTION FOR TARGET CURVE PROCESSING ---
function getSteppedCurveWithXY(arr, durationSeconds, framesPerSecond) {
  const result = [];
  const totalFrames = durationSeconds * framesPerSecond;

  for (let i = 0; i < totalFrames; i++) {
    const targetCurveIndex = Math.min(Math.floor(i / framesPerSecond), arr.length - 1);
    const yVal = arr[targetCurveIndex];
    const x = i / framesPerSecond;

    if (typeof yVal === 'number' && !isNaN(yVal)) {
      result.push({ x: parseFloat(x.toFixed(2)), y: parseFloat(yVal.toFixed(2)) });
    }
  }
  const lastX = parseFloat(durationSeconds.toFixed(2));
  const lastY = arr[arr.length - 1];
  if (typeof lastY === 'number' && !isNaN(lastY)) {
      if (result.length === 0 || result[result.length - 1].x !== lastX) {
          result.push({ x: lastX, y: parseFloat(lastY.toFixed(2)) });
      } else {
          result[result.length - 1].y = parseFloat(lastY.toFixed(2));
      }
  }
  return result;
}

const fullSteppedTargetXY = ref([]);

// --- CHART.JS PLUGIN FOR TOLERANCE AREA ---
const tolerancePlugin = {
  id: 'toleranceFill',
  beforeDatasetsDraw(chart, args, options) {
    const { ctx, chartArea: { left, right, top, bottom }, scales: { x, y } } = chart;

    const targetDataset = chart.data.datasets.find(ds => ds.id === 'targetLineId');
    if (!targetDataset || !targetDataset.data || targetDataset.data.length < 1) {
      return;
    }

    ctx.save();
    ctx.fillStyle = options.backgroundColor || 'rgba(255, 200, 0, 0.2)';
    // Use the dynamic tolerance value from options
    const toleranceValue = options.toleranceValue; // This is already correctly retrieving it from options

    const targetData = targetDataset.data;

    const upperBoundPoints = [];
    targetData.forEach((p, i) => {
        const prevY = i > 0 ? targetData[i-1].y : p.y;
        upperBoundPoints.push({ x: p.x, y: Math.min(prevY + toleranceValue, y.max) });
        if (prevY !== p.y) {
            upperBoundPoints.push({ x: p.x, y: Math.min(p.y + toleranceValue, y.max) });
        }
    });
    upperBoundPoints.sort((a,b) => a.x - b.x);

    const lowerBoundPoints = [];
    for (let i = targetData.length - 1; i >= 0; i--) {
        const p = targetData[i];
        const prevY = i > 0 ? targetData[i-1].y : p.y;
        if (prevY !== p.y) {
            lowerBoundPoints.push({ x: p.x, y: Math.max(p.y - toleranceValue, y.min) });
        }
        lowerBoundPoints.push({ x: p.x, y: Math.max(prevY - toleranceValue, y.min) });
    }
    lowerBoundPoints.sort((a,b) => a.x - b.x);

    ctx.beginPath();
    if (upperBoundPoints.length > 0) {
        ctx.moveTo(x.getPixelForValue(upperBoundPoints[0].x), y.getPixelForValue(upperBoundPoints[0].y));
    }
    upperBoundPoints.forEach(p => {
        ctx.lineTo(x.getPixelForValue(p.x), y.getPixelForValue(p.y));
    });
    for(let i = lowerBoundPoints.length - 1; i >= 0; i--) {
        const p = lowerBoundPoints[i];
        ctx.lineTo(x.getPixelForValue(p.x), y.getPixelForValue(p.y));
    }

    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }
};

ChartJS.register(tolerancePlugin);

// --- CHART.JS DATA CONFIGURATION ---
const chartData = computed(() => {
  // ... (no changes needed here, as it uses visibleTargetXY which is based on targetCurve.value)
  let visibleTargetXY = [];

  const chartXMinRaw = xMin.value;
  const chartXMaxRaw = xMax.value;

  const filteredTargetRaw = fullSteppedTargetXY.value.filter(point =>
    point.x >= chartXMinRaw && point.x <= chartXMaxRaw
  );

  if (filteredTargetRaw.length > 0 && filteredTargetRaw[0].x > chartXMinRaw) {
    const precedingPoint = fullSteppedTargetXY.value.slice().reverse().find(p => p.x < chartXMinRaw);
    if (precedingPoint) {
      visibleTargetXY.push({ x: chartXMinRaw, y: precedingPoint.y });
    } else {
      visibleTargetXY.push({ x: chartXMinRaw, y: filteredTargetRaw[0].y });
    }
  }
  visibleTargetXY.push(...filteredTargetRaw);

  if (visibleTargetXY.length > 0 && visibleTargetXY[visibleTargetXY.length - 1].x < chartXMaxRaw) {
    const succeedingPoint = fullSteppedTargetXY.value.find(p => p.x > chartXMaxRaw);
    if (succeedingPoint) {
      visibleTargetXY.push({ x: chartXMaxRaw, y: succeedingPoint.y });
    } else {
      visibleTargetXY.push({ x: chartXMaxRaw, y: visibleTargetXY[visibleTargetXY.length - 1].y });
    }
  }

  const seenTargetX = new Set();
  visibleTargetXY = visibleTargetXY.filter(point => {
    const fixedX = point.x.toFixed(5);
    if (seenTargetX.has(fixedX)) {
      return false;
    }
    seenTargetX.add(fixedX);
    return true;
  }).sort((a, b) => a.x - b.x);

  // --- Input Line ---
  // Only show points up to the current visualCurrentTick, and within the visible x-range
  let visibleActualXY = inputLineInterpolatedPoints.value.filter(point =>
    point.x >= xMin.value && point.x <= visualCurrentTick.value
  );

  // Crucially, add the current visualCurrentTick point to ensure the line always extends to the marker.
  // Use the 'lastActual' value for the Y-coordinate at this precise moment.
  if (visualCurrentTick.value >= 0 && (visibleActualXY.length === 0 || visibleActualXY[visibleActualXY.length - 1].x < visualCurrentTick.value)) {
    // Only add if we're within the game duration (or very slightly beyond to ensure line ends correctly)
    const effectiveGameDuration = gameTotalTicks.value;
    if (visualCurrentTick.value <= effectiveGameDuration + 0.1) { // Add a small buffer
      visibleActualXY.push({
        x: parseFloat(visualCurrentTick.value.toFixed(2)),
        y: parseFloat(lastActual.value.toFixed(2))
      });
    }
  }

  // Final deduplication and sort for the input line.
  const seenActualX = new Set();
  visibleActualXY = visibleActualXY.filter(point => {
    const fixedX = point.x.toFixed(5);
    if (seenActualX.has(fixedX)) return false;
    seenActualX.add(fixedX);
    return true;
  }).sort((a, b) => a.x - b.x);

  return {
    labels: [],
    datasets: [
      {
        id: 'targetLineId',
        label: 'Target',
        data: visibleTargetXY,
        borderColor: 'orange',
        borderDash: [4, 4],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        stepped: 'before',
        tension: 0,
        order: 1
      },
      {
        label: 'Input',
        data: visibleActualXY,
        borderColor: 'limegreen',
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0.2,
        stepped: false,
        order: 0
      }
    ]
  }
})

// --- CHART.JS OPTIONS CONFIGURATION ---
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 0 // Disable Chart.js animation for real-time updates
  },
  parsing: false, // Important for object data
  scales: {
    y: {
      min: 0,
      max: 60, // Consistent Y-axis range
      ticks: { color: 'black' },
      grid: { color: 'rgba(0,0,0,0.1)' }
    },
    x: {
      min: xMin.value, // Dynamic X-axis min
      max: xMax.value, // Dynamic X-axis max
      type: 'linear', // Ensure X-axis is linear
      ticks: {
        color: 'black',
        callback: function(value) {
            const step = 1; // Display labels every 1 second
            if (value % step === 0) {
              return `${Math.floor(value)}s`;
            }
            return null; // Don't display labels for fractional seconds
        },
        maxTicksLimit: chartWindowDuration + 1, // Limit number of labels
      },
      grid: { color: 'rgba(0,0,0,0.05)' }
    }
  },
  plugins: {
    legend: {
      labels: {
        color: 'black',
        filter: item => ['Input', 'Target'].includes(item.text), // Filter out internal dataset legends if any
        generateLabels: function(chart) {
            const defaultLabels = ChartJS.defaults.plugins.legend.labels.generateLabels(chart);
            // Add custom label for tolerance area
            defaultLabels.push({
                text: 'Tolerance',
                fillStyle: 'rgba(255, 200, 0, 0.2)',
                strokeStyle: 'transparent',
                lineWidth: 0,
                hidden: false,
                datasetIndex: -1
            });
            return defaultLabels;
        }
      }
    },
    annotation: {
      annotations: {
        inputMarker: {
          type: 'line',
          xMin: inputX.value,
          xMax: inputX.value + 0.001, // Draw a thin vertical line
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
    },
    toleranceFill: {
        backgroundColor: 'rgba(255, 200, 0, 0.2)',
        // MODIFICATION 3: Use the reactive dynamicTolerance value here
        toleranceValue: dynamicTolerance.value
    }
  }
}))

// --- GAME LOOP FOR SMOOTH VISUAL UPDATES ---
function runGameLoop() {
  function loop(currentTime) {
    // Only run if the game state is 'playing'
    if (gameState.value !== 'playing') {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
        console.log('[LOOP-STOP] runGameLoop: stopping animation frame.');
      }
      return; // Stop the loop
    }

    // Calculate smooth visual progress based on real time since game start
    if (gameStartTime !== null) {
      const elapsedSeconds = (currentTime - gameStartTime) / 1000;
      visualCurrentTick.value = Math.min(elapsedSeconds, gameTotalTicks.value);
    }

    // Add the current interpolated visual point to the inputLineInterpolatedPoints history
    if (gameState.value === 'playing' && typeof lastActual.value === 'number' && visualCurrentTick.value >= 0) {
        const newPoint = { x: visualCurrentTick.value, y: lastActual.value };
        const lastPointInHistory = inputLineInterpolatedPoints.value[inputLineInterpolatedPoints.value.length - 1];

        // Always add the new point if it has a greater X value than the last one.
        if (!lastPointInHistory || newPoint.x > lastPointInHistory.x) {
            inputLineInterpolatedPoints.value.push({
              x: parseFloat(newPoint.x.toFixed(3)),
              y: parseFloat(newPoint.y.toFixed(2))
            });

            // Prune old points to keep memory usage down
            const pruneThreshold = xMin.value - 5;
            inputLineInterpolatedPoints.value = inputLineInterpolatedPoints.value.filter(p => p.x >= pruneThreshold);
        } else if (lastPointInHistory && newPoint.x === lastPointInHistory.x) {
            // If X is the same, update the Y of the last point
            lastPointInHistory.y = parseFloat(newPoint.y.toFixed(2));
        }
    }

    // Request chart update without animation
    if (chartRef.value?.chart) {
      chartRef.value.chart.update('none');
    }

    animationFrameId = requestAnimationFrame(loop)
  }

  console.log('[LOOP-START] runGameLoop: Starting animation frame loop.');
  animationFrameId = requestAnimationFrame(loop)
}

// --- WEB SOCKET CONNECTION LOGIC ---
function connectWebSocket() {
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = import.meta.env.DEV ? 'localhost:8000' : location.host; // Use localhost:8000 for dev
  const socket = new WebSocket(`${wsProtocol}//${wsHost}/ws/game/${name.value}/${difficulty.value}`);

  socket.onopen = () => {
    console.log("WebSocket opened.");
  };

  socket.onmessage = event => {
    const data = JSON.parse(event.data);

    if (data.type === 'init') {
      console.log("Received 'init' message:", data);
      targetCurve.value = data.targetCurve;
      gameTotalTicks.value = data.duration;

      // MODIFICATION 2: Update dynamicTolerance from backend data
      if (data.toleranceCurve && data.toleranceCurve.length > 0) {
          dynamicTolerance.value = data.toleranceCurve[0];
          console.log(`[FRONTEND] Updated dynamicTolerance to: ${dynamicTolerance.value}`);
      }


      // Reset all relevant state for a new game
      lastActual.value = 0; // Reset last actual value
      score.value = 0; // Reset score
      visualCurrentTick.value = 0; // Reset visual time
      gameActuallyStarted.value = false; // Reset game started flag

      // Generate the full target curve data once - now using client time (0-based)
      fullSteppedTargetXY.value = getSteppedCurveWithXY(targetCurve.value, gameTotalTicks.value, fps);

      gameState.value = 'countdown';
      const countdownTimer = setInterval(() => {
        countdown.value--;
        console.log('Countdown:', countdown.value);
        if (countdown.value <= 0) {
          clearInterval(countdownTimer);
          gameState.value = 'playing';
          gameActuallyStarted.value = true; // Mark that the game has actually started
          console.log('Countdown finished, gameState set to playing. Starting runGameLoop.');

          // Send start signal to backend
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'start' }));
            console.log('Sent start signal to backend');
          }

          // Set the game start time to NOW - this is our reference point
          gameStartTime = performance.now();
          visualCurrentTick.value = 0; // Start at exactly 0

          // Initialize the input line to start at x=0 with the current actual value
          inputLineInterpolatedPoints.value = [{ x: 0, y: parseFloat(lastActual.value.toFixed(2)) }];
          console.log(`Game started at x=0 with initial value: ${lastActual.value}`);

          runGameLoop(); // Start the animation frame loop
        }
      }, 1000);
    } else if (data.type === 'tick') {
        // Only process tick data if the game has actually started (after countdown)
        if (gameActuallyStarted.value) {
          // Simply update the actual value - no complex offset calculations needed
          if (typeof data.actual === 'number') {
              lastActual.value = data.actual;
          }
          if (typeof data.totalScore === 'number') {
              score.value = data.totalScore;
          }
        } else {
          // During countdown, still update lastActual so we have the current value when game starts
          if (typeof data.actual === 'number') {
              lastActual.value = data.actual;
          }
          console.log('Ignoring tick during countdown phase');
        }
    } else if (data.type === 'end') {
        console.log("Received 'end' message from backend:", data);

        gameState.value = 'ended';
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
            console.log('[LOOP-STOP] Game ended: animation frame stopped.');
        }

        // Round the final score to a whole number
        const finalScore = Math.round(data.score || score.value);

        router.push({ path: '/end', query: { score: finalScore, name: name.value, difficulty: difficulty.value } });

        if (socket.readyState === WebSocket.OPEN) {
            socket.close();
            console.log('WebSocket closed by frontend on game end.');
        }
    } else {
      console.warn("Received unknown WebSocket message type:", data.type, data);
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
  };

  socket.onclose = (event) => {
    console.warn("WebSocket Closed:", event);
  };
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  console.log('Component mounted. Connecting WebSocket.');
  connectWebSocket();
});
</script>

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
  position: relative;
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
.countdown-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: black;
  font-size: 3rem;
  z-index: 50;
}



</style>
