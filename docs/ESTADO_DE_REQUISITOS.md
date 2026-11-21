# Trazabilidad E2 → E3 → E4

| Identificador | Estado técnico E4 | Evidencia | Limitación |
| --- | --- | --- | --- |
| RF-01 | Implementado | POST /api/tickets; CP-01 | Campos de prueba |
| RF-02 | Implementado | folios únicos DB; CP-02 | Nomenclatura académica |
| RF-03 | Implementado | POST /api/preventive; CP-03 | Lista -01 equivalente resumida |
| RF-04 | Implementado | POST /api/preventive/{id}/program; CP-04 | Borrador -03 sin aprobación |
| RF-05 | Parcial | Prioridad manual autorizada CP-05 | Falta motor de sugerencias configurables |
| RF-06 | Implementado | Asignación por destino CP-06 | Ruta inicial manual; no integración institucional |
| RF-07 | Implementado | Orden OT-... CP-07 | Equivalencia -04 simplificada |
| RF-08 | Implementado | Referencia obligatoria externa CP-08 | No ejecuta compras ni valida autorización oficial |
| RF-09 | Implementado | GET ticket y bitácora CP-09 | Alcance por rol |
| RF-10 | Parcial | Bitácora de eventos CP-10 | No implementa bandeja push o correo |
| RF-11 | Implementado | Intervención técnica CP-11 | Evidencia en texto, no multimedia |
| RF-12 | Implementado | Aprobación y rechazo CP-12 | Vo.Bo. de rol ficticio |
| RF-13 | Implementado | Cierre tras aprobación CP-13 | No firma electrónica formal |
| RF-14 | Implementado | Exportación CSV CP-14 | No conecta directamente POA/PIA |
| RF-15 | Implementado | Filtro por folio/área/activo CP-15 | Filtros avanzados limitados |
| RF-16 | Implementado | Métricas y conteos CP-16 | Muestra datos de prueba |
| RF-17 | Implementado | Bitácora solo lectura CP-17 | Un administrador DB externo puede alterar registros |
| RNF-01 | Probado en backend | CP-18, tests de rol | Sin SSO institucional |
| RNF-02 | Verificado sobre datos semilla | CP-19 | Evitar datos reales al probar |
| RNF-03 | Pendiente | Formulario SUS implementado | Faltan 5 personas reales y tiempos de tarea |
| RNF-04 | Pendiente de inspección | CSS responsive 360px | Compilación y prueba móvil aún no verificadas |
| RNF-05 | Probado localmente | benchmark 100 búsquedas | Medición de red local real pendiente |
| RNF-06 | Pendiente de auditoría | Label/foco base | Falta auditoría contrastes/teclado |
| RNF-07 | Probado | CP-02 y CP-24 | Concurrencia extrema no medida |
| RNF-08 | Pendiente | render.yaml | No hay URL pública ni uptime medido |
| RNF-09 | Pendiente | PostgreSQL previsto | Plan de recuperación por comprobar |
| RNF-10 | Probado en backend | CP-27 | Auditoría de campo sintético |
| RN-01 a RN-07 | Implementadas en reglas de negocio principales | CP-01..14 | Control institucional sigue humano |
| RN-08 | Parcial | Política CP-28 y no endpoint de borrado | Retención física a un año sin garantizar |

## Significado

**Implementado:** existe lógica y test automático. **Parcial:** hay soporte básico pero faltan componentes del requisito. **Pendiente:** no se debe afirmar cumplimiento hasta ejecutar la validación. Esta tabla es una declaración de alcance honesta para E4.
