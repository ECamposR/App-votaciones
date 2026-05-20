from __future__ import annotations

import csv
import io
import uuid
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import openpyxl

from app.models.poll import Category, Option


def normalize_header(header: str) -> str:
    """
    Normaliza el nombre de una cabecera para comparación flexible (minúsculas, sin acentos y limpia).
    """
    cleaned = header.strip().lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n"
    }
    for orig, rep in replacements.items():
        cleaned = cleaned.replace(orig, rep)
    return cleaned


def detect_columns(headers: list[str]) -> tuple[int | None, int | None, int | None]:
    """
    Detecta los índices de las columnas para categoría, opción e imagen.
    """
    cat_idx = None
    opt_idx = None
    img_idx = None

    cat_keywords = {"categoria", "category", "departamento", "department", "seccion", "section"}
    opt_keywords = {"nombre", "name", "candidato", "candidata", "opcion", "option", "candidatos"}
    img_keywords = {"foto", "photo", "imagen", "image", "foto_url", "photo_url", "imagen_url", "image_url"}

    for idx, raw_h in enumerate(headers):
        h = normalize_header(raw_h)
        if cat_idx is None and any(kw in h for kw in cat_keywords):
            cat_idx = idx
        elif opt_idx is None and any(kw in h for kw in opt_keywords):
            opt_idx = idx
        elif img_idx is None and any(kw in h for kw in img_keywords):
            img_idx = idx

    return cat_idx, opt_idx, img_idx


async def import_options_from_file(
    db: AsyncSession,
    poll_id: uuid.UUID,
    file_bytes: bytes,
    filename: str,
) -> dict[str, int]:
    """
    Parsea un archivo CSV o XLSX de opciones/candidatos,
    crea categorías nuevas de forma dinámica y carga las opciones asociadas al poll.
    Todo se ejecuta en una sola transacción asíncrona.
    """
    rows: list[dict[str, Any]] = []

    # 1. Parsear CSV
    if filename.endswith(".csv"):
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo decodificar el archivo CSV. Asegúrate de que use UTF-8 o Latin-1.",
                )
        
        csv_file = io.StringIO(content)
        reader = csv.reader(csv_file)
        try:
            headers = next(reader)
        except StopIteration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo CSV está vacío.",
            )
        
        cat_idx, opt_idx, img_idx = detect_columns(headers)
        if cat_idx is None or opt_idx is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se identificaron las columnas obligatorias para 'Categoría' y 'Nombre/Opción' en las cabeceras del CSV.",
            )

        for row in reader:
            if not row or len(row) <= max(cat_idx, opt_idx):
                continue
            cat_val = row[cat_idx].strip()
            opt_val = row[opt_idx].strip()
            img_val = row[img_idx].strip() if img_idx is not None and len(row) > img_idx else None
            
            if cat_val and opt_val:
                rows.append({"category": cat_val, "option": opt_val, "photo_url": img_val})

    # 2. Parsear XLSX (Excel)
    elif filename.endswith(".xlsx"):
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), read_only=True, data_only=True)
            sheet = wb.active
            if not sheet:
                raise ValueError("Hoja de Excel activa no encontrada.")
            
            iterator = sheet.iter_rows(values_only=True)
            headers_raw = next(iterator)
            headers = [str(h) for h in headers_raw if h is not None]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al leer planilla Excel: {str(e)}",
            )
        
        cat_idx, opt_idx, img_idx = detect_columns(headers)
        if cat_idx is None or opt_idx is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se identificaron las columnas obligatorias para 'Categoría' y 'Nombre/Opción' en las cabeceras de Excel.",
            )

        for row_tuple in iterator:
            if not row_tuple:
                continue
            cat_val = str(row_tuple[cat_idx]).strip() if cat_idx < len(row_tuple) and row_tuple[cat_idx] is not None else ""
            opt_val = str(row_tuple[opt_idx]).strip() if opt_idx < len(row_tuple) and row_tuple[opt_idx] is not None else ""
            img_val = str(row_tuple[img_idx]).strip() if img_idx is not None and img_idx < len(row_tuple) and row_tuple[img_idx] is not None else None
            
            if cat_val and opt_val:
                rows.append({"category": cat_val, "option": opt_val, "photo_url": img_val})
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Debe ser .csv o .xlsx",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron filas con datos válidos para importar.",
        )

    # 3. Procesar y guardar en Base de Datos de forma eficiente
    # Consultar categorías existentes para el poll
    cat_query = await db.execute(select(Category).where(Category.poll_id == poll_id))
    existing_cats = {c.name.strip().lower(): c for c in cat_query.scalars().all()}
    
    # Llevar tracking de los órdenes máximos existentes
    max_cat_order = max([c.order for c in existing_cats.values()], default=-1)
    
    cats_created = 0
    opts_created = 0

    # Agrupar las opciones por categoría para agregarlas de forma ordenada
    grouped_options: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        c_name = r["category"]
        grouped_options.setdefault(c_name, []).append(r)

    for cat_name, opt_list in grouped_options.items():
        cat_key = cat_name.strip().lower()
        if cat_key in existing_cats:
            category = existing_cats[cat_key]
        else:
            # Crear categoría nueva
            max_cat_order += 1
            category = Category(
                poll_id=poll_id,
                name=cat_name,
                order=max_cat_order,
            )
            db.add(category)
            # Guardamos en diccionario para evitar duplicación si viene repetida en formas alternas
            existing_cats[cat_key] = category
            cats_created += 1
            # Forzar persistencia para obtener el ID de la categoría
            await db.flush()

        # Obtener el orden máximo de opciones en esta categoría
        opt_query = await db.execute(
            select(Option.order)
            .where(Option.category_id == category.id)
        )
        max_opt_order = max(opt_query.scalars().all(), default=-1)

        for opt in opt_list:
            max_opt_order += 1
            new_opt = Option(
                poll_id=poll_id,
                category_id=category.id,
                name=opt["option"],
                photo_url=opt["photo_url"],
                order=max_opt_order,
            )
            db.add(new_opt)
            opts_created += 1

    await db.commit()

    return {
        "categories_created": cats_created,
        "options_created": opts_created,
    }
