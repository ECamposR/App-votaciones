<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>
          <div class="brand-title">Votaciones V2</div>
          <div class="muted">Admin Console</div>
        </div>
      </div>

      <nav class="nav-links">
        <RouterLink class="nav-link" :to="{ name: 'dashboard' }">Dashboard <span>01</span></RouterLink>
        <RouterLink class="nav-link" :to="{ name: 'users' }">Usuarios <span>02</span></RouterLink>
        <RouterLink class="nav-link" :to="{ name: 'import' }">Importar <span>03</span></RouterLink>
      </nav>

      <div class="subtle-border stack" style="margin-top: 18px">
        <div class="muted">Sesión</div>
        <div>{{ auth.user?.username ?? 'Sin sesión' }}</div>
        <div class="button-row">
          <RouterLink v-if="!auth.user" class="btn secondary small" to="/login">Ingresar</RouterLink>
          <button v-else class="btn secondary small" type="button" @click="signOut">Salir</button>
        </div>
      </div>
    </aside>

    <main class="content">
      <section class="hero">
        <div class="muted">Plataforma interna · modo administración</div>
        <h1>Controla polls, usuarios y exportaciones desde un panel unificado.</h1>
      </section>

      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function signOut() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>
