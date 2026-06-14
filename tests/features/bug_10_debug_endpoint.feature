# language: es
Característica: Bug 5B - Endpoint /debug que filtra config sensible
  Como cadete
  Quiero ver el bug del endpoint /debug sin auth
  Para aprender que los endpoints de debug no deben estar en producción

  Escenario: El endpoint /api/v1/debug devuelve secretos sin autenticación
    Dado que el server de RedTeam Lab está corriendo
    Cuando hago GET a "/api/v1/debug" sin auth
    Entonces el código de respuesta NO debería ser 200 con secretos
    Y debería ser 401 (no autorizado) o 404 (no existe)
