<template>
  <div class="stack">
    <section class="panel" style="padding: 24px">
      <div class="button-row" style="justify-content: space-between; align-items: start">
        <div>
          <div class="muted">Dashboard en vivo</div>
          <h2 class="section-title" style="font-size: 1.8rem">{{ pollId }}</h2>
          <p class="muted">Escucha actualizaciones SSE y refresca resultados cada pocos segundos.</p>
        </div>
        <div class="button-row" style="align-items: center">
          <label class="pill draft" style="gap: 8px; display: inline-flex; align-items: center; cursor: pointer">
            <input v-model="privacyMode" type="checkbox" />
            Privacidad
          </label>
          <button class="btn secondary" type="button" @click="connect">Reconectar</button>
        </div>
      </div>
    </section>

    <section v-if="error" class="card" style="border-color: rgba(255,125,125,0.32)">
      {{ error }}
    </section>

    <section class="grid two">
      <article v-for="category in results" :key="category.category_id" class="panel" style="padding: 22px">
        <div class="button-row" style="justify-content: space-between">
          <div>
            <div class="muted">Categoría</div>
            <h3 style="margin: 4px 0 0">{{ category.category_name }}</h3>
          </div>
          <span class="pill open">{{ category.total_votes }} votos</span>
        </div>

        <div class="stack subtle-border" style="margin-top: 14px">
          <div v-for="item in category.results" :key="item.option_id" class="card">
            <div class="button-row" style="justify-content: space-between">
              <strong>{{ privacyMode ? `Opción ${item.total_votes > 0 ? 'con votos' : 'oculta'}` : item.option_name }}</strong>
              <span class="pill draft">{{ item.score.toFixed(4) }}</span>
            </div>
            <div class="muted">Votos: {{ item.total_votes }}</div>
            <div
              style="
                height: 10px;
                margin-top: 10px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.08);
                overflow: hidden;
              "
            >
              <div
                style="height: 100%; background: linear-gradient(90deg, #78ffd6, #7c8cff)"
                :style="{ width: `${Math.max(item.score * 100, item.total_votes ? 12 : 0)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { streamDashboard } from '../../api/voting'

const props = defineProps({
  id: { type: String, required: true },
})

const pollId = props.id
const results = ref([])
const error = ref(null)
const privacyMode = ref(true)
let eventSource = null

function connect() {
  if (eventSource) {
    eventSource.close()
  }

  eventSource = new EventSource(streamDashboard(pollId), { withCredentials: true })

  eventSource.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      results.value = payload.categories || []
    } catch (err) {
      error.value = 'No se pudo parsear el dashboard SSE.'
    }
  }

  eventSource.addEventListener('error', (event) => {
    error.value = 'Se perdió la conexión SSE. Reintentando...'
  })
}

onMounted(connect)
onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>
