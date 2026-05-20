from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# En desarrollo podemos habilitar echo=True para ver las queries generadas
is_dev = settings.ENVIRONMENT == "development"

# Motor de base de datos asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=is_dev,
    future=True,
    pool_pre_ping=True, # Verifica conexiones muertas antes de usarlas
)

# Generador de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Evita recargas redundantes al terminar transacciones
)


# Clase base declarativa para SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass
