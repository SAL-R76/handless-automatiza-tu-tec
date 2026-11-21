#!/usr/bin/env python3
"""Verifica acceso público de Handless en Render sin credenciales ni escrituras."""
import json
import time
import urllib.error
import urllib.request

BASE = "https://handless.onrender.com"
ROLES = ("jefatura", "coordinacion", "tecnico", "planeacion")

def request(method, path, payload=None, token=None):
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, method=method, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as response:
        assert response.status == 200, f"{path}: status HTTP {response.status}"
        return json.load(response)

def run():
    health = None
    for i in range(10):
        try:
            health = request("GET", "/api/health")
            break
        except (urllib.error.URLError, TimeoutError):
            if i == 9:
                raise
            print("Servidor gratuito despertando; reintentando...", flush=True)
            time.sleep(15)
    assert health["status"] == "ok", "GET /api/health no devolvió status=ok"
    print("[OK] API disponible", flush=True)

    config = request("GET", "/api/public-demo")
    assert config.get("enabled") is True, (
        "El acceso público está desactivado. En Render > Environment configura "
        "PUBLIC_DEMO_ENABLED=true y asegúrate de que se desplegó el último commit.")
    print("[OK] Acceso público activado", flush=True)

    for role in ROLES:
        session = request("POST", "/api/public-demo/login", {"role": role})
        assert session.get("user", {}).get("role") == role and session.get("token"), (
            f"Sesión incorrecta para {role}")
        identity = request("GET", "/api/me", token=session["token"])
        assert identity["role"] == role, f"Rol incorrecto para {role}"
        print(f"[OK] Inicio de sesión público sin contraseña: {role}", flush=True)
    print("RESULTADO: 6 comprobaciones aprobadas, 0 fallidas. No se modificaron registros.", flush=True)

if __name__ == "__main__":
    run()
