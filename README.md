# Plataforma de Votaciones Internas (Votaciones V2)

Esta es la segunda versión (V2) de la plataforma de votaciones internas para organizaciones, rediseñada para ser segura, escalable y flexible. Permite configurar múltiples tipos de votaciones (mayoría simple, voto preferencial, etc.) y estructurar grupos de votación con pesos ponderados.

> Nota sobre este checkout: el árbol actual contiene el backend, las migraciones, los tests, la documentación de gobernanza y el frontend administrativo base. Lo que sigue pendiente es completar las pantallas de votación pública y dashboard en vivo.

---

## 🏗️ Arquitectura y Stack Tecnológico

El sistema utiliza una arquitectura desacoplada:

- **Backend**: API REST desarrollada con **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.0 (async)** y **PostgreSQL 16**.
- **Frontend**: Single Page Application (SPA) construida con **Vue 3 (Composition API)**, **Vite**, **TailwindCSS** y **Pinia**.
- **Servidor Web / Proxy**: **Nginx** sirviendo el build estático del frontend y haciendo proxy inverso hacia el backend de FastAPI, con soporte y optimización para Server-Sent Events (SSE).
- **Contenerización**: Empaquetado completo con **Docker / Podman** y **Docker Compose**.

---

## 📁 Estructura del Proyecto

```text
votaciones-v2/
├── backend/                  # Código fuente del Backend (FastAPI)
│   ├── alembic/              # Versiones y configuración de migraciones de base de datos
│   ├── app/                  # Módulos de la aplicación FastAPI
│   │   ├── models/           # Modelos de SQLAlchemy 2.0 (async)
│   │   ├── routers/          # Controladores y rutas de la API REST
│   │   ├── schemas/          # Esquemas de validación de datos (Pydantic v2)
│   │   ├── services/         # Lógica de negocio (importers, scoring, reports)
│   │   ├── config.py         # Configuración de variables de entorno (pydantic-settings)
│   │   ├── database.py       # Engine y fábrica de sesiones asíncronas de SQLAlchemy
│   │   └── deps.py           # Dependencias reutilizables de FastAPI (get_db, auth)
│   ├── tests/                # Suite de pruebas unitarias y de integración
│   ├── requirements.txt      # Dependencias de producción
│   └── requirements-dev.txt  # Dependencias de desarrollo (pytest, ruff, etc.)
├── docs/                     # Documentación de Gobernanza e Historial (ADR)
│   └── ai/                   # Protocolos de IA, ADRs y registro de decisiones
├── nginx/                    # Archivos de configuración de Nginx (servidor web)
├── docker-compose.yml        # Configuración de servicios para producción
├── docker-compose.dev.yml    # Configuración de servicios para desarrollo local
├── .env.example              # Plantilla de variables de entorno
└── README.md                 # Guía y manual de uso rápido
```

---

## 🚀 Setup en Desarrollo Local

### 1. Requisitos Previos
- Python 3.12 o superior.
- Docker o Podman.

### 2. Configurar Variables de Entorno
Copia la plantilla de variables de entorno y ajusta los valores necesarios en el archivo `.env`:
```bash
cp .env.example .env
```

### 3. Levantar la Base de Datos (PostgreSQL)
Si tienes `docker-compose` o `podman-compose` instalado:
```bash
docker compose -f docker-compose.dev.yml up -d db
```
Si usas **Podman** de forma nativa sin compose provider:
```bash
podman run --name votaciones_db_dev -d -p 127.0.0.1:5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres_secure_password -e POSTGRES_DB=votaciones docker.io/library/postgres:16-alpine
```

### 4. Configurar el Entorno Virtual del Backend
Entra en la carpeta `backend/`, crea el entorno virtual e instala todas las dependencias:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 5. Correr las Migraciones de Base de Datos
Asegúrate de tener configurado tu `.env` (o pasa las variables en la ejecución) y corre Alembic:
```bash
# Desde la carpeta backend/ con el entorno virtual activo:
JWT_SECRET=dummy_secret DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones alembic upgrade head
```

### 6. Levantar el Backend en Modo Desarrollo (Hot Reload)
```bash
# Desde la carpeta backend/ con el entorno virtual activo:
JWT_SECRET=dummy_secret DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones uvicorn app.main:app --reload
```
La API estará disponible en [http://localhost:8000](http://localhost:8000) y la documentación interactiva en [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🗃️ Migraciones con Alembic

Cuando realices modificaciones en los modelos de SQLAlchemy, debes generar y aplicar una nueva migración:

```bash
# 1. Crear una revisión de migración automática
JWT_SECRET=dummy_secret DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones alembic revision --autogenerate -m "descripcion_de_los_cambios"

# 2. Aplicar la migración a tu base de datos local
JWT_SECRET=dummy_secret DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones alembic upgrade head
```

---

## 🔒 Reglas de Seguridad en Producción
- Nunca expongas al exterior los puertos de la base de datos (`5432`) o de uvicorn (`8000`). Todo el tráfico debe ser enrutado y controlado por Nginx.
- Asegúrate de cambiar `JWT_SECRET` y las contraseñas de PostgreSQL por cadenas seguras y únicas antes de desplegar en producción.
- En producción, todas las cookies de sesión se expiden con las banderas `HttpOnly`, `Secure` y `SameSite=Strict/Lax`.
