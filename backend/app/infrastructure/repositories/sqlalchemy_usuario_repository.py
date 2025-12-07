"""
SQLAlchemy implementation of UsuarioRepository.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.usuario import Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.database import models


class SqlAlchemyUsuarioRepository(UsuarioRepository):
    """
    SQLAlchemy implementation of the Usuario repository.
    
    Uses SQLAlchemy ORM for persistence operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: models.Usuario) -> Usuario:
        """Converte modelo SQLAlchemy para entidade de domínio."""
        return Usuario(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            nome=model.nome,
            numero_funcionario=model.numero_funcionario,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    def _to_model(self, entity: Usuario) -> models.Usuario:
        """Converte entidade de domínio para modelo SQLAlchemy."""
        return models.Usuario(
            id=entity.id,
            telegram_user_id=entity.telegram_user_id,
            nome=entity.nome,
            numero_funcionario=entity.numero_funcionario,
        )

    async def buscar_por_telegram_id(self, telegram_user_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo Telegram user ID."""
        stmt = select(models.Usuario).where(
            models.Usuario.telegram_user_id == telegram_user_id
        )
        model = await self.session.scalar(stmt)
        if not model:
            return None
        return self._to_entity(model)

    async def criar(self, usuario: Usuario) -> Usuario:
        """Persiste um novo usuário."""
        model = self._to_model(usuario)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def atualizar(self, usuario: Usuario) -> Usuario:
        """Atualiza um usuário existente."""
        stmt = select(models.Usuario).where(
            models.Usuario.telegram_user_id == usuario.telegram_user_id
        )
        model = await self.session.scalar(stmt)
        if not model:
            raise ValueError(f"Usuario with telegram_user_id {usuario.telegram_user_id} not found")
        
        model.nome = usuario.nome
        model.numero_funcionario = usuario.numero_funcionario
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def existe_por_numero_funcionario(self, numero_funcionario: str) -> bool:
        """Verifica se já existe um usuário com o número de funcionário."""
        stmt = select(models.Usuario).where(
            models.Usuario.numero_funcionario == numero_funcionario
        )
        result = await self.session.scalar(stmt)
        return result is not None
