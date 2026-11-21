# E4: pruebas funcionales, métricas y estudio SUS

## Pruebas de API ejecutadas

- Comando: `PYTHONPATH=. pytest tests -q`
- Resultado de la sesión de generación: **32 passed**.
- Los casos `test_cpXX` se corresponden con la matriz E2; los demás cubren autenticación, errores y cálculo SUS.
- El diseño usa datos sintéticos y bases efímeras aisladas: no altera registros reales.

## Benchmark técnico

Ejecuta `PYTHONPATH=. python scripts/benchmark.py`; guarda el resultado en `docs/resultados_e4.json`.

> Es una medición del backend en proceso local. No demuestra rendimiento en internet ni ahorro de tiempo humano. El AS-IS de E1 era un **escenario simulado**, no una medición empírica.

## Protocolo SUS con al menos cinco participantes reales

1. Reclutar cinco voluntarios distintos. Informar del fin académico, pedir consentimiento y **no recopilar nombres ni números de control** en esta app.
2. Entregar a cada persona un código anónimo U-01, U-02,... U-05. Conservar por separado el consentimiento, si se requiere.
3. Registrar fecha y equipo de prueba sin datos personales. La tarea estandarizada es: "desde el rol jefatura, registra una falla ficticia completa, anota el folio y comprueba su estado".
4. Cronometrar desde que lee la tarea hasta que termina. Marcar si completó sin ayuda.
5. Inmediatamente después, abrir `Evaluación SUS` y responder **las diez afirmaciones en orden** (1–5; no modificar enunciados en mitad del estudio).
6. Calcular puntuación SUS: suma de (respuesta - 1) en preguntas impares y (5 - respuesta) en pares, multiplicada por 2.5. La aplicación lo calcula automáticamente.
7. Reportar las cinco puntuaciones individuales, promedio, número de personas que terminaron ≤240 s, incidencias y modificaciones UX sugeridas. Meta E2: ≥4/5 terminan sin ayuda en ≤4 min. Meta de guía para SUS: promedio ≥70.
8. Distinguir **no realizado** de **0**: si faltan usuarios no existe puntuación de resultado.

## Datos antes y después

- **Antes E1:** 32 solicitudes/mes, 18 min de captura y otras duraciones son *supuestos académicos*. No son cronometrajes certificados.
- **Después E4 técnico:** medimos creación de 100 folios, consultas, errores rechazados, bloqueos de cierre, integridad y exportación en backend (JSON).
- **Después E4 usuario:** solo se podrá reportar tras completar la sesión de cinco usuarios con cronómetro/SUS; no completar campos con datos fabricados.
- **Comparación válida futura:** medir al menos 10–20 trámites manuales en el campus y 10–20 equivalentes con la aplicación (mismo alcance de tarea, mismos participantes o grupos comparables).

## Formato de captura

Usa `docs/registro_sus_5_usuarios.csv` (sin datos). No se acepta una fila como realizada hasta que se registra la respuesta real.
