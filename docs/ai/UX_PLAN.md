# UX_PLAN — Simplificacion de experiencia administrativa

> Guia escrita para convertir la app en una herramienta facil de usar por personas no tecnicas
> que crean votaciones 1 o 2 veces al mes.

---

## Objetivo

La app debe permitir que una persona administrativa cree y opere una votacion comun sin entender
conceptos tecnicos del sistema.

Flujo objetivo:

1. Crear votacion
2. Definir grupos y pesos
3. Cargar candidatos
4. Revisar que este lista
5. Abrir votacion
6. Copiar enlaces por grupo
7. Ver resultados
8. Cerrar y descargar reporte

---

## Usuario objetivo

- Persona no tecnica.
- Usa la app ocasionalmente, aproximadamente 1 o 2 veces al mes.
- No debe recordar detalles internos como `poll`, `token`, `SSE`, `draft` o pesos decimales.
- Necesita acciones claras, estados visibles y mensajes que expliquen que falta para continuar.

---

## Principios UX

1. Usar lenguaje de trabajo, no lenguaje tecnico.
2. Mostrar el siguiente paso evidente en cada pantalla.
3. Evitar que el usuario tenga que navegar a otra pantalla para terminar una votacion.
4. Mostrar porcentajes humanos, no decimales internos.
5. Reemplazar tokens por enlaces copiables.
6. Validar antes de abrir, con una lista de requisitos visible.
7. Mantener una votacion simple como caso principal: "Empleado del mes".
8. No cambiar reglas de negocio sin ADR y aprobacion del usuario.

---

## Alcance inicial

El primer pase de UX debe enfocarse en el flujo administrativo mas frecuente:

- Crear una votacion tipo "Empleado del mes".
- Configurar 2 o mas grupos con peso total 100%.
- Cargar candidatos manualmente o por archivo.
- Abrir la votacion cuando este completa.
- Compartir enlaces por grupo.
- Monitorear y cerrar.

No entran en este pase:

- Tipos avanzados de votacion.
- QR codes.
- Notificaciones por correo.
- Historial entre votaciones.
- Fotos de candidatos, salvo conservar soporte existente de `photo_url`.

---

## Plan Por Tareas

### Fase 1 — Lenguaje y navegacion

**UX-001 — Renombrar navegacion principal**
- Cambiar `Dashboard` a `Votaciones`.
- Cambiar `Importar` a `Cargar candidatos` o moverlo dentro de votaciones.
- Cambiar `Admin Console` a `Administracion`.
- Ocultar numeracion `01`, `02`, `03` si no aporta al flujo.
- Validacion: una persona debe entender desde el menu donde crear o administrar una votacion.

**UX-002 — Traducir estados y tipos de votacion**
- Mostrar `Borrador`, `Abierta`, `Cerrada` en vez de `draft`, `open`, `closed`.
- Mostrar `Elegir una opcion` en vez de `Plurality`.
- Mantener valores internos sin cambios.
- Validacion: ninguna pantalla principal debe obligar a interpretar enums tecnicos.

**UX-003 — Ajustar pantalla de listado de votaciones**
- Enfocar la pantalla en "Crear votacion" y "Continuar configuracion".
- Mostrar estado, cantidad de grupos y accion recomendada.
- Cambiar botones `SSE` y `Abrir` por textos operativos: `Ver resultados`, `Configurar`.
- Validacion: desde cada tarjeta debe quedar claro que hacer despues.

### Fase 2 — Flujo guiado de configuracion

**UX-004 — Redisenar detalle como "Preparar votacion"**
- Reorganizar `PollDetailView.vue` en pasos visibles.
- Paso 1: Datos principales.
- Paso 2: Grupos y pesos.
- Paso 3: Candidatos.
- Paso 4: Revisar y abrir.
- Validacion: el usuario puede terminar una votacion sin salir del detalle.

**UX-005 — Mostrar pesos como porcentaje**
- Permitir ingresar `50` y guardar `0.50` internamente.
- Mostrar total acumulado: `Total: 100%`.
- Marcar error si no suma 100%.
- Validacion: dos grupos de 50% deben configurarse sin escribir decimales.

**UX-006 — Agregar checklist de apertura**
- Mostrar requisitos antes de abrir:
  - tiene nombre
  - tiene al menos un grupo
  - pesos suman 100%
  - tiene al menos una categoria
  - cada categoria tiene candidatos
- Deshabilitar o explicar `Abrir votacion` cuando falte algo.
- Validacion: el usuario entiende por que aun no puede abrir.

**UX-007 — Mover carga de candidatos al detalle**
- Agregar bloque `Candidatos` dentro del detalle.
- Incluir boton `Importar desde Excel/CSV`.
- Mantener la pantalla `/admin/import` solo como ruta secundaria o redireccionada desde el detalle.
- Validacion: no debe ser necesario descubrir la seccion `Importar`.

### Fase 3 — Candidatos manuales y archivo

**UX-008 — Listar candidatos existentes por categoria**
- Agregar soporte visual para ver candidatos ya cargados.
- Si el backend no expone lista de opciones, crear endpoint especifico.
- Validacion: despues de importar, el usuario ve que candidatos quedaron cargados.

**UX-009 — Agregar carga manual de candidatos**
- Permitir agregar candidato desde UI sin archivo.
- Mantener restriccion a votaciones en borrador.
- Validacion: una votacion pequena se puede preparar sin Excel/CSV.

**UX-010 — Agregar plantilla simple de CSV**
- Ofrecer ejemplo o descarga de plantilla para "Empleado del mes".
- Columnas recomendadas: `Categoria`, `Nombre`, `Foto`.
- Validacion: el usuario sabe que archivo subir sin consultar documentacion externa.

### Fase 4 — Enlaces y operacion

**UX-011 — Reemplazar token por enlace copiable**
- Mostrar `Enlace para votar` por grupo.
- Agregar boton `Copiar enlace`.
- Mostrar nombre del grupo junto al enlace.
- Validacion: el usuario puede compartir enlaces sin manipular UUIDs.

**UX-012 — Mejorar apertura y cierre**
- Cambiar `Abrir` por `Abrir votacion`.
- Cambiar `Cerrar` por `Cerrar votacion`.
- Agregar confirmacion con impacto: al cerrar ya no se podra votar.
- Validacion: no se cambia el estado por accidente.

**UX-013 — Mejorar resultados en vivo**
- Mostrar titulo real de la votacion, no UUID.
- Cambiar `SSE` por `Resultados en vivo`.
- Mantener privacidad como modo predeterminado, con texto claro.
- Validacion: la pantalla se entiende para presentar resultados sin explicar tecnologia.

### Fase 5 — Votacion publica

**UX-014 — Simplificar boleta publica**
- Mostrar nombre del grupo si ayuda a confirmar que el enlace es correcto.
- Agregar validacion visual antes de enviar.
- Cambiar errores tecnicos por mensajes accionables.
- Validacion: una persona votante entiende que debe elegir una opcion y enviar.

**UX-015 — Ajustar confirmacion de voto**
- Evitar sugerir "revisar seleccion" si el sistema ya bloquea voto repetido.
- Mostrar mensaje simple: `Tu voto fue registrado`.
- Validacion: no genera duda sobre si puede cambiar su voto.

### Fase 6 — Validacion y documentacion

**UX-016 — Crear prueba manual guiada "Empleado del mes"**
- Documentar pasos exactos para crear:
  - votacion `Empleado del mes`
  - 2 grupos de 50%
  - 1 categoria
  - 3 candidatos
  - apertura
  - voto con enlace
  - resultados
  - cierre y reporte
- Validacion: cualquier IA o usuario puede repetir el flujo.

**UX-017 — Actualizar README y handoff de uso**
- Agregar seccion "Probar una votacion completa".
- Mantener `HANDOFF.md`, `TASKS.md` y `WORKLOG.md` sincronizados.
- Validacion: la siguiente sesion puede continuar sin contexto externo.

---

## Orden Recomendado De Implementacion

1. UX-001 a UX-003: lenguaje y navegacion.
2. UX-004 a UX-007: detalle como flujo guiado.
3. UX-008 a UX-010: candidatos visibles y carga manual/archivo.
4. UX-011 a UX-013: enlaces, apertura/cierre y resultados.
5. UX-014 a UX-017: boleta publica, confirmacion y documentacion.

Este orden reduce riesgo porque primero mejora comprension sin tocar reglas de negocio, y despues
avanza sobre cambios que requieren endpoints o contratos nuevos.

---

## Criterio De Aceptacion Global

La mejora se considera lista cuando una persona no tecnica puede crear una votacion "Empleado del mes"
con 2 grupos al 50%, cargar candidatos, abrirla, compartir enlaces y cerrar con reporte sin consultar
codigo, API ni documentacion tecnica.
