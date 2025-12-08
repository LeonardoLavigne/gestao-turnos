from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import caldav
from caldav import DAVClient
from icalendar import Calendar, Event

from app.core.config import Settings
from app.domain.services.calendar_service import CalendarService
from app.domain.entities.turno import Turno

class CalDAVService(CalendarService):
    def __init__(self, settings: Settings):
        self.settings = settings

    def _get_client(self) -> DAVClient:
        url = self.settings.caldav_url.rstrip("/")
        return DAVClient(
            url=url,
            username=self.settings.caldav_username,
            password=self.settings.caldav_password,
        )

    def _get_calendar(self) -> caldav.Calendar:
        client = self._get_client()
        principal = client.principal()
        for cal in principal.calendars():
            if self.settings.caldav_calendar_path and self.settings.caldav_calendar_path in str(
                cal.url
            ):
                return cal
        raise RuntimeError("Calendário CalDAV não encontrado/configurado corretamente.")

    def _build_event(self, turno: Turno) -> Calendar:
        cal = Calendar()
        cal.add("prodid", "-//gestao-turnos//pt-BR")
        cal.add("version", "2.0")

        tz = ZoneInfo(self.settings.timezone)

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
        # Como o type hint é Turno entity, acessamos diretamente, mas mantemos robustez
        tipo_nome = "Turno"
        if turno.tipo:
             tipo_nome = turno.tipo
        
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

    def sync_event(self, turno: Turno) -> Optional[str]:
        try:
            cal = self._get_calendar()
            ical = self._build_event(turno).to_ical()

            if turno.event_uid:
                # busca simples e recria o evento
                results = cal.search(uid=turno.event_uid)
                for ev in results:
                    ev.delete()

            new_ev = cal.add_event(ical)
            return new_ev.vobject_instance.vevent.uid.value
        except Exception as e:
            # Em prod, logar o erro.
            # Retornar None indica falha na sync, mas não deve quebrar o fluxo principal se não for crítico.
            # O user case pode decidir logar ou ignorar.
            print(f"Erro no CalDAV: {e}")
            return None

