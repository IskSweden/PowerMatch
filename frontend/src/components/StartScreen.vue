<template>
  <div class="wrapper" @keydown="handleKey">
    <div class="card">
      <h1>⚡ PowerMatch</h1>

      <div class="form">
        <label>
          Name:
          <input
            ref="nameInput"
            v-model="name"
            placeholder="Enter your name"
            @keydown.enter.prevent="startGame"
          />
        </label>

        <label>
          Difficulty:
          <select
            ref="difficultySelect"
            v-model="difficulty"
            @keydown.down.prevent="nextDifficulty"
            @keydown.up.prevent="prevDifficulty"
          >
            <option>Easy</option>
            <option>Medium</option>
            <option>Hard</option>
          </select>
        </label>

        <button
          ref="startButton"
          @click="startGame"
          :disabled="!name"
          @keydown.enter.prevent="startGame"
        >
          Start Game
        </button>
      </div>

      <div class="leaderboard" v-if="highscores">
        <h2>All-Time Top 5</h2>
        <ul>
          <li v-for="(entry, i) in highscores.alltime" :key="'a'+i">
            <span class="rank">#{{ i + 1 }}</span>
            <span class="entry">{{ entry.name }}</span>
            <span class="score">{{ entry.score }}</span>
          </li>
        </ul>

        <h3>Recent (24h)</h3>
        <ul>
          <li v-for="(entry, i) in highscores.recent" :key="'r'+i">
            <span class="entry">{{ entry.name }}</span>
            <span class="score">{{ entry.score }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const name = ref('')
const difficulty = ref('Medium')
const highscores = ref(null)

const nameInput = ref(null)
const difficultySelect = ref(null)
const startButton = ref(null)

const fetchHighscores = async () => {
  try {
    const res = await fetch('/api/highscores')
    highscores.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch highscores:', e)
  }
}

const startGame = () => {
  if (!name.value) return
  router.push({
    path: '/game',
    query: {
      name: name.value,
      difficulty: difficulty.value
    }
  })
}

const nextDifficulty = () => {
  const order = ['Easy', 'Medium', 'Hard']
  const index = order.indexOf(difficulty.value)
  if (index < order.length - 1) difficulty.value = order[index + 1]
}
const prevDifficulty = () => {
  const order = ['Easy', 'Medium', 'Hard']
  const index = order.indexOf(difficulty.value)
  if (index > 0) difficulty.value = order[index - 1]
}

const handleKey = (e) => {
  if (e.key === 'Tab') {
    // allow normal tabbing
  } else if (e.key === 'Enter') {
    startGame()
  }
}

onMounted(() => {
  fetchHighscores()
  nameInput.value?.focus()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

* {
  font-family: 'Poppins', sans-serif;
  box-sizing: border-box;
}

.wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: rgb(0, 117, 130);
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 1rem;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
  text-align: center;
}

h1 {
  color: rgb(139, 191, 128);
}

input,
select {
  margin-top: 0.5rem;
  margin-bottom: 1rem;
  width: 80%;
  padding: 0.5rem;
  font-size: 1rem;
  border-radius: 0.4rem;
  border: 2px solid rgb(0, 54, 69);
}

input:focus,
select:focus {
  outline: 2px solid rgb(139, 191, 128);
}

button {
  background: rgb(0, 54, 69);
  color: white;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 0.4rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

button:disabled {
  background: #888;
  cursor: not-allowed;
}

button:hover:enabled {
  background: rgb(0, 40, 50);
}

.leaderboard {
  text-align: left;
  margin-top: 2rem;
}

.leaderboard ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.leaderboard li {
  display: flex;
  justify-content: space-between;
  padding: 0.3rem 0;
  border-bottom: 1px solid #eee;
  font-size: 0.95rem;
}

.rank {
  font-weight: bold;
  margin-right: 0.5rem;
  color: rgb(139, 191, 128);
}

.entry {
  flex: 1;
}

.score {
  font-weight: bold;
}
</style>
