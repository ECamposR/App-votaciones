from __future__ import annotations

import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import AdminUser, AdminRole
from app.services.auth import verify_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia para inyectar la sesión asíncrona de base de datos.
    Garantiza el cierre automático de la sesión al finalizar la petición.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """
    Dependencia para obtener el usuario administrador actualmente autenticado
    leyendo el access_token desde las HttpOnly cookies.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    user_id_str = verify_token(token, expected_type="access")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido",
        )

    # Buscar el usuario en la base de datos
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    return user


async def require_admin(
    current_user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """
    Dependencia para restringir endpoints únicamente a usuarios con rol 'admin'.
    """
    if current_user.role != AdminRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación permitida únicamente a administradores",
        )
    return current_user
