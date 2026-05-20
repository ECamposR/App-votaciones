# HANDOFF — Estado actual del proyecto

> **Este es el primer archivo que debe leer cualquier IA al iniciar una sesión.**
> Refleja el estado real del proyecto en este momento.
> Debe actualizarse al INICIO y al FINAL de cada sesión de trabajo.

---

## Identificación del proyecto

- **Nombre:** votaciones-v2
- **Propósito:** Plataforma de votaciones internas con soporte para múltiples tipos de encuesta
- **Versión actual:** 0.5.0 — Frontend admin base agregado (Sprint 4)
- **Repo:** ECamposR/App-votaciones (`git@github.com:ECamposR/App-votaciones.git`)
- **VPS destino:** Docker + Nginx + Let's Encrypt (ya operativo con MeshCentral)

---

## Estado actual — 2026-05-20

### ✅ Completado

**Sprint 0 — Gobernanza y scaffolding**
- Documentación de gobernanza completa (CONTRACT, ARCHITECTURE, CODING_STANDARDS, GOVERNANCE, DECISIONS, HANDOFF, WORKLOG, TASKS, V1_RETROSPECTIVE)
- Scaffolding base: docker-compose, docker-compose.dev, .env.example, .gitignore, nginx/votaciones.conf, README.md
- Repositorio Git inicializado y pusheado a GitHub

**Sprint 1 — Backend Core (modelos + auth)**
- Modelos SQLAlchemy 2.0: `AdminUser`, `Poll`, `VoterGroup`, `Category`, `Option`, `Vote`
- Primera migración Alembic (`create_initial_schema`) aplicada en PostgreSQL local
- `config.py` con pydantic-settings (falla al arrancar si faltan secretos)
- `database.py` con engine async y session factory
- `deps.py` con `get_db`, `get_current_user`, `require_admin`
- Router `auth.py`: `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`, `GET /auth/me`
- Router `setup.py`: `GET /setup`, `POST /setup` (primer admin)
- `middleware/security.py`: headers HTTP (CSP, HSTS, X-Frame, etc.), CSRF (starlette-csrf), rate limiting (slowapi)
- Tests de autenticación completos (4 tests, 91% cobertura global)

**Sprint 2 — Backend Polls + Votación**
- `schemas/poll.py`: Pydantic v2 para Polls, VoterGroups, Categories, Options y Votos públicos
- `services/importer.py`: Parser CSV/XLSX con detección automática de columnas en español e inglés
- `services/scoring.py`: Algoritmo de recuento ponderado con redistribución dinámica de pesos y desempate triple (score → votos → alfabético)
- `routers/polls.py`: CRUD completo de Polls, VoterGroups, Categories + endpoint de importación (solo en DRAFT)
- `routers/voting.py`: `GET /v/{token}/data` y `POST /v/{token}/vote` con deduplicación por cookie `voter_id`
- `routers/dashboard.py`: `GET /api/dashboard/{id}/stream` — SSE nativo con `StreamingResponse`, sin Redis ni WebSockets
- Tests: 23 tests en 3 archivos (test_auth, test_polls, test_scoring, test_voting) — **23/23 pasando, 90% cobertura global**

**Sprint 3 — Backend Reports + Users**
- `services/reports.py`: generador XLSX con hoja resumen y hoja de resultados
- `routers/polls.py`: `GET /api/polls/{id}/report.xlsx` con restricción a polls cerrados y acceso admin
- `routers/users.py`: CRUD completo de usuarios administrativos + cambio de contraseña con validaciones de seguridad
- `schemas/user.py`: esquemas para actualización y cambio de contraseña
- `tests/test_users_reports.py`: cobertura de CRUD de usuarios, permisos de rol y exportación XLSX

**Sprint 4 — Frontend Admin**
- `frontend/`: Vite + Vue 3 + Pinia + Vue Router con layout administrativo y CSS propio
- `src/stores/auth.js` y `src/stores/polls.js`: estado compartido del frontend
- `src/api/*`: cliente HTTP con cookies, CSRF y refresh automático
- `src/views/LoginView.vue` y `src/views/SetupView.vue`: acceso y configuración inicial
- `src/views/admin/DashboardView.vue`: lista y creación de polls
- `src/views/admin/PollDetailView.vue`: gestión de grupos y categorías
- `src/views/admin/ImportView.vue`: importación CSV/XLSX
- `src/views/admin/UsersView.vue`: CRUD administrativo

### 🔄 En progreso
- Nada actualmente en progreso

### ⬜ Siguiente acción inmediata
**→ Sprint 5: Frontend Votación + Dashboard (TASK-050 a TASK-053)**

Ver `TASKS.md` sección "Sprint 5" para la lista completa.

### 🚫 Bloqueado
- Nada bloqueado actualmente

### ⚠️ Desalineaciones detectadas en este checkout
- `README.md` y `ARCHITECTURE.md` describen una arquitectura objetivo más amplia que el estado físico actual del repo.
- La validación de runtime de la suite de pruebas quedó limitada en este sandbox por la indisponibilidad del PostgreSQL de pruebas usado en `backend/tests/conftest.py`.

### ❓ Decisiones pendientes
- Subdominio exacto del VPS donde se desplegará (para Nginx config y TrustedHostMiddleware)

---

## Cómo continuar desde aquí

1. Leer este archivo ✅
2. Leer `TASKS.md` → ver qué task es "next" (Sprint 5 → TASK-050)
3. Leer `CONTRACT.md` → reglas de negocio no negociables
4. Leer `ARCHITECTURE.md` → entender el diseño del sistema
5. Leer `V1_RETROSPECTIVE.md` → entender los hallazgos de seguridad y retrospectiva de V1
6. Si la task involucra decisiones de diseño → registrar en `DECISIONS.md`
7. Al finalizar → actualizar `WORKLOG.md` y este `HANDOFF.md`

---

## Contexto clave para continuar sin leer todo

### Stack implementado
- **Backend:** Python 3.14 + FastAPI + SQLAlchemy 2.0 async + Alembic + PostgreSQL 16
- **Auth:** JWT en httpOnly cookie (access 15min + refresh 7 días)
- **Real-time:** SSE (Server-Sent Events) via `StreamingResponse` nativo
- **Hashing:** `bcrypt` nativo (NO passlib — incompatible con Python 3.14+)
- **CSRF:** `starlette-csrf` con `re.compile()` en `exempt_urls` (strings raw NO funcionan)
- **Deploy:** Docker Compose + Nginx (en VPS con MeshCentral ya corriendo)

### Rutas de la API registradas
| Prefijo | Archivo | Descripción |
|---------|---------|-------------|
| `/setup` | `routers/setup.py` | Setup inicial sin prefijo |
| `/auth/...` | `routers/auth.py` | Auth sin prefijo |
| `/api/polls/...` | `routers/polls.py` | Admin polls con prefijo `/api` |
| `/v/{token}/...` | `routers/voting.py` | Votación pública sin prefijo |
| `/api/dashboard/...` | `routers/dashboard.py` | SSE dashboard con prefijo `/api` |

### Ejecución de tests
```bash
cd backend
PYTHONPATH=. JWT_SECRET=dummy_secret DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones \
  .venv/bin/pytest --asyncio-mode=auto --cov=app tests/
```
> La DB de test es `votaciones_test` (se crea automáticamente en conftest.py).

### Reglas de negocio core (no cambiar sin ADR)
1. Cada Poll tiene VoterGroups con weights que suman 1.0
2. Score final = suma de (score_normalizado_por_grupo × weight_efectivo_del_grupo)
3. Si un grupo no participa en una categoría, su peso se redistribuye entre los que sí
4. Las rutas de votación `/v/{token}` son siempre públicas
5. Dashboard y admin siempre requieren auth (cookie access_token)
6. Deduplicación por cookie httpOnly (`voter_id` UUID, 1 año, HttpOnly, Secure en producción)

### Convención de commits
```
feat: descripción
fix: descripción
docs: descripción
refactor: descripción
test: descripción
chore: descripción
```

---

## Sesiones anteriores

| Fecha | IA | Trabajo realizado |
|-------|----|-------------------|
| 2026-05-20 | Claude Sonnet 4.6 (Thinking) | Sprint 0: scaffolding completo + gobernanza inicial |
| 2026-05-20 | Gemini 3.5 Flash | Sprint 0 recovery + modelos SQLAlchemy + Alembic + README + GitHub |
| 2026-05-20 | Gemini 3.5 Flash → Claude Sonnet 4.6 | Sprint 1: auth, setup, security middleware, tests (4 tests, 91% cov) |
| 2026-05-20 | Claude Sonnet 4.6 (Thinking) | Sprint 2: polls CRUD, voting, scoring, SSE dashboard, tests (23 tests, 90% cov) |
