window.onerror = function(message, source, lineno, colno, error) {
  console.error("Global error:", message, source, lineno, colno, error);
};

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
