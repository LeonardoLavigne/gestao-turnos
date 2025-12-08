"""
Use case for deleting a turno.
"""
from app.domain.uow import AbstractUnitOfWork


class DeletarTurnoUseCase:
    """
    Use case for deleting a work shift.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def execute(self, turno_id: int, telegram_user_id: int) -> bool:
        """
        Deletes a turno.
        
        Args:
            turno_id: ID of the turno to delete
            telegram_user_id: ID of the user (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        async with self.uow:
            result = await self.uow.turnos.deletar(turno_id, telegram_user_id)
            if result:
                await self.uow.commit()
            return result
