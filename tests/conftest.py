import pytest
from fastapi.testclient import TestClient
from backend.main import create_app

@pytest.fixture()
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('DEMO_PASSWORD','HandlessDemo2026!')
    monkeypatch.setenv('PUBLIC_DEMO_ENABLED','false')
    app=create_app(f'sqlite:///{tmp_path / "test.db"}',token_secret='PRUEBA-segura-larga-que-no-es-produccion')
    with TestClient(app) as c:
        yield c

@pytest.fixture()
def actors(client):
    res={}
    for role in ['jefatura','coordinacion','tecnico','planeacion']:
        login=client.post('/api/login',json={'username':role,'password':'HandlessDemo2026!'})
        assert login.status_code==200
        payload=login.json()
        res[role]={'header':{'Authorization':'Bearer '+payload['token']},'id':payload['user']['id']}
    return res

@pytest.fixture()
def create(client,actors):
    def create_one():
        r=client.post('/api/tickets',headers=actors['jefatura']['header'],json={
          'area':'Laboratorio ficticio A','location':'Edificio 1 / Aula 4','asset':'Proyector simulado',
          'description':'El dispositivo de ensayo no responde al encendido.','contact':'Persona ficticia'})
        assert r.status_code==201,r.text
        return r.json()
    return create_one

@pytest.fixture()
def assigned(client,actors,create):
    t=create()
    r=client.post(f'/api/tickets/{t["id"]}/assign',headers=actors['coordinacion']['header'],json={'technician_id':actors['tecnico']['id'],'priority':'alta','destination':'Centro de Cómputo','route':'interna'})
    assert r.status_code==200,r.text
    return r.json()

@pytest.fixture()
def finished(client,actors,assigned):
    r=client.post(f'/api/tickets/{assigned["id"]}/work',headers=actors['tecnico']['header'],json={'note':'Se sustituyó la pieza de prueba y se verificó encendido.','finished':True})
    assert r.status_code==200,r.text
    return r.json()

@pytest.fixture()
def approved(client,actors,finished):
    r=client.post(f'/api/tickets/{finished["id"]}/decision',headers=actors['jefatura']['header'],json={'approved':True})
    assert r.status_code==200,r.text
    return r.json()
