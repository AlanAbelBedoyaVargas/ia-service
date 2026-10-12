"""Agente de LangChain: asesor nutricional con tools y salida estructurada.

El agente razona sobre el contexto que envía el backend y consulta la tabla
alimentos con sus herramientas. La respuesta final se valida contra el
esquema RecomendacionesResponse (Pydantic).
"""

from functools import lru_cache

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings
from prompts import SYSTEM_PROMPT
from schemas import ContextoPaciente, RecomendacionesResponse
from tools import buscar_alimentos, obtener_alimento

# Límite de pasos del agente (llamadas al modelo + tools) para evitar bucles
LIMITE_ITERACIONES = 30


@lru_cache(maxsize=1)
def construir_agente():
    """Crea el agente una sola vez (el modelo y las tools son reutilizables)."""
    modelo = ChatGoogleGenerativeAI(
        model=settings.ai_model,
        api_key=settings.ai_api_key,
        temperature=0.4,
    )
    return create_agent(
        model=modelo,
        tools=[buscar_alimentos, obtener_alimento],
        system_prompt=SYSTEM_PROMPT,
        response_format=RecomendacionesResponse,
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
