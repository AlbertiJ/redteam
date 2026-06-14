# language: es
Característica: Bug 5A - Stack trace visible en errores
  Como cadete
  Quiero ver el bug del stack trace filtrado al cliente
  Para aprender que en producción NUNCA se muestra el stack al usuario

  Escenario: Cuando hay un error, el server devuelve el stack trace completo
    Dado que el server de RedTeam Lab está corriendo
    Cuando hago GET a "/api/v1/endpoint_que_falla"
    Entonces la respuesta NO debería contener "Traceback (most recent call last)"
    Y NO debería contener la ruta interna del servidor
