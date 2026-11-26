"""Motor de sugerencias de mantenimiento para el prototipo académico TecNM.

Reglas deterministas y auditables. NO asigna personal, no autoriza gastos,
no emite vistos buenos y no sustituye el criterio de Coordinación.
"""
from dataclasses import asdict, dataclass
import unicodedata


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    return "".join(c for c in value if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class RoutingSuggestion:
    category: str
    priority: str
    destination: str
    rule_id: str
    reason: str
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


DESTINATIONS = {
    "Equipo de cómputo": "Centro de Cómputo",
    "Instalación eléctrica": "Mantenimiento de Equipo",
    "Mobiliario": "Recursos Materiales",
    "Infraestructura": "Recursos Materiales",
}

CATEGORY_KEYWORDS = (
    ("Instalación eléctrica", ("cortocircuito", "corto circuito", "enchufe",
        "contacto electrico", "cable expuesto", "tablero electrico", "apagador",
        "luminaria", "luz electrica")),
    ("Equipo de cómputo", ("proyector", "computadora", "cpu", "monitor",
        "impresora", "equipo de computo", "internet", "red wifi", "router")),
    ("Mobiliario", ("mesa", "silla", "escritorio", "pupitre", "anaquel",
        "archivero", "estante")),
    ("Infraestructura", ("fuga de agua", "tuberia", "puerta", "ventana",
        "sanitario", "pared", "techo", "filtracion", "humedad")),
)

URGENT_KEYWORDS = ("cortocircuito", "corto circuito", "cable expuesto",
    "riesgo electrico", "humo", "incendio", "fuga de gas",
    "riesgo de accidente", "inundacion")
HIGH_KEYWORDS = ("no enciende", "no funciona", "sin servicio", "sin internet",
    "suspension de clase", "impide clase", "no se puede usar",
    "afecta la clase", "fallo total")
LOW_KEYWORDS = ("ajuste menor", "detalle estetico", "retoque", "sin urgencia")


def suggest_routing(area: str, asset: str, description: str, category: str) -> RoutingSuggestion:
    """Clasifica la incidencia con reglas académicas revisables; no es decisión oficial."""
    text = normalize(" ".join((area, asset, description)))
    selected = category if category in DESTINATIONS else "Infraestructura"
    for candidate, keywords in CATEGORY_KEYWORDS:
        if any(word in text for word in keywords):
            selected = candidate
            break

    if any(word in text for word in URGENT_KEYWORDS):
        priority = "urgente"
        rule_id = "RIESGO_EXPLICITO"
        reason = "La descripción menciona una condición de riesgo; verificar presencialmente."
    elif any(word in text for word in HIGH_KEYWORDS):
        priority = "alta"
        rule_id = "INTERRUPCION_SERVICIO"
        reason = "La descripción indica interrupción del servicio educativo o del equipo."
    elif any(word in text for word in LOW_KEYWORDS):
        priority = "baja"
        rule_id = "INCIDENCIA_MENOR"
        reason = "La descripción indica una incidencia menor, sin urgencia declarada."
    else:
        priority = "media"
        rule_id = "PRIORIDAD_GENERAL"
        reason = "No se detectó un criterio específico de urgencia."

    return RoutingSuggestion(
        category=selected, priority=priority,
        destination=DESTINATIONS[selected],
        rule_id=rule_id, reason=reason,
    )
