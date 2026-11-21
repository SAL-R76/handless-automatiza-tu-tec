"""Comprobaciones de autenticación pública opcional, sin conocer contraseñas reales."""
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app

ROLES = ("jefatura", "coordinacion", "tecnico", "planeacion")

@pytest.fixture()
def make_client(tmp_path, monkeypatch):
    def create(enabled):
        monkeypatch.setenv("PUBLIC_DEMO_ENABLED", "true" if enabled else "false")
        monkeypatch.setenv("DEMO_PASSWORD", "valor-ficticio-usado-solo-en-test")
        app = create_app(
            f"sqlite:///{tmp_path / ('on.db' if enabled else 'off.db')}",
            token_secret="firmar-tokens-solo-para-test-e4"
        )
        return TestClient(app)
    return create

def test_public_demo_disabled_by_default(make_client):
    with make_client(False) as client:
        assert client.get("/api/public-demo").json() == {"enabled": False}
        assert client.post("/api/public-demo/login", json={"role": "jefatura"}).status_code == 404
        assert client.post("/api/login", json={
            "username": "jefatura", "password": "equivocada"}).status_code == 401

def test_public_demo_all_roles_without_password(make_client):
    with make_client(True) as client:
        assert client.get("/api/public-demo").json() == {"enabled": True}
        for role in ROLES:
            res = client.post("/api/public-demo/login", json={"role": role})
            assert res.status_code == 200, res.text
            payload = res.json()
            assert payload["user"]["role"] == role
            assert payload["token"] and "password" not in payload
            me = client.get("/api/me",
                headers={"Authorization": "Bearer " + payload["token"]})
            assert me.status_code == 200 and me.json()["role"] == role

def test_public_demo_rejects_unknown_roles_and_preserves_permissions(make_client):
    with make_client(True) as client:
        assert client.post("/api/public-demo/login",
                           json={"role": "administrador"}).status_code == 422
        assert client.post("/api/public-demo/login",
                           json={"role": "jefatura", "password": "no-guardar"}).status_code == 200
        tecnico = client.post("/api/public-demo/login",json={"role":"tecnico"}).json()["token"]
        # El acceso libre no elimina las reglas de autorización del proceso.
        r = client.post("/api/tickets",
            headers={"Authorization": "Bearer " + tecnico},
            json={"area": "Sala ficticia", "location": "Edificio ficticio",
                  "asset": "Proyector simulado",
                  "description": "Prueba con valores ficticios únicamente",
                  "contact": "Persona ficticia"})
        assert r.status_code == 403

def test_password_required_for_new_database_without_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    monkeypatch.setenv("PUBLIC_DEMO_ENABLED", "true")
    with pytest.raises(RuntimeError, match="DEMO_PASSWORD"):
        create_app(f"sqlite:///{tmp_path / 'missing.db'}",
                   token_secret="test")
