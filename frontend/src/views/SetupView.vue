<template>
  <div class="layout" style="grid-template-columns: minmax(0, 560px); justify-content: center">
    <section class="panel" style="padding: 32px">
      <div class="muted">Primer arranque</div>
      <h1 class="section-title" style="margin-top: 6px">Crear administrador inicial</h1>
      <p class="muted">
        Este formulario solo funciona si todavía no existe ningún usuario en el sistema.
      </p>

      <form class="stack" @submit.prevent="submit">
        <div class="field-grid">
          <label class="field">
            <span>Usuario</span>
            <input v-model="form.username" autocomplete="username" required />
          </label>
          <label class="field">
            <span>Contraseña</span>
            <input v-model="form.password" type="password" autocomplete="new-password" required />
          </label>
        </div>

        <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>

        <div class="button-row">
          <button class="btn" type="submit" :disabled="loading">
            {{ loading ? 'Creando...' : 'Crear administrador' }}
          </button>
          <RouterLink class="btn secondary" to="/login">Ir a login</RouterLink>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const error = ref(null)
const form = reactive({
  username: '',
  password: '',
})

async function submit() {
  loading.value = true
  error.value = null
  try {
    await auth.createInitialAdmin(form)
    router.push({ name: 'login' })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>
