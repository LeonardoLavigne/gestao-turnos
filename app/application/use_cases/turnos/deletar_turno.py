"""
Use case for deleting a turno.
"""
from app.domain.repositories.turno_repository import TurnoRepository


class DeletarTurnoUseCase:
    """
    Use case for deleting a work shift.
    """

    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    def execute(self, turno_id: int, telegram_user_id: int) -> bool:
        """
        Deletes a turno.
        
        Args:
            turno_id: ID of the turno to delete
            telegram_user_id: ID of the user (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        return self.turno_repository.deletar(turno_id, telegram_user_id)
