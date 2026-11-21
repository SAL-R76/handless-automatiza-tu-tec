# Handless · E4: pruebas funcionales automatizadas en la nube

## Alcance y evidencia

El flujo `.github/workflows/e4-live.yml` ejecuta `scripts/test_live_e4.py` **contra la URL pública real** `https://handless.onrender.com`, utilizando una contraseña de demostración almacenada en un *secreto del repositorio*. Es una prueba técnica reproducible; **no** sustituye las cinco pruebas de usabilidad con personas reales ni el cuestionario SUS.

El reporte JSON (artefacto `handless-e4-resultados-publicos`) registra resultados aprobados/fallidos, tiempos de respuesta por operación y el folio ficticio creado. No incluye contraseñas ni tokens de acceso.

## Antes de ejecutarla

1. Verifica que `https://handless.onrender.com/api/health` responda `status: ok`.
2. Ingresa al repositorio → **Settings → Secrets and variables → Actions → New repository secret**.
3. Usa exactamente el nombre `E4_DEMO_PASSWORD` y como valor la **contraseña que actualmente funciona** para los cuatro usuarios ficticios `jefatura`, `coordinacion`, `tecnico` y `planeacion`. No escribas la contraseña en el repositorio, en el chat ni en capturas de pantalla.
4. Abre **Actions → E4 · pruebas en Handless (Render) → Run workflow → Run workflow**. El archivo solo se ejecuta bajo demanda (**workflow_dispatch**) y no con cada `push`.
5. Espera a que termine, abre la ejecución, revisa el estado de la tarea y descarga **Artifacts → handless-e4-resultados-publicos**. Conserva el JSON y una captura de la ejecución para la E4.

**Atención:** cada ejecución crea **una solicitud correctiva ficticia y una verificación preventiva ficticia** en la base real de demostración. No ejecutes repetidamente si no necesitas nuevas evidencias. Para minimizar consecuencias no se borra ni modifica información de usuarios reales, y las nuevas entradas se identifican como `QA-E4`.

## Pruebas incluidas

- API con estado `ok`, interfaz HTTP disponible.
- Rechazo de consultas sin autenticación (`401`).
- Autenticación, identidad y rol de los cuatro perfiles.
- Rechazo de creación y asignación por perfiles sin permiso (`403`).
- Solicitud correctiva con folio generado y bloqueo de cierre anticipado (`409`).
- Asignación, intervención técnica, rechazo por jefatura, retrabajo, aprobación y cierre.
- Consulta para Planeación, bitácora de la orden, descarga CSV y métricas.
- Consulta del resumen SUS **sin insertar respuestas inventadas**.
- Política de formatos del procedimiento `TecNM-AD-PO-001`.
- Verificación preventiva `-01` y programa preventivo `-03`.

## Si falla

- **Falta el secreto:** comprueba que se creó como **Repository secret**, no como variable normal.
- **401 al iniciar sesión:** puede que la contraseña de las cuentas ya creadas en la base no coincida con la variable de entorno actual de Render. Cambiar `DEMO_PASSWORD` tras la primera inicialización no modifica contraseñas existentes.
- **502 / 503 / timeout:** Render Free puede tardar en despertar. La prueba reintenta la primera petición de salud; repite manualmente si hay una interrupción externa.
- **Falló una transición:** revisa el JSON adjunto y los logs de la ejecución. Reporta el fallo como evidencia, no lo sustituyas por un resultado inventado.

## Declaración de validez

Hasta que la ejecución de GitHub Actions termine y se descarguen las evidencias, el estado es **preparado, no ejecutado**. Los resultados de laboratorio de E4 existentes son independientes de los resultados de la aplicación pública. La evaluación SUS de cinco participantes y las métricas antes/después con personas reales siguen pendientes.
