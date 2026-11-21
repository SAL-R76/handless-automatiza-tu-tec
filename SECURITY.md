# Seguridad — límite del prototipo educativo

Handless E4 no está autorizado para procesos institucionales reales. Los datos, usuarios y roles semilla son ficticios y las credenciales de demostración son compartidas. Antes de producción deben implementarse SSO institucional, segregación de acceso por unidad, TLS, CSRF/cookies seguras, controles antispam, migraciones revisadas, respaldo/recuperación, retención legal y auditoría inalterable externa. Los tokens de ejemplo no constituyen un sistema de identidad certificado.

No registrar datos personales reales, credenciales, evidencias de contratos, ubicaciones sensibles o documentos internos en el repositorio de GitHub.

## Acceso público opcional a la demostración

Con `PUBLIC_DEMO_ENABLED=true`, cualquier visitante puede pedir una sesión como una de las cuatro cuentas ficticias (`jefatura`, `coordinacion`, `tecnico`, `planeacion`) y realizar las acciones de ese rol. **Este mecanismo no es autenticación de identidad**; es intencionalmente público y únicamente apto para un entorno con datos ficticios. Los registros se comparten entre visitantes y pueden ser modificados por otros visitantes. El endpoint `/api/public-demo/login` devuelve una sesión firmada y nunca devuelve `DEMO_PASSWORD` ni `SESSION_SECRET`. Si no se habilita `PUBLIC_DEMO_ENABLED`, responde 404.

Para reducir riesgos: usa base de datos exclusiva para la demostración, no introduzcas información real, evita utilizarla en producción, monitorea el consumo del plan gratuito y desactiva el flag después de la evaluación. Este prototipo no tiene limitación avanzada de peticiones ni aislamiento de registros por visitante.

El secreto `E4_DEMO_PASSWORD` existe solo en GitHub Actions para pruebas automatizadas; no está disponible en el backend de Render. Las variables de Render deben configurarse allí por separado.
