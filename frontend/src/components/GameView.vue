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
        <div>⏱ {{ Math.max(0, (gameTotalTicks - initialBackendTickOffset) - Math.floor(visualCurrentTick) - 1) }}s</div>
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

ChartJS.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Filler, Tooltip, Legend, annotationPlugin)
const LineChart = Line

const route = useRoute()
const router = useRouter()
const name = ref(route.query.name || 'Player')
const difficulty = ref(route.query.difficulty || 'Medium')

const targetCurve = ref([])
// actualValues now stores { x: rawBackendTickNumber, y: actualValue } *temporarily*
// These will be offset-corrected when moved to `processedActualValues`
const rawActualBuffer = ref([]);
const processedActualValues = ref([]); // Stores { x: offsetCorrectedClientTick, y: actualValue } for charting
const lastActual = ref(0)
const tolerance = 10
const score = ref(0)

const gameState = ref('loading')
const countdown = ref(3)

const gameTotalTicks = ref(30); // Total ticks from backend (raw, e.g., 30)

const chartRef = ref(null)
const fps = 60
let animationFrameId = null

const chartWindowDuration = 10;
const inputMarkerOffset = 3;

// To correct for backend ticks starting > 0
const initialBackendTickOffset = ref(0); // This will hold the raw backend tick number that corresponds to client's 0s

// For smooth interpolation of visual time
let lastTickReceivedTime = performance.now(); // Timestamp when last backend tick was received
let currentBackendTickValueAtLastMessage = -1; // Value of currentBackendTick (raw backend tick number) when the last message was received

// This will be the smoothly interpolated tick for visual purposes, always 0-based
const visualCurrentTick = ref(-1);

const xMin = computed(() => {
  const effectiveGameDuration = gameTotalTicks.value - initialBackendTickOffset.value;
  const scrollFreezePoint = Math.max(0, effectiveGameDuration - chartWindowDuration);

  const currentDynamicXMin = visualCurrentTick.value - inputMarkerOffset;
  const calculatedXMin = Math.max(0, Math.min(currentDynamicXMin, scrollFreezePoint));
  return calculatedXMin;
});

const xMax = computed(() => {
  const newXMax = xMin.value + chartWindowDuration;
  const effectiveGameDuration = gameTotalTicks.value - initialBackendTickOffset.value;
  return Math.min(newXMax, effectiveGameDuration);
});

const inputX = computed(() => {
  const effectiveGameDuration = gameTotalTicks.value - initialBackendTickOffset.value;
  const markerStartsAbsoluteMovementAt = effectiveGameDuration - chartWindowDuration + inputMarkerOffset;

  let calculatedInputX;

  if (visualCurrentTick.value < inputMarkerOffset) {
    calculatedInputX = visualCurrentTick.value;
  } else if (visualCurrentTick.value < markerStartsAbsoluteMovementAt) {
    calculatedInputX = xMin.value + inputMarkerOffset;
  } else {
    calculatedInputX = visualCurrentTick.value;
  }
  return calculatedInputX;
});


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
    const toleranceValue = options.toleranceValue;

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
    for(let i = lowerBoundPoints.length - 1; i >= 0; i--){
        const p = lowerBoundPoints[i];
        ctx.lineTo(x.getPixelForValue(p.x), y.getPixelForValue(p.y));
    }

    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }
};

ChartJS.register(tolerancePlugin);


const chartData = computed(() => {
  // --- Target Line (Preloading - FULL 10s window) ---
  const filteredTarget = fullSteppedTargetXY.value.filter(point =>
    point.x >= xMin.value + initialBackendTickOffset.value && point.x <= xMax.value + initialBackendTickOffset.value
  );

  let visibleTargetXY = [];

  if (filteredTarget.length > 0 && filteredTarget[0].x > xMin.value + initialBackendTickOffset.value) {
    const precedingPoint = fullSteppedTargetXY.value.slice().reverse().find(p => p.x < xMin.value + initialBackendTickOffset.value);
    if (precedingPoint) {
      visibleTargetXY.push({ x: xMin.value + initialBackendTickOffset.value, y: precedingPoint.y });
    } else {
      visibleTargetXY.push({ x: xMin.value + initialBackendTickOffset.value, y: filteredTarget[0].y });
    }
  }
  visibleTargetXY.push(...filteredTarget);

  if (visibleTargetXY.length > 0 && visibleTargetXY[visibleTargetXY.length - 1].x < xMax.value + initialBackendTickOffset.value) {
    const succeedingPoint = fullSteppedTargetXY.value.find(p => p.x > xMax.value + initialBackendTickOffset.value);
    if (succeedingPoint) {
      visibleTargetXY.push({ x: xMax.value + initialBackendTickOffset.value, y: succeedingPoint.y });
    } else {
      visibleTargetXY.push({ x: xMax.value + initialBackendTickOffset.value, y: visibleTargetXY[visibleTargetXY.length - 1].y });
    }
  }

  // Offset-correct the X values for the chart display (this creates the 0-based time on chart)
  visibleTargetXY = visibleTargetXY.map(p => ({ x: p.x - initialBackendTickOffset.value, y: p.y }));

  const seenTargetX = new Set();
  visibleTargetXY = visibleTargetXY.filter(point => {
    const fixedX = point.x.toFixed(5);
    if (seenTargetX.has(fixedX)) {
      return false;
    }
    seenTargetX.add(fixedX);
    return true;
  }).sort((a, b) => a.x - b.x);


  // --- Input Line (Building from processedActualValues) ---
  let visibleActualXY = [];

  // Filter processedActualValues based on the current chart window and visualCurrentTick
  const relevantProcessedPoints = processedActualValues.value.filter(point =>
    point.x >= xMin.value && point.x <= visualCurrentTick.value
  ).sort((a, b) => a.x - b.x);

  // Add the point at xMin if necessary, using the value from the last known actual point *before* xMin
  if (relevantProcessedPoints.length > 0 && relevantProcessedPoints[0].x > xMin.value) {
      // Find the last processed actual point that occurred BEFORE xMin (or at xMin)
      const precedingPointForXMin = processedActualValues.value.slice().reverse().find(p => p.x <= xMin.value);
      if (precedingPointForXMin) {
          visibleActualXY.push({ x: xMin.value, y: precedingPointForXMin.y });
      } else if (typeof lastActual.value === 'number') {
          // Fallback if no historical points, use the current interpolated value
          visibleActualXY.push({ x: xMin.value, y: lastActual.value });
      }
  } else if (relevantProcessedPoints.length === 0 && gameState.value === 'playing' && typeof lastActual.value === 'number' && visualCurrentTick.value >= 0) {
      // If no processed points in view yet, but playing, draw flat line from xMin using current value
      visibleActualXY.push({ x: xMin.value, y: lastActual.value });
  }

  // Add all filtered backend points
  visibleActualXY.push(...relevantProcessedPoints);

  // Add the current interpolated visual position point LAST. This is the "tip" of the input line.
  if (gameState.value === 'playing' && typeof lastActual.value === 'number' && visualCurrentTick.value >= 0) {
    const currentVisualPoint = { x: visualCurrentTick.value, y: lastActual.value };
    const existingIndex = visibleActualXY.findIndex(p => Math.abs(p.x - currentVisualPoint.x) < 0.0001);
    if (existingIndex !== -1) {
        // Update existing point to be precisely the interpolated point
        visibleActualXY[existingIndex] = currentVisualPoint;
    } else {
        visibleActualXY.push(currentVisualPoint);
    }
  }

  // Final Deduplication and Sorting for input line
  const tempMap = new Map();
  for (const point of visibleActualXY) {
      tempMap.set(point.x.toFixed(5), point);
  }
  const dedupedVisibleActualXY = Array.from(tempMap.values()).sort((a, b) => a.x - b.x);


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
        data: dedupedVisibleActualXY,
        borderColor: 'limegreen',
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0,
        stepped: 'after',
        order: 0
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 0
  },
  parsing: false,
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
      type: 'linear',
      ticks: {
        color: 'black',
        callback: function(value) {
            const step = 1;
            if (value % step === 0) {
              return `${Math.floor(value)}s`;
            }
            return null;
        },
        maxTicksLimit: chartWindowDuration + 1,
      },
      grid: { color: 'rgba(0,0,0,0.05)' }
    }
  },
  plugins: {
    legend: {
      labels: {
        color: 'black',
        filter: item => ['Input', 'Target'].includes(item.text),
        generateLabels: function(chart) {
            const defaultLabels = ChartJS.defaults.plugins.legend.labels.generateLabels(chart);
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
    },
    toleranceFill: {
        backgroundColor: 'rgba(255, 200, 0, 0.2)',
        toleranceValue: tolerance
    }
  }
}))

function runGameLoop() {
  function loop(currentTime) {
    if (gameState.value !== 'playing') {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
        console.log('[LOOP-STOP] runGameLoop: stopping animation frame.');
      }
      return;
    }

    const elapsedSinceLastTick = (currentTime - lastTickReceivedTime) / 1000; // in seconds
    if (currentBackendTickValueAtLastMessage !== -1 && initialBackendTickOffset.value !== -1) { // Ensure initial values are set
        // Calculate visualCurrentTick based on the initial offset
        visualCurrentTick.value = (currentBackendTickValueAtLastMessage - initialBackendTickOffset.value) + elapsedSinceLastTick;
        // Cap visualCurrentTick at the effective game duration for the client
        const effectiveGameDuration = gameTotalTicks.value - initialBackendTickOffset.value;
        visualCurrentTick.value = Math.min(visualCurrentTick.value, effectiveGameDuration);
    } else {
        // If initialBackendTickOffset is not yet determined, or no ticks received, visualCurrentTick stays at 0
        visualCurrentTick.value = 0;
    }

    console.log(`[LOOP] visualCurrentTick=${visualCurrentTick.value.toFixed(2)}, xMin=${xMin.value.toFixed(2)}, xMax=${xMax.value.toFixed(2)}, inputX=${inputX.value.toFixed(2)}, Timer: ${Math.max(0, (gameTotalTicks.value - initialBackendTickOffset.value) - Math.floor(visualCurrentTick.value) - 1)}s`);

    if (chartRef.value?.chart) {
      chartRef.value.chart.update('none');
    }

    animationFrameId = requestAnimationFrame(loop)
  }

  console.log('[LOOP-START] runGameLoop: Starting animation frame loop.');
  animationFrameId = requestAnimationFrame(loop)
}

function connectWebSocket() {
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = import.meta.env.DEV ? 'localhost:8000' : location.host;
  const socket = new WebSocket(`${wsProtocol}//${wsHost}/ws/game/${name.value}/${difficulty.value}`);

  socket.onopen = () => {
    console.log("WebSocket opened.");
  };

  let initialOffsetDetermined = false; // Flag to ensure offset is set only once after game starts playing

  socket.onmessage = event => {
    const data = JSON.parse(event.data);

    if (data.type === 'init') {
      console.log("Received 'init' message:", data);
      targetCurve.value = data.targetCurve;
      gameTotalTicks.value = data.duration; // Raw total duration from backend

      // Reset all relevant state for a new game
      initialBackendTickOffset.value = -1; // Indicate it's not yet determined
      initialOffsetDetermined = false;
      rawActualBuffer.value = []; // Clear buffer
      processedActualValues.value = []; // Clear processed data
      lastActual.value = 0;
      score.value = 0;
      visualCurrentTick.value = -1; // Reset to indicate no progress yet

      fullSteppedTargetXY.value = getSteppedCurveWithXY(targetCurve.value, gameTotalTicks.value, fps);

      gameState.value = 'countdown';
      const countdownTimer = setInterval(() => {
        countdown.value--;
        console.log('Countdown:', countdown.value);
        if (countdown.value <= 0) {
          clearInterval(countdownTimer);
          gameState.value = 'playing';
          console.log('Countdown finished, gameState set to playing. Starting runGameLoop.');

          // Now that game is playing, process the buffered raw ticks and set the initial offset
          if (!initialOffsetDetermined && rawActualBuffer.value.length > 0) {
              // The initialBackendTickOffset is the tickNumber of the very first data point we received
              initialBackendTickOffset.value = rawActualBuffer.value[0].x;
              initialOffsetDetermined = true;
              console.log(`[OFFSET-SET] Game started playing. First buffered raw tick: ${initialBackendTickOffset.value}. Setting initialBackendTickOffset.`);

              // Process all buffered raw ticks and add to processedActualValues
              processedActualValues.value = rawActualBuffer.value.map(p => ({
                  x: p.x - initialBackendTickOffset.value,
                  y: p.y
              })).sort((a, b) => a.x - b.x);

              // Initialize interpolation state with the *last* buffered raw tick
              const lastBufferedTick = rawActualBuffer.value[rawActualBuffer.value.length - 1];
              currentBackendTickValueAtLastMessage = lastBufferedTick.x;
              lastActual.value = lastBufferedTick.y; // Ensure lastActual is current
              lastTickReceivedTime = performance.now(); // Record current time for interpolation base

              // Set visualCurrentTick to match the last processed point for a smooth start
              visualCurrentTick.value = lastBufferedTick.x - initialBackendTickOffset.value;

              console.log(`[CLIENT-INIT] Interpolation base set: rawTick=${currentBackendTickValueAtLastMessage}, offset=${initialBackendTickOffset.value}, visualCurrentTick=${visualCurrentTick.value.toFixed(2)}`);

          } else if (!initialOffsetDetermined && rawActualBuffer.value.length === 0) {
              // This case means no ticks were received during countdown.
              // The very first tick received in 'playing' state will set the offset.
              initialBackendTickOffset.value = 0; // Temporarily set to 0, will be overwritten by first tick if needed
              initialOffsetDetermined = true; // Mark as determined (will use 0 or first tick)
              currentBackendTickValueAtLastMessage = 0; // Assume 0 if no ticks yet
              lastTickReceivedTime = performance.now();
              visualCurrentTick.value = 0;
              console.log("[OFFSET-SET] Game started playing. No buffered ticks. Assuming initialBackendTickOffset = 0.");
          }


          runGameLoop();
        }
      }, 1000);
    } else if (data.type === 'tick') {
        // console.log(`[RAW-TICK] data.tickNumber=${data.tickNumber}, gameState=${gameState.value}`);
        if (typeof data.actual === 'number') {
            lastActual.value = data.actual; // Always keep track of the latest actual value
        }
        if (typeof data.totalScore === 'number') {
            score.value = data.totalScore;
        }

        if (typeof data.tickNumber === 'number') {
            // Always buffer raw ticks, regardless of gameState
            const existingRawIndex = rawActualBuffer.value.findIndex(p => p.x === data.tickNumber);
            if (existingRawIndex === -1) {
                rawActualBuffer.value.push({ x: data.tickNumber, y: data.actual });
            } else {
                rawActualBuffer.value[existingRawIndex].y = data.actual;
            }
            rawActualBuffer.value.sort((a,b) => a.x - b.x);


            if (gameState.value === 'playing') {
                // If initial offset hasn't been determined yet (e.g., no ticks during countdown),
                // use the very first tick received while playing to set it.
                if (!initialOffsetDetermined) {
                    initialBackendTickOffset.value = data.tickNumber;
                    initialOffsetDetermined = true;
                    console.log(`[OFFSET-SET] First tick received in playing state: data.tickNumber=${data.tickNumber}, setting initialBackendTickOffset=${initialBackendTickOffset.value}`);

                    // Process all currently buffered raw ticks
                    processedActualValues.value = rawActualBuffer.value.map(p => ({
                        x: p.x - initialBackendTickOffset.value,
                        y: p.y
                    })).sort((a, b) => a.x - b.x);

                    // Ensure visualCurrentTick starts from 0 (client's perspective)
                    visualCurrentTick.value = 0;
                    currentBackendTickValueAtLastMessage = data.tickNumber; // Base for interpolation
                    lastTickReceivedTime = performance.now(); // Base for interpolation time

                } else {
                    // Game is playing, initial offset determined.
                    // Add the current tick data to processedActualValues
                    const offsetCorrectedTick = data.tickNumber - initialBackendTickOffset.value;
                    const existingProcessedIndex = processedActualValues.value.findIndex(p => Math.abs(p.x - offsetCorrectedTick) < 0.0001);
                    if (existingProcessedIndex === -1) {
                        processedActualValues.value.push({ x: offsetCorrectedTick, y: data.actual });
                    } else {
                        processedActualValues.value[existingProcessedIndex].y = data.actual;
                    }
                    processedActualValues.value.sort((a,b) => a.x - b.x);
                }

                // Always update these for interpolation base with raw backend tick values
                currentBackendTickValueAtLastMessage = data.tickNumber;
                lastTickReceivedTime = performance.now(); // Record time when *this specific tick message* was received

                console.log(`[TICK-PROCESS] RawTick=${data.tickNumber}, OffsetCorrectedTick=${(data.tickNumber - initialBackendTickOffset.value).toFixed(2)}, lastActual=${data.actual.toFixed(2)}, currentBackendTickValueAtLastMessage=${currentBackendTickValueAtLastMessage}, lastTickReceivedTime=${lastTickReceivedTime.toFixed(2)}`);
            }
        } else {
            console.error("Tick message received, but 'tickNumber' is missing or not a number!", data);
        }
    } else if (data.type === 'end') {
        console.log("Received 'end' message from backend:", data);

        gameState.value = 'ended';
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
            console.log('[LOOP-STOP] Game ended: animation frame stopped.');
        }

        router.push({ path: '/end', query: { score: data.score, name: name.value, difficulty: difficulty.value } });

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

onMounted(() => {
  console.log('Component mounted. Connecting WebSocket.');
  connectWebSocket();
});

watch(visualCurrentTick, (newValue, oldValue) => {
    // console.log(`visualCurrentTick changed from ${oldValue?.toFixed(2)} to ${newValue.toFixed(2)}. gameState: ${gameState.value}`);
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