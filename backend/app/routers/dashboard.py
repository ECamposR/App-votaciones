from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.deps import get_current_user
from app.models.user import AdminUser
from app.models.poll import Poll, PollStatus
from app.services.scoring import calculate_poll_results
from sqlalchemy import select

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Intervalo de actualización SSE en segundos
SSE_REFRESH_INTERVAL = 3


def serialize_results(data: dict[str, Any]) -> str:
    """
    Serializa los resultados del scoring a JSON seguro para SSE.
    Convierte UUIDs a strings.
    """
    def default_serializer(obj: Any) -> str:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(data, default=default_serializer)


async def results_event_generator(
    poll_id: uuid.UUID,
    request: Request,
) -> AsyncGenerator[str, None]:
    """
    Generador asíncrono que emite eventos SSE periódicamente con los resultados actuales del Poll.
    Se detiene cuando el cliente desconecta o el poll está cerrado.
    """
    while True:
        # Verificar si el cliente se desconectó
        if await request.is_disconnected():
            break

        # Abrir nueva sesión por cada actualización para obtener datos frescos
        async with AsyncSessionLocal() as db:
            # Verificar estado del poll
            poll_result = await db.execute(select(Poll).where(Poll.id == poll_id))
            poll = poll_result.scalar_one_or_none()

            if not poll:
                yield "event: error\ndata: {\"detail\": \"Poll no encontrado\"}\n\n"
                break

            # Calcular y emitir resultados
            try:
                results = await calculate_poll_results(db, poll_id)
                event_data = serialize_results(results)
                yield f"data: {event_data}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {{\"detail\": \"{str(e)}\"}}\n\n"
                break

            # Si la votación está cerrada, emitimos los resultados finales y terminamos
            if poll.status == PollStatus.CLOSED:
                yield "event: closed\ndata: {\"message\": \"La votacion ha sido cerrada\"}\n\n"
                break

        await asyncio.sleep(SSE_REFRESH_INTERVAL)


@router.get("/{id}/stream")
async def stream_dashboard(
    id: uuid.UUID,
    request: Request,
    current_user: AdminUser = Depends(get_current_user),
) -> StreamingResponse:
    """
    Endpoint SSE que transmite resultados en tiempo real del dashboard de un Poll.
    Requiere sesión activa de administrador u operador.
    Emite un evento data cada 3 segundos con los scores ponderados actualizados.
    """
    # Verificar que el poll existe
    async with AsyncSessionLocal() as db:
        poll_result = await db.execute(select(Poll).where(Poll.id == id))
        poll = poll_result.scalar_one_or_none()

    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    return StreamingResponse(
        results_event_generator(poll_id=id, request=request),
        media_type="text/event-stream",
        headers={
            # Desactivar buffering de Nginx/proxies para SSE
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
