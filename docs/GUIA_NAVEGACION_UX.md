# Handless · Rediseño UX orientado a tareas (26 de noviembre de 2026)

> Prototipo académico para el Instituto Tecnológico de Matehuala. No representa una plataforma oficial del TecNM.

## Problema observado

La navegación anterior distribuía muchas funciones al mismo nivel, mostraba numerosos indicadores antes de las acciones importantes y obligaba a descubrir manualmente cuál era el siguiente paso. Se rediseñó **la navegación**, no el procedimiento institucional.

## Cambios implementados

1. **Inicio adaptado al rol**: pregunta «¿Qué necesitas hacer hoy?», muestra tres accesos directos con verbos claros y expone de inmediato las tareas que requieren atención.
2. **Mis tareas**: bandeja exclusiva con expedientes sobre los que el rol puede actuar. Cada fila explica la siguiente acción y abre el expediente.
3. **Navegación priorizada**: Inicio → Mis tareas → Solicitudes → Mantenimiento preventivo/Informes (según permisos). Avisos permanece accesible en la navegación y el encabezado; «Evaluación SUS» y «Acerca de» quedan en una franja secundaria.
4. **Expedientes guiados**: ruta de navegación y bloque «¿Qué sigue?» según perfil y estado.
5. **Solicitudes**: búsqueda destacada, total de resultados y botón «Nueva solicitud» para Jefatura.
6. **Resumen del proceso**: etapas de mantenimiento como accesos filtrados, sin desplazar las acciones principales al final de una página extensa.
7. **Diseño adaptable**: tarjetas de acción en una columna en móvil; navegación principal desplazable horizontalmente si no cabe en la pantalla, sin ocultar funciones de su rol.
8. **Accesibilidad básica**: botones con texto, `aria-label` en elementos pertinentes, indicador de página actual y estilos visibles de enfoque al usar teclado.

## Guía rápida por rol

| Perfil | Primera acción en Inicio | Otras rutas |
| --- | --- | --- |
| Jefatura | Registrar una falla | Dar visto bueno → Mis tareas; consultar solicitudes |
| Coordinación | Asignar y cerrar órdenes → Mis tareas | Programa preventivo; indicadores |
| Técnico | Atender mis órdenes → Mis tareas | Consultar expedientes; avisos |
| Planeación | Consultar informes | Ver órdenes cerradas; avisos |

### Flujo a demostrar

1. Entrar con un perfil de prueba.
2. Verificar que la pantalla de Inicio describa su actividad en lenguaje cotidiano.
3. Abrir la acción principal; para Jefatura, registrar un reporte ficticio.
4. Cambiar a Coordinación y localizar en «Mis tareas» la solicitud recibida.
5. Abrir el expediente y leer «¿Qué sigue?» antes de realizar la asignación.
6. Repetir con el Técnico, luego Jefatura (Vo.Bo.) y finalmente Coordinación (cierre).
7. Como Planeación, consultar la orden cerrada.

Las recomendaciones automáticas, notificaciones y controles de aprobación se mantienen en el **backend**; este cambio solo modifica el modo de descubrir y usar las funciones.

## Protocolo de validación de usabilidad pendiente

Este rediseño responde a una observación cualitativa de un colega, no a un resultado medido. Para verificar que la navegación es más intuitiva, invita a cinco personas distintas y mide, con datos ficticios y sin registrar información personal:

- Si encuentran la primera acción de su perfil sin ayuda.
- Cantidad de clics hasta abrir una solicitud o una tarea asignada.
- Tiempo hasta completar la tarea solicitada.
- Confusiones, errores y rutas equivocadas.
- Encuesta SUS tras completar la tarea.

Comparar contra el diseño anterior solo cuando se disponga de medidas comparables, no afirmar mejoras numéricas sin evidencia. La última decisión de diseño podría ajustarse tras las pruebas.

## Límites

El acceso público mediante `PUBLIC_DEMO_ENABLED=true` permite actuar sobre registros ficticios compartidos. No se utiliza con datos reales. El rediseño no cambia autenticación, reglas de negocio, base de datos, roles ni aprobaciones institucionales.
