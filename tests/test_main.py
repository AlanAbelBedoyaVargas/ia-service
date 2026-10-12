"""Tests de la API: health, autenticación interna y validación de contexto.

No ejecutan el agente (no llaman a Gemini): solo cubren los caminos que
fallan antes de llegar al agente.
"""

from conftest import CLAVE_TEST


def test_health_ok(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_recomendaciones_sin_clave_interna_rechazada(cliente, contexto_valido):
    respuesta = cliente.post("/recomendaciones", json=contexto_valido)
    assert respuesta.status_code == 401


def test_recomendaciones_con_clave_invalida_rechazada(cliente, contexto_valido):
    respuesta = cliente.post(
        "/recomendaciones",
        json=contexto_valido,
        headers={"X-Internal-Key": "esta-clave-no-es"},
    )
    assert respuesta.status_code == 401
    assert "Clave interna" in respuesta.json()["detail"]


def test_recomendaciones_con_clave_valida_pero_contexto_invalido(cliente):
    # La clave es correcta pero el contexto no cumple el esquema -> 422
    # (validación de FastAPI) sin llegar a ejecutar el agente
    respuesta = cliente.post(
        "/recomendaciones",
        json={"paciente": {}},
        headers={"X-Internal-Key": CLAVE_TEST},
    )
    assert respuesta.status_code == 422


def test_recomendaciones_con_clave_invalida_y_contexto_invalido(cliente):
    # Sin clave válida la solicitud se rechaza: nunca se procesa el cuerpo
    # más allá de la validación estructural de FastAPI
    respuesta = cliente.post(
        "/recomendaciones",
        json={"paciente": {}},
        headers={"X-Internal-Key": "incorrecta"},
    )
    assert respuesta.status_code in (401, 422)
