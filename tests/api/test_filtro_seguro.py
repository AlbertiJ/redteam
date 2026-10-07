import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from filtro_seguro import evaluar_filtro  # noqa: E402

FILA = {"anio": 1973, "nombre": "Dark Side", "pais": None}


@pytest.mark.parametrize("filtro, esperado", [
    ("anio = 1973", True),
    ("anio == 1973 and nombre = 'Dark Side'", True),
    ("anio > 2000", False),
    ("nombre LIKE '%side%'", True),
    ("nombre LIKE 'X%'", False),
    ("anio IN (1973, 1980)".replace("IN", "in"), True),
    ("NOT anio = 1", True),
    ("1=1", True),                       # tautologia: sigue sirviendo para practicar
    ("anio = 1 OR 1=1", True),
    ("nombre = 'a=b'", False),           # el '=' dentro del texto no se toca
    ("anio > 'x'", False),               # tipos que no se comparan: no coincide
    ("pais = NULL", True),
])
def test_filtros_validos(filtro, esperado):
    assert evaluar_filtro(filtro, FILA) is esperado


@pytest.mark.parametrize("filtro", [
    "__import__('os').system('id')",
    "().__class__.__bases__[0].__subclasses__()",
    "open('/etc/passwd')",
    "[x for x in range(9)]",
    "anio.real > 0",
    "lambda: 1",
    "desconocida = 1",
    "a" * 400,
    "((((((" * 200,
])
def test_filtros_peligrosos_se_rechazan(filtro):
    with pytest.raises(ValueError):
        evaluar_filtro(filtro, FILA)
