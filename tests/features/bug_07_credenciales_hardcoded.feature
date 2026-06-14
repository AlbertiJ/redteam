# language: es
Característica: Bug 4A - Credenciales hardcoded
  Como cadete
  Quiero ver el bug de las credenciales en el código
  Para aprender que NUNCA se hardcodean passwords

  Escenario: El código tiene DB_PASSWORD y API_KEY en variables de entorno MAL cargadas
    Dado que leo el código del RedTeam Lab
    Cuando busco la palabra "PASSWORD" en el código
    Entonces aparece como "os.environ.get('DB_PASSWORD')" SIN valor por defecto
    Y NO como "os.environ.get('DB_PASSWORD', 'admin123')"
    Y NO como "DB_PASSWORD = 'admin123'  # MAL"
