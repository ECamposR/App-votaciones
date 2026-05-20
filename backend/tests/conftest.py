from __future__ import annotations

import asyncio
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base
from app.deps import get_db
from app.main import app

# Permitir el dominio virtual de pruebas de HTTPX en las cabeceras de host
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")

# URLs de base de datos para pruebas
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/votaciones_test"
ADMIN_DATABASE_URL = "postgresql+asyncpg://postgres:postgres_secure_password@127.0.0.1:5432/postgres"


@pytest.fixture(scope="session")
def event_loop():
    """
    Define el loop de eventos asíncronos para toda la sesión de pruebas.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db(event_loop):
    """
    Prepara la base de datos de pruebas creando la base de datos 'votaciones_test' si no existe,
    y generando todas las tablas a partir de los metadatos de los modelos.
    """
    # 1. Crear base de datos de prueba si no existe (requiere AUTOCOMMIT)
    admin_engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        try:
            await conn.execute(text("CREATE DATABASE votaciones_test"))
        except Exception:
            # Si ya existe (p. ej., de corridas anteriores), ignoramos el error
            pass
    await admin_engine.dispose()

    # 2. Generar el esquema inicial en la base de datos de pruebas
    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 3. Limpieza final de tablas tras terminar la suite de pruebas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture que provee una sesión de base de datos aislada para cada test.
    Envuelve la ejecución de cada prueba dentro de una transacción que hace rollback al finalizar.
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with async_session(bind=connection) as session:
            yield session
            await session.close()
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provee un cliente HTTP de pruebas asíncrono HTTPX que interactúa con la aplicación FastAPI
    y tiene la base de datos mockeada con la transacción aislada de la prueba.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
