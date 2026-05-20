# CODING_STANDARDS — Estándares de código

> Guía de estilo y convenciones para mantener consistencia entre sesiones de IA.

---

## 1. Backend — Python / FastAPI

### 1.1 Estilo general
- Python 3.12+, tipo estricto en todo (`from __future__ import annotations`)
- `ruff` para linting y formateo (reemplaza black + flake8 + isort)
- Máximo 100 caracteres por línea
- Docstrings solo donde el comportamiento no es obvio

### 1.2 Async
- Todos los endpoints FastAPI son `async def`
- Todas las operaciones de DB usan `await session.execute(...)` (SQLAlchemy 2.0 async)
- No mezclar sync y async en el mismo módulo sin justificación

### 1.3 Estructura de un router
```python
# routers/polls.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.models.user import AdminUser
from app.schemas.poll import PollCreate, PollRead
from app.services import polls as poll_service

router = APIRouter(prefix="/polls", tags=["polls"])


@router.post("/", response_model=PollRead, status_code=status.HTTP_201_CREATED)
async def create_poll(
    body: PollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> PollRead:
    return await poll_service.create(body, current_user, db)
```

### 1.4 Estructura de un modelo SQLAlchemy 2.0
```python
# models/poll.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import AdminUser


class PollStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class Poll(Base):
    __tablename__ = "poll"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[PollStatus] = mapped_column(default=PollStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("adminuser.id"))

    # Relationships
    created_by: Mapped[AdminUser] = relationship(back_populates="polls")
    voter_groups: Mapped[list[VoterGroup]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    categories: Mapped[list[Category]] = relationship(back_populates="poll", cascade="all, delete-orphan")
```

### 1.5 Estructura de un schema Pydantic
```python
# schemas/poll.py
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PollBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class PollCreate(PollBase):
    pass


class PollRead(PollBase):
    id: uuid.UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### 1.6 Manejo de errores
```python
# Siempre usar HTTPException con status_code apropiado
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll no encontrado")
raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya votaste en este poll")
raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")
```

### 1.7 Dependencias FastAPI
```python
# deps.py — centralizar todas las dependencias
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    # ... validar JWT
```

---

## 2. Frontend — Vue 3

### 2.1 Estilo general
- Vue 3 Composition API con `<script setup>` (no Options API)
- TypeScript opcional — se prefiere JS con JSDoc para velocidad de desarrollo
- `<script setup>` siempre antes de `<template>`
- Nombres de componentes: PascalCase (`PollCard.vue`)
- Nombres de archivos: PascalCase para componentes, camelCase para utilities

### 2.2 Estructura de un componente
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePollsStore } from '@/stores/polls'

// Props
const props = defineProps({
  pollId: { type: String, required: true }
})

// Emits
const emit = defineEmits(['closed'])

// Estado local
const loading = ref(false)
const error = ref(null)

// Store
const pollsStore = usePollsStore()

// Computed
const poll = computed(() => pollsStore.getPollById(props.pollId))

// Métodos
async function loadPoll() {
  loading.value = true
  try {
    await pollsStore.fetchPoll(props.pollId)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(loadPoll)
</script>

<template>
  <div v-if="loading">Cargando...</div>
  <div v-else-if="error">{{ error }}</div>
  <div v-else-if="poll">
    <!-- contenido -->
  </div>
</template>
```

### 2.3 API client
```javascript
// api/client.js — wrapper de fetch con manejo de auth
export async function apiFetch(url, options = {}) {
  const response = await fetch(`/api${url}`, {
    credentials: 'include',  // incluir cookies automáticamente
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (response.status === 401) {
    // Intentar refresh
    const refreshed = await tryRefresh()
    if (refreshed) return apiFetch(url, options)
    // Si falla el refresh → redirect a login
    window.location.href = '/login'
    return
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Error ${response.status}`)
  }

  return response.json()
}
```

### 2.4 TailwindCSS
- Usar clases utilitarias directamente en el template
- No crear clases CSS personalizadas salvo que sea absolutamente necesario
- Usar `@apply` en CSS solo para componentes muy repetitivos
- Paleta de colores: definir en `tailwind.config.js` sección `theme.extend`

---

## 3. Migraciones (Alembic)

### Crear migración
```bash
# Desde el directorio backend/
alembic revision --autogenerate -m "descripcion_del_cambio"
```

### Aplicar migración
```bash
alembic upgrade head
```

### Convención de nombres
- `add_{column}_to_{table}` — para agregar columnas
- `create_{table}_table` — para nuevas tablas
- `remove_{column}_from_{table}` — para eliminar columnas

### Regla
**Nunca** usar `Base.metadata.create_all()` en producción. Solo Alembic.
En tests sí se puede usar para crear el schema de test.

---

## 4. Testing

### Backend
```bash
# Correr todos los tests
pytest tests/

# Con cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

### Estructura de tests
```python
# tests/test_scoring.py
import pytest
from app.services.scoring import calcular_resultados

def test_scoring_dos_grupos_igual_participacion():
    """Con 2 grupos de igual participación, el score es 50/50"""
    # ... setup
    resultados = calcular_resultados(poll_id, session)
    assert resultados["Categoría A"][0]["score"] == 0.5

def test_scoring_un_solo_grupo():
    """Si solo participa un grupo, ese grupo tiene peso 100%"""
    # ...
```

### Cobertura mínima requerida
- `services/scoring.py`: 100% (lógica de negocio crítica)
- `routers/voting.py`: >80%
- `routers/auth.py`: >80%

---

## 5. Commits y ramas

### Formato de commit
```
tipo: descripción concisa en presente

[opcional: cuerpo con más detalle]
[opcional: referencia a TASK-XXX]
```

**Tipos:**
- `feat:` — nueva funcionalidad
- `fix:` — corrección de bug
- `docs:` — documentación
- `refactor:` — refactor sin cambio de comportamiento
- `test:` — agregar o corregir tests
- `chore:` — tareas de mantenimiento (deps, config)
- `security:` — parches de seguridad

### Ejemplos
```
feat: implementar endpoint POST /polls/{id}/vote

fix: corregir cálculo de score cuando solo un grupo vota

docs: actualizar HANDOFF con estado post-sprint-1

security: agregar rate limiting en /auth/login
```
