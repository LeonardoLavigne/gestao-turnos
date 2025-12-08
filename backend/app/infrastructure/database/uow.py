from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.uow import AbstractUnitOfWork
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: AsyncSession):
        self.session = session
        # Initialize repositories with the session
        self.turnos = SqlAlchemyTurnoRepository(session)
        self.usuarios = SqlAlchemyUsuarioRepository(session)
        self.assinaturas = SqlAlchemyAssinaturaRepository(session)

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type:
            await self.rollback()
        
    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
