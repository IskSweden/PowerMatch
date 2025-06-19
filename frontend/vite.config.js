import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/', // <-- this is key for FastAPI serving from root
  plugins: [vue()]
})
