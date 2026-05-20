# TASKS — Tablero de tareas

> Estados: `[ ]` pendiente | `[/]` en progreso | `[x]` completado | `[~]` cancelado

---

## Sprint 0 — Gobernanza y scaffolding ✅

- `[x]` TASK-001 — Crear documentación de gobernanza (CONTRACT, ARCHITECTURE, GOVERNANCE, CODING_STANDARDS, DECISIONS, HANDOFF, WORKLOG, TASKS)
- `[x]` TASK-002 — Crear estructura de directorios del proyecto
- `[x]` TASK-003 — Configurar backend base (FastAPI, SQLAlchemy, Alembic, requirements.txt, Dockerfile)
- `[x]` TASK-004 — Configurar frontend base (Vue 3, Vite, Pinia, Vue Router, package.json, Dockerfile) [CSS propio en este checkout]
- `[x]` TASK-005 — Crear docker-compose.yml (prod) y docker-compose.dev.yml
- `[x]` TASK-006 — Crear nginx/votaciones.conf con soporte SSE y HTTPS
- `[x]` TASK-007 — Crear .env.example y .gitignore

---

## Sprint 1 — Backend Core (modelos + auth)

- `[x]` TASK-010 — Implementar modelos SQLAlchemy: AdminUser, Poll, VoterGroup, Category, Option, Vote
- `[x]` TASK-011 — Crear primera migración Alembic (schema inicial completo)
- `[x]` TASK-012 — Implementar config.py con pydantic-settings (todas las variables de entorno)
- `[x]` TASK-013 — Implementar database.py (engine async, session factory)
- `[x]` TASK-014 — Implementar deps.py (get_db, get_current_user, require_admin)
- `[x]` TASK-015 — Implementar router auth: POST /auth/login, /auth/logout, /auth/refresh, GET /auth/me
- `[x]` TASK-016 — Implementar router setup: GET/POST /setup (primer admin)
- `[x]` TASK-017 — Implementar router health: GET /health
- `[x]` TASK-018 — Implementar middleware: security headers, CSRF, rate limiting
- `[x]` TASK-019 — Tests: auth flow completo (login, token refresh, logout, acceso denegado)

---

## Sprint 2 — Backend Polls + Votación ✅

- `[x]` TASK-020 — Implementar router polls: GET /polls, POST /polls, GET /polls/{id}, PATCH /polls/{id}, DELETE /polls/{id}
- `[x]` TASK-021 — Implementar router polls: POST /polls/{id}/status (draft→open→closed)
- `[x]` TASK-022 — Implementar router polls: GET+POST+PATCH+DELETE /polls/{id}/voter-groups (CRUD grupos)
- `[x]` TASK-023 — Implementar router polls: GET+POST+PATCH+DELETE /polls/{id}/categories (CRUD categorías)
- `[x]` TASK-024 — Implementar service importer.py (parseo CSV/XLSX → options)
- `[x]` TASK-025 — Implementar router polls: POST /polls/{id}/options/import
- `[x]` TASK-026 — Implementar service scoring.py (cálculo ponderado con redistribución dinámica de pesos)
- `[x]` TASK-027 — Implementar router voting: GET /v/{token}/data, POST /v/{token}/vote
- `[x]` TASK-028 — Implementar router dashboard: GET /api/dashboard/{id}/stream (SSE nativo)
- `[x]` TASK-029 — Tests: scoring con múltiples grupos y weights (97% cobertura en scoring.py)
- `[x]` TASK-030 — Tests: flujo de votación completo (doble voto, token inválido, poll cerrado)

---

## Sprint 3 — Backend Reports + Users ✅

- `[x]` TASK-031 — Implementar router polls: GET /polls/{id}/report.xlsx [rescatar de V1]
- `[x]` TASK-032 — Implementar router users: CRUD completo (solo role=admin)
- `[x]` TASK-033 — Implementar POST /users/{id}/change-password
- `[x]` TASK-034 — Tests: reports XLSX básicos
- `[x]` TASK-035 — Tests: users CRUD con restricciones de rol

---

## Sprint 4 — Frontend Admin ✅

- `[x]` TASK-040 — Setup Vue Router (rutas de admin, vote, dashboard, login)
- `[x]` TASK-041 — Setup Pinia stores (auth, polls)
- `[x]` TASK-042 — Implementar api/client.js con refresh token automático
- `[x]` TASK-043 — Implementar LoginView.vue + SetupView.vue
- `[x]` TASK-044 — Implementar DashboardView.vue (lista de polls con estado)
- `[x]` TASK-045 — Implementar PollDetailView.vue (gestión: grupos, categorías, opciones)
- `[x]` TASK-046 — Implementar ImportView.vue (upload CSV/XLSX + preview + confirmar)
- `[x]` TASK-047 — Implementar UsersView.vue (CRUD de usuarios admin)

---

## Sprint 5 — Frontend Votación + Dashboard

- `[x]` TASK-050 — Implementar VoteFormView.vue (formulario de voto mobile-first)
- `[x]` TASK-051 — Implementar VoteStatusView.vue (confirmación + cerrar pestaña)
- `[x]` TASK-052 — Implementar LiveDashboardView.vue (dashboard SSE con visualización simple)
- `[x]` TASK-053 — Implementar modo privacidad en dashboard (ocultar nombres por defecto)

---

## Sprint 6 — Infraestructura y Deploy

- `[ ]` TASK-060 — Configurar Nginx en VPS para nuevo subdominio (votaciones.dominio.com)
- `[ ]` TASK-061 — Obtener certificado Let's Encrypt para el subdominio
- `[ ]` TASK-062 — Configurar .env en VPS con todos los secretos
- `[ ]` TASK-063 — Primer deploy en VPS y smoke test completo
- `[ ]` TASK-064 — Configurar cron de backup pg_dump en VPS
- `[ ]` TASK-065 — Script de migración de datos V1 → V2 (opcional, si hay datos históricos)

---

## Backlog (post v2.0)

- `[ ]` TASK-100 — Historial de ganadores entre polls (vista `/admin/history`)
- `[ ]` TASK-101 — Foto/avatar de candidato en formulario de voto
- `[ ]` TASK-102 — Tipo de votación: Rating scale (1-5)
- `[ ]` TASK-103 — Tipo de votación: Yes/No
- `[ ]` TASK-104 — Tipo de votación: Ranked choice (preferencial)
- `[ ]` TASK-105 — Plantilla CSV descargable desde UI de importación
- `[ ]` TASK-106 — Edición manual de opciones (sin reimportar CSV)
- `[ ]` TASK-107 — Reporte PDF del dashboard
- `[ ]` TASK-108 — QR code para link de votación en UI admin
- `[ ]` TASK-109 — Cierre automático del poll por fecha/hora (`ends_at`)
- `[ ]` TASK-110 — Notificación por email al cerrar el poll (integración SMTP)
