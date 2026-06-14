# language: es
Característica: Bug 1B - URL mal concatenada con query params
  Como cadete
  Quiero ver el bug de concatenación mal armada
  Para aprender cómo se filtra info con un query mal puesto

  Escenario: La URL armada por el operador contiene el parámetro mal escapado
    Dado que visito la página "/static/dbbuilder.html"
    Cuando el operador y el servidor arman una URL con la plantilla y nombre bandas
    Y la plantilla se mete en el medio de un template string con backticks
    Entonces la URL final contiene "${nombre}&limite=${limite}"
    Y ese patrón debería ser seguro
