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
            <ul>
              <li v-for="(score, i) in alltime" :key="i">{{ score.name }} — {{ score.score }}</li>
            </ul>
          </div>
          <div>
            <h3>Last 24 h</h3>
            <ul>
              <li v-for="(score, i) in recent" :key="i">{{ score.name }} — {{ score.score }}</li>
            </ul>
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

        <router-link to="/game">
          <button class="start-btn">Start</button>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const playerName = ref('Finn')
const difficulty = ref('Hard')

// dummy data for now
const alltime = [
  { name: 'Finn', score: 7822 },
  { name: 'Lara', score: 7310 },
  { name: 'Jonas', score: 6892 },
  { name: 'Nico', score: 6645 },
  { name: 'Emma', score: 6308 }
]

const recent = [
  { name: 'Felix', score: 3823 },
  { name: 'Jakob', score: 3651 },
  { name: 'Mia', score: 3541 },
  { name: 'Tom', score: 3427 },
  { name: 'Anna', score: 3309 }
]
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
