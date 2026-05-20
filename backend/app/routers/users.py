from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, require_admin
from app.models.user import AdminUser, AdminRole
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserPasswordChange
from app.services.auth import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> AdminUser:
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


async def _count_active_admins(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(AdminUser)
        .where(AdminUser.role == AdminRole.ADMIN, AdminUser.is_active.is_(True))
    )
    return int(result.scalar_one())


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _current_user: AdminUser = Depends(require_admin),
) -> Any:
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: AdminUser = Depends(require_admin),
) -> Any:
    existing = await db.execute(select(AdminUser).where(AdminUser.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya existe")

    user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: AdminUser = Depends(require_admin),
) -> Any:
    user = await _get_user_or_404(db, user_id)

    update_data = payload.model_dump(exclude_unset=True)
    new_role = update_data.get("role", user.role)
    new_is_active = update_data.get("is_active", user.is_active)

    if user.role == AdminRole.ADMIN and user.is_active and (new_role != AdminRole.ADMIN or new_is_active is False):
        active_admins = await _count_active_admins(db)
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede dejar al sistema sin al menos un administrador activo.",
            )

    if "username" in update_data and update_data["username"] != user.username:
        existing = await db.execute(select(AdminUser).where(AdminUser.username == update_data["username"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya existe")

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(require_admin),
) -> None:
    user = await _get_user_or_404(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminar tu propio usuario")

    if user.role == AdminRole.ADMIN and user.is_active:
        active_admins = await _count_active_admins(db)
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar al último administrador activo.",
            )

    await db.delete(user)
    await db.commit()


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: uuid.UUID,
    payload: UserPasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> dict[str, str]:
    user = await _get_user_or_404(db, user_id)

    if current_user.id != user.id and current_user.role != AdminRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para cambiar esta contraseña")

    if current_user.id == user.id:
        if not payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes proporcionar la contraseña actual",
            )
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual no es correcta",
            )

    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"status": "success", "detail": "Contraseña actualizada correctamente"}
