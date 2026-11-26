# Handless · Automatización fase 1 (prototipo académico)

**Alcance:** facilitar la operación de mantenimiento con reglas explícitas, trazabilidad y avisos. Esta solución no es un sistema oficial del TecNM; todas las cuentas y registros son ficticios.

## Fundamentación en TecNM-AD-PO-001

Documento de referencia: https://www.tecnm.mx/dir_calidad/gestion_calidad/TecNM-AD-PO-001.pdf?archivo=53

| Actividad del procedimiento | Implementación académica | Intervención humana que se conserva |
| --- | --- | --- |
| Etapa B1 y B2: solicitud y entrega a área de mantenimiento | Al recibir -02, el backend genera folio único, deja evento en bitácora, calcula sugerencia y registra aviso para Coordinación | Jefatura describe la incidencia; Coordinación revisa y decide |
| Etapa 3: asigna orden de trabajo -04 | Sugiere área y prioridad con reglas; al confirmar asignación se genera número OT y aviso al técnico | Coordinación determina recursos, técnico, ruta y autorización; el sistema no compra |
| Etapa 5: verificación y evaluación del servicio | Tras marcar una intervención terminada, emite aviso a Jefatura; si se rechaza, avisa al técnico | Jefatura acepta o rechaza tras verificar; no hay aprobación automática |
| Etapa 6: registro del mantenimiento | El cierre autorizado genera fecha, bitácora y aviso interno a Planeación; permite exportar CSV de órdenes cerradas | Coordinación cierra después de Vo.Bo.; el aviso no equivale a entrega institucional formal |

## Motor de reglas

Módulo: `backend/automation.py`.

Reglas **demostrativas y editables**:
- `RIESGO_EXPLICITO`: incidente descrito con riesgo explícito → prioridad *urgente* sugerida.
- `INTERRUPCION_SERVICIO`: fallo que interrumpe el uso del equipo o de una clase → *alta* sugerida.
- `INCIDENCIA_MENOR`: detalle menor descrito explícitamente → *baja* sugerida.
- `PRIORIDAD_GENERAL`: sin criterio especial → *media* sugerida.

También se propone destino entre Centro de Cómputo, Mantenimiento de Equipo y Recursos Materiales en función de palabras clave del activo y la falla. **Es una propuesta del equipo de desarrollo, no una tabla de prioridades autorizada por el TecNM.** La prioridad final y la asignación las confirma Coordinación.

El resultado se almacena en la bitácora del expediente con `action=sugerencia_automatica`, `actor_role=sistema`, identificador de regla y explicación. El valor real de `ticket.priority` no cambia por la sugerencia.

## Avisos internos automáticos

Los eventos generan registros persistentes en la tabla `notifications`, creada por SQLAlchemy sin modificar las tablas preexistentes. La bandeja `Avisos` consulta `GET /api/notifications` y solo presenta los avisos del rol activo.

| Evento | Rol destinatario |
| --- | --- |
| Solicitud recibida | Coordinación |
| Orden asignada | Técnico |
| Intervención terminada, pendiente de Vo.Bo. | Jefatura |
| Servicio rechazado: retrabajo | Técnico |
| Vo.Bo. aprobado | Coordinación |
| Orden cerrada | Planeación |

No hay envío por correo, SMS, mensajería ni programaciones de recordatorios. Los avisos son **internos** y no sustituyen comunicaciones oficiales.

## Evaluación técnica

`tests/test_automation.py` cubre reglas, auditoría de la sugerencia, segmentación de avisos por rol, asignación humana, visto bueno y rechazo. El benchmark `scripts/benchmark.py` comprueba el historial completo, incluida la nueva sugerencia automática.

Estas pruebas no demuestran ahorro de tiempo humano ni satisfacción SUS. Para reclamar una mejora efectiva hay que comparar el procedimiento manual con el automatizado, cronometrando tareas reales comparables y sin inventar resultados.

## Límites y riesgos

- Las clasificaciones son heurísticas; pueden errar. Deben ser revisadas antes de tomar decisiones.
- Las cuatro cuentas son públicas y compartidas si `PUBLIC_DEMO_ENABLED=true`, por lo que todos los visitantes de cada rol ven los mismos avisos y registros de prueba. No introducir datos reales.
- No existe aún programación duradera de recordatorios de vencimientos, SLA institucional, correo ni integración POA/PIA.
- No hay compras ni autorizaciones automáticas; se mantienen las restricciones del procedimiento TecNM-AD-PO-001.
- La identidad visual utiliza la paleta TecNM 2026 y un recurso gráfico de referencia; **no implica aval institucional**.
