# language: es
Característica: Bug 2B - Tipo de dato incorrecto
  Como cadete
  Quiero ver el bug del límite como string
  Para aprender que los tipos importan

  Escenario: El endpoint falla con 500 cuando le pasás un string en vez de int
    Dado que el server de RedTeam Lab está corriendo
    Cuando hago GET a "/api/v1/dbbuilder/consultar?db=bandas&limite=uchos"
    Entonces el código de respuesta debería ser 400 o 422
    Y NO debería ser 500
