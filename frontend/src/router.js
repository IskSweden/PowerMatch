import { createRouter, createWebHistory } from 'vue-router'
import StartGame from './views/StartGame.vue'
import PowerCurveGame from './views/PowerCurveGame.vue'

const routes = [
  { path: '/', component: StartGame },
  { path: '/game', component: PowerCurveGame }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
