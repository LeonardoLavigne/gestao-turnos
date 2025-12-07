"""
SQLAlchemy implementation of TurnoRepository.
"""
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository
from app import models


class SQLAlchemyTurnoRepository(TurnoRepository):
    """
    SQLAlchemy implementation of the Turno repository.
    
    Uses SQLAlchemy ORM for persistence operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: models.Turno) -> Turno:
        """Converte modelo SQLAlchemy para entidade de domínio."""
        tipo_nome = model.tipo.nome if model.tipo is not None else model.tipo_livre
        return Turno(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            data_referencia=model.data_referencia,
            hora_inicio=model.hora_inicio,
            hora_fim=model.hora_fim,
            duracao_minutos=model.duracao_minutos,
            tipo=tipo_nome,
            descricao_opcional=model.descricao_opcional,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    def _to_model(self, entity: Turno) -> models.Turno:
        """Converte entidade de domínio para modelo SQLAlchemy."""
        return models.Turno(
            id=entity.id,
            telegram_user_id=entity.telegram_user_id,
            data_referencia=entity.data_referencia,
            hora_inicio=entity.hora_inicio,
            hora_fim=entity.hora_fim,
            duracao_minutos=entity.duracao_minutos,
            tipo_livre=entity.tipo,  # Using tipo_livre for simplicity
            descricao_opcional=entity.descricao_opcional,
        )

    def criar(self, turno: Turno) -> Turno:
        """Persiste um novo turno."""
        model = self._to_model(turno)
        self.session.add(model)
        self.session.flush()
        
        # Expunge to prevent lazy loading issues after commit
        self.session.expunge(model)
        self.session.commit()
        
        return self._to_entity(model)

    def buscar_por_id(self, turno_id: int, telegram_user_id: int) -> Optional[Turno]:
        """Busca um turno por ID."""
        model = self.session.get(models.Turno, turno_id)
        if not model:
            return None
        return self._to_entity(model)

    def listar_por_periodo(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> List[Turno]:
        """Lista turnos de um usuário em um período."""
        stmt = (
            select(models.Turno)
            .where(models.Turno.data_referencia >= inicio)
            .where(models.Turno.data_referencia <= fim)
            .order_by(models.Turno.data_referencia, models.Turno.hora_inicio)
        )
        results = self.session.scalars(stmt).all()
        return [self._to_entity(model) for model in results]

    def listar_recentes(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> List[Turno]:
        """Lista os turnos mais recentes de um usuário."""
        stmt = (
            select(models.Turno)
            .order_by(models.Turno.criado_em.desc())
            .limit(limit)
        )
        results = self.session.scalars(stmt).all()
        return [self._to_entity(model) for model in results]

    def deletar(self, turno_id: int, telegram_user_id: int) -> bool:
        """Deleta um turno."""
        model = self.session.get(models.Turno, turno_id)
        if not model:
            return False
        
        self.session.delete(model)
        self.session.commit()
        return True
