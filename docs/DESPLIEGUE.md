# Publicación de Handless · GitHub + Render

## 1. Qué es cada servicio

**GitHub** almacena el código y ejecuta la verificación automática. **Render** ejecuta el servidor Python, construye la interfaz React y aloja PostgreSQL; su URL es la que se mostrará al docente. GitHub Pages **no** basta para una API FastAPI con base de datos.

## 2. Subida a GitHub (Windows)

Abre el ZIP, extrae su carpeta y abre PowerShell en la raíz `handless-e4-repo`.

Si tienes GitHub CLI y has iniciado sesión con `gh auth login`:

```powershell
git init
git branch -M main
git add .
git commit -m "feat: E4 Handless API React pruebas y calidad"
gh repo create handless-automatiza-tu-tec --private --source=. --remote=origin --push
```

Si el repositorio ya existe, usa su **URL real** (no la inventes):

```powershell
git remote add origin https://github.com/TU_USUARIO/handless-automatiza-tu-tec.git
git push -u origin main
```

Si se conectó GitHub directamente en ChatGPT, es posible publicar el repositorio desde el conector autorizado. Ninguna publicación remota se produce por tener este ZIP.

## 3. Despliegue en Render

1. Inicia sesión en Render con GitHub.
2. `New` → `Blueprint` y selecciona el repositorio.
3. Revisa el archivo `render.yaml`: **web Docker** y **PostgreSQL** administrado. No aceptar cargos sin comprobarlos.
4. Ajusta `DEMO_PASSWORD` al secreto que usarás en la demostración; no lo guardes en Git.
5. Confirma el despliegue y copia la URL asignada. En ella debe cargar la pantalla de inicio de sesión.
6. Abre `https://TU_URL_REAL/api/health`. Debe responder `status: ok`.
7. Haz una solicitud ficticia y sigue el flujo por los cuatro roles. Exporta el CSV y conserva capturas de pantalla como evidencia.
8. Ejecuta las cinco pruebas reales de usabilidad y aplica SUS, dejando intactos los resultados originales.

**Advertencia:** este proyecto es una muestra educativa; las cuentas compartidas para demostración no son apropiadas para una operación institucional real.

## 4. Variables de entorno

- `DATABASE_URL`: cadena de conexión PostgreSQL del servicio administrado. Render la inyecta mediante `fromDatabase`.
- `SESSION_SECRET`: valor largo, aleatorio, para firmar sesiones. Render lo genera en Blueprint.
- `DEMO_PASSWORD`: contraseña de las cuatro identidades ficticias **al iniciar una base nueva**. No se actualizan las contraseñas de usuarios existentes cuando cambias esta variable.

## 5. Pruebas antes de enseñar

- Confirmar que `Actions` de GitHub tiene la ejecución en verde.
- `GET /api/health` devuelve 200.
- Probar con `jefatura` → solicitud con folio → `coordinacion` asigna → `tecnico` realiza trabajo → `jefatura` otorga Vo.Bo. → `coordinacion` cierra → `planeacion` exporta.
- Confirmar que el cierre sin aprobación devuelve 409 y una acción con el rol incorrecto devuelve 403.
- Verificar que una segunda encuesta con el mismo código de participante devuelve 409.

## 6. Anexos de entrega

Guarda el enlace al repositorio, enlace a Render, comprobante de Github Actions, capturas de roles, resultados de tests y respuestas auténticas de cinco evaluadores. No presentes como realizada una publicación o prueba que no hayas ejecutado.
