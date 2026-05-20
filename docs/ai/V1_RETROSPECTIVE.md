# Retrospectiva de V1 y Auditoría de Migración a VPS

Este documento recopila las lecciones aprendidas de la versión 1.0 (MVP para LAN), los hallazgos de seguridad derivados del análisis para la exposición a internet (VPS), y la justificación técnica que guio el diseño de la arquitectura V2.

---

## 1. Puntos Alcanzados en la V1 (MVP LAN)

La versión V1.0 de la aplicación validó con éxito el flujo de negocio y las reglas de votación para el caso de uso inicial ("Empleado del Mes"):

- **Carga de Datos:** Implementación de un parser en `app/importers.py` capaz de leer candidatos desde archivos CSV o planillas Excel (XLSX) con validación de columnas obligatorias.
- **Flujo de Votación:**
  - Emisión de un voto por cada uno de los 4 departamentos de la organización (4 votos en total por elector).
  - Interfaz de búsqueda de candidatos asistida por autocompletado en tiempo real (HTMX typeahead).
  - Deduplicación básica mediante un fingerprint generado con el hash de `IP + User-Agent`.
- **Lógica de Scoring:**
  - Cálculo de resultados aplicando ponderación de peso equivalente (50% personal base y 50% jefaturas).
  - Normalización de votos para evitar distorsiones por diferente volumen de participación entre grupos.
- **Resultados en Tiempo Real:**
  - Dashboard en vivo proyectable utilizando Server-Sent Events (SSE) sin sobrecargar al servidor con polling continuo.
  - Visualización del gráfico de donut departamental de forma anónima (porcentajes de Top N y hover detallado con nombres).

---

## 2. Auditoría de Seguridad: Vulnerabilidades de V1 ante Internet

Al planificarse la migración de la app a un VPS accesible desde internet, se identificaron 7 fallos críticos (BLOCKERS) en V1:

### B-1 · Ausencia de cifrado (HTTPS)
La sesión de administración (`session_id`) viajaba en texto plano sobre HTTP. Expuesto a internet, esto posibilitaba ataques de secuestro de sesión (*session hijacking*).

### B-2 · Secreto de sesión hardcodeado
La variable `SESSION_SECRET` contaba con un valor por defecto. De no configurarse el entorno en el VPS, cualquiera podría forjar cookies de sesión admin legítimas.

### B-3 · Falta de banderas de seguridad en cookies
Las cookies carecían de los modificadores `Secure` (envío solo en HTTPS) y `SameSite` estricto, dejando expuesta la sesión del administrador.

### B-4 · Vulnerabilidad CSRF (Cross-Site Request Forgery)
Los formularios del panel de administración realizaban mutaciones mediante peticiones POST sin un mecanismo de validación de origen (tokens CSRF), exponiendo las acciones de administración a ejecuciones desde portales maliciosos externos.

### B-5 · Dashboard público y IDs enumerables
La URL de visualización en vivo `/dashboard/{evento_id}` era pública y utilizaba IDs correlativos enteros (1, 2, 3...). Un tercero en internet podía adivinar los IDs y monitorizar el recuento en vivo de cualquier votación activa de la empresa.

### B-6 · Links de votación perpetuos
Los enlaces únicos para votantes (empleados/jefaturas) eran UUIDs persistentes que carecían de fecha de expiración y revocabilidad.

### B-7 · Deduplicación por IP+UA rota en internet
El fingerprinting mediante `SHA256(IP + UA)` genera colisiones inmediatas en internet debido a:
- **CGNAT de operadoras móviles:** Múltiples teléfonos bajo una misma IP pública. El voto de un empleado bloqueaba a los demás.
- **VPNs de la empresa:** Todo el tráfico corporativo sale por la misma IP.
- **Redes compartidas (WiFi de oficina/café):** Misma IP externa.

---

## 3. Deuda Técnica de la V1

Aparte de la seguridad, el desarrollo y mantenimiento del MVP presentaba los siguientes límites:

- **Monolito en un solo archivo:** `main.py` centralizaba 794 líneas con lógica de controladores, base de datos, routing, auth, e importaciones cruzadas.
- **Sin migraciones de DB:** Se dependía de `create_all()`. Cualquier modificación estructural obligaba a purgar la base de datos SQLite o a alterarla a mano.
- **Sin suite de pruebas:** No existían tests unitarios para validar la lógica del cálculo matemático de scoring (50/50) ni el flujo de votación.
- **Inflexibilidad del Modelo de Datos:** Las tablas del modelo estaban rígidamente asociadas al caso de uso de "Empleado del Mes" (dos links fijos por evento, columnas con categorías de departamentos fijas).

---

## 4. Transición a V2: Principios del Rediseño

Para solucionar los problemas de seguridad y posibilitar la extensión de la plataforma a más tipos de votación en diferentes contextos organizacionales, se tomó la decisión de reconstruir la app desde cero (V2) bajo las siguientes directrices:

### 4.1 Modelo de Datos Extensible
En lugar de fijar los grupos y los departamentos en el esquema de tablas, se introdujeron relaciones dinámicas:
- `Poll` (Encuesta) → Se configura dinámicamente el tipo de votación (plurality, ranked, etc.) y los límites de fechas.
- `VoterGroup` (Grupo de Votantes) → Se pueden registrar 1, 2, 3 o N grupos con su propio peso (`weight`) asignado (por ejemplo, 50% empleados, 50% jefes).
- `Category` (Categorías) → Dinámicas (los antiguos departamentos).
- `Option` (Opciones) → Los candidatos, vinculados a una categoría y un evento.

### 4.2 Deduplicación por Cookies del Navegador
Reemplaza el fingerprinting de IP+UA. Al ingresar al link de votación, el sistema expide una cookie HTTPOnly de larga duración (1 año) llamada `voter_id` que contiene un UUIDv4 único. Este UUID es guardado de forma cifrada en la base de datos al votar, impidiendo duplicar el voto en el mismo dispositivo, sin importar si los electores comparten red, IP o VPN.

### 4.3 Seguridad By Design
- Control de tokens con JWT distribuidos en cookies `HttpOnly` y `Secure` (Access Token + Refresh Token).
- Cierre del puerto expuesto de FastAPI (`8000`) al exterior, permitiendo únicamente el puente local a través de la red interna de Docker desde un proxy inverso Nginx.
- Middleware obligatorio de cabeceras de seguridad (HSTS, X-Content-Type, X-Frame).
- Integración de `slowapi` para mitigar ataques de fuerza bruta en accesos del panel y spam de votos.
- Implementación obligatoria de CSRF tokens en formularios.
- Migración a **PostgreSQL** para manejo óptimo de concurrencia y seguridad transaccional frente al SQLite monolítico de la versión LAN.
