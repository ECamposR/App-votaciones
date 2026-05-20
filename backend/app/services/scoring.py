from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poll import Poll, VoterGroup, Category, Option
from app.models.vote import Vote


async def calculate_poll_results(
    db: AsyncSession,
    poll_id: uuid.UUID,
) -> dict[str, Any]:
    """
    Calcula los resultados ponderados y normalizados de un Poll.
    
    Aplica la fórmula:
      score_normalizado = votos_de_opcion_en_grupo / total_votos_del_grupo_en_categoria
      score_final = Σ (score_normalizado × weight_grupo_efectivo)
      
    Si algún grupo no participa en una categoría, se recalcula el peso efectivo de los demás.
    
    Retorna la estructura detallada de resultados agrupada por categorías.
    """
    # 1. Obtener el Poll
    poll_query = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = poll_query.scalar_one_or_none()
    if not poll:
        return {}

    # 2. Obtener grupos de votantes
    groups_query = await db.execute(select(VoterGroup).where(VoterGroup.poll_id == poll_id))
    groups = groups_query.scalars().all()
    group_map = {g.id: g for g in groups}

    # 3. Obtener categorías
    categories_query = await db.execute(
        select(Category)
        .where(Category.poll_id == poll_id)
        .order_by(Category.order)
    )
    categories = categories_query.scalars().all()

    # 4. Obtener opciones (candidatos)
    options_query = await db.execute(
        select(Option)
        .where(Option.poll_id == poll_id)
        .order_by(Option.order)
    )
    options = options_query.scalars().all()

    # 5. Obtener todos los votos del Poll
    votes_query = await db.execute(select(Vote).where(Vote.poll_id == poll_id))
    votes = votes_query.scalars().all()

    # 6. Indexar opciones por categoría
    options_by_category: dict[uuid.UUID, list[Option]] = {}
    for opt in options:
        options_by_category.setdefault(opt.category_id, []).append(opt)

    # 7. Contabilizar votos en memoria para alta performance
    # Estructura: vote_counts[category_id][group_id][option_id] = count
    vote_counts: dict[uuid.UUID, dict[uuid.UUID, dict[uuid.UUID, int]]] = {}
    # Estructura: group_totals[category_id][group_id] = total_votes
    group_totals: dict[uuid.UUID, dict[uuid.UUID, int]] = {}

    for v in votes:
        # Inicializar estructuras si no existen
        cat_counts = vote_counts.setdefault(v.category_id, {})
        grp_counts = cat_counts.setdefault(v.voter_group_id, {})
        grp_counts[v.option_id] = grp_counts.get(v.option_id, 0) + 1

        cat_totals = group_totals.setdefault(v.category_id, {})
        cat_totals[v.voter_group_id] = cat_totals.get(v.voter_group_id, 0) + 1

    # 8. Procesar resultados por categoría
    category_results = []

    for cat in categories:
        cat_options = options_by_category.get(cat.id, [])
        cat_totals = group_totals.get(cat.id, {})

        # Identificar qué grupos tienen al menos 1 voto en esta categoría (grupos activos)
        active_group_ids = [g_id for g_id, tot in cat_totals.items() if tot > 0]
        
        # Calcular la suma de pesos de los grupos activos
        total_active_weight = sum(group_map[g_id].weight for g_id in active_group_ids if g_id in group_map)

        # Resultados de opciones en esta categoría
        option_results_list = []
        total_votes_in_category = sum(cat_totals.values())

        for opt in cat_options:
            final_score = 0.0
            votes_by_group_dict = {}
            total_votes_for_option = 0

            for grp in groups:
                # Contar votos del grupo para esta opción
                grp_votes = vote_counts.get(cat.id, {}).get(grp.id, {}).get(opt.id, 0)
                total_votes_for_option += grp_votes
                votes_by_group_dict[grp.name] = grp_votes

                # Si el grupo tiene votos en esta categoría, calcular su aporte ponderado
                total_grp_votes = cat_totals.get(grp.id, 0)
                if total_grp_votes > 0:
                    score_normalizado = grp_votes / total_grp_votes
                    
                    # Calcular el peso efectivo del grupo para esta categoría
                    if total_active_weight > 0:
                        weight_efectivo = grp.weight / total_active_weight
                    else:
                        weight_efectivo = 1.0 / len(active_group_ids)
                    
                    final_score += score_normalizado * weight_efectivo

            option_results_list.append({
                "option_id": opt.id,
                "option_name": opt.name,
                "photo_url": opt.photo_url,
                "score": round(final_score, 6),
                "total_votes": total_votes_for_option,
                "votes_by_group": votes_by_group_dict,
            })

        # Ordenar resultados:
        # 1. Score descendente
        # 2. Votos totales descendente (desempate)
        # 3. Nombre alfabético ascendente (desempate final)
        option_results_list.sort(
            key=lambda x: (-x["score"], -x["total_votes"], x["option_name"])
        )

        category_results.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "total_votes": total_votes_in_category,
            "results": option_results_list,
        })

    return {
        "poll_id": poll.id,
        "title": poll.title,
        "status": poll.status,
        "categories": category_results,
    }
