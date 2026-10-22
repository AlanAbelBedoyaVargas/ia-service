"""API del servicio de IA (FastAPI).

Endpoints:
- GET  /health          -> estado del servicio
- POST /recomendaciones -> ejecuta el agente con el contexto enviado por el backend

Comunicación interna con el backend: cabecera X-Internal-Key con la clave
compartida (IA_INTERNAL_KEY en el .env). El frontend nunca llama a este
servicio: solo el backend.
"""

import logging

from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from agent import ejecutar_agente, ejecutar_agente_plan_alternativo
from config import settings
from schemas import (
    ContextoPaciente,
    ContextoPlanAlternativo,
    PlanAlternativoResponse,
    RecomendacionesResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IA de recomendaciones alimentarias",
    description=(
        "Agente de LangChain (vía OpenRouter) que sugiere alimentos del catálogo para "
        "acercar al paciente a sus objetivos del día. El contexto lo arma el "
        "backend y el catálogo se consulta con tools sobre la base de datos."
    ),
)


def exigir_key_interna(x_internal_key: str | None) -> None:
    """Verifica la clave compartida con el backend."""
    if not settings.ia_internal_key:
        raise HTTPException(
            status_code=503,
            detail="Servicio de IA no configurado: falta IA_INTERNAL_KEY en el archivo .env",
        )
    if x_internal_key != settings.ia_internal_key:
        raise HTTPException(status_code=401, detail="Clave interna inválida")


def clasificar_error_proveedor(exc: Exception) -> tuple[int, str]:
    """Clasifica un error del proveedor en (código HTTP, mensaje para el usuario)."""
    mensaje_original = str(exc)
    texto = mensaje_original.lower()

    if texto.startswith("el servicio de ia no está configurado"):
        return 500, mensaje_original
    if any(clave in texto for clave in ("api key", "401", "403", "permission", "invalid_argument")):
        return 502, "La API rechazó la solicitud: revisa AI_API_KEY y AI_MODEL en el archivo .env del ia-service"
    if any(clave in texto for clave in ("insufficient", "credit")):
        return 502, "Saldo insuficiente en OpenRouter: carga créditos para seguir usando el servicio"
    if any(clave in texto for clave in ("429", "resource_exhausted", "quota", "cuota")):
        return 429, "Se excedió la cuota del proveedor de IA. Intenta más tarde."
    if isinstance(exc, TimeoutError) or "timeout" in texto or "deadline" in texto:
        return 504, "El proveedor de IA no respondió a tiempo. Intenta de nuevo en un momento."
    return 502, "El proveedor de IA no respondió correctamente"


@app.get("/health")
def health() -> dict:
    return {"estado": "ok"}


@app.post("/recomendaciones", response_model=RecomendacionesResponse)
async def recomendaciones(
    contexto: ContextoPaciente,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
) -> RecomendacionesResponse:
    exigir_key_interna(x_internal_key)

    logger.info(
        "Solicitud de recomendaciones recibida (paciente: %s)",
        contexto.paciente.objetivo or "sin objetivo",
    )
    try:
        # El agente se ejecuta de forma bloqueante: se corre en un threadpool
        # para no frenar el event loop mientras el LLM y las tools trabajan.
        return await run_in_threadpool(ejecutar_agente, contexto)
    except HTTPException:
        raise
    except Exception as exc:
        estado, mensaje = clasificar_error_proveedor(exc)
        logger.error("Error ejecutando el agente (%s): %s", type(exc).__name__, exc)
        raise HTTPException(status_code=estado, detail=mensaje) from exc


@app.post("/plan-alternativo", response_model=PlanAlternativoResponse)
async def plan_alternativo(
    contexto: ContextoPlanAlternativo,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
) -> PlanAlternativoResponse:
    exigir_key_interna(x_internal_key)

    logger.info(
        "Solicitud de plan alternativo recibida (día: %s, objetivo: %s)",
        contexto.plan_base.nombre_dia,
        contexto.paciente.objetivo or "sin objetivo",
    )
    try:
        return await run_in_threadpool(ejecutar_agente_plan_alternativo, contexto)
    except HTTPException:
        raise
    except Exception as exc:
        estado, mensaje = clasificar_error_proveedor(exc)
        logger.error("Error ejecutando el agente de plan alternativo (%s): %s", type(exc).__name__, exc)
        raise HTTPException(status_code=estado, detail=mensaje) from exc
