from abc import ABC, abstractmethod
from typing import Optional
from app.domain.repositories.turno_repository import TurnoRepository
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.domain.repositories.assinatura_repository import AssinaturaRepository

class AbstractUnitOfWork(ABC):

    turnos: TurnoRepository
    usuarios: UsuarioRepository
    assinaturas: AssinaturaRepository

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type:
            await self.rollback()
        # Explicit commit should be called by uses cases, but strict UoW often commits on exit if no error?
        # Better pattern: manual commit in UseCase, rollback on error in exit if not committed.
        # Minimal interface:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
