from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.poll import Poll, VoterGroup, Category, Option, PollStatus
from app.models.vote import Vote
from app.schemas.poll import PublicPollRead, PublicCategoryRead, PublicOptionRead, VoteSubmit
from app.config import settings

router = APIRouter(prefix="/v", tags=["voting"])

# Duración de la cookie de votante: 1 año en segundos
VOTER_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


@router.get("/{token}/data", response_model=PublicPollRead)
async def get_voting_data(
    token: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    voter_id: str | None = Cookie(default=None),
) -> Any:
    """
    Retorna los datos públicos de una votación (categorías y opciones).
    Si la cookie voter_id no existe, se genera y establece en la respuesta.
    Indica si el votante ya emitió su voto anteriormente en esta encuesta.
    """
    # Buscar el grupo de votantes con el token proporcionado
    vg_result = await db.execute(
        select(VoterGroup).where(VoterGroup.token == token)
    )
    voter_group = vg_result.scalar_one_or_none()

    if not voter_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link de votación inválido o no encontrado.",
        )

    # Cargar el Poll asociado
    poll_result = await db.execute(
        select(Poll).where(Poll.id == voter_group.poll_id)
    )
    poll = poll_result.scalar_one_or_none()

    if not poll or poll.status != PollStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Esta votación no está disponible o ya ha sido cerrada.",
        )

    # Generar o recuperar el voter_id de la cookie
    effective_voter_id = voter_id
    if not effective_voter_id:
        effective_voter_id = str(uuid.uuid4())
        response.set_cookie(
            key="voter_id",
            value=effective_voter_id,
            max_age=VOTER_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT == "production",
            path="/",
        )

    # Verificar si el votante ya votó (existe al menos 1 voto para este voter_id + voter_group)
    already_voted_result = await db.execute(
        select(Vote).where(
            Vote.poll_id == poll.id,
            Vote.voter_group_id == voter_group.id,
            Vote.voter_token == effective_voter_id,
        ).limit(1)
    )
    already_voted = already_voted_result.scalar_one_or_none() is not None

    # Construir la respuesta con categorías y opciones del poll
    cat_result = await db.execute(
        select(Category)
        .where(Category.poll_id == poll.id)
        .order_by(Category.order)
    )
    categories = cat_result.scalars().all()

    public_categories = []
    for cat in categories:
        opt_result = await db.execute(
            select(Option)
            .where(Option.category_id == cat.id)
            .order_by(Option.order)
        )
        options = opt_result.scalars().all()
        public_categories.append(
            PublicCategoryRead(
                id=cat.id,
                name=cat.name,
                order=cat.order,
                options=[
                    PublicOptionRead(
                        id=opt.id,
                        name=opt.name,
                        photo_url=opt.photo_url,
                        order=opt.order,
                    )
                    for opt in options
                ],
            )
        )

    return PublicPollRead(
        id=poll.id,
        title=poll.title,
        description=poll.description,
        voting_type=poll.voting_type,
        voter_group_name=voter_group.name,
        categories=public_categories,
        already_voted=already_voted,
    )


@router.post("/{token}/vote", status_code=status.HTTP_201_CREATED)
async def submit_vote(
    token: str,
    payload: VoteSubmit,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    voter_id: str | None = Cookie(default=None),
) -> Any:
    """
    Procesa los votos de un votante.
    Realiza la deduplicación por cookie httpOnly y valida que:
      - El poll esté abierto.
      - El votante no haya votado previamente.
      - Cada voto corresponda a una categoría y opción del poll.
      - Se vote exactamente 1 opción por cada categoría.
    """
    # Buscar el grupo de votantes
    vg_result = await db.execute(
        select(VoterGroup).where(VoterGroup.token == token)
    )
    voter_group = vg_result.scalar_one_or_none()

    if not voter_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link de votación inválido o no encontrado.",
        )

    # Cargar y verificar el poll
    poll_result = await db.execute(
        select(Poll).where(Poll.id == voter_group.poll_id)
    )
    poll = poll_result.scalar_one_or_none()

    if not poll or poll.status != PollStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Esta votación no está disponible o ya ha sido cerrada.",
        )

    # Generar o recuperar el voter_id de la cookie
    effective_voter_id = voter_id
    if not effective_voter_id:
        effective_voter_id = str(uuid.uuid4())
        response.set_cookie(
            key="voter_id",
            value=effective_voter_id,
            max_age=VOTER_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT == "production",
            path="/",
        )

    # Verificar si el votante ya votó (deduplicación por cookie + grupo)
    existing_vote_result = await db.execute(
        select(Vote).where(
            Vote.poll_id == poll.id,
            Vote.voter_group_id == voter_group.id,
            Vote.voter_token == effective_voter_id,
        ).limit(1)
    )
    if existing_vote_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya emitiste tu voto en esta encuesta. Solo se permite un voto por enlace.",
        )

    # Obtener categorías del poll
    cat_result = await db.execute(
        select(Category).where(Category.poll_id == poll.id)
    )
    categories = cat_result.scalars().all()
    category_ids = {cat.id for cat in categories}

    # Validar que se haya enviado exactamente 1 voto por categoría
    submitted_categories = {sv.category_id for sv in payload.votes}
    if submitted_categories != category_ids:
        missing = category_ids - submitted_categories
        extra = submitted_categories - category_ids
        details = []
        if missing:
            details.append(f"Faltan votos para las categorías con IDs: {[str(m) for m in missing]}")
        if extra:
            details.append(f"Se enviaron votos para categorías no válidas: {[str(e) for e in extra]}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=". ".join(details) or "Votos inválidos.",
        )

    # Cargar opciones válidas del poll (indexadas por ID)
    opt_result = await db.execute(
        select(Option).where(Option.poll_id == poll.id)
    )
    options = opt_result.scalars().all()
    option_map = {opt.id: opt for opt in options}

    # Obtener IP del votante para auditoría
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")

    # Insertar votos en transacción
    for sv in payload.votes:
        # Validar que la opción existe y pertenece a la categoría enviada
        opt = option_map.get(sv.option_id)
        if not opt or opt.category_id != sv.category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La opción con ID {sv.option_id} no es válida para la categoría indicada.",
            )

        vote = Vote(
            poll_id=poll.id,
            voter_group_id=voter_group.id,
            category_id=sv.category_id,
            option_id=sv.option_id,
            voter_token=effective_voter_id,
            ip=client_ip,
        )
        db.add(vote)

    await db.commit()

    return {"message": "Voto registrado exitosamente.", "already_voted": True}
