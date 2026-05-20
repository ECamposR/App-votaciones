from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.user import AdminUser, AdminRole
from app.schemas.user import SetupStatus, UserRead, UserSetup
from app.services.auth import hash_password

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("", response_model=SetupStatus)
async def check_setup_status(db: AsyncSession = Depends(get_db)) -> SetupStatus:
    """
    Verifica si ya existe al menos un usuario administrador registrado en el sistema.
    """
    result = await db.execute(select(func.count()).select_from(AdminUser))
    count = result.scalar() or 0
    return SetupStatus(has_admin=count > 0)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def perform_initial_setup(
    setup_data: UserSetup,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """
    Crea el primer usuario administrador del sistema.
    Si ya existe algún usuario en la base de datos, este endpoint retorna un error 403 Forbidden.
    """
    # Verificar si ya existe algún administrador
    result = await db.execute(select(func.count()).select_from(AdminUser))
    count = result.scalar() or 0
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El sistema ya ha sido configurado previamente.",
        )

    # Crear el primer usuario con rol ADMIN
    hashed_pwd = hash_password(setup_data.password)
    new_admin = AdminUser(
        username=setup_data.username,
        password_hash=hashed_pwd,
        role=AdminRole.ADMIN,
        is_active=True,
    )

    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)

    return new_admin
