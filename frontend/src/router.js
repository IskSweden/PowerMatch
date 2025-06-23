import { createRouter, createWebHistory } from 'vue-router'
import StartScreen from './components/StartScreen.vue'
import GameView from './components/GameView.vue'
import EndScreen from './components/EndScreen.vue'

const routes = [
  { path: '/', component: StartScreen },
  { path: '/game', component: GameView },
  { path: '/end', component: EndScreen }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
