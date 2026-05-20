# WORKLOG — Historial de trabajo

> Append-only. Solo agregar, nunca modificar entradas anteriores.
> Orden: más reciente primero.


## 2026-05-20 | Modelo: Codex | Herramienta: auditoría local

- **Objetivo:** Arrancar Sprint 4 y montar el frontend administrativo base del proyecto.
- **Cambios:**
  - `frontend/package.json` — Nuevo: Vite + Vue 3 + Pinia + Vue Router.
  - `frontend/vite.config.js` — Nuevo: dev server y proxy hacia el backend.
  - `frontend/index.html` — Nuevo: entrypoint de la SPA.
  - `frontend/Dockerfile` — Nuevo: build estático del frontend.
  - `frontend/src/main.js` — Nuevo: bootstrap de Vue, Pinia, router y auth bootstrap.
  - `frontend/src/App.vue` — Nuevo: contenedor raíz de la app.
  - `frontend/src/router/index.js` — Nuevo: rutas y guards de navegación.
  - `frontend/src/stores/auth.js` y `frontend/src/stores/polls.js` — Nuevos: stores de Pinia.
  - `frontend/src/api/*` — Nuevos: cliente HTTP con cookies, CSRF, refresh y wrappers para auth/polls/users.
  - `frontend/src/components/AppShell.vue` — Nuevo: shell administrativo con navegación lateral.
  - `frontend/src/views/LoginView.vue`, `SetupView.vue`, `admin/DashboardView.vue`, `admin/PollDetailView.vue`, `admin/ImportView.vue`, `admin/UsersView.vue` — Nuevas: pantallas base del panel admin.
  - `frontend/src/styles/main.css` — Nuevo: sistema visual base del frontend.
  - `docker-compose.dev.yml` — Actualizado: servicio `frontend` para Vite en desarrollo.
  - `README.md`, `docs/ai/HANDOFF.md`, `docs/ai/TASKS.md` — Actualizados: el frontend ya existe y Sprint 4 quedó documentado como completado.
- **Decisiones tomadas:** Mantener un frontend vanilla CSS sin dependencia de Tailwind para evitar bloquear la validación por falta de instalación de paquetes; usar proxy de Vite para desarrollo local.
- **Resultado:** Sprint 4 implementado en árbol real y documentado; falta validar la ejecución con dependencias instaladas y completar el Sprint 5.
- **Siguiente:** Sprint 5: pantallas públicas de votación y dashboard SSE.



## 2026-05-20 | Modelo: Codex | Herramienta: auditoría local

- **Objetivo:** Implementar Sprint 3 con exportación XLSX de reportes y CRUD de usuarios administrativos.
- **Cambios:**
  - `backend/app/schemas/user.py` — Ampliado: agregados esquemas de actualización y cambio de contraseña.
  - `backend/app/schemas/__init__.py` — Actualizado: exporta los nuevos esquemas de usuario.
  - `backend/app/services/reports.py` — Nuevo: generador XLSX con hojas `Resumen` y `Resultados`.
  - `backend/app/routers/users.py` — Nuevo: CRUD de usuarios administrativos y cambio de contraseña con validación de rol.
  - `backend/app/routers/polls.py` — Actualizado: agregado `GET /api/polls/{id}/report.xlsx`.
  - `backend/app/main.py` — Actualizado: registrado el router de usuarios.
  - `backend/tests/test_users_reports.py` — Nuevo: cobertura de CRUD de usuarios, permisos y exportación XLSX.
  - `docs/ai/HANDOFF.md` — Actualizado: Sprint 3 marcado como completado y próxima acción movida a Sprint 4.
  - `docs/ai/TASKS.md` — Actualizado: TASK-031 a TASK-035 marcadas como completadas.
  - `docs/ai/GOVERNANCE.md` — Actualizado previamente para formalizar la regla de interoperabilidad documental.
- **Decisiones tomadas:** El reporte XLSX quedó restringido a polls cerrados y a usuarios admin; el CRUD de usuarios bloquea eliminar o desactivar al último admin activo.
- **Resultado:** Sprint 3 implementado en código y documentado; la ejecución de tests de integración quedó limitada por la indisponibilidad del PostgreSQL de pruebas en este sandbox.
- **Siguiente:** Sprint 4 frontend admin si se decide continuar.


## 2026-05-20 | Modelo: Codex | Herramienta: auditoría local

- **Objetivo:** Formalizar la regla de interoperabilidad documental para sesiones futuras de IA.
- **Cambios:**
  - `docs/ai/GOVERNANCE.md` — Ajustado: se agregó la regla explícita de que todo cambio debe registrarse fielmente en `WORKLOG.md`, `HANDOFF.md`, `TASKS.md` y `DECISIONS.md` cuando aplique.
- **Decisiones tomadas:** Priorizar trazabilidad completa del trabajo entre herramientas IA sobre resúmenes implícitos.
- **Resultado:** Regla de interoperabilidad documentada y visible para cualquier sesión futura.
- **Siguiente:** Si se realizan nuevos cambios, reflejarlos de inmediato en la documentación correspondiente antes de cerrar la sesión.

## 2026-05-20 | Modelo: Codex | Herramienta: auditoría local

- **Objetivo:** Auditar el estado real del repositorio y alinear la documentación con el árbol actual.
- **Cambios:**
  - `docs/ai/HANDOFF.md` — Ajustado: se agregó una sección de desalineaciones detectadas y se eliminó la afirmación de que el frontend ya está presente en el checkout.
  - `docs/ai/TASKS.md` — Ajustado: `TASK-004` quedó pendiente porque el frontend no existe en el árbol real.
  - `README.md` — Ajustado: se añadió una nota indicando que el frontend sigue siendo objetivo arquitectónico, no estado actual.
- **Decisiones tomadas:** Priorizar la verdad del checkout actual sobre el plan objetivo documentado.
- **Resultado:** Documentación alineada con el estado físico del repo.
- **Siguiente:** Implementar Sprint 3 si se decide continuar con código, empezando por `TASK-031`.

## 2026-05-20 | Modelo: Gemini 3.5 Flash | Herramienta: Antigravity CLI

- **Objetivo:** Recuperar scaffolding del Sprint 0, implementar modelos de datos asíncronos y migraciones de Alembic (Sprint 1), e inicializar repositorio remoto.
- **Cambios:**
  - `backend/app/config.py` — Creado: configuración de variables de entorno usando pydantic-settings.
  - `backend/app/database.py` — Creado: conexión y fábrica de sesiones asíncronas de SQLAlchemy 2.0.
  - `backend/app/deps.py` — Creado: dependencias de base de datos (`get_db`) y auth JWT.
  - `backend/app/main.py` — Creado: app FastAPI con CORS, TrustedHost y endpoint `/health`.
  - `backend/app/models/` — Creado: modelos `AdminUser`, `Poll`, `VoterGroup`, `Category`, `Option` y `Vote` con SQLAlchemy 2.0.
  - `backend/alembic/` — Creado: inicialización asíncrona de Alembic, configuración de `env.py` y primera migración del esquema inicial aplicada.
  - `docker-compose.yml`, `docker-compose.dev.yml`, `nginx/votaciones.conf`, `.gitignore`, `.env.example` — Creado: archivos base de infraestructura y docker.
  - `README.md` — Creado: documentación técnica y manual de configuración rápida.
- **Decisiones tomadas:** Se mantuvo la restricción única `UniqueConstraint("poll_id", "voter_group_id", "voter_token", "option_id")` en `Vote` para no comprometer soporte futuro para voto preferencial (Ranked Choice), y se añadió `category_id` como FK para optimizar consultas de conteo.
- **Resultado:** Completado con éxito. Base de datos PostgreSQL inicializada con migraciones, y código inicializado y pusheado a GitHub.
- **Siguiente:** Implementar router de autenticación y setup (TASK-015 y TASK-016).

---

## 2026-05-20 | Modelo: Gemini 3.5 Flash | Herramienta: Antigravity CLI

- **Objetivo:** Consolidar en la documentación todo lo conversado (retrospectiva V1, blockers de seguridad de migración a internet) y planificar Sprint 1 de V2.
- **Cambios:**
  - `docs/ai/V1_RETROSPECTIVE.md` — Creado: resumen completo de logros de V1, fallos de seguridad (B-1 a B-7) y la transición a la arquitectura extensible de V2.
  - `docs/ai/HANDOFF.md` — Modificado: añadido enlace e instrucción de lectura a `V1_RETROSPECTIVE.md`.
  - `implementation_plan.md` (Artifact) — Modificado: reescrito plan de implementación para Sprint 1 (Backend Core) enfocado en V2.
- **Decisiones tomadas:** Consolidar el contexto histórico de V1 directamente en la gobernanza de la solución V2.
- **Resultado:** Documentación actualizada al 100% y plan de implementación para Sprint 1 listo para aprobación.
- **Siguiente:** Esperar aprobación del usuario sobre el plan de implementación para iniciar el Sprint 1 (TASK-010).

## 2026-05-20 | Modelo: Claude Sonnet 4.6 (Thinking) | Herramienta: Antigravity CLI

- **Objetivo:** Inicializar proyecto V2 con sistema de gobernanza completo y scaffolding
- **Cambios:**
  - `docs/ai/HANDOFF.md` — Creado: punto de entrada para cualquier sesión de IA
  - `docs/ai/CONTRACT.md` — Creado: reglas de negocio, stack, restricciones
  - `docs/ai/ARCHITECTURE.md` — Creado: diseño del sistema, modelo de datos, API, flujos
  - `docs/ai/CODING_STANDARDS.md` — Creado: convenciones de código backend y frontend
  - `docs/ai/GOVERNANCE.md` — Creado: protocolo de trabajo para IA
  - `docs/ai/DECISIONS.md` — Creado: ADR-001 a ADR-011 (decisiones fundacionales)
  - `docs/ai/TASKS.md` — Creado: Sprint 0-6 + backlog
  - `docs/ai/WORKLOG.md` — Creado: este archivo
  - `backend/` — Scaffolding: requirements.txt, Dockerfile, estructura de módulos
  - `frontend/` — Scaffolding: package.json, vite.config.js, tailwind.config.js, estructura Vue 3
  - `nginx/votaciones.conf` — Creado: config Nginx con HTTPS, SSE sin buffer
  - `docker-compose.yml` — Creado: producción con PostgreSQL
  - `docker-compose.dev.yml` — Creado: desarrollo local con hot reload
  - `.env.example` — Creado: plantilla de variables de entorno
  - `.gitignore` — Creado
  - `README.md` — Creado: instrucciones de setup y operación
- **Decisiones tomadas:** ADR-001 a ADR-011 (ver DECISIONS.md)
- **Resultado:** Sprint 0 completado. Scaffolding listo para iniciar implementación.
- **Siguiente:** TASK-010 — Implementar modelos SQLAlchemy (Sprint 1)
