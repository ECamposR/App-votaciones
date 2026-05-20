<template>
  <div class="layout" style="grid-template-columns: minmax(0, 820px); justify-content: center">
    <section class="panel" style="padding: 28px" v-if="poll">
      <div class="muted">Boleta de votación</div>
      <h1 class="section-title" style="margin-top: 6px">{{ poll.title }}</h1>
      <p class="muted">{{ poll.description || 'Sin descripción' }}</p>

      <div v-if="poll.already_voted" class="card" style="margin-top: 18px; border-color: rgba(120,255,214,0.26)">
        Ya emitiste tu voto en este enlace.
      </div>

      <form v-else class="stack" @submit.prevent="submit">
        <section v-for="category in poll.categories" :key="category.id" class="card">
          <h3 style="margin-top: 0">{{ category.name }}</h3>
          <div class="grid two">
            <label
              v-for="option in category.options"
              :key="option.id"
              class="card"
              style="cursor: pointer; border-color: rgba(140,168,255,0.16)"
            >
              <input
                v-model="selections[category.id]"
                type="radio"
                :name="category.id"
                :value="option.id"
                style="margin-right: 10px"
              />
              <strong>{{ option.name }}</strong>
              <div v-if="option.photo_url" class="muted" style="font-size: 0.9rem">
                {{ option.photo_url }}
              </div>
            </label>
          </div>
        </section>

        <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>

        <div class="button-row">
          <button class="btn" type="submit" :disabled="loading">Enviar voto</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getVotingData, submitVote } from '../../api/voting'

const props = defineProps({
  token: { type: String, required: true },
})

const router = useRouter()
const poll = ref(null)
const loading = ref(false)
const error = ref(null)
const selections = reactive({})

async function load() {
  poll.value = await getVotingData(props.token)
  for (const category of poll.value.categories) {
    selections[category.id] = selections[category.id] || category.options[0]?.id || null
  }
}

async function submit() {
  loading.value = true
  error.value = null
  try {
    const votes = poll.value.categories.map((category) => ({
      category_id: category.id,
      option_id: selections[category.id],
    }))
    await submitVote(props.token, { votes })
    router.push({ name: 'vote-status', params: { token: props.token } })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
