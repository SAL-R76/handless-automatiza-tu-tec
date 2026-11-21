# Handless · Automatiza tu Tec · E4

**Gestión de mantenimiento preventivo y correctivo**, basada en el procedimiento TecNM-AD-PO-001 del Tecnológico Nacional de México (campus Matehuala), como **prototipo académico**, no sistema oficial.

> **Estado de entrega:** aplicación E4 publicada en [Render](https://handless.onrender.com/) y código en GitHub. La ejecución [GitHub Actions #44872231317](https://github.com/SAL-R76/handless-automatiza-tu-tec/actions/runs/44872231317) acreditó 31/31 pruebas funcionales (antes de añadir el acceso público opcional). La evaluación de usabilidad con cinco usuarios reales continúa pendiente.

## Qué cambia respecto a E3

No es un `.html` abierto desde el disco. Ahora existe una aplicación cliente React + API FastAPI + persistencia SQL. Las reglas de permisos, asignación y visto bueno se verifican en el **servidor**. El mismo servicio entrega la interfaz y la API; el despliegue previsto usa PostgreSQL.

## Funciones

- **Jefatura:** registra solicitud correctiva -02, ve su folio y estado, acepta/rechaza el servicio, registra verificaciones preventivas -01.
- **Coordinación:** clasifica y asigna, emite orden -04, registra referencia de autorización externa sin comprar, prepara programa preventivo -03 y cierra tras Vo.Bo.
- **Técnico:** documenta trabajo, solicita aprobación y reinterviene ante rechazo.
- **Planeación:** consulta únicamente órdenes cerradas, indicadores y exporta CSV para POA/PIA.
- **Todas las funciones críticas:** bitácora con usuario, rol, fecha, cambio anterior y nuevo; rechazo de transiciones indebidas y bloqueo de folios duplicados.
- **Usabilidad:** formulario SUS de 10 preguntas con cálculo automático y código anónimo. No contiene respuestas inventadas.

## Requisitos

- Python 3.11+ / Node 22+ (o Docker).
- En local: SQLite. En nube: PostgreSQL mediante `DATABASE_URL`.

### Ejecutar en local (dos consolas)

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. La API está disponible en `http://localhost:8000/docs`.

**No hay contraseñas de demostración precargadas en la interfaz.** Para ejecutar el proyecto desde una base de datos nueva, configura las variables de entorno `DEMO_PASSWORD` y `SESSION_SECRET` con valores privados; la plantilla `.env.example` no contiene claves. Las cuentas ficticias son `jefatura`, `coordinacion`, `tecnico` y `planeacion`.

### Acceso libre de demostración (sin revelar contraseñas)

Para que cualquier visitante pueda entrar a la aplicación y escoger uno de los cuatro roles, entra a **Render → servicio Handless → Environment** y establece `PUBLIC_DEMO_ENABLED=true`. Vuelve a desplegar o reiniciar el servicio para aplicar la variable. La aplicación mostrará el botón **Entrar sin contraseña**. Por defecto esta capacidad está desactivada si la variable no existe.

La contraseña `DEMO_PASSWORD` permanece protegida **en Render** y se utiliza para crear las cuentas la primera vez; no se envía al navegador para permitir el acceso libre. El secreto de GitHub Actions `E4_DEMO_PASSWORD` se usa **solo para los tests de GitHub** y no se comparte automáticamente con Render.

**Advertencia:** cuando el acceso libre está activo, cualquier persona puede actuar como los cuatro roles, consultar y modificar los **registros compartidos** de la demostración. No uses datos personales, institucionales ni confidenciales. Deshabilita `PUBLIC_DEMO_ENABLED` en Render después de la revisión pública o si quieres bloquear accesos. Los endpoints con permisos siguen comprobando cada rol.

## Pruebas ejecutadas

```bash
PYTHONPATH=. pytest tests -q
PYTHONPATH=. python scripts/benchmark.py
```

Resultado de esta entrega: **32/32 tests automáticos aprobados**; benchmark reproducible en `docs/resultados_e4.json` (100 folios únicos, 100 búsquedas, cierres prematuros y accesos indebidos bloqueados). **El frontend no pudo instalarse/compilarse en el entorno de generación por inaccesibilidad de npm**: se incluye CI de GitHub para compilarlo cuando el repositorio se publique. No se ha medido aún la latencia desde internet.




### Verificación pública de E4

El usuario indicó que [Handless en Render](https://handless.onrender.com/) responde con `status: ok` en `/api/health`. Se añadió un flujo **manual**, distinto de las pruebas locales, para iniciar sesión con los cuatro roles y ejecutar un proceso completo con datos ficticios: [Actions → E4 · pruebas en Handless](../../actions/workflows/e4-live.yml). Requiere el **secreto de repositorio `E4_DEMO_PASSWORD`**. Se descarga un reporte JSON con resultados reales y tiempos de cada operación, sin contraseñas. **Ejecución #1 verificada: 31 pruebas aprobadas, 0 fallidas** ([GitHub Actions #44872231317](https://github.com/SAL-R76/handless-automatiza-tu-tec/actions/runs/44872231317), 21 de noviembre de 2026, 05:44 UTC). Se creó el folio ficticio `HLS-2026-00002`. El reporte `handless-e4-resultados-publicos` quedó guardado como artefacto de esa ejecución. Esta evidencia técnica **no sustituye** la evaluación SUS con cinco personas reales. Cada ejecución crea una solicitud y una verificación preventiva ficticias. Consulta [la guía](docs/E4_PRUEBAS_ONLINE.md).

## E2/E3: cobertura de requisitos

Cobertura técnico-funcional principal: RF-01..04, RF-06..09, RF-11..17; RF-05 (prioridad configurable: implementación parcial), RF-10 (avisos mediante bitácora, sin notificaciones push). RNF-01/02/07/10 se verifican en backend; RNF-03/04/06 requieren estudio/inspección UX; RNF-08/09 y RN-08 requieren infraestructura y procedimientos operativos. Véase `docs/ESTADO_DE_REQUISITOS.md`.

## Límites importantes

- Todos los perfiles, fallas, activos y autorizaciones son ficticios; la aplicación no se conecta a sistemas reales del TecNM.
- No implementa compras, firmas electrónicas con validez jurídica ni SSO del TecNM.
- El token de demostración es un mecanismo académico, **no** autenticación institucional. Antes de producción se requiere SSO, cookies seguras y controles de sesión reforzados.
- La política documental declara retención de un año, pero su garantía operativa, respaldos y acceso institucional requieren configuración y supervisión del cliente.
- El formulario SUS está listo, pero **faltan cinco personas reales y sus respuestas**: no se atribuyen participantes o puntajes ficticios a pruebas reales.
- Las mediciones E1 de tiempos son simulaciones: no se deben presentar como mejoras reales al comparar con benchmarks técnicos E4.

**Autor académico:** Juan Diego Rosas Vázquez · 24660281 · Fundamentos de Ingeniería de Software SCC-1007. **Consultora ficticia:** Handless · «Menos trámites. Más soluciones.»
