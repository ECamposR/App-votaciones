from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestión del ciclo de vida de la aplicación.
    Verifica la conexión a la base de datos al arrancar.
    """
    # Verificar conexión a base de datos
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Conexión exitosa a la base de datos PostgreSQL")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a la base de datos PostgreSQL: {e}")
        # En producción podríamos decidir abortar el arranque,
        # pero en desarrollo permitimos arrancar para correr migraciones.
    
    yield
    
    # Cerrar el motor al apagar la aplicación
    await engine.dispose()


app = FastAPI(
    title="Sistema de Votaciones V2",
    description="API REST de la plataforma de votaciones internas organizacionales",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware de Hosts Permitidos para mitigar ataques de cabeceras HTTP Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check() -> dict[str, str]:
    """
    Endpoint de salud para monitoreo por Docker y balanceadores de carga.
    Verifica también el estado de la conexión a la base de datos.
    """
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status,
    }
