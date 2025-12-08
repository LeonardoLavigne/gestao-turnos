"""
Use case for creating a new Turno.
"""
import logging
import calendar
from datetime import date, time
from typing import Optional

from app.domain.entities.turno import Turno
from app.domain.uow import AbstractUnitOfWork
from app.domain.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException
from app.core.config import get_settings


class CriarTurnoUseCase:
    """
    Use case for creating a new work shift.
    
    Encapsulates the business logic for creating a turno,
    including duration calculation, validation, and CalDAV sync.
    """

    def __init__(
        self, 
        uow: AbstractUnitOfWork,
        calendar_service: CalendarService,
    ):
        self.uow = uow
        self.calendar_service = calendar_service

    async def execute(
        self,
        telegram_user_id: int,
        data_referencia: date,
        hora_inicio: time,
        hora_fim: time,
        tipo: Optional[str] = None,
        descricao_opcional: Optional[str] = None,
    ) -> Turno:
        """
        Creates a new turno asynchronously.
        """
        async with self.uow:
            # 0. Check Freemium Limits
            assinatura = await self.uow.assinaturas.get_by_user_id(telegram_user_id)
            if assinatura and assinatura.is_free:
                settings = get_settings()
                
                # Determine start/end of the month for data_referencia
                start_date = data_referencia.replace(day=1)
                _, last_day = calendar.monthrange(data_referencia.year, data_referencia.month)
                end_date = data_referencia.replace(day=last_day)
                
                count = await self.uow.turnos.contar_por_periodo(telegram_user_id, start_date, end_date)
                
                if count >= settings.free_tier_max_shifts:
                    raise LimiteTurnosExcedidoException(settings.free_tier_max_shifts, count)
    
            # 1. Create Entity (Business Logic)
            turno = Turno.criar(
                telegram_user_id=telegram_user_id,
                data_referencia=data_referencia,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                tipo=tipo,
                descricao_opcional=descricao_opcional,
            )
            
            # 1.1 Normalize Tipo (Domain Logic moved from Infrastructure)
            if tipo:
                tipo_existente = await self.uow.turnos.buscar_tipo_por_nome(tipo)
                if tipo_existente:
                    turno.tipo_id = tipo_existente.id
                    # We keep turno.tipo as string for display/fallback, but ID takes precedence in persistence
            
            # 2. Persist (Infrastructure)
            saved_turno = await self.uow.turnos.criar(turno)
            
            # 3. CalDAV Integration (Injected Logic)
            # Only sync if user is NOT Free (Premium feature)
            if assinatura and not assinatura.is_free:
                try:
                    # Use abstraction, no infrastructure import here
                    new_uid = self.calendar_service.sync_event(saved_turno)
                    if new_uid:
                        saved_turno.event_uid = new_uid
                        
                        # 4. Update with UID if needed
                        saved_turno = await self.uow.turnos.atualizar(saved_turno)
                except Exception as e:
                    logger.error(f"Failed to sync CalDAV for turno {saved_turno.id}: {e}", exc_info=True)
                    # Integration failure should be non-blocking for shift creation
                
            # 5. Commit Transaction
            await self.uow.commit()
            
            return saved_turno
