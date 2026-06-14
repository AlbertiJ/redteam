# language: es
Característica: Bug 2A - No validar input vacío
  Como cadete
  Quiero ver el bug del input vacío que el server acepta
  Para entender por qué validar SIEMPRE es importante

  Escenario: El endpoint acepta un nombre vacío y devuelve 200
    Dado que el server de RedTeam Lab está corriendo
    Cuando hago POST a "/api/v1/dbbuilder/crear" con nombre ""
    Entonces el código de respuesta NO debería ser 200
    Y debería ser 400 o 422
