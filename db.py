"""Acceso a la base de datos (SOLO LECTURA de la tabla alimentos).

El motor se crea con la sesión en modo read-only a nivel de PostgreSQL
(default_transaction_read_only=on): aunque por error se intentara escribir,
la base de datos lo rechazaría.
"""

from functools import lru_cache

from sqlalchemy import column, create_engine, func, select, table
from sqlalchemy.engine import Engine

from config import settings

# translate() de PostgreSQL sustituye carácter por carácter: ambas cadenas
# deben tener la misma longitud y el mismo orden para normalizar tildes y ñ.
_CARACTERES_ACENTUADOS = "áéíóúüñÁÉÍÓÚÜÑ"
_CARACTERES_SIN_ACENTO = "aeiouunAEIOUUN"

# Tabla declarada sin ORM: solo se usa para construir consultas
# parametrizadas de lectura sobre alimentos.
alimentos_tbl = table(
    "alimentos",
    column("id"),
    column("nombre"),
    column("categoria"),
    column("descripcion"),
    column("calorias_100g"),
    column("proteinas_g"),
    column("carbohidratos_g"),
    column("grasas_g"),
    column("es_vegano"),
    column("sin_gluten"),
    column("sin_lactosa"),
)


@lru_cache(maxsize=1)
def obtener_engine() -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"options": "-c default_transaction_read_only=on"},
    )


def _normalizar(fila) -> dict:
    """Convierte una fila de la BD en un dict plano (Decimal -> float)."""
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "categoria": fila["categoria"],
        "descripcion": fila["descripcion"],
        "calorias_100g": float(fila["calorias_100g"] or 0),
        "proteinas_g": float(fila["proteinas_g"] or 0),
        "carbohidratos_g": float(fila["carbohidratos_g"] or 0),
        "grasas_g": float(fila["grasas_g"] or 0),
        "es_vegano": bool(fila["es_vegano"]),
        "sin_gluten": bool(fila["sin_gluten"]),
        "sin_lactosa": bool(fila["sin_lactosa"]),
    }


def buscar_alimentos_db(
    nombre: str | None = None,
    categoria: str | None = None,
    calorias_min: float | None = None,
    calorias_max: float | None = None,
    proteinas_min: float | None = None,
    carbohidratos_max: float | None = None,
    grasas_max: float | None = None,
    es_vegano: bool | None = None,
    sin_gluten: bool | None = None,
    sin_lactosa: bool | None = None,
    limite: int = 10,
) -> list[dict]:
    """Busca alimentos con filtros combinables (todos opcionales)."""
    filtros = []
    if nombre:
        filtros.append(
            func.translate(alimentos_tbl.c.nombre, _CARACTERES_ACENTUADOS, _CARACTERES_SIN_ACENTO).ilike(
                func.translate(f"%{nombre}%", _CARACTERES_ACENTUADOS, _CARACTERES_SIN_ACENTO)
            )
        )
    if categoria:
        filtros.append(alimentos_tbl.c.categoria == categoria)
    if calorias_min is not None:
        filtros.append(alimentos_tbl.c.calorias_100g >= calorias_min)
    if calorias_max is not None:
        filtros.append(alimentos_tbl.c.calorias_100g <= calorias_max)
    if proteinas_min is not None:
        filtros.append(alimentos_tbl.c.proteinas_g >= proteinas_min)
    if carbohidratos_max is not None:
        filtros.append(alimentos_tbl.c.carbohidratos_g <= carbohidratos_max)
    if grasas_max is not None:
        filtros.append(alimentos_tbl.c.grasas_g <= grasas_max)
    if es_vegano:
        filtros.append(alimentos_tbl.c.es_vegano.is_(True))
    if sin_gluten:
        filtros.append(alimentos_tbl.c.sin_gluten.is_(True))
    if sin_lactosa:
        filtros.append(alimentos_tbl.c.sin_lactosa.is_(True))

    consulta = select(*alimentos_tbl.c)
    if filtros:
        consulta = consulta.where(*filtros)
    consulta = consulta.order_by(alimentos_tbl.c.nombre).limit(limite)

    with obtener_engine().connect() as conexion:
        filas = conexion.execute(consulta).mappings().all()
        return [_normalizar(fila) for fila in filas]


def obtener_alimento_db(id_alimento: int) -> dict | None:
    """Obtiene un alimento por su id (o None si no existe)."""
    consulta = select(*alimentos_tbl.c).where(alimentos_tbl.c.id == id_alimento)
    with obtener_engine().connect() as conexion:
        fila = conexion.execute(consulta).mappings().first()
        return _normalizar(fila) if fila else None
