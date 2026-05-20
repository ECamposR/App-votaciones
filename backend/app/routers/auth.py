from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_db, get_current_user
from app.models.user import AdminUser
from app.schemas.user import UserLogin, UserRead
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)

from app.middleware.security import limiter

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Ruta de la cookie de refresh token adaptada al entorno (desarrollo vs producción tras Nginx)
REFRESH_COOKIE_PATH = "/api/auth/refresh" if settings.ENVIRONMENT == "production" else "/auth/refresh"


@router.post("/login", response_model=UserRead)
@limiter.limit("10/minute")
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """
    Inicia sesión verificando credenciales. Si son válidas, emite access_token y refresh_token
    en cookies HttpOnly y Secure. Retorna la información del usuario autenticado.
    """
    # Buscar usuario por nombre de usuario
    result = await db.execute(select(AdminUser).where(AdminUser.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    # Generar tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Configurar cookies
    is_prod = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return user


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """
    Cierra la sesión borrando las cookies de autenticación.
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path=REFRESH_COOKIE_PATH)
    return {"status": "success", "detail": "Sesión cerrada correctamente"}


@router.post("/refresh")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Genera un nuevo access_token a partir de un refresh_token válido recibido en cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no proporcionado",
        )

    # Verificar token
    user_id_str = verify_token(refresh_token, expected_type="refresh")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    # Buscar usuario y validar
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    # Generar y configurar el nuevo access_token
    access_token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"status": "success"}


@router.get("/me", response_model=UserRead)
async def get_me(current_user: AdminUser = Depends(get_current_user)) -> AdminUser:
    """
    Retorna la información del usuario administrador actual.
    """
    return current_user
