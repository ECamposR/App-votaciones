from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AdminUser, AdminRole
from app.services.auth import verify_password, hash_password, create_access_token

# Forzar que todos los tests de este módulo sean asíncronos
pytestmark = pytest.mark.asyncio


async def test_setup_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Verifica el flujo del endpoint /setup:
    1. GET inicial -> retorna false (sin administrador) y setea csrftoken cookie.
    2. POST de creación -> crea el administrador correctamente enviando x-csrftoken header.
    3. GET posterior -> retorna true.
    4. POST posterior -> retorna 403 Forbidden (ya configurado).
    """
    # 1. GET /setup inicial
    response = await client.get("/setup")
    assert response.status_code == 200
    assert response.json() == {"has_admin": False}
    
    # Extraer el token CSRF generado en la cookie
    csrf_token = response.cookies.get("csrftoken")
    assert csrf_token is not None

    # 2. POST /setup exitoso
    setup_payload = {
        "username": "admin_test",
        "password": "supersecurepassword123",
    }
    response = await client.post(
        "/setup",
        json=setup_payload,
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == "admin_test"
    assert user_data["role"] == "admin"
    assert "id" in user_data

    # Verificar registro en base de datos
    result = await db_session.execute(
        select(AdminUser).where(AdminUser.username == "admin_test")
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.role == AdminRole.ADMIN
    assert verify_password("supersecurepassword123", db_user.password_hash)

    # 3. GET /setup posterior (debe dar True)
    response = await client.get("/setup")
    assert response.status_code == 200
    assert response.json() == {"has_admin": True}

    # 4. POST /setup posterior (debe fallar con 403)
    csrf_token = response.cookies.get("csrftoken") or csrf_token
    response = await client.post(
        "/setup",
        json=setup_payload,
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 403
    assert "previamente" in response.json()["detail"]


async def test_login_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba el ciclo de vida de autenticación:
    1. Login fallido por credenciales inválidas.
    2. Login exitoso con cookies HttpOnly seteadas.
    3. Acceso a /auth/me sin y con cookie access_token.
    4. Refresco de token usando la cookie refresh_token.
    5. Cierre de sesión (logout).
    """
    # Obtener token CSRF inicial
    response = await client.get("/setup")
    csrf_token = response.cookies.get("csrftoken")
    assert csrf_token is not None

    # Crear un administrador en la BD de pruebas
    admin_user = AdminUser(
        username="login_test",
        password_hash=hash_password("correct_password_123"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    # 1. Login incorrecto
    login_payload = {
        "username": "login_test",
        "password": "wrong_password",
    }
    response = await client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]

    # 2. Login correcto
    login_payload["password"] = "correct_password_123"
    response = await client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "login_test"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Extraer tokens de las cookies recibidas
    access_token = response.cookies.get("access_token")
    refresh_token = response.cookies.get("refresh_token")

    # Limpiar cookies del cliente HTTPX para simular peticiones sin estado
    client.cookies.clear()

    # 3. Acceso a /auth/me sin autenticación (debe fallar)
    response = await client.get("/auth/me")
    assert response.status_code == 401

    # 4. Acceso a /auth/me con access_token cookie
    client.cookies.set("access_token", access_token)
    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "login_test"

    # 5. Renovación de token (Refresh)
    client.cookies.clear()
    
    # Obtener un nuevo token CSRF para refresco (al limpiar cookies se borró el csrftoken)
    response = await client.get("/setup")
    csrf_token = response.cookies.get("csrftoken")
    assert csrf_token is not None
    
    # Intentar refresco sin refresh_token
    response = await client.post(
        "/auth/refresh",
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 401

    # Intentar refresco con refresh_token
    client.cookies.set("refresh_token", refresh_token)
    response = await client.post(
        "/auth/refresh",
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    new_access_token = response.cookies.get("access_token")

    # 6. Logout (Borrado de cookies)
    client.cookies.clear()
    # Necesitamos csrftoken y access_token para desloguear de forma segura
    response = await client.get("/setup")
    csrf_token = response.cookies.get("csrftoken")
    client.cookies.set("access_token", new_access_token)
    client.cookies.set("refresh_token", refresh_token)
    
    response = await client.post(
        "/auth/logout",
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 200
    
    # Las cookies deben estar borradas o vacías
    assert response.cookies.get("access_token") in ("", None)
    assert response.cookies.get("refresh_token") in ("", None)


# --- RUTAS DE PRUEBA DENTRO DE LOS TEST ---
from fastapi import Depends
from app.deps import require_admin
from app.main import app
import uuid

@app.get("/test-admin-only")
async def test_admin_only(current_user: AdminUser = Depends(require_admin)):
    return {"status": "ok"}


async def test_edge_cases_and_require_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Cubre casos extremos:
    1. Login con usuario inactivo.
    2. Validación de token de usuario inactivo.
    3. Validación de token de usuario inexistente (UUID).
    4. Validación de token con formato de UUID malformado.
    5. Restricción de rol (Operador no entra a /test-admin-only, Administrador sí).
    """
    # 1. Crear usuarios de prueba
    inactive_user = AdminUser(
        username="inactive_user",
        password_hash=hash_password("password123"),
        role=AdminRole.ADMIN,
        is_active=False,
    )
    operator_user = AdminUser(
        username="operator_user",
        password_hash=hash_password("password123"),
        role=AdminRole.OPERATOR,
        is_active=True,
    )
    admin_user = AdminUser(
        username="admin_user",
        password_hash=hash_password("password123"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([inactive_user, operator_user, admin_user])
    await db_session.commit()

    # Obtener token CSRF inicial
    response = await client.get("/setup")
    csrf_token = response.cookies.get("csrftoken")

    # 2. Login con usuario inactivo -> 401
    login_payload = {"username": "inactive_user", "password": "password123"}
    response = await client.post(
        "/auth/login",
        json=login_payload,
        headers={"x-csrftoken": csrf_token},
    )
    assert response.status_code == 401
    assert "inactivo" in response.json()["detail"]

    # 3. Acceso a /auth/me con token de usuario inactivo -> 401
    inactive_token = create_access_token(inactive_user.id)
    client.cookies.set("access_token", inactive_token)
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert "inactivo" in response.json()["detail"]

    # 4. Acceso a /auth/me con token de usuario inexistente -> 401
    fake_uuid = uuid.uuid4()
    fake_token = create_access_token(fake_uuid)
    client.cookies.set("access_token", fake_token)
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert "Usuario no encontrado" in response.json()["detail"]

    # 5. Acceso a /auth/me con UUID malformado en sub -> 401
    import app.deps as deps
    orig_verify = deps.verify_token
    # Simulamos que verify_token retorna un string que no es un UUID válido
    deps.verify_token = lambda token, expected_type: "not-a-valid-uuid"
    try:
        client.cookies.set("access_token", "malformed_token")
        response = await client.get("/auth/me")
        assert response.status_code == 401
        assert "Token de autenticación inválido" in response.json()["detail"]
    finally:
        # Restaurar función original
        deps.verify_token = orig_verify

    # 6. Intentar acceder a ruta restringida con rol OPERATOR -> 403 Forbidden
    operator_token = create_access_token(operator_user.id)
    client.cookies.set("access_token", operator_token)
    response = await client.get("/test-admin-only")
    assert response.status_code == 403
    assert "únicamente a administradores" in response.json()["detail"]

    # 7. Acceder a ruta restringida con rol ADMIN -> 200 OK
    admin_token = create_access_token(admin_user.id)
    client.cookies.set("access_token", admin_token)
    response = await client.get("/test-admin-only")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
