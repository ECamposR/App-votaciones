# ARCHITECTURE — Diseño del sistema

> Describe CÓMO está construido el sistema.
> Actualizar cuando cambie la arquitectura. Registrar la decisión en DECISIONS.md.

---

## 1. Visión general

```
                    ┌──────────────────────────────────────┐
Internet ──HTTPS──▶ │  Nginx (TLS termination)             │
                    │  VPS — ya operativo con MeshCentral  │
                    └───────────┬──────────────────────────┘
                                │ HTTP interno (red Docker)
              ┌─────────────────┼─────────────────────┐
              ▼                 ▼                       ▼
    ┌──────────────┐   ┌──────────────┐      ┌──────────────┐
    │  Frontend    │   │  Backend     │      │  PostgreSQL  │
    │  Vue 3 SPA   │   │  FastAPI     │      │  (interno)   │
    │  :3000 dev   │   │  :8000       │      │  :5432       │
    │  static prod │   │              │      │  NO expuesto │
    └──────────────┘   └──────┬───────┘      └──────────────┘
                              │
                    SSE stream (dashboard)
```

**En producción:** Nginx sirve el build estático de Vue y hace proxy_pass al backend FastAPI.
No hay servidor de Node en producción.

---

## 2. Estructura de directorios

```
votaciones-v2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # Engine, session async
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── poll.py          # Poll, VoterGroup, Category, Option
│   │   │   ├── vote.py          # Vote
│   │   │   └── user.py          # AdminUser
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── poll.py
│   │   │   ├── vote.py
│   │   │   └── user.py
│   │   ├── routers/             # FastAPI routers por dominio
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # POST /auth/login, /auth/logout, /auth/refresh
│   │   │   ├── polls.py         # CRUD /polls (admin)
│   │   │   ├── voting.py        # GET/POST /v/{token} (público)
│   │   │   ├── dashboard.py     # GET /dashboard/{poll_id} + SSE stream
│   │   │   ├── users.py         # CRUD /users (solo admin)
│   │   │   └── health.py        # GET /health
│   │   ├── services/            # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── scoring.py       # Cálculo de resultados ponderados
│   │   │   ├── importer.py      # Parseo CSV/XLSX
│   │   │   └── reports.py       # Generación XLSX
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── security.py      # Headers, CSRF, rate limit setup
│   │   └── deps.py              # FastAPI dependencies (get_db, get_current_user)
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/            # Migraciones
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_scoring.py
│   │   ├── test_voting.py
│   │   └── test_polls.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js         # Vue Router
│   │   ├── stores/
│   │   │   ├── auth.js          # Pinia — estado de autenticación
│   │   │   └── polls.js         # Pinia — estado de polls
│   │   ├── api/
│   │   │   ├── client.js        # fetch wrapper con refresh token
│   │   │   ├── polls.js
│   │   │   ├── auth.js
│   │   │   └── voting.js
│   │   ├── views/
│   │   │   ├── admin/
│   │   │   │   ├── DashboardView.vue    # Lista de polls
│   │   │   │   ├── PollDetailView.vue   # Gestión de un poll
│   │   │   │   ├── ImportView.vue       # Importar opciones
│   │   │   │   └── UsersView.vue        # Gestión de usuarios
│   │   │   ├── vote/
│   │   │   │   ├── VoteFormView.vue     # Formulario de voto (público)
│   │   │   │   └── VoteStatusView.vue   # Confirmación/estado
│   │   │   ├── dashboard/
│   │   │   │   └── LiveDashboardView.vue # Dashboard en vivo (SSE)
│   │   │   ├── LoginView.vue
│   │   │   └── SetupView.vue
│   │   └── components/
│   │       ├── PollCard.vue
│   │       ├── CategoryCard.vue
│   │       ├── OptionCard.vue
│   │       └── ResultsChart.vue
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── votaciones.conf
├── scripts/
│   └── backup.sh
├── docs/
│   └── ai/                      # Gobernanza (todos los .md de este sistema)
├── docker-compose.yml           # Producción
├── docker-compose.dev.yml       # Desarrollo local
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Modelo de datos

### Diagrama de entidades

```
AdminUser
├── id: UUID PK
├── username: str UNIQUE
├── password_hash: str
├── role: enum(admin, operator)
├── is_active: bool
└── created_at: datetime

Poll
├── id: UUID PK
├── title: str
├── description: str?
├── voting_type: enum(PLURALITY, RANKED, RATING, YES_NO)
├── status: enum(DRAFT, OPEN, CLOSED)
├── starts_at: datetime?
├── ends_at: datetime?
├── created_by: FK → AdminUser
├── created_at: datetime
└── updated_at: datetime

VoterGroup                         Category
├── id: UUID PK                    ├── id: UUID PK
├── poll_id: FK → Poll             ├── poll_id: FK → Poll
├── name: str                      ├── name: str
├── token: str UNIQUE              ├── order: int
└── weight: float (0.0-1.0)       └── created_at: datetime

Option
├── id: UUID PK
├── poll_id: FK → Poll
├── category_id: FK → Category
├── name: str
├── photo_url: str?
└── order: int

Vote
├── id: UUID PK
├── poll_id: FK → Poll
├── option_id: FK → Option
├── voter_group_id: FK → VoterGroup
├── voter_token: str               # cookie httpOnly del navegador
├── ip: str                        # auditoría
├── rank: int?                     # para voto preferencial (futuro)
└── created_at: datetime
```

### Regla de integridad: constraint UNIQUE en Vote
```sql
UNIQUE (poll_id, voter_group_id, voter_token, option_id)
-- Un votante no puede votar por la misma opción dos veces
-- Para detectar "ya votó en este poll+grupo":
--   SELECT COUNT(*) FROM vote WHERE poll_id=? AND voter_group_id=? AND voter_token=?
```

### Regla de integridad: sum de weights por Poll
```
VoterGroup.weight debe ser validado en capa de servicio:
  sum(group.weight for group in poll.voter_groups) == 1.0
  (tolerancia: abs(sum - 1.0) < 0.001)
```

---

## 4. Diseño de la API REST

### Auth
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/login` | — | Login; devuelve access+refresh en httpOnly cookies |
| POST | `/auth/logout` | ✅ | Limpia cookies |
| POST | `/auth/refresh` | refresh cookie | Renueva access token |
| GET | `/auth/me` | ✅ | Usuario autenticado actual |

### Setup
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/setup` | — | Verifica si hay usuarios. Si no → permite crear el primero |
| POST | `/setup` | — | Crea el primer admin (solo si no hay usuarios) |

### Polls (admin)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/polls` | ✅ | Lista todos los polls |
| POST | `/polls` | ✅ | Crear poll |
| GET | `/polls/{id}` | ✅ | Detalle de poll |
| PATCH | `/polls/{id}` | ✅ | Editar poll (solo en DRAFT) |
| DELETE | `/polls/{id}` | ✅ admin | Eliminar (confirmación requerida) |
| POST | `/polls/{id}/status` | ✅ | Cambiar estado |
| POST | `/polls/{id}/voter-groups` | ✅ | Agregar grupo de votantes |
| POST | `/polls/{id}/categories` | ✅ | Agregar categoría |
| POST | `/polls/{id}/options/import` | ✅ | Importar opciones desde CSV/XLSX |
| GET | `/polls/{id}/options` | ✅ | Listar opciones (con categoría) |
| GET | `/polls/{id}/results` | ✅ | Resultados calculados |
| GET | `/polls/{id}/report.xlsx` | ✅ | Reporte XLSX (solo CLOSED) |

### Votación (pública)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/v/{token}` | — | Pantalla de voto (HTML via Vue) |
| GET | `/v/{token}/data` | — | JSON con datos del poll para el formulario |
| POST | `/v/{token}/vote` | — | Registrar votos |

### Dashboard (autenticado)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/dashboard/{poll_id}` | ✅ | Vista del dashboard (HTML via Vue) |
| GET | `/dashboard/{poll_id}/stream` | ✅ | SSE stream de resultados |

### Users (solo admin)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/users` | ✅ admin | Lista usuarios |
| POST | `/users` | ✅ admin | Crear usuario |
| PATCH | `/users/{id}` | ✅ admin | Editar usuario |
| DELETE | `/users/{id}` | ✅ admin | Eliminar (restricciones de seguridad) |
| POST | `/users/{id}/change-password` | ✅ | Cambiar propia contraseña |

### Sistema
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | — | Healthcheck (Docker + load balancer) |

---

## 5. Flujo de autenticación JWT

```
Login:
  POST /auth/login {username, password}
  → Verifica credenciales
  → Genera access_token (JWT, 15min) + refresh_token (JWT, 7 días)
  → Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict; Path=/
  → Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh
  → 200 OK {user: {id, username, role}}

Request autenticado:
  → Browser envía access_token cookie automáticamente
  → Backend valida JWT, extrae user_id
  → Si expirado → 401 Unauthorized

Refresh (automático en frontend):
  POST /auth/refresh (con refresh_token cookie)
  → Genera nuevo access_token
  → Set-Cookie: access_token=... (nuevo)
  → 200 OK

Logout:
  POST /auth/logout
  → Set-Cookie: access_token=; Max-Age=0 (elimina cookie)
  → Set-Cookie: refresh_token=; Max-Age=0
```

---

## 6. Flujo de votación

```
Votante accede a /v/{token}:
  1. Vue Router intercepta → carga VoteFormView
  2. VoteFormView hace GET /v/{token}/data
  3. Backend busca VoterGroup por token
     → Si no existe: 404
     → Si Poll.status != OPEN: 409 (con mensaje apropiado)
     → Si voter_token en cookie ya votó: 409 (ya votó)
  4. Backend devuelve JSON con:
     - poll: {title, description}
     - voter_group: {name}
     - categories: [{name, options: [{id, name, photo_url}]}]
     - voter_already_voted: false
  5. Frontend setea cookie voter_id si no existe (o la lee si existe)
  6. Usuario completa el formulario → POST /v/{token}/vote
     - Body: {votes: [{option_id, category_id}]}
     - Cookie: voter_id (automática)
  7. Backend valida:
     - 1 voto por categoría
     - Opciones válidas para el poll/grupo
     - No duplicado (voter_token + poll_id + voter_group_id)
  8. → 200 OK → VoteStatusView (confirmación)
```

---

## 7. Algoritmo de scoring (invariante de negocio)

```python
def calcular_resultados(poll_id, session):
    poll = get_poll(poll_id, session)
    voter_groups = get_voter_groups(poll_id, session)  # con weight
    categories = get_categories(poll_id, session)

    resultados = {}
    for category in categories:
        options = get_options(category.id, session)
        option_ids = {opt.id for opt in options}

        ranking = []
        for option in options:
            score_final = 0.0
            votos_totales = 0

            grupos_con_participacion = [
                g for g in voter_groups
                if count_votes(poll_id, g.id, category.id) > 0
            ]
            peso_efectivo = 1.0 / len(grupos_con_participacion) if grupos_con_participacion else 0.0

            for group in voter_groups:
                votos_grupo = get_votes(poll_id, group.id, category.id)
                total_votos_grupo = len(votos_grupo)

                if total_votos_grupo == 0:
                    continue

                votos_opcion = count_votes_for_option(poll_id, group.id, option.id)
                score_normalizado = votos_opcion / total_votos_grupo

                # Si ambos grupos participaron: usar weight original
                # Si solo uno: usar 1.0 para ese grupo
                peso = group.weight if len(grupos_con_participacion) == len(voter_groups) else peso_efectivo
                score_final += score_normalizado * peso
                votos_totales += votos_opcion

            ranking.append({
                "option_id": option.id,
                "nombre": option.name,
                "score": round(score_final, 4),
                "votos_totales": votos_totales,
            })

        ranking.sort(key=lambda r: (r["score"], r["votos_totales"], r["nombre"]), reverse=True)
        resultados[category.name] = ranking

    return resultados
```
