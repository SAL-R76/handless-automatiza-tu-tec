"""CP = identificadores de aceptación de la E2; ejecuciones de backend reales."""
import csv
import io
import time
import pytest
from sqlalchemy import select
from backend.main import Audit


def test_cp01_required_fields(client,actors):
    r=client.post('/api/tickets',headers=actors['jefatura']['header'],json={'area':'A','description':'corta'})
    assert r.status_code==422

def test_cp02_unique_folios(create):
    ids=[create()['folio'] for _ in range(4)]
    assert len(set(ids))==len(ids)

def test_cp03_preventive_verification(client,actors):
    r=client.post('/api/preventive',headers=actors['jefatura']['header'],json={'area':'Edificio ficticio','period':'2026-2','findings':['Revisar luces']})
    assert r.status_code==201 and r.json()['format'].endswith('-01')

def test_cp04_preventive_program(client,actors):
    p=client.post('/api/preventive',headers=actors['jefatura']['header'],json={'area':'Edificio ficticio','period':'2026-2','findings':['Revisar luces']}).json()
    r=client.post(f'/api/preventive/{p["id"]}/program',headers=actors['coordinacion']['header'])
    assert r.status_code==200 and r.json()['format'].endswith('-03')

def test_cp05_priority_configured(client,actors,create):
    t=create();r=client.post(f'/api/tickets/{t["id"]}/assign',headers=actors['coordinacion']['header'],json={'technician_id':actors['tecnico']['id'],'priority':'urgente','destination':'Centro de Cómputo','route':'interna'})
    assert r.status_code==200 and r.json()['priority']=='urgente'

def test_cp06_routing(assigned):
    assert assigned['destination']=='Centro de Cómputo'

def test_cp07_order_generated(assigned):
    assert assigned['order_number']=='OT-'+assigned['folio']

def test_cp08_external_requires_reference(client,actors,create):
    t=create();url=f'/api/tickets/{t["id"]}/assign'
    payload={'technician_id':actors['tecnico']['id'],'route':'externa'}
    assert client.post(url,headers=actors['coordinacion']['header'],json=payload).status_code==422
    payload['external_reference']='AUT-FICTICIA-123'
    r=client.post(url,headers=actors['coordinacion']['header'],json=payload)
    assert r.status_code==200 and r.json()['external_reference']=='AUT-FICTICIA-123'

def test_cp09_timeline_read(client,actors,assigned):
    r=client.get(f'/api/tickets/{assigned["id"]}',headers=actors['jefatura']['header'])
    assert r.status_code==200 and len(r.json()['audit'])>=2

def test_cp10_audited_notification_event(client,actors,assigned):
    acts=client.get(f'/api/tickets/{assigned["id"]}',headers=actors['jefatura']['header']).json()['audit']
    assert any(a['action']=='asignar_orden' for a in acts)

def test_cp11_technical_execution(finished):
    assert finished['status']=='pendiente_vobo' and 'pieza de prueba' in finished['work_notes']

def test_cp12_rejection_rework(client,actors,finished):
    t=finished;r=client.post(f'/api/tickets/{t["id"]}/decision',headers=actors['jefatura']['header'],json={'approved':False,'reason':'La reparación sigue fallando'})
    assert r.status_code==200 and r.json()['status']=='retrabajo'
    again=client.post(f'/api/tickets/{t["id"]}/work',headers=actors['tecnico']['header'],json={'note':'Segunda intervención correctiva de prueba','finished':True})
    assert again.status_code==200 and again.json()['status']=='pendiente_vobo'

def test_cp13_closed_only_after_approved(client,actors,approved):
    r=client.post(f'/api/tickets/{approved["id"]}/close',headers=actors['coordinacion']['header'])
    assert r.status_code==200 and r.json()['status']=='cerrada' and r.json()['closed_at']

def test_cp14_export_only_closed(client,actors,approved,create):
    create()
    client.post(f'/api/tickets/{approved["id"]}/close',headers=actors['coordinacion']['header'])
    res=client.get('/api/exports/closed.csv',headers=actors['planeacion']['header'])
    assert res.status_code==200
    rows=list(csv.reader(io.StringIO(res.content.decode('utf-8-sig'))))
    assert len(rows)==2 and approved['folio'] in rows[1]

def test_cp15_filter_folio(client,actors,create):
    a=create();b=create();r=client.get('/api/tickets?q='+a['folio'],headers=actors['jefatura']['header'])
    assert r.status_code==200 and [e['folio'] for e in r.json()]==[a['folio']]

def test_cp16_kpi_counts(client,actors,create):
    create();create();r=client.get('/api/metrics',headers=actors['coordinacion']['header'])
    assert r.status_code==200 and r.json()['total']==2 and r.json()['pending']==2

def test_cp17_immutable_audit_api(client,actors,assigned):
    r=client.get(f'/api/tickets/{assigned["id"]}',headers=actors['coordinacion']['header'])
    entry=r.json()['audit'][0]
    for k in ['actor_id','actor_role','action','old_value','new_value','created_at']:
        assert k in entry and entry[k] is not None
    assert client.patch('/api/audit/1',headers=actors['coordinacion']['header'],json={}).status_code==404

def test_cp18_access_by_role(client,actors,create):
    t=create();id=t['id']
    assert client.post(f'/api/tickets/{id}/close',headers=actors['jefatura']['header']).status_code==403
    assert client.get(f'/api/tickets/{id}',headers=actors['planeacion']['header']).status_code==404
    assert client.post('/api/tickets',headers=actors['tecnico']['header'],json={'area':'Laboratorio ficticio A','location':'Edificio 1 / Aula 4','asset':'Proyector simulado','description':'El dispositivo no responde en la prueba','contact':'Contacto ficticio'}).status_code==403

def test_cp19_no_real_identity_in_seed(client,actors):
    r=client.get('/api/users',headers=actors['coordinacion']['header'])
    assert all('fictici' in u['display'].lower() or 'ficticia' in u['display'].lower() for u in r.json())

def test_cp24_block_close_without_vobo(client,actors,assigned):
    r=client.post(f'/api/tickets/{assigned["id"]}/close',headers=actors['coordinacion']['header'])
    assert r.status_code==409

def test_cp27_audit_fields(client,actors,approved):
    log=client.get(f'/api/tickets/{approved["id"]}',headers=actors['jefatura']['header']).json()['audit']
    assert all(a['actor_role'] and a['action'] and a['created_at'] and a['new_value'] for a in log)

def test_cp28_retention_policy(client,actors):
    r=client.get('/api/policy',headers=actors['planeacion']['header'])
    assert r.status_code==200 and r.json()['min_retention_days']>=365 and not r.json()['automatic_deletion']

def test_login_invalid_password(client):
    r=client.post('/api/login',json={'username':'jefatura','password':'mal'})
    assert r.status_code==401

def test_token_missing(client):
    assert client.get('/api/tickets').status_code==401

def test_planning_cannot_approve(client,actors,finished):
    r=client.post(f'/api/tickets/{finished["id"]}/decision',headers=actors['planeacion']['header'],json={'approved':True})
    assert r.status_code==403

def test_technical_cannot_view_unassigned(client,actors,create):
    t=create();assert client.get(f'/api/tickets/{t["id"]}',headers=actors['tecnico']['header']).status_code==404

def test_repeat_close_blocked(client,actors,approved):
    url=f'/api/tickets/{approved["id"]}/close';client.post(url,headers=actors['coordinacion']['header'])
    assert client.post(url,headers=actors['coordinacion']['header']).status_code==409

def test_external_no_buy_api(client,actors):
    assert client.post('/api/purchases',headers=actors['coordinacion']['header'],json={}).status_code==404

def test_sus_correct_scoring(client,actors):
    answers=[5,1,5,1,5,1,5,1,5,1]
    r=client.post('/api/sus',headers=actors['jefatura']['header'],json={'participant_code':'U-01','responses':answers,'task_completed':True,'task_seconds':140})
    assert r.status_code==201 and r.json()['score']==100
    agg=client.get('/api/sus/summary',headers=actors['coordinacion']['header']).json()
    assert agg['participants']==1 and agg['mean_sus']==100 and not agg['complete']

def test_sus_not_fabricated_duplicate(client,actors):
    payload={'participant_code':'U-01','responses':[3]*10,'task_completed':False,'task_seconds':350}
    assert client.post('/api/sus',headers=actors['jefatura']['header'],json=payload).status_code==201
    assert client.post('/api/sus',headers=actors['jefatura']['header'],json=payload).status_code==409

def test_sus_invalid_answer(client,actors):
    r=client.post('/api/sus',headers=actors['jefatura']['header'],json={'participant_code':'U-01','responses':[9]*10,'task_completed':True,'task_seconds':140})
    assert r.status_code==422

def test_sus_summary_restricted(client,actors):
    assert client.get('/api/sus/summary',headers=actors['tecnico']['header']).status_code==403
