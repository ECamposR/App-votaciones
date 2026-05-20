<template>
  <div class="stack">
    <section class="panel" style="padding: 24px">
      <h2 class="section-title" style="font-size: 1.8rem">Usuarios administrativos</h2>
      <p class="muted">Crea, desactiva, edita y cambia contraseñas de administradores y operadores.</p>

      <form class="grid two subtle-border" style="margin-top: 16px" @submit.prevent="create">
        <label class="field">
          <span>Usuario</span>
          <input v-model="createForm.username" required />
        </label>
        <label class="field">
          <span>Contraseña</span>
          <input v-model="createForm.password" type="password" required />
        </label>
        <label class="field">
          <span>Rol</span>
          <select v-model="createForm.role">
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <div class="button-row" style="align-self: end">
          <button class="btn" type="submit">Crear usuario</button>
          <button class="btn secondary" type="button" @click="refresh">Actualizar</button>
        </div>
      </form>
    </section>

    <section class="panel" style="padding: 24px">
      <table class="table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Rol</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <strong>{{ user.username }}</strong>
              <div class="muted" style="font-size: 0.9rem">{{ user.id }}</div>
            </td>
            <td>{{ user.role }}</td>
            <td>{{ user.is_active ? 'Sí' : 'No' }}</td>
            <td>
              <div class="button-row">
                <button class="btn small secondary" @click="selectUser(user)">Editar</button>
                <button class="btn small danger" @click="remove(user.id)">Eliminar</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="grid two" v-if="selected">
      <article class="panel" style="padding: 24px">
        <h3>Editar usuario</h3>
        <form class="stack" @submit.prevent="save">
          <label class="field">
            <span>Usuario</span>
            <input v-model="editForm.username" />
          </label>
          <label class="field">
            <span>Rol</span>
            <select v-model="editForm.role">
              <option value="operator">Operator</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label class="field">
            <span>Activo</span>
            <select v-model="editForm.is_active">
              <option :value="true">Sí</option>
              <option :value="false">No</option>
            </select>
          </label>
          <button class="btn" type="submit">Guardar</button>
        </form>
      </article>

      <article class="panel" style="padding: 24px">
        <h3>Cambiar contraseña</h3>
        <form class="stack" @submit.prevent="changeUserPassword">
          <label class="field">
            <span>Contraseña actual</span>
            <input v-model="passwordForm.current_password" type="password" />
          </label>
          <label class="field">
            <span>Nueva contraseña</span>
            <input v-model="passwordForm.new_password" type="password" />
          </label>
          <button class="btn" type="submit">Actualizar contraseña</button>
        </form>
      </article>
    </section>

    <p v-if="error" class="muted" style="color: var(--danger)">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { changePassword, createUser, deleteUser, listUsers, updateUser } from '../../api/users'

const users = ref([])
const selected = ref(null)
const error = ref(null)

const createForm = reactive({
  username: '',
  password: '',
  role: 'operator',
})

const editForm = reactive({
  username: '',
  role: 'operator',
  is_active: true,
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
})

async function refresh() {
  users.value = await listUsers()
}

async function create() {
  await createUser(createForm)
  createForm.username = ''
  createForm.password = ''
  createForm.role = 'operator'
  await refresh()
}

function selectUser(user) {
  selected.value = user
  editForm.username = user.username
  editForm.role = user.role
  editForm.is_active = user.is_active
  passwordForm.current_password = ''
  passwordForm.new_password = ''
}

async function save() {
  await updateUser(selected.value.id, editForm)
  await refresh()
  selected.value = null
}

async function changeUserPassword() {
  await changePassword(selected.value.id, passwordForm)
  passwordForm.current_password = ''
  passwordForm.new_password = ''
}

async function remove(id) {
  if (!window.confirm('¿Eliminar este usuario?')) return
  await deleteUser(id)
  await refresh()
}

onMounted(refresh)
</script>
