<template>
  <div class="wrapper" @keydown.enter="playAgain" tabindex="0">
    <div class="card">
      <h1>Game Over</h1>

      <p class="message">Well done, <strong>{{ name }}</strong>!</p>
      <p>Your score: <span class="score">{{ score }}</span></p>
      <p>Difficulty: <span class="difficulty">{{ difficulty }}</span></p>

      <div v-if="isHighscore" class="highlight">
        New High Score!
      </div>

      <button ref="playButton" @click="playAgain">Play Again</button>

      <div class="leaderboard" v-if="highscores">
        <h2>All-Time Top 5</h2>
        <ul>
          <li v-for="(entry, i) in highscores.alltime" :key="'a' + i">
            <span class="rank">#{{ i + 1 }}</span>
            <span class="entry">{{ entry.name }}</span>
            <span class="score">{{ entry.score }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const name = ref(route.query.name || 'Player')
const score = ref(route.query.score || 0)
const difficulty = ref(route.query.difficulty || 'Medium')
const highscores = ref(null)
const isHighscore = ref(false)
const playButton = ref(null)


const callHighscoreAPI = () => {
  fetch('esp32-F57EF4.local/api/highscore') // REPLACE url
    .catch(e => console.error('failed t call highscore API', e))
}

const fetchHighscores = async () => {
  try {
    const res = await fetch('/api/highscores')
    const data = await res.json()
    highscores.value = data

    isHighscore.value = [...data.alltime, ...data.recent]
      .some(entry => entry.name === name.value && entry.score === +score.value)

    if (isHighscore.value) {
      callHighscoreAPI() // HIGHSCORE API CALL
    }
  } catch (e) {
    console.error('Failed to fetch highscores:', e)
  }
}

const playAgain = () => {
  router.push('/')
}

onMounted(() => {
  fetchHighscores()
  playButton.value?.focus()
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

.message {
  font-size: 1.2rem;
  margin: 1rem 0;
}

.score {
  font-weight: bold;
  font-size: 1.5rem;
  color: rgb(0, 54, 69);
}

.difficulty {
  font-weight: 600;
  color: rgb(0, 54, 69);
}

.highlight {
  margin-top: 1rem;
  font-size: 1.1rem;
  color: rgb(139, 191, 128);
  font-weight: bold;
}

button {
  margin-top: 1.5rem;
  background: rgb(0, 54, 69);
  color: white;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 0.4rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

button:hover {
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
