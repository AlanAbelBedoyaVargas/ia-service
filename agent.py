"""Agente de LangChain: asesor nutricional con tools y salida estructurada.

El agente razona sobre el contexto que envía el backend y consulta la tabla
alimentos con sus herramientas. La respuesta final se valida contra el
esquema RecomendacionesResponse (Pydantic).
"""

from functools import lru_cache

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain_openai import ChatOpenAI

from config import settings
from prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_PLAN_ALTERNATIVO
from schemas import (
    ContextoPaciente,
    ContextoPlanAlternativo,
    PlanAlternativoResponse,
    RecomendacionesResponse,
)
from tools import buscar_alimentos, obtener_alimento

# Límite de pasos del agente (llamadas al modelo + tools) para evitar bucles
LIMITE_ITERACIONES = 30


@lru_cache(maxsize=1)
def construir_agente():
    """Crea el agente una sola vez (el modelo y las tools son reutilizables)."""
    modelo = ChatOpenAI(
        model=settings.ai_model,
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        temperature=0.4,
    )
    return create_agent(
        model=modelo,
        tools=[buscar_alimentos, obtener_alimento],
        system_prompt=SYSTEM_PROMPT,
        response_format=ProviderStrategy(RecomendacionesResponse),
    )


@lru_cache(maxsize=1)
def construir_agente_plan_alternativo():
    """Crea el agente generador de opciones de día alternativo una sola vez."""
    modelo = ChatOpenAI(
        model=settings.ai_model,
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        temperature=0.5,
    )
    return create_agent(
        model=modelo,
        tools=[buscar_alimentos, obtener_alimento],
        system_prompt=SYSTEM_PROMPT_PLAN_ALTERNATIVO,
        response_format=ProviderStrategy(PlanAlternativoResponse),
    )


def ejecutar_agente(contexto: ContextoPaciente) -> RecomendacionesResponse:
    """Ejecuta el agente con el contexto del paciente y devuelve la respuesta estructurada."""
    if not settings.ai_api_key:
        raise RuntimeError(
            "El servicio de IA no está configurado: falta AI_API_KEY en el archivo .env"
        )

    entrada = {"messages": [{"role": "user", "content": contexto.model_dump_json()}]}
    resultado = construir_agente().invoke(entrada, config={"recursion_limit": LIMITE_ITERACIONES})
    return resultado["structured_response"]


def ejecutar_agente_plan_alternativo(contexto: ContextoPlanAlternativo) -> PlanAlternativoResponse:
    """Ejecuta el agente para diseñar 2 opciones de menú diario alternativo."""
    if not settings.ai_api_key:
        raise RuntimeError(
            "El servicio de IA no está configurado: falta AI_API_KEY en el archivo .env"
        )

    entrada = {"messages": [{"role": "user", "content": contexto.model_dump_json()}]}
    resultado = construir_agente_plan_alternativo().invoke(
        entrada,
        config={"recursion_limit": LIMITE_ITERACIONES},
    )
    return resultado["structured_response"]
