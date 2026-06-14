# language: es
Característica: Bug 4B - Token que no expira
  Como cadete
  Quiero ver el bug del token sin expiración
  Para aprender que un token válido para siempre es un riesgo

  Escenario: Si el lab tiene generación de tokens, no debe tener expiración
    Dado que leo el código del RedTeam Lab
    Cuando busco la función que genera tokens
    Entonces si existe, NO debe tener expires_delta ni exp en el payload
