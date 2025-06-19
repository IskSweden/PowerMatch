<template>
  <div class="start-screen">
    <div class="logo-title">
      <img src="/vite.svg" class="logo" />
      <h1>PowerMatch Challenge</h1>
    </div>

    <div class="start-content">
      <div class="scores">
        <h2>Highscores</h2>
        <div class="score-lists">
          <div>
            <h3>Alltime</h3>
            <ul v-if="alltime.value?.length">
              <li v-for="(score, i) in alltime.value" :key="i">
                {{ score.name }} — {{ score.score }}
              </li>
            </ul>
            <p v-else>No alltime scores yet.</p>
            <h3>Recent Scores</h3>
            <ul v-if="recent.value?.length">
              <li v-for="(score, i) in recent.value" :key="i">
                {{ score.name }} — {{ score.score }}
              </li>
            </ul>
            <p v-else>No recent scores yet.</p>
          </div>
        </div>
      </div>

      <div class="player-config">
        <label>Name</label>
        <input v-model="playerName" placeholder="Your name" />

        <label>Schwierigkeit</label>
        <div class="difficulty">
          <button
            v-for="level in ['Easy', 'Medium', 'Hard']"
            :key="level"
            :class="{ active: difficulty === level }"
            @click="difficulty = level"
          >
            {{ level }}
          </button>
        </div>

        <button class="start-btn" @click="startGame">Start Game</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const playerName = ref('Name')
const difficulty = ref('Medium')

const alltime = ref([])
const recent = ref([])

function startGame() {
  sessionStorage.setItem("playerName", playerName.value || 'Unknown')
  sessionStorage.setItem("difficulty", difficulty.value || 'Medium')

  setTimeout(() => {
    console.log("Saved to session:", playerName.value, difficulty.value)
    router.push('/game')
  }, 10)
}

onMounted(async () => {
  try {
    const res = await fetch("/api/highscores")
    const data = await res.json()

    console.log("Fetched highscores:", data)
    console.log("Is alltime an array?", Array.isArray(data.alltime))

    alltime.value = Array.isArray(data.alltime) ? data.alltime : []
    recent.value = Array.isArray(data.recent) ? data.recent : []
  } catch (err) {
    console.error("❌ Failed to fetch highscores", err)
  }
})
</script>

<style scoped>
.start-screen {
  background-color: #1b6b73;
  color: white;
  min-height: 100vh;
  padding: 2rem;
  font-family: sans-serif;
}

.logo-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 2rem;
}

.logo {
  width: 50px;
}

.start-content {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.scores {
  background-color: #004f5c;
  padding: 1.5rem;
  border-radius: 1rem;
  min-width: 300px;
}

.scores h2, .scores h3 {
  margin-bottom: 0.5rem;
}

.score-lists {
  display: flex;
  gap: 2rem;
}

.player-config {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 250px;
}

input {
  padding: 0.5rem;
  font-size: 1rem;
  border-radius: 0.4rem;
  border: none;
  background-color: #0e4a56;
  color: white;
}

.difficulty button {
  margin-right: 1rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.4rem;
  background-color: #0e4a56;
  color: white;
  cursor: pointer;
}

.difficulty button.active {
  background-color: #b9ec30;
  color: black;
  font-weight: bold;
}

.start-btn {
  background-color: #b9ec30;
  color: black;
  padding: 1rem;
  font-size: 1.2rem;
  font-weight: bold;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  margin-top: 1rem;
}
</style>
