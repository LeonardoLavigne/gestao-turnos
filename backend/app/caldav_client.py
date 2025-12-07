from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import caldav
from caldav import DAVClient
from icalendar import Calendar, Event

from .config import get_settings
# from . import models # Avoiding circular or direct dependency, using duck typing given shared structure


def _get_client() -> DAVClient:
    settings = get_settings()
    url = settings.caldav_url.rstrip("/")
    return DAVClient(
        url=url,
        username=settings.caldav_username,
        password=settings.caldav_password,
    )


def _get_calendar() -> caldav.Calendar:
    settings = get_settings()
    client = _get_client()
    principal = client.principal()
    for cal in principal.calendars():
        if settings.caldav_calendar_path and settings.caldav_calendar_path in str(
            cal.url
        ):
            return cal
    raise RuntimeError("Calendário CalDAV não encontrado/configurado corretamente.")


def build_event(turno) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//gestao-turnos//pt-BR")
    cal.add("version", "2.0")

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)

    dt_start = datetime.combine(turno.data_referencia, turno.hora_inicio).replace(
        tzinfo=tz
    )
    dt_end = datetime.combine(turno.data_referencia, turno.hora_fim).replace(
        tzinfo=tz
    )
    if dt_end <= dt_start:
        dt_end = dt_end.replace(day=dt_end.day + 1)

    evt = Event()
    
    # Lógica híbrida para suportar Model SQLAlchemy e Domain Entity
    tipo_nome = "Turno"
    if hasattr(turno, "tipo") and turno.tipo:
        if isinstance(turno.tipo, str):
            tipo_nome = turno.tipo
        elif hasattr(turno.tipo, "nome"):
            tipo_nome = turno.tipo.nome
    
    if tipo_nome == "Turno" and hasattr(turno, "tipo_livre") and turno.tipo_livre:
        tipo_nome = turno.tipo_livre

    horas = turno.duracao_minutos / 60.0
    evt.add("summary", f"{tipo_nome} ({horas:.2f}h)")
    evt.add("dtstart", dt_start)
    evt.add("dtend", dt_end)
    evt.add(
        "description",
        f"Turno {tipo_nome} de {turno.hora_inicio} a {turno.hora_fim} em {turno.data_referencia}",
    )

    cal.add_component(evt)
    return cal


def criar_ou_atualizar_evento(turno, uid_existente: Optional[str]) -> str:
    cal = _get_calendar()
    ical = build_event(turno).to_ical()

    if uid_existente:
        # busca simples e recria o evento
        results = cal.search(uid=uid_existente)
        for ev in results:
            ev.delete()

    new_ev = cal.add_event(ical)
    return new_ev.vobject_instance.vevent.uid.value


