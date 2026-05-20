from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, require_admin
from app.models.user import AdminUser
from app.models.poll import Poll, VoterGroup, Category, Option, PollStatus
from app.schemas.poll import (
    PollCreate, PollUpdate, PollRead, PollStatusUpdate,
    VoterGroupCreate, VoterGroupUpdate, VoterGroupRead,
    CategoryCreate, CategoryUpdate, CategoryRead
)
from app.services.importer import import_options_from_file
from app.services.reports import generate_poll_report_xlsx

router = APIRouter(prefix="/polls", tags=["polls"])


# --- POLLS CRUD ENDPOINTS ---

@router.get("", response_model=list[PollRead])
async def list_polls(
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Lista todos los Polls registrados en el sistema.
    """
    result = await db.execute(select(Poll).order_by(Poll.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=PollRead, status_code=status.HTTP_201_CREATED)
async def create_poll(
    payload: PollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Crea un nuevo Poll en estado 'draft'.
    """
    new_poll = Poll(
        title=payload.title,
        description=payload.description,
        voting_type=payload.voting_type,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        created_by_id=current_user.id,
        status=PollStatus.DRAFT,
    )
    db.add(new_poll)
    await db.commit()
    await db.refresh(new_poll)
    return new_poll


@router.get("/{id}", response_model=PollRead)
async def get_poll(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Obtiene el detalle de un Poll específico.
    """
    result = await db.execute(select(Poll).where(Poll.id == id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )
    return poll


@router.patch("/{id}", response_model=PollRead)
async def update_poll(
    id: uuid.UUID,
    payload: PollUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Actualiza la configuración de un Poll.
    """
    result = await db.execute(select(Poll).where(Poll.id == id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(poll, key, val)
        
    await db.commit()
    await db.refresh(poll)
    return poll


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poll(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> None:
    """
    Elimina un Poll y todos sus elementos anidados por cascade delete.
    """
    result = await db.execute(select(Poll).where(Poll.id == id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )
    
    await db.delete(poll)
    await db.commit()


@router.post("/{id}/status", response_model=PollRead)
async def transition_poll_status(
    id: uuid.UUID,
    payload: PollStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Gestiona la transición de estados de una votación con validación estricta al abrirse.
    """
    result = await db.execute(select(Poll).where(Poll.id == id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    new_status = payload.status
    if new_status == PollStatus.OPEN and poll.status != PollStatus.OPEN:
        # Validar consistencia antes de abrir
        # 1. Obtener grupos de votantes
        vg_res = await db.execute(select(VoterGroup).where(VoterGroup.poll_id == id))
        voter_groups = vg_res.scalars().all()
        if not voter_groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede abrir una encuesta sin al menos un grupo de votantes.",
            )

        # 2. Obtener categorías
        cat_res = await db.execute(select(Category).where(Category.poll_id == id))
        categories = cat_res.scalars().all()
        if not categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede abrir una encuesta sin categorías.",
            )

        # 3. Validar que cada categoría tenga al menos una opción asignada
        for cat in categories:
            opt_res = await db.execute(select(Option).where(Option.category_id == cat.id))
            if not opt_res.scalars().all():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La categoría '{cat.name}' no tiene ninguna opción/candidato asignado.",
                )

        # 4. Validar suma de pesos de grupos de votantes si hay más de 1
        if len(voter_groups) > 1:
            total_weight = sum(vg.weight for vg in voter_groups)
            if abs(total_weight - 1.0) > 0.0001:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La suma de los pesos de los grupos de votantes debe ser exactamente 1.0 para abrir. Suma actual: {total_weight}",
                )

    poll.status = new_status
    await db.commit()
    await db.refresh(poll)
    return poll


# --- VOTER GROUPS CRUD ENDPOINTS ---

@router.get("/{id}/voter-groups", response_model=list[VoterGroupRead])
async def list_voter_groups(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Lista todos los grupos de votantes asociados a un Poll.
    """
    result = await db.execute(select(VoterGroup).where(VoterGroup.poll_id == id))
    return result.scalars().all()


@router.post("/{id}/voter-groups", response_model=VoterGroupRead, status_code=status.HTTP_201_CREATED)
async def create_voter_group(
    id: uuid.UUID,
    payload: VoterGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Crea un nuevo VoterGroup para un Poll, generando un token único aleatorio.
    """
    # Verificar existencia del Poll
    poll_res = await db.execute(select(Poll).where(Poll.id == id))
    if not poll_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    new_group = VoterGroup(
        poll_id=id,
        name=payload.name,
        weight=payload.weight,
        token=str(uuid.uuid4()),
    )
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group


@router.patch("/{id}/voter-groups/{group_id}", response_model=VoterGroupRead)
async def update_voter_group(
    id: uuid.UUID,
    group_id: uuid.UUID,
    payload: VoterGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Actualiza la configuración de un grupo de votantes específico.
    """
    result = await db.execute(
        select(VoterGroup)
        .where(VoterGroup.poll_id == id, VoterGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de votantes no encontrado",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(group, key, val)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{id}/voter-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voter_group(
    id: uuid.UUID,
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> None:
    """
    Elimina un grupo de votantes.
    """
    result = await db.execute(
        select(VoterGroup)
        .where(VoterGroup.poll_id == id, VoterGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de votantes no encontrado",
        )

    await db.delete(group)
    await db.commit()


# --- CATEGORIES CRUD ENDPOINTS ---

@router.get("/{id}/categories", response_model=list[CategoryRead])
async def list_categories(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Lista todas las categorías de un Poll.
    """
    result = await db.execute(
        select(Category)
        .where(Category.poll_id == id)
        .order_by(Category.order)
    )
    return result.scalars().all()


@router.post("/{id}/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    id: uuid.UUID,
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Crea una nueva categoría para un Poll.
    """
    # Verificar existencia del Poll
    poll_res = await db.execute(select(Poll).where(Poll.id == id))
    if not poll_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    new_cat = Category(
        poll_id=id,
        name=payload.name,
        order=payload.order,
    )
    db.add(new_cat)
    await db.commit()
    await db.refresh(new_cat)
    return new_cat


@router.patch("/{id}/categories/{cat_id}", response_model=CategoryRead)
async def update_category(
    id: uuid.UUID,
    cat_id: uuid.UUID,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Actualiza una categoría específica.
    """
    result = await db.execute(
        select(Category)
        .where(Category.poll_id == id, Category.id == cat_id)
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(cat, key, val)

    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/{id}/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    id: uuid.UUID,
    cat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> None:
    """
    Elimina una categoría.
    """
    result = await db.execute(
        select(Category)
        .where(Category.poll_id == id, Category.id == cat_id)
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    await db.delete(cat)
    await db.commit()


# --- OPTIONS IMPORT ENDPOINT ---

@router.post("/{id}/options/import", status_code=status.HTTP_200_OK)
async def import_options(
    id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Any:
    """
    Recibe un archivo XLSX o CSV para importar de forma masiva opciones y categorías al Poll.
    """
    # Verificar existencia del Poll y que esté en borrador
    poll_res = await db.execute(select(Poll).where(Poll.id == id))
    poll = poll_res.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )
    if poll.status != PollStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden importar opciones cuando la encuesta está en estado borrador (draft).",
        )

    file_bytes = await file.read()
    summary = await import_options_from_file(
        db=db,
        poll_id=id,
        file_bytes=file_bytes,
        filename=file.filename,
    )
    return summary


@router.get("/{id}/report.xlsx")
async def download_poll_report(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: AdminUser = Depends(require_admin),
) -> Response:
    """
    Genera un reporte XLSX del poll. Solo disponible cuando la votación está cerrada.
    """
    result = await db.execute(select(Poll).where(Poll.id == id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    if poll.status != PollStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El reporte XLSX solo puede generarse cuando la encuesta está cerrada.",
        )

    file_bytes, filename = await generate_poll_report_xlsx(db, id)
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
