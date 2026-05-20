<template>
  <div class="layout" style="grid-template-columns: minmax(0, 560px); justify-content: center">
    <section class="panel" style="padding: 32px">
      <div class="muted">Confirmación</div>
      <h1 class="section-title" style="margin-top: 6px">Tu voto fue registrado</h1>
      <p class="muted">
        Puedes cerrar esta pestaña o volver al enlace de votación si necesitas revisar tu selección.
      </p>

      <div class="button-row">
        <button class="btn secondary" type="button" @click="closeTab">Cerrar pestaña</button>
        <RouterLink class="btn secondary" :to="{ name: 'vote-form', params: { token } }">
          Ver boleta
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup>
const props = defineProps({
  token: { type: String, required: true },
})

function closeTab() {
  window.close()
}

const token = props.token
</script>
