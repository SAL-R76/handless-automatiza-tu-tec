"""Regresión: una orden correctiva únicamente puede asignarse por primera vez."""
from backend.main import Audit, Notification, Ticket
from sqlalchemy import select, func


def test_second_assignment_is_rejected_without_overwriting_or_extra_events(client, actors, assigned):
    ticket_id = assigned["id"]
    url = f"/api/tickets/{ticket_id}/assign"
    headers = actors["coordinacion"]["header"]

    # Registra el estado original de la asignación y su bitácora.
    details_before = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()
    original = details_before["ticket"]
    first_audits = [a for a in details_before["audit"] if a["action"] == "asignar_orden"]
    assert len(first_audits) == 1

    with client.app.state.db() as db:
        notification_count = db.scalar(
            select(func.count()).select_from(Notification)
            .where(Notification.ticket_id == ticket_id, Notification.event == "orden_asignada")
        )
        assert notification_count == 1

    # Incluso si cambian prioridad, técnico o ruta, ya no se puede asignar.
    for attempt in range(5):
        result = client.post(url, headers=headers, json={
            "technician_id": actors["tecnico"]["id"],
            "priority": "urgente" if attempt % 2 else "baja",
            "destination": "Recursos Materiales",
            "route": "interna"
        })
        assert result.status_code == 409, result.text
        assert "ya fue asignada" in result.json()["detail"]

    after = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()
    current = after["ticket"]
    for field in ("order_number", "technician_id", "priority", "destination",
                  "route", "status", "updated_at"):
        assert current[field] == original[field], field

    second_audits = [a for a in after["audit"] if a["action"] == "asignar_orden"]
    assert len(second_audits) == 1
    assert len(after["audit"]) == len(details_before["audit"])

    with client.app.state.db() as db:
        assert db.scalar(
            select(func.count()).select_from(Notification)
            .where(Notification.ticket_id == ticket_id, Notification.event == "orden_asignada")
        ) == 1
        assert db.scalar(select(func.count()).select_from(Ticket).where(Ticket.id == ticket_id)) == 1


def test_assignment_allowed_once_then_only_technical_work(client, actors, create):
    ticket = create()
    url = f"/api/tickets/{ticket['id']}/assign"
    payload = {
        "technician_id": actors["tecnico"]["id"],
        "priority": "alta", "destination": "Centro de Cómputo", "route": "interna"
    }
    coord = actors["coordinacion"]["header"]
    first = client.post(url, headers=coord, json=payload)
    assert first.status_code == 200
    assert first.json()["status"] == "asignada"
    assert first.json()["order_number"] == "OT-" + ticket["folio"]

    duplicate = client.post(url, headers=coord, json=payload)
    assert duplicate.status_code == 409

    work = client.post(f"/api/tickets/{ticket['id']}/work",
        headers=actors["tecnico"]["header"],
        json={"note": "Intervención técnica ficticia y revisión", "finished": False})
    assert work.status_code == 200
    assert work.json()["status"] == "en_atencion"

    assert client.post(url, headers=coord, json=payload).status_code == 409
