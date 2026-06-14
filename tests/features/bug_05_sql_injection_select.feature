# language: es
Característica: Bug 3A - Concatenar input en SELECT
  Como cadete
  Quiero ver el bug del SQL Injection clásico
  Para aprender OWASP Top 10

  Escenario: El endpoint arma el SELECT concatenando el input del usuario
    Dado que el server de RedTeam Lab está corriendo
    Cuando leo el código de la función "api_dbbuilder_consultar"
    Entonces la query SQL se arma con f-string o concatenación (+)
    Y NO usa parámetros preparados (?) o placeholders
