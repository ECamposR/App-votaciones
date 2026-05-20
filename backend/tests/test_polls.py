from __future__ import annotations

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AdminUser, AdminRole
from app.models.poll import Poll, VoterGroup, Category, Option, PollStatus, VotingType
from app.services.auth import hash_password, create_access_token

pytestmark = pytest.mark.asyncio


async def _create_admin_and_login(client: AsyncClient, db: AsyncSession) -> tuple[AdminUser, str]:
    """Helper: crea un admin activo y devuelve el usuario y la cookie de acceso."""
    admin = AdminUser(
        username=f"poll_admin_{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("password"),
        role=AdminRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    token = create_access_token(admin.id)
    client.cookies.set("access_token", token)
    return admin, token


async def test_poll_crud_lifecycle(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba el ciclo de vida completo de un Poll:
    crear → leer → actualizar → eliminar.
    """
    await _create_admin_and_login(client, db_session)

    # Obtener CSRF token
    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    # 1. Crear poll
    resp = await client.post(
        "/api/polls",
        json={"title": "Empleado del Mes", "description": "Votación mensual"},
        headers=headers,
    )
    assert resp.status_code == 201
    poll_data = resp.json()
    poll_id = poll_data["id"]
    assert poll_data["title"] == "Empleado del Mes"
    assert poll_data["status"] == "draft"

    # 2. Listar polls
    resp = await client.get("/api/polls")
    assert resp.status_code == 200
    assert any(p["id"] == poll_id for p in resp.json())

    # 3. Obtener poll específico
    resp = await client.get(f"/api/polls/{poll_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == poll_id

    # 4. Actualizar poll
    resp = await client.patch(
        f"/api/polls/{poll_id}",
        json={"title": "Empleado del Mes - Junio"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Empleado del Mes - Junio"

    # 5. Eliminar poll
    resp = await client.delete(f"/api/polls/{poll_id}", headers=headers)
    assert resp.status_code == 204

    # 6. Verificar que ya no existe
    resp = await client.get(f"/api/polls/{poll_id}")
    assert resp.status_code == 404


async def test_poll_status_transition_validations(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba que las validaciones de pre-apertura se aplican correctamente:
    - Sin grupos → 400
    - Con grupo pero sin categorías → 400
    - Con categoría sin opciones → 400
    - Con pesos incorrectos → 400
    - Todo correcto → 200 (status=open)
    """
    admin, _ = await _create_admin_and_login(client, db_session)

    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    # Crear poll
    resp = await client.post("/api/polls", json={"title": "Status Test"}, headers=headers)
    poll_id = resp.json()["id"]

    open_payload = {"status": "open"}

    # a. Sin grupos → 400
    resp = await client.post(f"/api/polls/{poll_id}/status", json=open_payload, headers=headers)
    assert resp.status_code == 400
    assert "grupo de votantes" in resp.json()["detail"]

    # b. Agregar un grupo
    resp = await client.post(
        f"/api/polls/{poll_id}/voter-groups",
        json={"name": "Empleados", "weight": 0.6},
        headers=headers,
    )
    assert resp.status_code == 201
    group1_id = resp.json()["id"]

    # c. Sin categorías → 400
    resp = await client.post(f"/api/polls/{poll_id}/status", json=open_payload, headers=headers)
    assert resp.status_code == 400
    assert "categoría" in resp.json()["detail"].lower()

    # d. Agregar categoría
    resp = await client.post(
        f"/api/polls/{poll_id}/categories",
        json={"name": "Departamento TI", "order": 0},
        headers=headers,
    )
    assert resp.status_code == 201
    cat_id = resp.json()["id"]

    # e. Categoría sin opciones → 400
    resp = await client.post(f"/api/polls/{poll_id}/status", json=open_payload, headers=headers)
    assert resp.status_code == 400
    assert "opción" in resp.json()["detail"].lower() or "candidato" in resp.json()["detail"].lower()

    # f. Agregar segundo grupo con pesos que no suman 1.0
    resp = await client.post(
        f"/api/polls/{poll_id}/voter-groups",
        json={"name": "Jefaturas", "weight": 0.5},   # 0.6 + 0.5 = 1.1
        headers=headers,
    )
    assert resp.status_code == 201

    # g. Añadir opciones directamente en DB para avanzar al test de pesos
    db_session.add(Option(
        poll_id=uuid.UUID(poll_id),
        category_id=uuid.UUID(cat_id),
        name="Candidato Test",
        order=0,
    ))
    await db_session.commit()

    # h. Pesos no suman 1.0 → 400
    resp = await client.post(f"/api/polls/{poll_id}/status", json=open_payload, headers=headers)
    assert resp.status_code == 400
    assert "peso" in resp.json()["detail"].lower() or "weight" in resp.json()["detail"].lower()

    # i. Corregir peso del segundo grupo a 0.4
    resp = await client.patch(
        f"/api/polls/{poll_id}/voter-groups/{resp.request.url.path.split('/')[-1]}",
        json={"weight": 0.4},
        headers=headers,
    )
    # Obtener ID del segundo grupo
    vg_resp = await client.get(f"/api/polls/{poll_id}/voter-groups")
    groups = vg_resp.json()
    second_group = next(g for g in groups if g["id"] != group1_id)
    
    resp = await client.patch(
        f"/api/polls/{poll_id}/voter-groups/{second_group['id']}",
        json={"weight": 0.4},
        headers=headers,
    )
    assert resp.status_code == 200

    # j. Ahora debería poder abrirse
    resp = await client.post(f"/api/polls/{poll_id}/status", json=open_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


async def test_voter_groups_crud(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba el CRUD de grupos de votantes.
    """
    await _create_admin_and_login(client, db_session)
    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    # Crear poll
    resp = await client.post("/api/polls", json={"title": "Groups Test"}, headers=headers)
    poll_id = resp.json()["id"]

    # Crear grupo
    resp = await client.post(
        f"/api/polls/{poll_id}/voter-groups",
        json={"name": "Colaboradores", "weight": 0.5},
        headers=headers,
    )
    assert resp.status_code == 201
    group_id = resp.json()["id"]
    assert resp.json()["token"]  # Debe tener un token generado

    # Listar grupos
    resp = await client.get(f"/api/polls/{poll_id}/voter-groups")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Actualizar grupo
    resp = await client.patch(
        f"/api/polls/{poll_id}/voter-groups/{group_id}",
        json={"name": "Colaboradores Actualizados"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Colaboradores Actualizados"

    # Eliminar grupo
    resp = await client.delete(f"/api/polls/{poll_id}/voter-groups/{group_id}", headers=headers)
    assert resp.status_code == 204

    # Verificar eliminación
    resp = await client.get(f"/api/polls/{poll_id}/voter-groups")
    assert resp.json() == []


async def test_categories_crud(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba el CRUD de categorías de un Poll.
    """
    await _create_admin_and_login(client, db_session)
    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    resp = await client.post("/api/polls", json={"title": "Categories Test"}, headers=headers)
    poll_id = resp.json()["id"]

    # Crear categoría
    resp = await client.post(
        f"/api/polls/{poll_id}/categories",
        json={"name": "Departamento IT", "order": 1},
        headers=headers,
    )
    assert resp.status_code == 201
    cat_id = resp.json()["id"]
    assert resp.json()["name"] == "Departamento IT"

    # Listar categorías
    resp = await client.get(f"/api/polls/{poll_id}/categories")
    assert len(resp.json()) == 1

    # Actualizar
    resp = await client.patch(
        f"/api/polls/{poll_id}/categories/{cat_id}",
        json={"name": "Tecnología"},
        headers=headers,
    )
    assert resp.json()["name"] == "Tecnología"

    # Eliminar
    resp = await client.delete(f"/api/polls/{poll_id}/categories/{cat_id}", headers=headers)
    assert resp.status_code == 204


async def test_import_options_xlsx(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba la importación de opciones/candidatos desde un archivo XLSX en memoria.
    """
    import openpyxl

    await _create_admin_and_login(client, db_session)
    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    resp = await client.post("/api/polls", json={"title": "Import Test"}, headers=headers)
    poll_id = resp.json()["id"]

    # Crear un XLSX en memoria
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Candidatos"
    ws.append(["categoria", "nombre", "photo_url"])
    ws.append(["Departamento A", "Candidato 1", None])
    ws.append(["Departamento A", "Candidato 2", "https://example.com/img.png"])
    ws.append(["Departamento B", "Candidato 3", None])

    xlsx_buffer = io.BytesIO()
    wb.save(xlsx_buffer)
    xlsx_buffer.seek(0)

    # Importar
    resp = await client.post(
        f"/api/polls/{poll_id}/options/import",
        files={"file": ("candidatos.xlsx", xlsx_buffer.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["categories_created"] == 2
    assert data["options_created"] == 3

    # Verificar que se crearon correctamente las categorías
    resp = await client.get(f"/api/polls/{poll_id}/categories")
    cats = resp.json()
    assert len(cats) == 2
    cat_names = {c["name"] for c in cats}
    assert "Departamento A" in cat_names
    assert "Departamento B" in cat_names


async def test_import_options_csv(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Prueba la importación desde CSV con columnas en español.
    """
    await _create_admin_and_login(client, db_session)
    csrf_resp = await client.get("/setup")
    csrf_token = csrf_resp.cookies.get("csrftoken")
    headers = {"x-csrftoken": csrf_token}

    resp = await client.post("/api/polls", json={"title": "CSV Import Test"}, headers=headers)
    poll_id = resp.json()["id"]

    csv_content = "categoría,nombre\nVentas,Empleado X\nTI,Empleado Y\nTI,Empleado Z\n"
    csv_bytes = csv_content.encode("utf-8")

    resp = await client.post(
        f"/api/polls/{poll_id}/options/import",
        files={"file": ("candidatos.csv", csv_bytes, "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["categories_created"] == 2
    assert data["options_created"] == 3
