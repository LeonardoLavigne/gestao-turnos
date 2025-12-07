"""
Use case for listing turnos by period.
"""
from datetime import date
from typing import List

from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository


class ListarTurnosPeriodoUseCase:
    """
    Use case for listing turnos within a date range.
    """

    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    def execute(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> List[Turno]:
        """
        Lists turnos for a user within the given period.
        
        Args:
            telegram_user_id: ID of the user
            inicio: Start date (inclusive)
            fim: End date (inclusive)
            
        Returns:
            List of Turno entities ordered by date and time
        """
        return self.turno_repository.listar_por_periodo(
            telegram_user_id=telegram_user_id,
            inicio=inicio,
            fim=fim,
        )


class ListarTurnosRecentesUseCase:
    """
    Use case for listing recent turnos.
    """

    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    def execute(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> List[Turno]:
        """
        Lists the most recent turnos for a user.
        
        Args:
            telegram_user_id: ID of the user
            limit: Maximum number of turnos to return
            
        Returns:
            List of Turno entities ordered by creation time (newest first)
        """
        return self.turno_repository.listar_recentes(
            telegram_user_id=telegram_user_id,
            limit=limit,
        )
