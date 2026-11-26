"""Pruebas de automatización académica; todas las identidades son ficticias."""
from backend.automation import suggest_routing


def test_rule_engine_detects_electrical_risk():
    result=suggest_routing(
        "Aula ficticia", "Tablero", "Se ve un cable expuesto y riesgo eléctrico",
        "Infraestructura")
    assert result.priority=="urgente"
    assert result.category=="Instalación eléctrica"
    assert result.destination=="Mantenimiento de Equipo"
    assert result.rule_id=="RIESGO_EXPLICITO"
    assert result.requires_confirmation is True


def test_rule_engine_detects_class_interruption():
    result=suggest_routing(
        "Aula ficticia", "Proyector", "El proyector no enciende y afecta la clase",
        "Infraestructura")
    assert result.priority=="alta"
    assert result.category=="Equipo de cómputo"
    assert result.destination=="Centro de Cómputo"


def test_rule_engine_default_does_not_invent_emergency():
    result=suggest_routing(
        "Espacio de prueba", "Activo genérico", "Revisar el equipo por desgaste",
        "Mobiliario")
    assert result.priority=="media"
    assert result.destination=="Recursos Materiales"


def test_create_ticket_generates_audit_and_internal_notice(client,actors,create):
    ticket=create()
    auth=actors["jefatura"]["header"]
    detail=client.get(f"/api/tickets/{ticket['id']}",headers=auth)
    assert detail.status_code==200
    payload=detail.json()
    assert payload["automation"]["priority"] in ("media","alta","urgente","baja")
    assert payload["automation"]["requires_confirmation"]
    events=[e for e in payload["audit"] if e["action"]=="sugerencia_automatica"]
    assert len(events)==1
    assert events[0]["actor_role"]=="sistema"
    assert ticket["priority"]=="media"  # La sugerencia no altera la decisión humana.

    notices=client.get("/api/notifications",headers=actors["coordinacion"]["header"])
    assert notices.status_code==200
    assert any(n["event"]=="solicitud_nueva" and n["ticket_id"]==ticket["id"]
               for n in notices.json())
    assert client.get("/api/notifications").status_code==401
    assert client.get("/api/notifications",headers=auth).json()==[]


def test_automated_notices_follow_human_approval(client,actors,create):
    ticket=create()
    id=ticket["id"]
    technician_id=actors["tecnico"]["id"]
    result=client.post(f"/api/tickets/{id}/assign",
       headers=actors["coordinacion"]["header"],
       json={"technician_id":technician_id,"priority":"alta",
             "destination":"Centro de Cómputo","route":"interna"})
    assert result.status_code==200
    technician_feed=client.get("/api/notifications",headers=actors["tecnico"]["header"]).json()
    assert any(n["event"]=="orden_asignada" for n in technician_feed)

    work=client.post(f"/api/tickets/{id}/work",
       headers=actors["tecnico"]["header"],
       json={"note":"Intervención ficticia registrada y verificada","finished":True})
    assert work.status_code==200
    jefe_feed=client.get("/api/notifications",headers=actors["jefatura"]["header"]).json()
    assert any(n["event"]=="vobo_pendiente" for n in jefe_feed)

    # No basta que una intervención esté terminada: cierre sin Vo.Bo. bloqueado.
    blocked=client.post(f"/api/tickets/{id}/close",headers=actors["coordinacion"]["header"])
    assert blocked.status_code==409
    assert client.get("/api/notifications",headers=actors["planeacion"]["header"]).json()==[]

    approval=client.post(f"/api/tickets/{id}/decision",
       headers=actors["jefatura"]["header"],json={"approved":True})
    assert approval.status_code==200
    coordination_feed=client.get("/api/notifications",
        headers=actors["coordinacion"]["header"]).json()
    assert any(n["event"]=="vobo_aprobado" for n in coordination_feed)

    closure=client.post(f"/api/tickets/{id}/close",headers=actors["coordinacion"]["header"])
    assert closure.status_code==200
    planning_feed=client.get("/api/notifications",
        headers=actors["planeacion"]["header"]).json()
    assert any(n["event"]=="orden_cerrada" for n in planning_feed)


def test_rejection_notifies_technician(client,actors,finished):
    id=finished["id"]
    result=client.post(f"/api/tickets/{id}/decision",
        headers=actors["jefatura"]["header"],
        json={"approved":False,"reason":"Prueba ficticia: servicio incompleto"})
    assert result.status_code==200
    feed=client.get("/api/notifications",headers=actors["tecnico"]["header"]).json()
    assert any(n["event"]=="retrabajo" for n in feed)
    assert client.get("/api/notifications",headers=actors["planeacion"]["header"]).json()==[]
