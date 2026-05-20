<template>
  <div class="stack">
    <section class="panel" style="padding: 24px" v-if="poll">
      <div class="button-row" style="justify-content: space-between; align-items: start">
        <div>
          <div class="muted">Poll</div>
          <h2 class="section-title" style="font-size: 1.9rem">{{ poll.title }}</h2>
          <p class="muted">{{ poll.description || 'Sin descripción' }}</p>
        </div>
        <span class="pill" :class="poll.status">{{ poll.status }}</span>
      </div>

      <div class="button-row" style="margin-top: 16px">
        <button class="btn small secondary" type="button" @click="setStatus('open')">Abrir</button>
        <button class="btn small secondary" type="button" @click="setStatus('closed')">Cerrar</button>
        <button class="btn small secondary" type="button" @click="exportReport">Descargar reporte</button>
        <button class="btn small secondary" type="button" @click="reload">Recargar</button>
      </div>
    </section>

    <section class="grid two">
      <article class="panel" style="padding: 24px">
        <h3>Grupos de votantes</h3>
        <form class="field-grid subtle-border" @submit.prevent="addGroup">
          <label class="field">
            <span>Nombre</span>
            <input v-model="groupForm.name" required />
          </label>
          <label class="field">
            <span>Peso</span>
            <input v-model.number="groupForm.weight" type="number" min="0" max="1" step="0.01" required />
          </label>
          <button class="btn small" type="submit">Agregar grupo</button>
        </form>

        <div class="stack subtle-border" style="margin-top: 14px">
          <article v-for="group in groups" :key="group.id" class="card">
            <div class="button-row" style="justify-content: space-between">
              <div>
                <strong>{{ group.name }}</strong>
                <div class="muted">Peso: {{ group.weight }}</div>
                <div class="muted" style="font-size: 0.9rem">Token: {{ group.token }}</div>
              </div>
              <div class="button-row">
                <button class="btn small secondary" @click="editGroup(group)">Editar</button>
                <button class="btn small danger" @click="removeGroup(group.id)">Borrar</button>
              </div>
            </div>
          </article>
        </div>
      </article>

      <article class="panel" style="padding: 24px">
        <h3>Categorías</h3>
        <form class="field-grid subtle-border" @submit.prevent="addCategory">
          <label class="field">
            <span>Nombre</span>
            <input v-model="categoryForm.name" required />
          </label>
          <label class="field">
            <span>Orden</span>
            <input v-model.number="categoryForm.order" type="number" min="0" step="1" required />
          </label>
          <button class="btn small" type="submit">Agregar categoría</button>
        </form>

        <div class="stack subtle-border" style="margin-top: 14px">
          <article v-for="category in categories" :key="category.id" class="card">
            <div class="button-row" style="justify-content: space-between">
              <div>
                <strong>{{ category.name }}</strong>
                <div class="muted">Orden: {{ category.order }}</div>
              </div>
              <div class="button-row">
                <button class="btn small secondary" @click="editCategory(category)">Editar</button>
                <button class="btn small danger" @click="removeCategory(category.id)">Borrar</button>
              </div>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section class="panel" style="padding: 24px">
      <h3>Editar selección</h3>
      <div class="grid two">
        <form class="field-grid" @submit.prevent="saveGroup" v-if="selectedGroup">
          <label class="field">
            <span>Grupo</span>
            <input v-model="selectedGroup.name" />
          </label>
          <label class="field">
            <span>Peso</span>
            <input v-model.number="selectedGroup.weight" type="number" min="0" max="1" step="0.01" />
          </label>
          <button class="btn small" type="submit">Guardar grupo</button>
        </form>

        <form class="field-grid" @submit.prevent="saveCategory" v-if="selectedCategory">
          <label class="field">
            <span>Nombre</span>
            <input v-model="selectedCategory.name" />
          </label>
          <label class="field">
            <span>Orden</span>
            <input v-model.number="selectedCategory.order" type="number" min="0" step="1" />
          </label>
          <button class="btn small" type="submit">Guardar categoría</button>
        </form>
      </div>
    </section>

    <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { downloadReport } from '../../api/polls'
import { usePollsStore } from '../../stores/polls'

const route = useRoute()
const pollsStore = usePollsStore()
const poll = computed(() => pollsStore.currentPoll)
const groups = ref([])
const categories = ref([])
const selectedGroup = ref(null)
const selectedCategory = ref(null)
const error = ref(null)

const groupForm = reactive({ name: '', weight: 1 })
const categoryForm = reactive({ name: '', order: 0 })

async function reload() {
  const id = route.params.id
  await pollsStore.loadPoll(id)
  groups.value = await pollsStore.loadGroups(id)
  categories.value = await pollsStore.loadCategories(id)
}

async function setStatus(status) {
  try {
    await pollsStore.transitionStatus(route.params.id, status)
    await reload()
  } catch (err) {
    error.value = err.message
  }
}

async function exportReport() {
  const blob = await downloadReport(route.params.id)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `poll-${route.params.id}.xlsx`
  anchor.click()
  URL.revokeObjectURL(url)
}

async function addGroup() {
  await pollsStore.createGroup(route.params.id, groupForm)
  groupForm.name = ''
  groupForm.weight = 1
  await reload()
}

async function addCategory() {
  await pollsStore.createCategory(route.params.id, categoryForm)
  categoryForm.name = ''
  categoryForm.order = 0
  await reload()
}

function editGroup(group) {
  selectedGroup.value = { ...group }
}

async function saveGroup() {
  await pollsStore.updateGroup(route.params.id, selectedGroup.value.id, selectedGroup.value)
  selectedGroup.value = null
  await reload()
}

async function removeGroup(id) {
  if (!window.confirm('¿Borrar grupo?')) return
  await pollsStore.deleteGroup(route.params.id, id)
  await reload()
}

function editCategory(category) {
  selectedCategory.value = { ...category }
}

async function saveCategory() {
  await pollsStore.updateCategory(route.params.id, selectedCategory.value.id, selectedCategory.value)
  selectedCategory.value = null
  await reload()
}

async function removeCategory(id) {
  if (!window.confirm('¿Borrar categoría?')) return
  await pollsStore.deleteCategory(route.params.id, id)
  await reload()
}

onMounted(reload)
</script>
