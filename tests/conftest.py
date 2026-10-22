"""Fixtures compartidas de los tests del ia-service.

Los tests de API NO llaman al proveedor de IA (el agente no se ejecuta):
solo prueban autenticación interna y validación de contexto.
Los tests de tools usan la base de datos local (debe estar seedeada).
"""

import pytest
from fastapi.testclient import TestClient

import main
from config import settings

CLAVE_TEST = "clave-interna-solo-para-tests"


@pytest.fixture
def contexto_valido() -> dict:
    """Contexto completo y válido, con la misma forma que arma el backend."""
    return {
        "paciente": {
            "objetivo": "Perder peso",
            "nivel_actividad": "ligero",
            "sexo": "masculino",
            "edad": 35,
            "peso_kg": 85.0,
            "altura_cm": 178.0,
        },
        "restricciones_dietarias": {
            "alergias": [],
            "intolerancias": ["Lactosa"],
            "restricciones": [],
        },
        "plan": {
            "titulo": "Plan de reducción calórica",
            "descripcion": None,
            "calorias_diarias": 2200,
            "comidas_de_hoy": [
                {
                    "tipo_comida": "desayuno",
                    "kcal": 450.0,
                    "proteinas_g": 25.0,
                    "carbohidratos_g": 55.0,
                    "grasas_g": 12.0,
                    "alimentos": [{"nombre": "Avena en hojuelas", "cantidad_g": 60}],
                }
            ],
            "objetivos_del_dia": {
                "kcal": 2200.0,
                "proteinas_g": 110.0,
                "carbohidratos_g": 250.0,
                "grasas_g": 70.0,
            },
        },
        "consumo_registrado_hoy": {
            "fecha": "2026-10-12",
            "kcal": 180.0,
            "proteinas_g": 12.0,
            "carbohidratos_g": 20.0,
            "grasas_g": 4.0,
            "por_tipo_comida": {"desayuno": 180.0},
        },
        "desvio": {
            "kcal_restantes": 2020.0,
            "proteinas_restantes": 98.0,
            "carbohidratos_restantes": 230.0,
            "grasas_restantes": 66.0,
        },
        "comidas_sin_registrar": ["almuerzo", "cena", "snack"],
    }


@pytest.fixture
def contexto_plan_alternativo_valido() -> dict:
    """Contexto válido para generar alternativas de un día del plan."""
    return {
        "paciente": {
            "objetivo": "Perder peso",
            "nivel_actividad": "ligero",
            "sexo": "masculino",
            "edad": 35,
            "peso_kg": 85.0,
            "altura_cm": 178.0,
        },
        "restricciones_dietarias": {
            "alergias": [],
            "intolerancias": ["Lactosa"],
            "restricciones": [],
        },
        "plan_base": {
            "titulo": "Plan de reducción calórica",
            "descripcion": "Plan equilibrado",
            "dia_semana": 2,
            "nombre_dia": "Martes",
            "objetivos_del_dia": {
                "kcal": 1850.0,
                "proteinas_g": 140.0,
                "carbohidratos_g": 180.0,
                "grasas_g": 60.0,
            },
            "comidas_originales_del_dia": [
                {
                    "tipo_comida": "desayuno",
                    "kcal": 450.0,
                    "proteinas_g": 25.0,
                    "carbohidratos_g": 55.0,
                    "grasas_g": 12.0,
                    "alimentos": [{"nombre": "Avena en hojuelas", "cantidad_g": 60}],
                }
            ],
        },
        "preferencias": {
            "alimentos_evitar": ["Salmón"],
            "alimentos_preferidos": ["Atún al agua", "Huevo"],
        },
    }


@pytest.fixture
def clave_test() -> str:
    return CLAVE_TEST


@pytest.fixture
def cliente():
    """Cliente de pruebas con la clave interna parcheada (sin tocar el .env)."""
    clave_original = settings.ia_internal_key
    settings.ia_internal_key = CLAVE_TEST
    with TestClient(main.app) as client:
        yield client
    settings.ia_internal_key = clave_original
