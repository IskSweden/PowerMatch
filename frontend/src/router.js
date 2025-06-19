import { createRouter, createWebHistory } from 'vue-router'
import StartGame from './views/StartGame.vue'
import PowerCurveGame from './views/PowerCurveGame.vue'
import EndScreen from './views/EndScreen.vue'

const routes = [
  { path: '/', component: StartGame },
  { path: '/game', component: PowerCurveGame },
  { path: '/end', component: EndScreen }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router


// This file sets up the Vue Router for the application, defining routes for the start screen, game screen, and end screen.
// It uses the createRouter and createWebHistory functions from 'vue-router' to manage navigation between different components in the app.
// The routes array maps paths to their respective components, allowing users to navigate through the game flow