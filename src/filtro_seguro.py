"""Evaluador seguro para el parametro `filtro` de las DBs predefinidas.

Antes se usaba eval() con __builtins__ vacio, que se puede escapar y ejecutar codigo en el
servidor. Aca el texto se traduce de SQL basico a una expresion y se evalua recorriendo su
arbol (AST) con una lista blanca: solo comparaciones, and/or/not, columnas, numeros, textos,
listas de constantes y LIKE. Nada de llamadas, atributos ni indices.

Sigue siendo util para practicar: condiciones como `1=1` siguen funcionando (tautologias).
"""

from __future__ import annotations

import ast
import re

MAX_LARGO = 300

_COMPARADORES = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}
_TEXTO = r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""


def _like(valor, patron) -> bool:
    patron = re.sub(r"%+", "%", str(patron))[:100]
    rx = "".join(".*" if c == "%" else "." if c == "_" else re.escape(c) for c in patron)
    return re.fullmatch(rx, str(valor), re.IGNORECASE | re.DOTALL) is not None


def _traducir(filtro: str) -> str:
    """SQL basico -> sintaxis de expresion. No toca el contenido de los textos entre comillas."""
    filtro = re.sub(r"(\b[A-Za-z_]\w*)\s+LIKE\s+" + _TEXTO, r"like(\1, \2)", filtro, flags=re.IGNORECASE)
    partes = re.split(_TEXTO, filtro)
    for i in range(0, len(partes), 2):  # solo fuera de comillas
        p = partes[i].replace("<>", "!=")
        p = re.sub(r"(?<![<>=!])=(?!=)", "==", p)
        p = re.sub(r"\bAND\b", " and ", p, flags=re.IGNORECASE)
        p = re.sub(r"\bOR\b", " or ", p, flags=re.IGNORECASE)
        p = re.sub(r"\bNOT\b", " not ", p, flags=re.IGNORECASE)
        p = re.sub(r"\bNULL\b", "None", p, flags=re.IGNORECASE)
        p = re.sub(r"\bTRUE\b", "True", p, flags=re.IGNORECASE)
        p = re.sub(r"\bFALSE\b", "False", p, flags=re.IGNORECASE)
        partes[i] = p
    return "".join(partes).strip()


def _ev(nodo, fila):
    if isinstance(nodo, ast.Expression):
        return _ev(nodo.body, fila)
    if isinstance(nodo, ast.BoolOp):
        valores = (_ev(v, fila) for v in nodo.values)
        return all(valores) if isinstance(nodo.op, ast.And) else any(valores)
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.Not):
        return not _ev(nodo.operand, fila)
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub):
        return -_ev(nodo.operand, fila)
    if isinstance(nodo, ast.Compare):
        izq = _ev(nodo.left, fila)
        for op, comp in zip(nodo.ops, nodo.comparators):
            if type(op) not in _COMPARADORES:
                raise ValueError("operador no permitido")
            der = _ev(comp, fila)
            try:
                if not _COMPARADORES[type(op)](izq, der):
                    return False
            except TypeError:  # tipos que no se comparan: no coincide
                return False
            izq = der
        return True
    if isinstance(nodo, ast.Name):
        if nodo.id in fila:
            return fila[nodo.id]
        raise ValueError(f"columna desconocida: {nodo.id}")
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (str, int, float, bool, type(None))):
        return nodo.value
    if isinstance(nodo, (ast.Tuple, ast.List)):
        return tuple(_ev(e, fila) for e in nodo.elts)
    if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == "like"
            and len(nodo.args) == 2 and not nodo.keywords):
        return _like(_ev(nodo.args[0], fila), _ev(nodo.args[1], fila))
    raise ValueError("expresion no permitida")


def evaluar_filtro(filtro: str, fila: dict) -> bool:
    """True si la fila cumple el filtro. Lanza ValueError si el filtro no es valido o no esta permitido."""
    if len(filtro) > MAX_LARGO:
        raise ValueError("filtro demasiado largo")
    try:
        arbol = ast.parse(_traducir(filtro), mode="eval")
        return bool(_ev(arbol, fila))
    except (SyntaxError, RecursionError, MemoryError) as e:
        raise ValueError("filtro mal formado") from e
