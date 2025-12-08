from datetime import date
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from app.domain.entities.turno import Turno
from app.domain.entities.tipo_turno import TipoTurno
from app.domain.repositories.turno_repository import TurnoRepository
from app.infrastructure.database import models

class SqlAlchemyTurnoRepository(TurnoRepository):
    """
    Implementação SQLAlchemy do repositório de turnos.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: models.TurnoModel) -> Turno:
        """Converte Model SQLAlchemy para Domain Entity."""
        return Turno(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            data_referencia=model.data_referencia,
            hora_inicio=model.hora_inicio,
            hora_fim=model.hora_fim,
            duracao_minutos=model.duracao_minutos,
            tipo=model.tipo.nome if model.tipo else model.tipo_livre,
            tipo_id=model.tipo_turno_id,
            descricao_opcional=model.descricao_opcional,
            event_uid=model.integracao.event_uid if model.integracao else None,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    def _to_model(self, entity: Turno) -> models.TurnoModel:
        """Converte Domain Entity para Model SQLAlchemy (para criação)."""
        db_turno = models.TurnoModel(
            telegram_user_id=entity.telegram_user_id,
            data_referencia=entity.data_referencia,
            hora_inicio=entity.hora_inicio,
            hora_fim=entity.hora_fim,
            duracao_minutos=entity.duracao_minutos,
            tipo_turno_id=entity.tipo_id,
            tipo_livre=entity.tipo if not entity.tipo_id else None,
            descricao_opcional=entity.descricao_opcional,
        )
        
        if entity.event_uid:
            db_turno.integracao = models.IntegracaoCalendario(event_uid=entity.event_uid)

        return db_turno

    async def buscar_tipo_por_nome(self, nome: str) -> Optional[TipoTurno]:
        stmt = select(models.TipoTurno).where(models.TipoTurno.nome.ilike(nome))
        result = await self.session.scalar(stmt)
        if result:
            return TipoTurno(id=result.id, nome=result.nome)
        return None

    async def criar(self, turno: Turno) -> Turno:
        db_turno = self._to_model(turno)
        
        self.session.add(db_turno)
        # Flush para gerar ID
        await self.session.flush()
        
        # Expunge para desconectar da sessão e retornar objeto puro
        # ou apenas refresh para pegar dados gerados
        await self.session.refresh(db_turno)
        
        # Construir entidade manualmente para evitar lazy load trigger em db_turno.tipo
        # E também porque _to_entity faz queries lazy se não estiver carregado
        
        # Mas para garantir consistência, vamos usar o que foi persistido:
        # Porem, db_turno.tipo pode não estar carregado.
        # Simplificação: retorne uma Entity baseada no que inserimos + ID.
        
        return Turno(
            id=db_turno.id,
            telegram_user_id=db_turno.telegram_user_id,
            data_referencia=db_turno.data_referencia,
            hora_inicio=db_turno.hora_inicio,
            hora_fim=db_turno.hora_fim,
            duracao_minutos=db_turno.duracao_minutos,
            tipo=turno.tipo, 
            tipo_id=db_turno.tipo_turno_id,
            descricao_opcional=db_turno.descricao_opcional,
            event_uid=turno.event_uid, 
            criado_em=db_turno.criado_em,
            atualizado_em=db_turno.atualizado_em,
        )

    async def buscar_por_id(self, turno_id: int, telegram_user_id: int) -> Optional[Turno]:
        stmt = select(models.TurnoModel).options(selectinload(models.TurnoModel.tipo)).options(selectinload(models.TurnoModel.integracao)).where(
            models.TurnoModel.id == turno_id,
            models.TurnoModel.telegram_user_id == telegram_user_id
        )
        result = await self.session.scalar(stmt)
        if not result:
            return None
        return self._to_entity(result)

    async def listar_por_periodo(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> List[Turno]:
        stmt = (
            select(models.TurnoModel)
            .options(selectinload(models.TurnoModel.tipo))
            .options(selectinload(models.TurnoModel.integracao))
            .where(models.TurnoModel.telegram_user_id == telegram_user_id)
            .where(models.TurnoModel.data_referencia >= inicio)
            .where(models.TurnoModel.data_referencia <= fim)
            .order_by(models.TurnoModel.data_referencia, models.TurnoModel.hora_inicio)
        )
        result = await self.session.scalars(stmt)
        return [self._to_entity(t) for t in result.all()]

    async def listar_recentes(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> List[Turno]:
        stmt = (
            select(models.TurnoModel)
            .options(selectinload(models.TurnoModel.tipo))
            .options(selectinload(models.TurnoModel.integracao))
            .where(models.TurnoModel.telegram_user_id == telegram_user_id)
            .order_by(models.TurnoModel.criado_em.desc())
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return [self._to_entity(t) for t in result.all()]

    async def deletar(self, turno_id: int, telegram_user_id: int) -> bool:
        stmt = select(models.TurnoModel).where(
            models.TurnoModel.id == turno_id,
            models.TurnoModel.telegram_user_id == telegram_user_id
        )
        turno = await self.session.scalar(stmt)
        if not turno:
            return False
            
        await self.session.delete(turno)
        # O Commit deve ser responsabilidade da UoW ou do Use Case (ou controlador)
        # Mas neste padrão simples, flush aqui.
        await self.session.flush()
        return True

    async def atualizar(self, turno: Turno) -> Turno:
        stmt = select(models.TurnoModel).options(selectinload(models.TurnoModel.tipo)).options(selectinload(models.TurnoModel.integracao)).where(
            models.TurnoModel.id == turno.id,
            models.TurnoModel.telegram_user_id == turno.telegram_user_id
        )
        db_turno = await self.session.scalar(stmt)
        if not db_turno:
            raise ValueError(f"Turno {turno.id} não encontrado para atualização.")

        # Atualiza campos básicos
        db_turno.data_referencia = turno.data_referencia
        db_turno.hora_inicio = turno.hora_inicio
        db_turno.hora_fim = turno.hora_fim
        db_turno.duracao_minutos = turno.duracao_minutos
        db_turno.descricao_opcional = turno.descricao_opcional
        # TODO: Atualizar tipo se mudou

        # Atualiza Integração
        if turno.event_uid:
            if db_turno.integracao:
                db_turno.integracao.event_uid = turno.event_uid
            else:
                db_turno.integracao = models.IntegracaoCalendario(event_uid=turno.event_uid)
        
        await self.session.flush()
        await self.session.refresh(db_turno)
        return self._to_entity(db_turno)

    async def contar_por_periodo(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(models.TurnoModel)
            .where(models.TurnoModel.telegram_user_id == telegram_user_id)
            .where(models.TurnoModel.data_referencia >= inicio)
            .where(models.TurnoModel.data_referencia <= fim)
        )
        return await self.session.scalar(stmt) or 0

