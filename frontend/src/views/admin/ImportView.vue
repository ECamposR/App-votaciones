<template>
  <div class="panel" style="padding: 24px">
    <h2 class="section-title" style="font-size: 1.8rem">Cargar candidatos</h2>
    <p class="muted">Sube un CSV o XLSX para crear categorias y candidatos de forma masiva.</p>

    <form class="stack" @submit.prevent="submit">
      <label class="field">
        <span>Votacion</span>
        <select v-model="pollId" required>
          <option value="" disabled>Selecciona una votacion</option>
          <option v-for="poll in polls" :key="poll.id" :value="poll.id">{{ poll.title }}</option>
        </select>
      </label>

      <label class="field">
        <span>Archivo</span>
        <input type="file" accept=".csv,.xlsx" @change="onFile" required />
      </label>

      <div class="button-row">
        <button class="btn" type="submit" :disabled="loading">Cargar candidatos</button>
        <RouterLink v-if="pollId" class="btn secondary" :to="{ name: 'poll-detail', params: { id: pollId } }">
          Ir a la votacion
        </RouterLink>
      </div>

      <p v-if="message" class="muted">{{ message }}</p>
      <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { importOptions } from '../../api/polls'
import { usePollsStore } from '../../stores/polls'

const route = useRoute()
const router = useRouter()
const pollsStore = usePollsStore()
const polls = computed(() => pollsStore.polls)
const pollId = ref(route.query.pollId || '')
const selectedFile = ref(null)
const loading = ref(false)
const message = ref('')
const error = ref(null)

function onFile(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function submit() {
  loading.value = true
  message.value = ''
  error.value = null
  try {
    const result = await importOptions(pollId.value, selectedFile.value)
    message.value = `Importados ${result.options_created} candidatos y ${result.categories_created} categorías.`
    await pollsStore.loadPolls()
    router.push({ name: 'poll-detail', params: { id: pollId.value } })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await pollsStore.loadPolls()
})
</script>
