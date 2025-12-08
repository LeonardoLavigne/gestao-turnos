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
from datetime import datetime, UTC
from app.domain.entities.assinatura import Assinatura, AssinaturaStatus, PlanoType
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException
from app.core.config import Settings
from app.domain.ports.caldav_sync_port import CalDavSyncTaskPort
from app.application.dtos.caldav_sync_dto import SyncTurnoCalDavCommand


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
        settings: Settings,
        caldav_sync_task_port: CalDavSyncTaskPort,
    ):
        self.uow = uow
        self.calendar_service = calendar_service
        self.settings = settings
        self.caldav_sync_task_port = caldav_sync_task_port

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
            # Lock row to prevent race condition
            assinatura = await self.uow.assinaturas.get_by_user_id(telegram_user_id, for_update=True)
            
            # 0.1 If Legacy User (no signature), create default FREE one now to enable locking/checking
            if not assinatura:
                logger.info(f"Usuário {telegram_user_id} sem assinatura (legacy). Criando assinatura FREE padrão.")
                agora = datetime.now(UTC)
                nova_assinatura = Assinatura(
                    id=None, # DB will generate
                    telegram_user_id=telegram_user_id,
                    stripe_customer_id=f"legacy_{telegram_user_id}", # Placeholder
                    stripe_subscription_id=None,
                    status=AssinaturaStatus.ACTIVE.value,
                    plano=PlanoType.FREE.value,
                    data_inicio=agora,
                    data_fim=None,
                    criado_em=agora,
                    atualizado_em=agora,
                )
                assinatura = await self.uow.assinaturas.criar(nova_assinatura)
                # Note: 'criar' usually does flush/refresh, so we get the ID and it's part of the transaction.
                # Since we are in the same transaction, we effectively hold the lock on this new row if we were to select it again,
                # but since we just created it, no one else could have it yet (or they would have blocked us on insert if unique constraint exists).
            
            if assinatura and assinatura.is_free:
                
                # Determine start/end of the month for data_referencia
                start_date = data_referencia.replace(day=1)
                _, last_day = calendar.monthrange(data_referencia.year, data_referencia.month)
                end_date = data_referencia.replace(day=last_day)
                
                count = await self.uow.turnos.contar_por_periodo(telegram_user_id, start_date, end_date)
                
                if count >= self.settings.free_tier_max_shifts:
                    raise LimiteTurnosExcedidoException(self.settings.free_tier_max_shifts, count)
    
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
            
            # 2. Persist (Infrastructure)
            saved_turno = await self.uow.turnos.criar(turno)
            
            # 3. Commit Transaction (Must commit to get ID before background task usually)
            # UoW commit does flush and commit.
            await self.uow.commit()

            # 4. CalDAV Integration (Background)
            if assinatura and not assinatura.is_free:
                self.caldav_sync_task_port.add_sync_task(SyncTurnoCalDavCommand(turno_id=saved_turno.id))
            
            return saved_turno
