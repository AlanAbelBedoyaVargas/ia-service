"""Tests de las consultas a la tabla alimentos (requisito: BD seedeada)."""

import json

from db import buscar_alimentos_db, obtener_alimento_db
from tools import buscar_alimentos as tool_buscar_alimentos
from tools import obtener_alimento as tool_obtener_alimento


# ---------- Consultas directas a la BD ----------

def test_buscar_por_nombre_parcial():
    resultados = buscar_alimentos_db(nombre="pollo")
    nombres = [a["nombre"] for a in resultados]
    assert "Pechuga de pollo" in nombres
    assert "Muslo de pollo" in nombres


def test_filtro_proteinas_min():
    resultados = buscar_alimentos_db(proteinas_min=25)
    assert len(resultados) > 0
    assert all(a["proteinas_g"] >= 25 for a in resultados)


def test_filtro_calorias_max():
    resultados = buscar_alimentos_db(calorias_max=50)
    assert len(resultados) > 0
    assert all(a["calorias_100g"] <= 50 for a in resultados)


def test_filtro_sin_lactosa_excluye_lacteos():
    resultados = buscar_alimentos_db(sin_lactosa=True)
    assert len(resultados) > 0
    assert all(a["sin_lactosa"] for a in resultados)


def test_filtro_es_vegano_excluye_carnes_y_lacteos():
    resultados = buscar_alimentos_db(es_vegano=True)
    assert len(resultados) > 0
    assert all(a["es_vegano"] for a in resultados)
    nombres = {a["nombre"] for a in resultados}
    assert "Pechuga de pollo" not in nombres
    assert "Manteca" not in nombres
    assert "Leche entera" not in nombres


def test_filtros_combinados():
    resultados = buscar_alimentos_db(
        es_vegano=True,
        sin_gluten=True,
        proteinas_min=8,
    )
    assert len(resultados) > 0
    for alimento in resultados:
        assert alimento["es_vegano"]
        assert alimento["sin_gluten"]
        assert alimento["proteinas_g"] >= 8


def test_limite_respetado():
    assert len(buscar_alimentos_db(limite=5)) == 5


def test_sin_filtros_devuelve_orden_alfabetico():
    resultados = buscar_alimentos_db()
    nombres = [a["nombre"] for a in resultados]
    assert nombres == sorted(nombres)


def test_obtener_alimento_por_id():
    manzana = buscar_alimentos_db(nombre="Manzana")[0]
    alimento = obtener_alimento_db(manzana["id"])
    assert alimento is not None
    assert alimento["nombre"] == "Manzana"
    assert alimento["descripcion"]  # el seeder cargó la descripción
    assert alimento["es_vegano"] is True


def test_obtener_alimento_inexistente():
    assert obtener_alimento_db(999999) is None


# ---------- Tools de LangChain (wrappers sobre las consultas) ----------

def test_tool_buscar_alimentos_devuelve_json():
    resultado = tool_buscar_alimentos.invoke({"nombre": "arroz", "limite": 5})
    datos = json.loads(resultado)
    assert isinstance(datos, list)
    assert len(datos) > 0
    assert all("arroz" in a["nombre"].lower() for a in datos)


def test_tool_buscar_alimentos_con_filtros_dietarios():
    resultado = tool_buscar_alimentos.invoke({"sin_lactosa": True, "limite": 20})
    datos = json.loads(resultado)
    assert len(datos) > 0
    assert all(a["sin_lactosa"] for a in datos)


def test_tool_obtener_alimento_existente():
    manzana = buscar_alimentos_db(nombre="Manzana")[0]
    resultado = tool_obtener_alimento.invoke({"id": manzana["id"]})
    datos = json.loads(resultado)
    assert datos["nombre"] == "Manzana"


def test_tool_obtener_alimento_inexistente():
    resultado = tool_obtener_alimento.invoke({"id": 999999})
    datos = json.loads(resultado)
    assert "error" in datos
