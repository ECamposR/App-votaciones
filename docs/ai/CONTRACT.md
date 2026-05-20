# CONTRACT — Contrato técnico y de negocio

> Documento fundacional. Define QUÉ construimos y POR QUÉ.
> Ninguna IA debe cambiar el contenido de este archivo sin aprobación explícita del usuario.
> Los cambios se registran como ADR en DECISIONS.md.

---

## 1. Propósito

Plataforma web interna para gestionar votaciones y encuestas organizacionales.
Desplegada en VPS propio, accesible desde internet, multi-tenant por evento (Poll).

### Casos de uso iniciales (v2.0)
- Votación mensual "Empleado del Mes" con ponderación por grupo de votantes
- Base extensible para otros tipos de encuesta

### Visión de producto (largo plazo)
- Múltiples tipos de votación: plurality, ranked choice, rating scale, yes/no
- Grupos de votantes configurables con pesos diferenciados
- Categorías (departamentos) configurables por encuesta
- Links de votación por grupo (no por individuo)
- Dashboard en vivo proyectable en reuniones
- Exportación de resultados (XLSX, PDF)
- Historial de ganadores entre encuestas

---

## 2. Reglas de negocio core

### 2.1 Poll (encuesta/votación)
- Un Poll tiene estado: `draft` → `open` → `closed`
- Solo se puede votar cuando el Poll está `open`
- Los resultados son definitivos cuando el Poll está `closed`
- Los reportes se habilitan solo en estado `closed`
- El dashboard es visible en cualquier estado (para usuarios autenticados)

### 2.2 Grupos de votantes (VoterGroup)
- Cada Poll define sus propios grupos de votantes (no hardcodeados globalmente)
- Cada grupo tiene un token único (UUID) que es el link de votación
- Cada grupo tiene un weight (0.0–1.0); la suma de todos los weights de un Poll = 1.0
- Si un Poll tiene un solo grupo activo, ese grupo tiene weight = 1.0 efectivo
- Los grupos son configurables: puede haber 1, 2, 3 o más grupos por Poll

### 2.3 Categorías (Category)
- Cada Poll define sus propias categorías (equivalente a "departamentos")
- No hay categorías globales hardcodeadas
- Un votante debe emitir exactamente 1 voto por categoría que tenga opciones
- Si una categoría no tiene opciones (Option), el Poll no puede abrirse

### 2.4 Opciones (Option)
- Equivalente a "candidatos" en el caso de uso de empleado del mes
- Cada Option pertenece a una Category y a un Poll
- Opcionales: foto_url para mostrar imagen en el formulario de voto

### 2.5 Votos (Vote)
- Un votante (identificado por voter_token = cookie httpOnly) puede votar UNA sola vez por Poll+VoterGroup
- Un voto registra: option_id, voter_group_id, voter_token (cookie), ip (auditoría)
- Para voto preferencial (ranked): se agrega campo `rank` (int, opcional)
- Un votante no puede votar por la misma opción dos veces en el mismo Poll

### 2.6 Scoring (cálculo de resultados)
- Por cada Category y por cada VoterGroup: se calcula el score normalizado
  - `score_normalizado = votos_a_opción / total_votos_del_grupo_en_categoría`
- Score final de una opción = `Σ (score_normalizado_grupo × weight_grupo)`
- Cuando solo un grupo participó: ese grupo tiene weight efectivo = 1.0 (no se divide)
- El ranking final se ordena por score descendente; en empate por votos totales; en empate por nombre alfabético

### 2.7 Deduplicación de votantes
- Se usa una cookie httpOnly (`voter_id`) con un UUID v4 aleatorio
- La cookie se establece al primer acceso al link de votación
- Duración de la cookie: 1 año
- La cookie es `Secure`, `HttpOnly`, `SameSite=Lax`
- El `voter_token` guardado en `Vote` es el valor de esa cookie
- Limitación conocida y aceptada: modo incógnito / borrar cookies permite votar nuevamente

### 2.8 Autenticación admin
- El panel administrativo requiere login con usuario y contraseña
- Roles: `admin` (acceso total) y `operator` (puede operar polls, no gestiona usuarios)
- Auth vía JWT en httpOnly cookie (access token 15min, refresh token 7 días)
- Las rutas de votación `/v/{token}` son siempre públicas (sin login)

---

## 3. Stack tecnológico

### 3.1 Backend
| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Lenguaje | Python | 3.12+ |
| Framework | FastAPI | latest stable |
| ORM | SQLAlchemy 2.0 (async) | latest stable |
| Migraciones | Alembic | latest stable |
| Base de datos | PostgreSQL | 16+ |
| Auth | python-jose + passlib[bcrypt] | latest |
| Servidor | Uvicorn | latest stable |
| Validación | Pydantic v2 | (viene con FastAPI) |
| Archivos | python-multipart + openpyxl | latest |
| Rate limiting | slowapi | latest |

### 3.2 Frontend
| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Framework | Vue 3 (Composition API) | latest stable |
| Build | Vite | latest stable |
| Estado | Pinia | latest stable |
| Router | Vue Router 4 | latest stable |
| Estilos | TailwindCSS | 3.x |
| HTTP | fetch API nativa | — |
| Icons | Lucide Vue | latest |
| Charts | Chart.js + vue-chartjs | latest |

### 3.3 Infraestructura
| Componente | Tecnología |
|-----------|-----------|
| Contenerización | Docker + Docker Compose |
| Proxy | Nginx (ya en VPS con MeshCentral) |
| TLS | Let's Encrypt / Certbot (ya configurado en VPS) |
| Base de datos | PostgreSQL en Docker |
| Real-time | SSE (Server-Sent Events) — sin WebSockets, sin Redis |
| Backup | Script SQLite/pg_dump + cron en host |

---

## 4. Restricciones y anti-patrones

- ❌ No usar WebSockets ni Redis — SSE es suficiente para el caso de uso
- ❌ No usar frameworks de estado complejos en frontend (Vuex legacy, Redux, etc.)
- ❌ No hardcodear departamentos, grupos o tipos de votación en el código
- ❌ No usar ORMs diferentes a SQLAlchemy 2.0 para el backend
- ❌ No agregar dependencias nuevas sin registrar ADR en DECISIONS.md
- ❌ No usar `SECRET_KEY` o cualquier secreto con valor por defecto — la app debe fallar al arrancar si no está configurado
- ❌ No exponer el puerto de uvicorn (8000) ni el de PostgreSQL (5432) al exterior — solo Nginx y Docker internal network

---

## 5. Seguridad — principios no negociables

1. Todos los secretos via variables de entorno — nunca en código ni en repositorio
2. JWT en httpOnly cookie — nunca en localStorage
3. HTTPS siempre en producción — Nginx termina TLS
4. Rate limiting en endpoints de auth y votación
5. CSRF protection en todos los endpoints POST del panel admin
6. Cabeceras de seguridad HTTP en todas las respuestas
7. PostgreSQL no expuesto al exterior — solo accesible desde el container de backend
8. `proxy_headers=True` en Uvicorn — confiar en X-Forwarded-For de Nginx
