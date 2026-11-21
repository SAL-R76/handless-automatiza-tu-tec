"""Pruebas técnicas ejecutables con datos ficticios; NO es estudio con usuarios humanos."""
import json, statistics, tempfile, time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import create_app

here=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    app=create_app('sqlite:///'+str(Path(temp)/'measure.db'),token_secret='bench-e4-not-production')
    with TestClient(app) as c:
        roles={}
        for name in ['jefatura','coordinacion','tecnico','planeacion']:
            j=c.post('/api/login',json={'username':name,'password':'HandlessDemo2026!'}).json()
            roles[name]={'Authorization':'Bearer '+j['token'],'id':j['user']['id']}
        created=[];times_create=[]
        for n in range(100):
            payload={'area':'Aula ficticia','location':'Edificio ficticio A','asset':f'Activo de prueba {n:03d}',
                'description':'Falla creada para ensayo funcional y rendimiento.', 'contact':'Contacto simulado'}
            start=time.perf_counter();r=c.post('/api/tickets',headers={'Authorization':roles['jefatura']['Authorization']},json=payload)
            elapsed=(time.perf_counter()-start)*1000
            assert r.status_code==201
            times_create.append(elapsed);created.append(r.json())
        times_queries=[]
        for t in created:
            start=time.perf_counter();r=c.get('/api/tickets?q='+t['folio'],headers={'Authorization':roles['jefatura']['Authorization']})
            times_queries.append((time.perf_counter()-start)*1000)
            assert r.status_code==200 and len(r.json())==1
        blocked_closures=[]
        for t in created[:10]:
            blocked_closures.append(c.post(f'/api/tickets/{t["id"]}/close',headers={'Authorization':roles['coordinacion']['Authorization']}).status_code==409)
        blocked_roles=[]
        for t in created[:10]:
            blocked_roles.append(c.get(f'/api/tickets/{t["id"]}',headers={'Authorization':roles['tecnico']['Authorization']}).status_code==404)
        bad_fields=[]
        for n in range(10):
            bad_fields.append(c.post('/api/tickets',headers={'Authorization':roles['jefatura']['Authorization']},json={'description':'falta'}).status_code==422)
        t=created[0]
        steps=[
          c.post(f'/api/tickets/{t["id"]}/assign',headers={'Authorization':roles['coordinacion']['Authorization']},json={'technician_id':roles['tecnico']['id'],'priority':'alta','destination':'Centro de Cómputo','route':'interna'}),
          c.post(f'/api/tickets/{t["id"]}/work',headers={'Authorization':roles['tecnico']['Authorization']},json={'note':'Equipo reparado y verificado en simulación técnica','finished':True}),
          c.post(f'/api/tickets/{t["id"]}/decision',headers={'Authorization':roles['jefatura']['Authorization']},json={'approved':True}),
          c.post(f'/api/tickets/{t["id"]}/close',headers={'Authorization':roles['coordinacion']['Authorization']})
        ]
        assert all(r.status_code==200 for r in steps)
        audit=c.get(f'/api/tickets/{t["id"]}',headers={'Authorization':roles['coordinacion']['Authorization']}).json()['audit']
        assert len(audit)==5
        export=c.get('/api/exports/closed.csv',headers={'Authorization':roles['planeacion']['Authorization']})
        assert export.status_code==200 and t['folio'] in export.text
        report={'run_type':'Prueba técnica local y reproducible; no prueba UX con usuarios',
            'environment':'TestClient de FastAPI + SQLite temporal, mismo proceso Python',
            'records_created':len(created),'unique_folio_count':len({x['folio'] for x in created}),
            'folio_duplicate_count':len(created)-len({x['folio'] for x in created}),
            'creation_ms_mean':round(statistics.mean(times_create),2),
            'query_ms_mean':round(statistics.mean(times_queries),2),
            'query_ms_p95':round(sorted(times_queries)[94],2),
            'queries_under_3000ms':sum(t<=3000 for t in times_queries),
            'queries_count':len(times_queries),
            'unauthorized_read_attempts_blocked':sum(blocked_roles),'unauthorized_read_attempts':len(blocked_roles),
            'premature_closures_blocked':sum(blocked_closures),'premature_closure_attempts':len(blocked_closures),
            'invalid_submissions_rejected':sum(bad_fields),'invalid_submission_attempts':len(bad_fields),
            'workflow_steps_passed':sum(r.status_code==200 for r in steps),'workflow_steps_total':len(steps),
            'audits_of_full_workflow':len(audit),'csv_export_ok':export.status_code==200,
            'sus_participants_collected':0, 'sus_status':'Pendiente de cinco usuarios reales; no se han inventado resultados',
            'limitations':'Resultados de pruebas en memoria, no equivalen a latencia de internet ni rendimiento de producción.'}
        out=here/'docs'/'resultados_e4.json'
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(report,indent=2,ensure_ascii=False))
