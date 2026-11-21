# Handless E4 · Publicación gratuita (GitHub + Neon + Render)

Este proyecto académico tiene frontend React y backend FastAPI integrados en una sola imagen Docker. No es un archivo HTML que se abre localmente. El despliegue público puede hacerse con **Web Service Free de Render** y **PostgreSQL Free de Neon**. No contrates servicios pagos para seguir esta guía.

> **Estado:** el código está en GitHub. Este documento describe pasos para que el propietario configure los servicios externos. No implica que ya se haya desplegado la aplicación.

## 1. Distribución y límites

| Componente | Servicio | Costo de partida |
| --- | --- | --- |
| Código y pruebas | GitHub, rama `main` | Gratis para este uso |
| React + FastAPI (un solo servicio Docker) | Render Web Service, instancia **Free** | $0 dentro de sus cuotas |
| Datos persistentes | Neon PostgreSQL, plan **Free** | $0 dentro de sus cuotas |

**Por qué no usar SQLite en Render:** el disco local del plan Free es efímero; los datos pueden perderse si se reinicia el servicio. La base PostgreSQL gratuita de Render solo dura 30 días. Neon Free es más útil para conservar resultados de E4.

**Atención:** Render suspende temporalmente un servicio Free tras 15 minutos sin solicitudes; la primera carga al despertar puede tardar aproximadamente un minuto. Vigila los límites de la cuenta; no autorices un upgrade de pago.

Fuentes oficiales: https://render.com/docs/free · https://render.com/docs/web-services · https://neon.com/pricing

## 2. Crear base de datos gratuita en Neon

1. Entra a https://console.neon.tech/ y crea una cuenta.
2. Elige **Free** y crea un proyecto llamado `handless-e4`. La región puede ser la más cercana disponible a la región de Render.
3. Abre **Connect** y copia la **cadena completa de conexión PostgreSQL** (con SSL, típicamente incluye `sslmode=require`). 
4. Guarda esa cadena en un gestor de contraseñas; **no la subas a GitHub ni la pegues en documentos, chat o capturas**. El backend crea las tablas al iniciar.

## 3. Crear Web Service gratuito en Render, sin Blueprint

1. Entra en https://dashboard.render.com y elige **New → Web Service**. **No elijas Blueprint**.
2. Conecta GitHub a Render y autoriza el repositorio privado `SAL-R76/handless-automatiza-tu-tec`.
3. Elige el repositorio, rama `main`. Configura:

| Campo en Render | Valor |
| --- | --- |
| Name | `handless-e4` o nombre disponible |
| Region | Próxima a Neon |
| Language/Runtime | `Docker` |
| Root Directory | Dejar vacío |
| Dockerfile Path | `./Dockerfile` |
| Instance Type | **Free** |
| Health Check Path | `/api/health` |

4. En las variables de entorno agrega **tres secretos**:

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | URL PostgreSQL privada copiada desde Neon |
| `SESSION_SECRET` | Cadena aleatoria larga, distinta de la contraseña |
| `DEMO_PASSWORD` | Contraseña propia, segura, para los cuatro usuarios ficticios |

No incluyas secretos en el código ni en GitHub. `DEMO_PASSWORD` se usa al crear las cuentas por primera vez; cambiarla después no modifica automáticamente contraseñas existentes.

5. Confirma que **Compute** indique `Free` y **$0** antes de pulsar **Create Web Service**. Si solo aparecen planes pagos, detente: no aceptes el cargo.

Render construirá la interfaz React (Vite) y la API FastAPI desde el `Dockerfile` raíz del repositorio. No es necesario crear un Static Site aparte.

## 4. Verificación

1. Abre la URL real de Render (formato `https://<nombre>.onrender.com`); debe aparecer Handless.
2. En `/api/health` debe responder JSON con `status: ok`.
3. Accede con `jefatura` y tu `DEMO_PASSWORD`; crea una solicitud ficticia y anota el folio.
4. Accede con `coordinacion`, asigna la orden; con `tecnico`, registra el trabajo; con `jefatura`, da el Vo.Bo.; con `coordinacion`, cierra; con `planeacion`, exporta el CSV.
5. Comprueba rechazo de cierre sin Vo.Bo. (409) y denegación a un rol incorrecto (403).
6. Ejecuta con **cinco personas reales** las tareas UX y el cuestionario SUS; conserva respuestas verificables y anonimiza participantes.
7. Añade a la entrega E4 la URL del repositorio, URL pública real, captura de GitHub Actions, capturas de flujo y resultados que realmente observaste.

## 5. Alternativas y advertencias

- GitHub Pages solo aloja un frontend estático; no ejecuta FastAPI ni guarda datos como este proyecto lo requiere.
- La configuración `render.yaml` del repositorio se adaptó a un Web Service Free y **sin base de datos de pago**, pero el método manual anterior es más claro.
- **No uses información real del TecNM** ni credenciales institucionales; el prototipo es una demostración académica.
- El plan gratuito puede cambiar y está sujeto a límites; consulta siempre la pantalla de precios antes de confirmar.

