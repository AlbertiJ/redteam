# language: es
Característica: Bug 3B - INSERT sin prepared statements
  Como cadete
  Quiero ver el bug del INSERT vulnerable
  Para aprender que TODA query con input del usuario debe ser parametrizada

  Escenario: El lab enseña que un INSERT vulnerable concatena valores
    Dado que leo el código del RedTeam Lab
    Cuando busco "INSERT INTO" en el código
    Entonces el código de RedTeam Lab DEBE usar placeholders (?) en TODOS los INSERT
    Y NUNCA debe concatenar valores con + str() ni con f-strings
