"""Esquemas Pydantic.

1. ContextoPaciente: espejo del contexto que arma el backend
   (services/ia.service.js -> construirContexto) SIN el catálogo:
   el catálogo ya no viaja en el prompt, el agente lo consulta con tools.
2. RecomendacionesResponse: salida estructurada exigida al agente
   (se usa como response_format de create_agent).
"""

from typing import Literal

from pydantic import BaseModel, Field


# ---------- Contexto enviado por el backend ----------

class PacienteContexto(BaseModel):
    objetivo: str | None = None
    condicion_medica: str | None = None
    nivel_actividad: str | None = None
    sexo: str | None = None
    edad: int | None = None
    peso_kg: float | None = None
    altura_cm: float | None = None


class RestriccionesDietarias(BaseModel):
    alergias: list[str] = []
    intolerancias: list[str] = []
    restricciones: list[str] = []


class AlimentoPlanItem(BaseModel):
    nombre: str
    cantidad_g: float | None = None


class ComidaPlan(BaseModel):
    tipo_comida: str
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float
    alimentos: list[AlimentoPlanItem] = []


class ObjetivosDia(BaseModel):
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float


class PlanContexto(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    calorias_diarias: int
    comidas_de_hoy: list[ComidaPlan] = []
    objetivos_del_dia: ObjetivosDia


class ConsumoHoy(BaseModel):
    fecha: str
    kcal: float
    proteinas_g: float
    carbohidratos_g: float
    grasas_g: float
    por_tipo_comida: dict[str, float] = {}


class Desvio(BaseModel):
    kcal_restantes: float
    proteinas_restantes: float
    carbohidratos_restantes: float
    grasas_restantes: float


class ContextoPaciente(BaseModel):
    paciente: PacienteContexto
    restricciones_dietarias: RestriccionesDietarias
    plan: PlanContexto
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
        description="de 1 a 3 sugerencias de alimentos del catálogo",
    )
