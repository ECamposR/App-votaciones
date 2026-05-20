# GOVERNANCE — Cómo trabaja la IA en este proyecto

> Este documento define el PROTOCOLO de trabajo para cualquier IA (Claude, GPT, Gemini, etc.)
> que colabore en este proyecto. Debe leerse junto con HANDOFF.md al iniciar cualquier sesión.

---

## 1. Principio fundamental

Este proyecto es **impulsado íntegramente por IA** (vibecoding). Múltiples modelos y herramientas
pueden participar en distintas sesiones. La documentación de gobernanza ES el proyecto —
sin ella, el contexto se pierde.

**Regla de oro:** Si no está documentado, no ocurrió.

---

## 2. Protocolo de sesión

### Al INICIAR una sesión

1. **Leer `HANDOFF.md`** — Estado actual, qué hay que hacer, qué está bloqueado
2. **Leer `TASKS.md`** — Tomar la siguiente tarea en estado `todo`
3. Si la tarea involucra decisiones de diseño → leer `ARCHITECTURE.md` y `CONTRACT.md`
4. Confirmar el plan con el usuario antes de ejecutar cambios grandes
5. Marcar la tarea como `in_progress` en `TASKS.md`

### Al FINALIZAR una sesión (o al hacer pausa)

1. **Actualizar `WORKLOG.md`** — Qué se hizo, qué cambió, resultado
2. **Actualizar `HANDOFF.md`** — Estado actual, siguiente acción inmediata
3. **Actualizar `TASKS.md`** — Marcar tareas completadas, agregar tareas nuevas descubiertas
4. Si se tomaron decisiones de diseño → registrar en `DECISIONS.md`
5. Hacer commit con mensaje descriptivo

### Formato de entrada en WORKLOG.md
```markdown
## YYYY-MM-DD | Modelo: [nombre del modelo] | Herramienta: [nombre]
- **Objetivo:** [qué se intentó hacer]
- **Cambios:**
  - [archivo modificado] — [qué cambió]
  - ...
- **Decisiones tomadas:** [si aplica, referenciar ADR-XXX]
- **Resultado:** [completado / parcial / bloqueado]
- **Siguiente:** [qué sigue o qué queda pendiente]
```

---

## 3. Cómo tomar decisiones técnicas

### Decisiones menores (sin ADR)
Ejemplos: renombrar una variable, ajustar un mensaje de error, agregar un índice obvio.
→ Solo hacer el cambio y mencionarlo en WORKLOG.

### Decisiones de diseño (requieren ADR)
Ejemplos: agregar una dependencia nueva, cambiar el schema de DB, cambiar una regla de negocio,
cambiar el stack, agregar una nueva feature.

**Formato en `DECISIONS.md`:**
```markdown
## ADR-XXX | Título descriptivo
- **Fecha:** YYYY-MM-DD
- **Estado:** Aceptado / En revisión / Rechazado / Supersedido por ADR-YYY
- **Contexto:** Por qué se necesitó tomar esta decisión
- **Decisión:** Qué se decidió hacer
- **Consecuencias:** Qué cambia, qué queda pendiente, qué riesgos se aceptan
```

### Reglas de negocio (inmutables sin aprobación explícita)
Las reglas en `CONTRACT.md` sección "Reglas de negocio core" NO pueden cambiarse
sin aprobación explícita del usuario. Si una tarea parece requerir cambiarlas,
**pausar y consultar** antes de proceder.

---

## 4. Convenciones de código

Ver `CODING_STANDARDS.md` para el detalle completo.

Resumen:
- Backend: Python 3.12+, typing estricto, async/await, snake_case
- Frontend: Vue 3 Composition API, `<script setup>`, camelCase, kebab-case en archivos
- Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Sin comentarios obvios — el código debe ser autoexplicativo

---

## 5. Qué NO hacer sin consultar al usuario

- Cambiar el stack tecnológico (agregar frameworks, cambiar DB, etc.)
- Cambiar reglas de negocio core (scoring, deduplicación, estados de poll)
- Eliminar o cambiar nombres de rutas API existentes (rompe el frontend)
- Cambiar el schema de DB sin una migración Alembic correspondiente
- Exponer puertos de servicios internos (PostgreSQL, uvicorn) al exterior
- Pushear a producción sin que el usuario haya validado en desarrollo

---

## 6. Estructura de TASKS.md

```markdown
## Sprint N — Nombre del sprint
### En progreso
- `[/]` TASK-XXX — descripción (en progreso)

### Pendiente
- `[ ]` TASK-XXX — descripción
- `[ ]` TASK-XXX — descripción

### Completado
- `[x]` TASK-XXX — descripción
```

**Estados de task:**
- `[ ]` — pendiente
- `[/]` — en progreso (solo UNA a la vez idealmente)
- `[x]` — completado
- `[~]` — cancelado / ya no aplica

---

## 7. Flujo de trabajo recomendado para una sesión típica

```
1. Usuario abre sesión con IA
2. IA lee HANDOFF.md → entiende el estado
3. IA propone qué hacer en esta sesión (basado en TASKS.md)
4. Usuario aprueba
5. IA ejecuta la tarea:
   a. Escribe/modifica código
   b. Actualiza docs si hay decisiones
   c. Corre tests si aplica
6. IA actualiza WORKLOG.md + HANDOFF.md + TASKS.md
7. IA propone el commit
8. Sesión terminada — cualquier IA puede continuar desde aquí
```

---

## 8. Referencia rápida de archivos de gobernanza

| Archivo | Propósito | ¿Cuándo leer? | ¿Cuándo escribir? |
|---------|-----------|--------------|------------------|
| `HANDOFF.md` | Estado actual | SIEMPRE al inicio | Al final de cada sesión |
| `TASKS.md` | Qué hay que hacer | Al inicio | Al cambiar estado de tareas |
| `CONTRACT.md` | Reglas de negocio y stack | Cuando hay dudas sobre reglas | Raramente (requiere aprobación) |
| `ARCHITECTURE.md` | Diseño técnico | Al implementar algo nuevo | Cuando cambia la arquitectura |
| `DECISIONS.md` | Por qué se hizo X | Cuando hay confusión sobre una decisión | Al tomar decisiones de diseño |
| `WORKLOG.md` | Historial de trabajo | Para entender qué pasó antes | Al finalizar cada sesión |
| `CODING_STANDARDS.md` | Cómo escribir código | Al escribir código nuevo | Raramente |

---

## 9. Ante la duda

Si no está claro qué hacer:
1. Leer `CONTRACT.md` — ¿va en contra de las reglas de negocio?
2. Leer `DECISIONS.md` — ¿ya se decidió esto antes?
3. Preguntar al usuario — mejor preguntar que asumir
4. Documentar la duda en `HANDOFF.md` sección "❓ Decisiones pendientes"
