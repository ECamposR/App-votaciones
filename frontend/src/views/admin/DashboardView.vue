<template>
  <div class="stack">
    <section class="grid three">
      <article class="card kpi">
        <span class="muted">Votaciones</span>
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
          <h2 class="section-title" style="font-size: 1.6rem">Votaciones</h2>
          <div class="muted">Crea una votacion, preparala y siguela hasta cerrarla.</div>
        </div>
        <button class="btn secondary" type="button" @click="refresh">Actualizar</button>
      </div>

      <form class="grid two subtle-border" style="margin-top: 16px" @submit.prevent="create">
        <label class="field">
          <span>Titulo de la votacion</span>
          <input v-model="form.title" required />
        </label>
        <label class="field">
          <span>Tipo de votacion</span>
          <select v-model="form.voting_type">
            <option v-for="option in votingTypeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field" style="grid-column: 1 / -1">
          <span>Descripción</span>
          <textarea v-model="form.description" rows="3"></textarea>
        </label>
        <div class="button-row" style="grid-column: 1 / -1">
          <button class="btn" type="submit" :disabled="loading">Crear votacion</button>
          <span v-if="error" class="muted" style="color: var(--danger)">{{ error }}</span>
        </div>
      </form>
    </section>

    <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>

    <section v-if="polls.length" class="grid two">
      <article v-for="poll in polls" :key="poll.id" class="card stack">
        <div class="button-row" style="justify-content: space-between; align-items: start">
          <div>
            <h3 style="margin-bottom: 4px">{{ poll.title }}</h3>
            <div class="muted">{{ poll.description || 'Sin descripcion' }}</div>
          </div>
          <span class="pill" :class="poll.status">{{ getPollStatusLabel(poll.status) }}</span>
        </div>

        <div class="muted">Tipo: {{ getVotingTypeLabel(poll.voting_type) }}</div>
        <div class="muted">
          {{ metaFor(poll.id).groupCount }} grupos · {{ metaFor(poll.id).categoryCount }} categorias
        </div>
        <div class="muted">Siguiente paso: {{ getDashboardNextAction(poll, metaFor(poll.id)) }}</div>

        <div class="button-row">
          <RouterLink class="btn small secondary" :to="{ name: 'poll-detail', params: { id: poll.id } }">
            Configurar
          </RouterLink>
          <RouterLink class="btn small secondary" :to="{ name: 'live-dashboard', params: { id: poll.id } }">
            Resultados en vivo
          </RouterLink>
          <button class="btn small secondary" type="button" @click="openImport(poll.id)">
            Cargar candidatos
          </button>
          <button class="btn small danger" type="button" @click="removePoll(poll.id)">Eliminar</button>
        </div>
      </article>
    </section>

    <section v-else class="panel" style="padding: 24px">
      <h3 style="margin-top: 0">Aun no hay votaciones</h3>
      <p class="muted">Crea la primera votacion para empezar a configurar grupos, candidatos y enlaces.</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { usePollsStore } from '../../stores/polls'
import {
  getDashboardNextAction,
  getPollStatusLabel,
  getVotingTypeLabel,
  votingTypeOptions,
} from '../../utils/pollPresentation'

const auth = useAuthStore()
const pollsStore = usePollsStore()
const router = useRouter()
const polls = computed(() => pollsStore.polls)
const loading = ref(false)
const error = ref(null)
const pollMeta = ref({})

const form = reactive({
  title: '',
  description: '',
  voting_type: 'PLURALITY',
})

async function refresh() {
  error.value = null
  try {
    await pollsStore.loadPolls()
    const summaries = await Promise.all(
      polls.value.map(async (poll) => {
        const [groups, categories] = await Promise.all([
          pollsStore.loadGroups(poll.id),
          pollsStore.loadCategories(poll.id),
        ])
        return [
          poll.id,
          {
            groupCount: groups.length,
            categoryCount: categories.length,
          },
        ]
      }),
    )
    pollMeta.value = Object.fromEntries(summaries)
  } catch (err) {
    error.value = err.message
  }
}

function metaFor(id) {
  return pollMeta.value[id] ?? { groupCount: 0, categoryCount: 0 }
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
  if (!window.confirm('¿Eliminar esta votacion?')) return
  await pollsStore.deletePoll(id)
  await refresh()
}

function openImport(id) {
  router.push({ name: 'import', query: { pollId: id } })
}

onMounted(refresh)
</script>
