"""
Use case for creating a new Turno.
"""
from datetime import date, time
from typing import Optional

from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository


class CriarTurnoUseCase:
    """
    Use case for creating a new work shift.
    
    Encapsulates the business logic for creating a turno,
    including duration calculation and validation.
    """

    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    def execute(
        self,
        telegram_user_id: int,
        data_referencia: date,
        hora_inicio: time,
        hora_fim: time,
        tipo: Optional[str] = None,
        descricao_opcional: Optional[str] = None,
    ) -> Turno:
        """
        Creates a new turno.
        
        Args:
            telegram_user_id: ID of the user creating the turno
            data_referencia: Date of the shift
            hora_inicio: Start time
            hora_fim: End time
            tipo: Type/location of the shift
            descricao_opcional: Optional description
            
        Returns:
            The created Turno entity
        """
        # Create entity with calculated duration
        turno = Turno.criar(
            telegram_user_id=telegram_user_id,
            data_referencia=data_referencia,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            tipo=tipo,
            descricao_opcional=descricao_opcional,
        )
        
        # Persist and return
        return self.turno_repository.criar(turno)
