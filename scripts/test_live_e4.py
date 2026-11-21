#!/usr/bin/env python3
"""Pruebas E4 de extremo a extremo contra Handless desplegado.

Ejecución MANUAL. Genera un ticket y una verificación preventiva ficticios
en la base de datos compartida. Nunca genera respuestas SUS ni muestra
contraseñas o tokens de sesión en reportes.
"""
import csv
import io
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.environ.get("HANDLESS_BASE_URL", "https://handless.onrender.com").rstrip("/")
PASSWORD = os.environ.get("E4_DEMO_PASSWORD", "")
REPORT = Path(os.environ.get("E4_REPORT_PATH", "artifacts/e4_live_report.json"))
records = []
folio = None


def demand(condition, description):
    if not condition:
        raise AssertionError(description)


def call(method, path, expected=200, token=None, payload=None):
    url = BASE + path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=40) as response:
            code, data, mime = response.status, response.read(2_000_000), response.headers.get("Content-Type", "")
    except HTTPError as exc:
        code, data, mime = exc.code, exc.read(2_000_000), exc.headers.get("Content-Type", "")
    if code != expected:
        # No escribimos respuestas completas: podrían contener datos o secretos.
        raise AssertionError(f"{method} {path}: HTTP {code}; se esperaba {expected}")
    if "text/csv" in mime:
        return data.decode("utf-8-sig")
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{method} {path}: JSON inválido") from exc
    return None


def test(label, method, path, status=200, token=None, payload=None, check=None):
    start = time.monotonic()
    try:
        result = call(method, path, status, token, payload)
        if check:
            check(result)
        records.append({"prueba": label, "resultado": "APROBADA", "duracion_ms": round((time.monotonic()-start)*1000)})
        print(f"[OK] {label}")
        return result
    except Exception as exc:
        records.append({"prueba": label, "resultado": "FALLIDA", "detalle": str(exc)[:280], "duracion_ms": round((time.monotonic()-start)*1000)})
        print(f"[FALLÓ] {label}: {str(exc)[:280]}", file=sys.stderr)
        raise


def wake_service():
    # Render Free puede necesitar despertarse. Solo repetimos la petición GET.
    for attempt in range(1, 9):
        try:
            return test("Disponibilidad de API", "GET", "/api/health",
                        check=lambda r: demand(r.get("status") == "ok", "health no devolvió status=ok"))
        except Exception:
            if attempt == 8:
                raise
            print(f"Reintentando disponibilidad (intento {attempt}/8)...")
            time.sleep(15)


def run():
    global folio
    demand(BASE == "https://handless.onrender.com", "Destino no autorizado para pruebas de esta entrega")
    demand(bool(PASSWORD), "Falta configurar el secreto E4_DEMO_PASSWORD en GitHub Actions")

    wake_service()
    test("Interfaz disponible", "GET", "/", check=lambda v: demand(
        isinstance(v, (dict, str)), "El servidor no entregó la interfaz"))
    # Nota: la API anterior puede devolver HTML; GET / se comprueba por HTTP 200.
    test("Solicitud sin autenticación rechazada", "GET", "/api/tickets", status=401)

    sessions = {}
    for role in ("jefatura", "coordinacion", "tecnico", "planeacion"):
        login = test("Inicio de sesión: " + role, "POST", "/api/login", payload={
            "username": role, "password": PASSWORD},
            check=lambda r, role=role: demand(
                r.get("user", {}).get("role") == role and bool(r.get("token")),
                "No devolvió usuario/rol/token válido"))
        sessions[role] = login["token"]
        test("Identidad y permisos: " + role, "GET", "/api/me",
             token=sessions[role],
             check=lambda r, role=role: demand(r.get("role") == role, "Rol incorrecto"))

    jefe, coord, tecnico, planeacion = (
        sessions["jefatura"], sessions["coordinacion"],
        sessions["tecnico"], sessions["planeacion"])

    test("Técnico no puede crear solicitudes", "POST", "/api/tickets",
         status=403, token=tecnico,
         payload={"area": "QA", "location": "Sala ficticia",
                  "asset": "Proyector ficticio", "description": "Revisión simulada sin datos personales",
                  "contact": "Persona ficticia"})

    team = test("Directorio de técnicos", "GET", "/api/users", token=coord)
    technicians = [member["id"] for member in team if member.get("role") == "tecnico"]
    demand(technicians, "No existe usuario técnico de prueba")

    marker = uuid.uuid4().hex[:10].upper()
    ticket = test("Alta de solicitud correctiva", "POST", "/api/tickets", 201, token=jefe,
                  payload={"area": "QA-E4 / Entorno ficticio",
                           "location": "Aula ficticia " + marker,
                           "asset": "Proyector simulado",
                           "description": "Prueba automatizada E4 con información completamente ficticia. Referencia " + marker,
                           "contact": "Evaluador ficticio"},
                  check=lambda r: demand(r.get("status") == "recibida" and r.get("folio", "").startswith("HLS-"),
                                         "Folio o estado inicial incorrecto"))
    ticket_id, folio = ticket["id"], ticket["folio"]
    print("Folio de demostración:", folio)

    test("Planeación no ve casos abiertos", "GET", f"/api/tickets/{ticket_id}",
         status=404, token=planeacion)
    test("Cierre prematuro bloqueado", "POST", f"/api/tickets/{ticket_id}/close",
         status=409, token=coord)
    test("Asignación por rol incorrecto bloqueada", "POST",
         f"/api/tickets/{ticket_id}/assign", status=403, token=jefe,
         payload={"technician_id": technicians[0]})

    test("Asignación de orden -04", "POST", f"/api/tickets/{ticket_id}/assign",
         token=coord,
         payload={"technician_id": technicians[0], "priority": "media",
                  "destination": "Recursos Materiales", "route": "interna"},
         check=lambda r: demand(r.get("status") == "asignada" and bool(r.get("order_number")),
                                "Asignación o número de orden incorrecto"))
    test("Registro de intervención técnica", "POST", f"/api/tickets/{ticket_id}/work",
         token=tecnico, payload={"note": "Diagnóstico técnico ficticio, etapa inicial.", "finished": False},
         check=lambda r: demand(r.get("status") == "en_atencion", "Estado incorrecto"))
    test("Finalización técnica y envío a visto bueno", "POST", f"/api/tickets/{ticket_id}/work",
         token=tecnico, payload={"note": "Intervención ficticia completada.", "finished": True},
         check=lambda r: demand(r.get("status") == "pendiente_vobo", "Estado incorrecto"))
    test("Visto bueno rechazado con motivo", "POST", f"/api/tickets/{ticket_id}/decision",
         token=jefe, payload={"approved": False, "reason": "Falta una verificación simulada."},
         check=lambda r: demand(r.get("status") == "retrabajo", "No generó retrabajo"))
    test("Reintervención registrada", "POST", f"/api/tickets/{ticket_id}/work",
         token=tecnico, payload={"note": "Corrección ficticia después del rechazo.", "finished": True},
         check=lambda r: demand(r.get("status") == "pendiente_vobo", "No regresó a validación"))
    test("Visto bueno aprobado por jefatura", "POST", f"/api/tickets/{ticket_id}/decision",
         token=jefe, payload={"approved": True},
         check=lambda r: demand(r.get("status") == "aprobada" and bool(r.get("vobo_at")),
                                "No registró Vo.Bo."))
    test("Cierre por coordinación", "POST", f"/api/tickets/{ticket_id}/close",
         token=coord,
         check=lambda r: demand(r.get("status") == "cerrada" and bool(r.get("closed_at")),
                                "La orden no quedó cerrada"))

    detail = test("Consulta del cierre por Planeación", "GET", f"/api/tickets/{ticket_id}",
                  token=planeacion,
                  check=lambda r: demand(r.get("ticket", {}).get("folio") == folio, "Folio no visible"))
    actions = {event.get("action") for event in detail.get("audit", [])}
    demand({"crear_solicitud", "asignar_orden", "registrar_intervencion",
            "rechazar_servicio", "validar_vobo", "cerrar_orden"} <= actions,
           "La bitácora no contiene todas las etapas")

    def check_csv(csv_text):
        rows = list(csv.reader(io.StringIO(csv_text)))
        demand(any(row and row[0] == folio for row in rows[1:]), "El CSV no contiene el folio cerrado")
    test("Exportación CSV de órdenes cerradas", "GET", "/api/exports/closed.csv",
         token=planeacion, check=check_csv)
    test("Indicadores de Planeación", "GET", "/api/metrics",
         token=planeacion, check=lambda r: demand(r.get("closed", 0) >= 1, "No figura el cierre"))
    test("Resumen SUS consultado sin fabricar respuestas", "GET", "/api/sus/summary",
         token=coord, check=lambda r: demand("participants" in r, "Resumen SUS incompleto"))
    test("Control documental", "GET", "/api/policy",
         token=coord, check=lambda r: demand("TecNM-AD-PO-001-04" in r.get("document_codes", []),
                                            "No incluye formato -04"))

    # La ruta preventiva también se prueba con registros totalmente ficticios.
    ver = test("Verificación preventiva -01", "POST", "/api/preventive", 201,
               token=jefe,
               payload={"area": "QA-E4 / Ficticia", "period": "Ciclo de prueba " + marker,
                        "findings": ["Revisar luminaria ficticia", "Verificar equipo simulado"]},
               check=lambda r: demand(r.get("format") == "TecNM-AD-PO-001-01",
                                      "Formato de verificación incorrecto"))
    test("Programa preventivo -03", "POST", f"/api/preventive/{ver['id']}/program",
         token=coord,
         check=lambda r: demand(r.get("format") == "TecNM-AD-PO-001-03"
                                and bool(r.get("activities")), "Programa preventivo incorrecto"))


def save_report(outcome):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "proyecto": "Handless E4",
        "servidor": BASE,
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "resultado_general": outcome,
        "casos_aprobados": sum(r["resultado"] == "APROBADA" for r in records),
        "casos_fallidos": sum(r["resultado"] == "FALLIDA" for r in records),
        "folio_simulado": folio,
        "advertencias": [
            "Prueba técnica automatizada; no sustituye evaluación de usabilidad con 5 personas reales.",
            "Se generan un caso correctivo y una verificación preventiva ficticios en la base persistente.",
            "No se generan ni modifican respuestas de participantes SUS."
        ],
        "casos": records,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write(f"## Handless E4 · pruebas en Render\n\n**{outcome}** · "
                         f"{report['casos_aprobados']} aprobadas, "
                         f"{report['casos_fallidos']} fallidas.\n\n")
            if folio:
                output.write(f"Folio ficticio de prueba: \`{folio}\`.\n\n")
            output.write("El archivo JSON del artefacto contiene el detalle. "
                         "No se simularon personas ni resultados SUS.\n")


if __name__ == "__main__":
    outcome = "APROBADO"
    try:
        run()
    except Exception as exc:
        outcome = "FALLIDO"
        print("La prueba terminó con error; ver resultados del artefacto.", file=sys.stderr)
    finally:
        save_report(outcome)
    sys.exit(0 if outcome == "APROBADO" else 1)
