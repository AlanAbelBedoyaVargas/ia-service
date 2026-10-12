"""Tools del agente: consultas inteligentes sobre la tabla alimentos.

La primera fuente de sugerencias es SIEMPRE la base de datos, nunca la
memoria del modelo: el agente debe usar estas herramientas para buscar
alimentos reales del catálogo.
"""

import json
import logging
from typing import Literal

from langchain_core.tools import tool

from db import buscar_alimentos_db, obtener_alimento_db

logger = logging.getLogger(__name__)

CategoriaAlimento = Literal[
    "frutas",
    "verduras",
    "carnes",
    "lacteos",
    "cereales",
    "legumbres",
    "grasas",
    "bebidas",
    "otros",
]


@tool
def buscar_alimentos(
    nombre: str | None = None,
    categoria: CategoriaAlimento | None = None,
    calorias_min: float | None = None,
    calorias_max: float | None = None,
    proteinas_min: float | None = None,
    carbohidratos_max: float | None = None,
    grasas_max: float | None = None,
    es_vegano: bool | None = None,
    sin_gluten: bool | None = None,
    sin_lactosa: bool | None = None,
    limite: int = 10,
) -> str:
    """Busca alimentos reales del catálogo con filtros combinables.

    Devuelve una lista JSON (máximo `limite`) con id, nombre, categoría,
    descripción y valores por 100 g (calorías y macronutrientes) de cada
    alimento. Úsala para elegir alimentos concretos para tus sugerencias:

    - si falta un macronutriente en el día: proteinas_min / carbohidratos_max / grasas_max;
    - si faltan o sobran calorías: calorias_min / calorias_max;
    - si el paciente tiene restricciones: es_vegano / sin_gluten / sin_lactosa en true;
    - usa nombre para buscar por palabra (por ejemplo "pollo", "arroz");
    - usa categoria para explorar un grupo completo.

    Args:
        nombre: texto a buscar dentro del nombre del alimento (coincidencia parcial, sin acentos estrictos).
        categoria: categoría del alimento.
        calorias_min: kcal mínimas por 100 g.
        calorias_max: kcal máximas por 100 g.
        proteinas_min: gramos mínimos de proteína por 100 g.
        carbohidratos_max: gramos máximos de carbohidratos por 100 g.
        grasas_max: gramos máximos de grasa por 100 g.
        es_vegano: True para excluir alimentos no veganos.
        sin_gluten: True para excluir alimentos con gluten.
        sin_lactosa: True para excluir alimentos con lactosa.
        limite: cantidad máxima de resultados (entre 1 y 20).
    """
    limite = max(1, min(int(limite), 20))
    logger.info(
        "Tool buscar_alimentos: nombre=%r categoria=%r calorias=%s/%s proteinas_min=%s "
        "carbohidratos_max=%s grasas_max=%s es_vegano=%s sin_gluten=%s sin_lactosa=%s limite=%d",
        nombre, categoria, calorias_min, calorias_max, proteinas_min,
        carbohidratos_max, grasas_max, es_vegano, sin_gluten, sin_lactosa, limite,
    )
    resultados = buscar_alimentos_db(
        nombre=nombre,
        categoria=categoria,
        calorias_min=calorias_min,
        calorias_max=calorias_max,
        proteinas_min=proteinas_min,
        carbohidratos_max=carbohidratos_max,
        grasas_max=grasas_max,
        es_vegano=es_vegano,
        sin_gluten=sin_gluten,
        sin_lactosa=sin_lactosa,
        limite=limite,
    )
    logger.info("Tool buscar_alimentos devolvió %d alimentos", len(resultados))
    return json.dumps(resultados, ensure_ascii=False)


@tool
def obtener_alimento(id: int) -> str:
    """Obtiene un alimento exacto del catálogo por su id.

    Devuelve un JSON con id, nombre, categoría, descripción y valores por
    100 g, o un error si no existe. Úsala para confirmar los datos de un
    alimento (y su id) justo antes de incluirlo en una sugerencia.

    Args:
        id: id numérico del alimento en el catálogo.
    """
    logger.info("Tool obtener_alimento: id=%s", id)
    alimento = obtener_alimento_db(int(id))
    if alimento is None:
        return json.dumps({"error": f"No existe un alimento con id {id}"}, ensure_ascii=False)
    return json.dumps(alimento, ensure_ascii=False)


__all__ = ["buscar_alimentos", "obtener_alimento"]
