"""
Use case for creating a new Turno.
"""
from datetime import date, time
from typing import Optional
import calendar

from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository
from app.domain.repositories.assinatura_repository import AssinaturaRepository
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException
from app.config import get_settings


class CriarTurnoUseCase:
    """
    Use case for creating a new work shift.
    
    Encapsulates the business logic for creating a turno,
    including duration calculation, validation, and CalDAV sync.
    """

    def __init__(self, turno_repository: TurnoRepository, assinatura_repository: AssinaturaRepository, session):
        self.turno_repository = turno_repository
        self.assinatura_repository = assinatura_repository
        # Session is treated as a Unit of Work here
        self.session = session

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
        # 0. Check Freemium Limits
        assinatura = await self.assinatura_repository.get_by_user_id(telegram_user_id)
        if assinatura and assinatura.is_free:
            settings = get_settings()
            
            # Determine start/end of the month for data_referencia
            start_date = data_referencia.replace(day=1)
            _, last_day = calendar.monthrange(data_referencia.year, data_referencia.month)
            end_date = data_referencia.replace(day=last_day)
            
            count = await self.turno_repository.contar_por_periodo(telegram_user_id, start_date, end_date)
            
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
        
        # 2. Persist (Infrastructure)
        saved_turno = await self.turno_repository.criar(turno)
        
        # 3. CalDAV Integration (Infrastructure / External Service)
        # Only sync if user is NOT Free (Premium feature)
        if assinatura and not assinatura.is_free:
            # TODO: Inject CalDAV service instead of importing directly ideally
            from app.caldav_client import criar_ou_atualizar_evento
            
            try:
                new_uid = criar_ou_atualizar_evento(saved_turno, None)
                saved_turno.event_uid = new_uid
                
                # 4. Update with UID if needed
                saved_turno = await self.turno_repository.atualizar(saved_turno)
            except Exception:
                # Log error but don't fail the transaction?
                # Or pass? crud.py passed.
                pass
            
        # 5. Commit Transaction
        await self.session.commit()
        # await self.session.refresh(saved_turno) # Cannot refresh Entity, but repository logic handles it internally? 
        # Actually repo returns Entity, so we are fine. 
        # But session commit might expire objects if using Models directly.
        # Since we use Repositories converting to Entities, we are safe.
        
        return saved_turno
