# DECISIONS — Registro de Decisiones de Arquitectura (ADR)

> Append-only. Nunca eliminar entradas, solo superseder.
> Formato: ADR-XXX | Título | Fecha | Estado

---

## ADR-001 | Reconstrucción desde cero (V2) en lugar de evolucionar V1
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** La app V1 fue diseñada para uso LAN-only. Se necesita migrar a VPS/internet y soportar múltiples tipos de votación. El modelo de datos de V1 tiene restricciones de negocio hardcodeadas (2 grupos fijos, 4 departamentos fijos) que no pueden extenderse sin rediseñar las tablas.
- **Decisión:** Reconstruir desde cero con stack moderno, seguro por diseño y modelo de datos extensible. Rescatar lógica de negocio (scoring, importador) y toda la documentación de ADRs de V1.
- **Consecuencias:** Mayor tiempo al primer deploy. Los datos de V1 requieren script de migración. El código de V1 se mantiene en repo separado como referencia.

---

## ADR-002 | PostgreSQL en lugar de SQLite
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba SQLite que es adecuado para LAN. En VPS con múltiples conexiones concurrentes (votantes + SSE) y acceso desde internet, se necesita mejor manejo de concurrencia y backup estándar.
- **Decisión:** PostgreSQL 16+ via Docker. Backup con `pg_dump`. Migraciones con Alembic.
- **Consecuencias:** Agrega un servicio al docker-compose. Backup vía `pg_dump` en lugar de copiar archivo. Más robusto para internet.

---

## ADR-003 | SQLAlchemy 2.0 async + Alembic en lugar de SQLModel
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba SQLModel (wrapper de SQLAlchemy). Para V2 se necesitan migraciones formales desde el primer día y control total sobre el ORM.
- **Decisión:** SQLAlchemy 2.0 con API moderna (Mapped, mapped_column) + Alembic para migraciones. Sin SQLModel.
- **Consecuencias:** Más verboso que SQLModel. Mejor control. Migraciones desde el commit inicial.

---

## ADR-004 | JWT en httpOnly cookie en lugar de SessionMiddleware
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba SessionMiddleware de Starlette con cookie de sesión. En internet, JWT stateless es mejor para escalabilidad y permite API-first.
- **Decisión:** Access token (15min) + Refresh token (7 días), ambos en httpOnly cookies. Access token path `/`, Refresh token path `/auth/refresh` para minimizar exposición.
- **Consecuencias:** Requiere lógica de refresh en el frontend. Sin estado de sesión en el servidor (stateless). Permite futura API móvil sin cambios de auth.

---

## ADR-005 | Vue 3 + Vite en lugar de HTMX + Jinja2
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba HTMX + Jinja2 que funciona bien para formularios simples. Para múltiples tipos de votación (drag-and-drop para ranking, wizards multi-paso, etc.) se necesita un framework frontend más capaz.
- **Decisión:** Vue 3 (Composition API + script setup) + Vite + Pinia + Vue Router. TailwindCSS se mantiene.
- **Consecuencias:** Build step requerido para el frontend. Nginx sirve el build estático. Mejor DX para UIs complejas. Permite mobile en el futuro.

---

## ADR-006 | Modelo de datos extensible (Poll/VoterGroup/Category/Option)
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 hardcodeaba 2 grupos de votantes y 4 departamentos en el schema y en el código. Imposible agregar nuevos tipos de votación sin breaking changes.
- **Decisión:** Modelo genérico: Poll → [VoterGroup con weight] + [Category] → [Option]. Los grupos, categorías y opciones son configurables por Poll. La lógica de ponderación usa el weight del grupo, no valores hardcodeados.
- **Consecuencias:** Más flexible. El caso de uso "empleado del mes" se configura como Poll con 2 VoterGroups (weight=0.5 cada uno) + 4 Categories. La UI admin debe permitir configurar estos elementos.

---

## ADR-007 | UUIDs como primary keys en lugar de integers
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba IDs enteros secuenciales. En internet, IDs enumerables exponen el dashboard de eventos a cualquiera que adivine el número.
- **Decisión:** UUIDs v4 como primary key en todas las tablas. URLs de dashboard: `/dashboard/{uuid}` — no enumerable.
- **Consecuencias:** URLs más largas. No enumerables. Mejor para URLs públicas de votación. Compatibilidad total con PostgreSQL UUID type.

---

## ADR-008 | Deduplicación por cookie httpOnly (voter_id)
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** V1 usaba SHA256(IP+UA) que falla en internet por CGNAT y VPNs compartidas. Se evaluaron: links individuales por empleado (más complejo), código PIN (requiere distribución), cookie de navegador (más simple, misma robustez pragmática).
- **Decisión:** Cookie httpOnly con UUID v4 generado al primer acceso al link de votación. Secure, SameSite=Lax, Max-Age=1 año. El voter_token es el valor de esta cookie.
- **Consecuencias:** Limitación conocida y aceptada: modo incógnito o borrar cookies permite votar nuevamente. Solución pragmática equivalente a la de V1 pero que funciona en internet.

---

## ADR-009 | SSE para dashboard en tiempo real (sin WebSockets ni Redis)
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** SSE funcionó bien en V1. WebSockets agregarían complejidad. Redis no es necesario para el volumen actual.
- **Decisión:** Mantener SSE con cache en memoria de 3 segundos (evita recalcular por cada conexión). Un endpoint por poll: `/dashboard/{poll_id}/stream`.
- **Consecuencias:** Nginx requiere `proxy_buffering off` para el path `/dashboard/`. Máximo ~50 conexiones simultáneas aceptables para el caso de uso.

---

## ADR-010 | Rate limiting con slowapi (sin Redis)
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** Se necesita rate limiting en internet para login y votación. Redis agrega infraestructura. Para el volumen esperado, rate limiting en memoria es suficiente.
- **Decisión:** `slowapi` con almacenamiento en memoria. Límites: login 10/min por IP, votación 5/min por IP.
- **Consecuencias:** El rate limiting se reinicia al reiniciar el contenedor. Aceptable para el caso de uso.

---

## ADR-011 | FastAPI sirve tanto API como archivos estáticos del frontend
- **Fecha:** 2026-05-20
- **Estado:** Aceptado
- **Contexto:** Vue 3 genera un build estático (dist/). Se puede servir con Nginx directamente o hacer que FastAPI sirva los archivos.
- **Decisión:** En producción, Nginx sirve los archivos estáticos del frontend directamente (más eficiente) y hace proxy_pass solo a `/api/` para el backend. Vue Router usa modo history (HTML5), Nginx está configurado para hacer fallback a `index.html`.
- **Consecuencias:** Separación clara entre frontend estático y backend API. Build del frontend requerido en el proceso de deploy.
