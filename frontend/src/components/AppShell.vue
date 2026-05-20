<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>
          <div class="brand-title">Votaciones V2</div>
          <div class="muted">Administracion</div>
        </div>
      </div>

      <nav class="nav-links">
        <RouterLink class="nav-link" :to="{ name: 'dashboard' }">Votaciones</RouterLink>
        <RouterLink class="nav-link" :to="{ name: 'users' }">Usuarios</RouterLink>
        <RouterLink class="nav-link" :to="{ name: 'import' }">Cargar candidatos</RouterLink>
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
        <div class="muted">Plataforma interna · modo administracion</div>
        <h1>Administra votaciones, usuarios y reportes desde un panel claro.</h1>
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
