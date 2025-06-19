<template>
  <div class="end-screen">
    <h1>🎉 Game Over</h1>
    <p>Your Score: {{ score }}</p>

    <router-link to="/">
      <button class="btn">Back to Start</button>
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const score = ref(0)

onMounted(() => {
  score.value = sessionStorage.getItem("finalScore") || 0
})
</script>

<style scoped>
.end-screen {
  text-align: center;
  padding: 5rem;
  font-family: sans-serif;
  background: #1b6b73;
  color: white;
  min-height: 100vh;
}

h1 {
  font-size: 3rem;
  margin-bottom: 2rem;
}

.btn {
  padding: 1rem 2rem;
  font-size: 1.2rem;
  border: none;
  background-color: #b9ec30;
  color: black;
  font-weight: bold;
  border-radius: 0.4rem;
  cursor: pointer;
  margin-top: 2rem;
}
</style>
