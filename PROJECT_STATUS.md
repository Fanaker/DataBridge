# Estado — DataBridge v1.0.0

- Implementado: ETL CSV/JSON, validación, idempotencia, rechazo y auditoría, CSV export, dashboard de seis vistas, PostgreSQL DDL y sincronización opcional.
- Verificado: compilación Python, `node --check`, 4 pruebas Pytest, respuestas de API, renderizado de 6 pantallas sin errores JavaScript.
- Capturas: frontend ejecutado en navegador con respuestas exportadas del API real (el sandbox bloquea navegación directa localhost de Chromium); visualizaciones respaldadas por dataset sintético.
- No verificado: ejecución real de Docker/PostgreSQL por falta de servidor Docker disponible en el entorno.
- Limitaciones: API demo en SQLite; PostgreSQL solo réplica opcional; feed JSON simula una API de terceros; no hay servicio en la nube.
