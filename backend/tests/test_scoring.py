from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poll import Poll, VoterGroup, Category, Option, PollStatus, VotingType
from app.models.user import AdminUser, AdminRole
from app.models.vote import Vote
from app.services.auth import hash_password
from app.services.scoring import calculate_poll_results

pytestmark = pytest.mark.asyncio


async def _create_base_poll(db: AsyncSession, admin: AdminUser) -> tuple[Poll, Category, Category, Option, Option, Option]:
    """Helper: crea un poll con 2 categorías y 3 opciones para tests."""
    poll = Poll(
        title="Test Scoring Poll",
        voting_type=VotingType.PLURALITY,
        status=PollStatus.OPEN,
        created_by_id=admin.id,
    )
    db.add(poll)
    await db.flush()

    cat1 = Category(poll_id=poll.id, name="Departamento A", order=0)
    cat2 = Category(poll_id=poll.id, name="Departamento B", order=1)
    db.add_all([cat1, cat2])
    await db.flush()

    opt1 = Option(poll_id=poll.id, category_id=cat1.id, name="Candidato A1", order=0)
    opt2 = Option(poll_id=poll.id, category_id=cat1.id, name="Candidato A2", order=1)
    opt3 = Option(poll_id=poll.id, category_id=cat2.id, name="Candidato B1", order=0)
    db.add_all([opt1, opt2, opt3])
    await db.flush()

    return poll, cat1, cat2, opt1, opt2, opt3


async def test_scoring_single_group(db_session: AsyncSession) -> None:
    """
    Con un único grupo (weight=1.0), el score final debe coincidir con el score normalizado:
    votos_opción / total_votos_grupo_en_categoría.
    """
    admin = AdminUser(
        username="scorer_single",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll, cat1, cat2, opt1, opt2, opt3 = await _create_base_poll(db_session, admin)

    group = VoterGroup(poll_id=poll.id, name="Grupo Único", weight=1.0, token=str(uuid.uuid4()))
    db_session.add(group)
    await db_session.flush()

    # 3 votos en cat1: 2 para opt1, 1 para opt2
    for i in range(2):
        db_session.add(Vote(
            poll_id=poll.id, voter_group_id=group.id,
            category_id=cat1.id, option_id=opt1.id,
            voter_token=f"voter-cat1-a-{i}",
        ))
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group.id,
        category_id=cat1.id, option_id=opt2.id,
        voter_token="voter-cat1-b",
    ))
    # 1 voto en cat2 para opt3
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group.id,
        category_id=cat2.id, option_id=opt3.id,
        voter_token="voter-cat2-a",
    ))
    await db_session.commit()

    results = await calculate_poll_results(db_session, poll.id)

    assert results["poll_id"] == poll.id
    cats = {c["category_name"]: c["results"] for c in results["categories"]}

    # Departamento A: opt1 -> 2/3 ≈ 0.666, opt2 -> 1/3 ≈ 0.333
    dep_a = {r["option_name"]: r["score"] for r in cats["Departamento A"]}
    assert abs(dep_a["Candidato A1"] - 2 / 3) < 0.0001
    assert abs(dep_a["Candidato A2"] - 1 / 3) < 0.0001

    # Departamento B: opt3 -> 1/1 = 1.0
    dep_b = {r["option_name"]: r["score"] for r in cats["Departamento B"]}
    assert abs(dep_b["Candidato B1"] - 1.0) < 0.0001

    # El ganador en dep_a debe ser A1 (mayor score)
    assert cats["Departamento A"][0]["option_name"] == "Candidato A1"


async def test_scoring_weighted_two_groups(db_session: AsyncSession) -> None:
    """
    Con 2 grupos (weights 0.7 y 0.3), el score final debe ser la suma ponderada
    de los scores normalizados de cada grupo.
    """
    admin = AdminUser(
        username="scorer_two_groups",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll, cat1, cat2, opt1, opt2, opt3 = await _create_base_poll(db_session, admin)

    group_base = VoterGroup(poll_id=poll.id, name="Base", weight=0.7, token=str(uuid.uuid4()))
    group_jefes = VoterGroup(poll_id=poll.id, name="Jefaturas", weight=0.3, token=str(uuid.uuid4()))
    db_session.add_all([group_base, group_jefes])
    await db_session.flush()

    # Grupo Base (weight 0.7): vota por opt1 en cat1 (2 votos de 3 total)
    for i in range(2):
        db_session.add(Vote(
            poll_id=poll.id, voter_group_id=group_base.id,
            category_id=cat1.id, option_id=opt1.id,
            voter_token=f"base-a-{i}",
        ))
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group_base.id,
        category_id=cat1.id, option_id=opt2.id,
        voter_token="base-b",
    ))

    # Grupo Jefes (weight 0.3): opt2 en cat1 (1 voto de 1 total → opt2 gana en este grupo)
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group_jefes.id,
        category_id=cat1.id, option_id=opt2.id,
        voter_token="jefe-a",
    ))
    await db_session.commit()

    results = await calculate_poll_results(db_session, poll.id)
    cats = {c["category_name"]: c["results"] for c in results["categories"]}
    dep_a = {r["option_name"]: r["score"] for r in cats["Departamento A"]}

    # opt1: score_base = 2/3, score_jefes = 0 (no votes) → weight efectivo sólo base
    # Como sólo hay jefes y base en cat1, pero jefes participó → pesos completos
    # opt1: 0.7*(2/3) + 0.3*(0/1) = 0.4667
    # opt2: 0.7*(1/3) + 0.3*(1/1) = 0.2333 + 0.3 = 0.5333
    assert abs(dep_a["Candidato A1"] - (0.7 * (2 / 3) + 0.3 * 0)) < 0.001
    assert abs(dep_a["Candidato A2"] - (0.7 * (1 / 3) + 0.3 * 1)) < 0.001
    # opt2 debe ganar en esta categoría con ponderación
    assert cats["Departamento A"][0]["option_name"] == "Candidato A2"


async def test_scoring_missing_group_participation(db_session: AsyncSession) -> None:
    """
    Si un grupo no participa en una categoría, su peso debe redistribuirse
    dinámicamente entre los grupos que sí participaron.
    """
    admin = AdminUser(
        username="scorer_missing_group",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll, cat1, cat2, opt1, opt2, opt3 = await _create_base_poll(db_session, admin)

    group_base = VoterGroup(poll_id=poll.id, name="Base", weight=0.6, token=str(uuid.uuid4()))
    group_jefes = VoterGroup(poll_id=poll.id, name="Jefaturas", weight=0.4, token=str(uuid.uuid4()))
    db_session.add_all([group_base, group_jefes])
    await db_session.flush()

    # Solo el grupo Base participa en cat1 (Jefaturas no vota)
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group_base.id,
        category_id=cat1.id, option_id=opt1.id,
        voter_token="base-only-vote",
    ))
    await db_session.commit()

    results = await calculate_poll_results(db_session, poll.id)
    cats = {c["category_name"]: c["results"] for c in results["categories"]}
    dep_a = {r["option_name"]: r["score"] for r in cats["Departamento A"]}

    # Solo base participa → peso efectivo redistribuido a 1.0
    # opt1: score_base = 1/1 * (0.6/0.6) = 1.0, opt2: 0.0
    assert abs(dep_a["Candidato A1"] - 1.0) < 0.0001
    assert dep_a["Candidato A2"] == 0.0


async def test_scoring_tiebreaker_alphabetical(db_session: AsyncSession) -> None:
    """
    Cuando dos opciones tienen exactamente el mismo score y el mismo número de votos,
    el desempate debe resolverse por orden alfabético ascendente.
    """
    admin = AdminUser(
        username="scorer_tie",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll = Poll(
        title="Tie Test Poll",
        voting_type=VotingType.PLURALITY,
        status=PollStatus.OPEN,
        created_by_id=admin.id,
    )
    db_session.add(poll)
    await db_session.flush()

    cat = Category(poll_id=poll.id, name="Cat Tie", order=0)
    db_session.add(cat)
    await db_session.flush()

    # Dos opciones con nombres en orden invertido para probar desempate
    opt_z = Option(poll_id=poll.id, category_id=cat.id, name="Zebra Corp", order=0)
    opt_a = Option(poll_id=poll.id, category_id=cat.id, name="Alpha Inc", order=1)
    db_session.add_all([opt_z, opt_a])
    await db_session.flush()

    group = VoterGroup(poll_id=poll.id, name="Único", weight=1.0, token=str(uuid.uuid4()))
    db_session.add(group)
    await db_session.flush()

    # Ambas opciones reciben exactamente 1 voto → empate perfecto
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group.id,
        category_id=cat.id, option_id=opt_z.id,
        voter_token="voter-z",
    ))
    db_session.add(Vote(
        poll_id=poll.id, voter_group_id=group.id,
        category_id=cat.id, option_id=opt_a.id,
        voter_token="voter-a",
    ))
    await db_session.commit()

    results = await calculate_poll_results(db_session, poll.id)
    cat_results = results["categories"][0]["results"]

    # En caso de empate: orden alfabético → Alpha Inc primero
    assert cat_results[0]["option_name"] == "Alpha Inc"
    assert cat_results[1]["option_name"] == "Zebra Corp"


async def test_scoring_empty_poll(db_session: AsyncSession) -> None:
    """
    Un Poll sin votos debe retornar scores de 0.0 para todas las opciones.
    """
    admin = AdminUser(
        username="scorer_empty",
        password_hash=hash_password("pass"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    poll, cat1, cat2, opt1, opt2, opt3 = await _create_base_poll(db_session, admin)
    group = VoterGroup(poll_id=poll.id, name="Único", weight=1.0, token=str(uuid.uuid4()))
    db_session.add(group)
    await db_session.commit()

    results = await calculate_poll_results(db_session, poll.id)

    for cat in results["categories"]:
        for opt_result in cat["results"]:
            assert opt_result["score"] == 0.0
            assert opt_result["total_votes"] == 0
