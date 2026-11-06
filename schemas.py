"""Esquemas Pydantic del ia-service.

1. Contextos: la ÚNICA información que el backend envía al agente, sin ruido:
   restricciones dietarias + metas del plan (fijadas por el nutricionista) +
   consumo/desvío (recomendaciones) o referencia del día original (plan
   alternativo). El catálogo NO viaja: el agente lo consulta con las tools.
2. Salidas estructuradas exigidas al agente (response_model / response_format):
   - RecomendacionesResponse (POST /recomendaciones)
   - PlanAlternativoResponse (POST /plan-alternativo)
"""

from typing import Literal

from pydantic import BaseModel, Field


# ---------- Contexto enviado por el backend ----------

class RestriccionesDietarias(BaseModel):
    alergias: list[str] = []
    intolerancias: list[str] = []
    restricciones: list[str] = []


class ObjetivosDia(BaseModel):
    """Metas diarias fijadas por el nutricionista en el plan."""

    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float


class ConsumoHoy(BaseModel):
    """Suma de lo ya registrado por el paciente HOY (recomendaciones)."""

    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float


class Desvio(BaseModel):
    """Objetivo - consumo: los nutrientes que aún faltan del día."""

    kcal_restantes: float
    proteinas_restantes: float
    carbohidratos_restantes: float
    grasas_restantes: float


class ContextoPaciente(BaseModel):
    restricciones_dietarias: RestriccionesDietarias
    objetivos_del_dia: ObjetivosDia
    consumo_registrado_hoy: ConsumoHoy
    desvio: Desvio
    comidas_sin_registrar: list[str] = []


# ---------- Salida estructurada exigida al agente ----------

TipoComida = Literal["desayuno", "almuerzo", "cena", "snack"]


class Sugerencia(BaseModel):
    id_alimento: int = Field(description="id del alimento del catálogo, obtenido con las herramientas")
    cantidad_g: float = Field(description="cantidad sugerida en gramos (entre 1 y 999)")
    tipo_sugerido: TipoComida = Field(description="comida del día para la que encaja la sugerencia")
    justificacion: str = Field(description="por qué ese alimento ayuda (1-2 frases, en español)")


class RecomendacionesResponse(BaseModel):
    analisis: str = Field(description="resumen del estado del día del paciente (2-3 frases, en español)")
    sugerencias: list[Sugerencia] = Field(
        default_factory=list,
        description="de 3 a 5 sugerencias de alimentos del catálogo (menos si ya completó el día)",
    )


# ---------- Plan alternativo por día (contexto + salida estructurada) ----------

class AlimentoPlanItem(BaseModel):
    """Ítem de referencia de una comida del día original (solo lectura)."""

    nombre: str
    cantidad_g: float | None = None


class ComidaPlan(BaseModel):
    tipo_comida: str
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float
    alimentos: list[AlimentoPlanItem] = []


class PlanBaseDiaContexto(BaseModel):
    objetivos_del_dia: ObjetivosDia
    comidas_originales_del_dia: list[ComidaPlan] = []


class PreferenciasPlanAlternativo(BaseModel):
    alimentos_evitar: list[str] = []
    alimentos_preferidos: list[str] = []


class ContextoPlanAlternativo(BaseModel):
    restricciones_dietarias: RestriccionesDietarias
    plan_base: PlanBaseDiaContexto
    preferencias: PreferenciasPlanAlternativo = Field(default_factory=PreferenciasPlanAlternativo)


class AlimentoPropuesto(BaseModel):
    id_alimento: int = Field(description="id del alimento del catálogo, obtenido con las herramientas")
    cantidad_g: float = Field(description="cantidad sugerida en gramos (entre 1 y 999)")


class ComidaPropuesta(BaseModel):
    tipo_comida: TipoComida = Field(description="tipo de comida del día: desayuno, almuerzo, cena o snack")
    alimentos: list[AlimentoPropuesto] = Field(
        default_factory=list,
        description="alimentos del catálogo que componen esta comida (de 2 a 4 ítems)",
    )


class OpcionDiaAlternativo(BaseModel):
    titulo: str = Field(description="título breve y descriptivo de esta opción de menú (en español)")
    justificacion: str = Field(
        description=(
            "explicación breve (1-2 frases, en español) de cómo esta opción adapta el día "
            "respetando las metas del nutricionista y las preferencias del paciente"
        )
    )
    comidas: list[ComidaPropuesta] = Field(
        default_factory=list,
        description="las 4 comidas del día: desayuno, almuerzo, cena y snack",
    )


class PlanAlternativoResponse(BaseModel):
    opciones: list[OpcionDiaAlternativo] = Field(
        default_factory=list,
        description="exactamente 2 opciones de menú diario diferentes entre sí",
    )
