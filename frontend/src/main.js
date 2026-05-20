import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { createAppRouter, installRouteGuards } from './router'
import { useAuthStore } from './stores/auth'
import './styles/main.css'

const app = createApp(App)
const pinia = createPinia()
const router = createAppRouter()

app.use(pinia)
app.use(router)

installRouteGuards(router, pinia)

async function bootstrapApp() {
  const authStore = useAuthStore(pinia)
  await authStore.bootstrap()
  app.mount('#app')
}

bootstrapApp().catch((error) => {
  console.error('Failed to bootstrap application:', error)
})
