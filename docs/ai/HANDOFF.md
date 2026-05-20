# HANDOFF — Estado actual del proyecto

> **Este es el primer archivo que debe leer cualquier IA al iniciar una sesión.**
> Refleja el estado real del proyecto en este momento.
> Debe actualizarse al INICIO y al FINAL de cada sesión de trabajo.

---

## Identificación del proyecto

- **Nombre:** votaciones-v2
- **Propósito:** Plataforma de votaciones internas con soporte para múltiples tipos de encuesta
- **Versión actual:** 0.1.0 — scaffolding inicial
- **Repo:** ECamposR/votaciones-v2
- **VPS destino:** Docker + Nginx + Let's Encrypt (ya operativo con MeshCentral)

---

## Estado actual — 2026-05-20

### ✅ Completado
- Documentación de gobernanza (CONTRACT, ARCHITECTURE, CODING_STANDARDS, GOVERNANCE, DECISIONS, WORKLOG, TASKS)
- Scaffolding inicial del proyecto (estructura de directorios, Dockerfiles, docker-compose, .env.example)
- Configuración base de backend (FastAPI, SQLAlchemy 2.0, Alembic, estructura de módulos)
- Configuración base de frontend (Vue 3, Vite, TailwindCSS, Vue Router, Pinia)
- Nginx config con SSE support

### 🔄 En progreso
- Nada actualmente en progreso

### ⬜ Siguiente acción inmediata
**→ Implementar los modelos de datos del backend**

Ver `TASKS.md` sección "Sprint 1 — Backend Core" para la lista completa y ordenada.

### 🚫 Bloqueado
- Nada bloqueado actualmente

### ❓ Decisiones pendientes
- Subdominio exacto del VPS donde se desplegará (para Nginx config y TrustedHostMiddleware)

---

## Cómo continuar desde aquí

1. Leer este archivo ✅
2. Leer `TASKS.md` → ver qué task es "next"
3. Leer `CONTRACT.md` → reglas de negocio no negociables
4. Leer `ARCHITECTURE.md` → entender el diseño del sistema
5. Leer `V1_RETROSPECTIVE.md` → entender los hallazgos de seguridad y retrospectiva de V1
6. Si la task involucra decisiones de diseño → registrar en `DECISIONS.md`
7. Al finalizar → actualizar `WORKLOG.md` y este `HANDOFF.md`

---

## Contexto clave para continuar sin leer todo

### Stack
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 async + Alembic + PostgreSQL
- **Frontend:** Vue 3 + Vite + TailwindCSS + Pinia + Vue Router
- **Auth:** JWT en httpOnly cookie (access 15min + refresh 7 días)
- **Real-time:** SSE (Server-Sent Events)
- **Deploy:** Docker Compose + Nginx (en VPS con MeshCentral ya corriendo)

### Estructura de directorios
```
votaciones-v2/
├── backend/          # FastAPI app
├── frontend/         # Vue 3 SPA
├── nginx/            # Nginx config
├── scripts/          # Backup, utilidades
├── docs/ai/          # Gobernanza (ESTE DIRECTORIO)
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

### Reglas de negocio core (no cambiar sin ADR)
1. Cada Poll tiene VoterGroups con weights que suman 1.0
2. Score final = suma de (score_normalizado_por_grupo × weight_del_grupo)
3. Las rutas de votación `/v/{token}` son siempre públicas
4. Dashboard y admin siempre requieren auth
5. Deduplicación por cookie httpOnly (voter_id UUID, 1 año)

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
| 2026-05-20 | Claude Sonnet 4.6 | Scaffolding completo + gobernanza inicial |
