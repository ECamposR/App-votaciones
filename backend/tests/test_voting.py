from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AdminUser, AdminRole
from app.models.poll import Poll, VoterGroup, Category, Option, PollStatus, VotingType
from app.models.vote import Vote
from app.services.auth import hash_password, create_access_token

pytestmark = pytest.mark.asyncio


async def _setup_open_poll(db: AsyncSession) -> tuple[Poll, VoterGroup, Category, Option, Option]:
    """
    Helper: crea un Poll abierto con 1 grupo de votantes, 1 categoría y 2 opciones.
    """
    admin = AdminUser(
        username=f"voting_admin_{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    await db.flush()

    poll = Poll(
        title="Votación de Prueba",
        voting_type=VotingType.PLURALITY,
        status=PollStatus.OPEN,
        created_by_id=admin.id,
    )
    db.add(poll)
    await db.flush()

    group = VoterGroup(
        poll_id=poll.id,
        name="Empleados",
        weight=1.0,
        token=str(uuid.uuid4()),
    )
    db.add(group)
    await db.flush()

    cat = Category(poll_id=poll.id, name="Empleado Destacado", order=0)
    db.add(cat)
    await db.flush()

    opt1 = Option(poll_id=poll.id, category_id=cat.id, name="Candidato A", order=0)
    opt2 = Option(poll_id=poll.id, category_id=cat.id, name="Candidato B", order=1)
    db.add_all([opt1, opt2])
    await db.commit()

    return poll, group, cat, opt1, opt2


async def test_get_voting_data_sets_voter_id_cookie(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Al acceder a /v/{token}/data sin cookie voter_id, debe establecerse una nueva.
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)

    # Limpiar cualquier cookie previa de voter_id
    client.cookies.delete("voter_id")

    resp = await client.get(f"/v/{group.token}/data")
    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == str(poll.id)
    assert data["voter_group_name"] == "Empleados"
    assert data["already_voted"] is False
    assert len(data["categories"]) == 1
    assert len(data["categories"][0]["options"]) == 2

    # Debe haber seteado la cookie voter_id
    assert "voter_id" in resp.cookies


async def test_get_voting_data_invalid_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Un token de votación inválido debe retornar 404.
    """
    resp = await client.get("/v/invalid-nonexistent-token-xyz/data")
    assert resp.status_code == 404


async def test_get_voting_data_closed_poll(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Un poll cerrado no debe retornar datos de votación (410 Gone).
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)
    # Cerrar el poll
    poll.status = PollStatus.CLOSED
    await db_session.commit()

    resp = await client.get(f"/v/{group.token}/data")
    assert resp.status_code == 410


async def test_submit_vote_successful(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Flujo de voto exitoso: el votante accede, recibe datos y envía su voto correctamente.
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)

    # Paso 1: obtener datos (establece cookie voter_id)
    client.cookies.delete("voter_id")
    resp = await client.get(f"/v/{group.token}/data")
    assert resp.status_code == 200
    assert "voter_id" in resp.cookies

    # Paso 2: enviar voto
    vote_payload = {
        "votes": [
            {"category_id": str(cat.id), "option_id": str(opt1.id)}
        ]
    }
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 201
    assert resp.json()["already_voted"] is True

    # Paso 3: verificar que el poll refleja el voto
    resp = await client.get(f"/v/{group.token}/data")
    assert resp.json()["already_voted"] is True


async def test_submit_vote_duplicate_prevented(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Un votante que ya emitió su voto no puede volver a votar en el mismo poll+grupo.
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)

    # Crear voter_id fijo para el test
    voter_id = str(uuid.uuid4())
    client.cookies.set("voter_id", voter_id)

    vote_payload = {
        "votes": [{"category_id": str(cat.id), "option_id": str(opt1.id)}]
    }

    # Primer voto → debe pasar
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 201

    # Segundo intento → debe fallar con 400
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 400
    assert "ya emitiste" in resp.json()["detail"].lower()


async def test_submit_vote_invalid_category(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Enviar votos con una categoría que no pertenece al poll debe retornar 400.
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)

    fake_cat_id = str(uuid.uuid4())
    vote_payload = {
        "votes": [{"category_id": fake_cat_id, "option_id": str(opt1.id)}]
    }

    client.cookies.delete("voter_id")
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 400


async def test_submit_vote_missing_category(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    No enviar votos para todas las categorías del poll debe retornar 400.
    """
    # Crear un poll con 2 categorías
    admin = AdminUser(
        username=f"missing_cat_{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll = Poll(
        title="Multi-cat Poll",
        voting_type=VotingType.PLURALITY,
        status=PollStatus.OPEN,
        created_by_id=admin.id,
    )
    db_session.add(poll)
    await db_session.flush()

    group = VoterGroup(poll_id=poll.id, name="G", weight=1.0, token=str(uuid.uuid4()))
    db_session.add(group)
    await db_session.flush()

    cat1 = Category(poll_id=poll.id, name="Cat 1", order=0)
    cat2 = Category(poll_id=poll.id, name="Cat 2", order=1)
    db_session.add_all([cat1, cat2])
    await db_session.flush()

    opt_a = Option(poll_id=poll.id, category_id=cat1.id, name="Opt A", order=0)
    opt_b = Option(poll_id=poll.id, category_id=cat2.id, name="Opt B", order=0)
    db_session.add_all([opt_a, opt_b])
    await db_session.commit()

    client.cookies.delete("voter_id")

    # Solo se vota en cat1, falta cat2
    vote_payload = {
        "votes": [{"category_id": str(cat1.id), "option_id": str(opt_a.id)}]
    }
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 400
    assert "faltan" in resp.json()["detail"].lower()


async def test_submit_vote_invalid_option_for_category(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Enviar el ID de una opción que no pertenece a la categoría indicada debe retornar 400.
    """
    poll, group, cat, opt1, opt2 = await _setup_open_poll(db_session)

    # Crear una segunda categoría con otra opción
    cat2 = Category(poll_id=poll.id, name="Cat 2", order=1)
    db_session.add(cat2)
    await db_session.flush()
    opt_wrong = Option(poll_id=poll.id, category_id=cat2.id, name="Opcion Cat2", order=0)
    db_session.add(opt_wrong)
    await db_session.commit()

    client.cookies.delete("voter_id")

    # Intentamos votar en cat con opt_wrong (que pertenece a cat2)
    vote_payload = {
        "votes": [
            {"category_id": str(cat.id), "option_id": str(opt_wrong.id)},  # opción incorrecta para cat
            {"category_id": str(cat2.id), "option_id": str(opt_wrong.id)},
        ]
    }
    resp = await client.post(f"/v/{group.token}/vote", json=vote_payload)
    assert resp.status_code == 400
