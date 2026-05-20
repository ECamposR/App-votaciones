<template>
  <div class="stack">
    <section class="grid three">
      <article class="card kpi">
        <span class="muted">Polls</span>
        <strong>{{ polls.length }}</strong>
      </article>
      <article class="card kpi">
        <span class="muted">Autenticado</span>
        <strong>{{ auth.user?.username ?? 'No' }}</strong>
      </article>
      <article class="card kpi">
        <span class="muted">Estado</span>
        <strong>{{ auth.hasSetup ? 'Sistema configurado' : 'Setup pendiente' }}</strong>
      </article>
    </section>

    <section class="panel" style="padding: 24px">
      <div class="button-row" style="justify-content: space-between; align-items: center">
        <div>
          <h2 class="section-title" style="font-size: 1.6rem">Polls</h2>
          <div class="muted">Crea, abre, cierra y administra encuestas.</div>
        </div>
        <button class="btn secondary" type="button" @click="refresh">Actualizar</button>
      </div>

      <form class="grid two subtle-border" style="margin-top: 16px" @submit.prevent="create">
        <label class="field">
          <span>Título</span>
          <input v-model="form.title" required />
        </label>
        <label class="field">
          <span>Tipo</span>
          <select v-model="form.voting_type">
            <option value="PLURALITY">Plurality</option>
            <option value="RANKED">Ranked</option>
            <option value="RATING">Rating</option>
            <option value="YES_NO">Yes/No</option>
          </select>
        </label>
        <label class="field" style="grid-column: 1 / -1">
          <span>Descripción</span>
          <textarea v-model="form.description" rows="3"></textarea>
        </label>
        <div class="button-row" style="grid-column: 1 / -1">
          <button class="btn" type="submit" :disabled="loading">Crear poll</button>
          <span v-if="error" class="muted" style="color: var(--danger)">{{ error }}</span>
        </div>
      </form>
    </section>

    <section class="grid two">
      <article v-for="poll in polls" :key="poll.id" class="card stack">
        <div class="button-row" style="justify-content: space-between; align-items: start">
          <div>
            <h3 style="margin-bottom: 4px">{{ poll.title }}</h3>
            <div class="muted">{{ poll.description || 'Sin descripción' }}</div>
          </div>
          <span class="pill" :class="poll.status">{{ poll.status }}</span>
        </div>

        <div class="muted">Tipo: {{ poll.voting_type }}</div>

        <div class="button-row">
          <RouterLink class="btn small secondary" :to="{ name: 'poll-detail', params: { id: poll.id } }">
            Abrir
          </RouterLink>
          <button class="btn small secondary" type="button" @click="openImport(poll.id)">Importar</button>
          <button class="btn small danger" type="button" @click="removePoll(poll.id)">Eliminar</button>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { usePollsStore } from '../../stores/polls'

const auth = useAuthStore()
const pollsStore = usePollsStore()
const router = useRouter()
const polls = computed(() => pollsStore.polls)
const loading = ref(false)
const error = ref(null)

const form = reactive({
  title: '',
  description: '',
  voting_type: 'PLURALITY',
})

async function refresh() {
  await pollsStore.loadPolls()
}

async function create() {
  loading.value = true
  error.value = null
  try {
    const poll = await pollsStore.createPoll(form)
    form.title = ''
    form.description = ''
    router.push({ name: 'poll-detail', params: { id: poll.id } })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function removePoll(id) {
  if (!window.confirm('¿Eliminar este poll?')) return
  await pollsStore.deletePoll(id)
}

function openImport(id) {
  router.push({ name: 'import', query: { pollId: id } })
}

onMounted(refresh)
</script>
