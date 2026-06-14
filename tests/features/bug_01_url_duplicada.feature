# language: es
Característica: Bug 1A - URL duplicada en dbbuilder.html
  Como cadete
  Quiero que el bug de la URL duplicada sea detectable
  Para verificar que el lab enseña la falla correcta

  Escenario: El frontend construye la URL con el host duplicado
    Dado que visito la página "/static/dbbuilder.html"
    Cuando el frontend arma la URL para consultar datos
    Entonces la URL resultante empieza con "${host}/api/"
    Y no contiene "${host}${host}"
