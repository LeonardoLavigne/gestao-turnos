from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository
from app import models

class SqlAlchemyTurnoRepository(TurnoRepository):
    """
    Implementação SQLAlchemy do repositório de turnos.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: models.Turno) -> Turno:
        """Converte Model SQLAlchemy para Domain Entity."""
        return Turno(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            data_referencia=model.data_referencia,
            hora_inicio=model.hora_inicio,
            hora_fim=model.hora_fim,
            duracao_minutos=model.duracao_minutos,
            tipo=model.tipo.nome if model.tipo else model.tipo_livre,
            descricao_opcional=model.descricao_opcional,
            event_uid=model.integracao.event_uid if model.integracao else None,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    async def criar(self, turno: Turno) -> Turno:
        # TODO: Lookup TipoTurno logic if needed, but for now using tipo_livre primarily
        # unless name matches existing type.
        
        tipo_db = None
        tipo_livre = None
        
        if turno.tipo:
            # Tenta buscar tipo existente pelo nome (case insensitive)
            stmt = select(models.TipoTurno).where(
                models.TipoTurno.nome.ilike(turno.tipo)
            )
            tipo_db = await self.session.scalar(stmt)
            if not tipo_db:
                tipo_livre = turno.tipo
        
        db_turno = models.Turno(
            telegram_user_id=turno.telegram_user_id,
            data_referencia=turno.data_referencia,
            hora_inicio=turno.hora_inicio,
            hora_fim=turno.hora_fim,
            duracao_minutos=turno.duracao_minutos,
            tipo=tipo_db,
            tipo_livre=tipo_livre,
            descricao_opcional=turno.descricao_opcional,
        )
        
        if turno.event_uid:
            db_turno.integracao = models.IntegracaoCalendario(event_uid=turno.event_uid)

        self.session.add(db_turno)
        # Flush para gerar ID
        await self.session.flush()
        
        # Expunge para desconectar da sessão e retornar objeto puro
        # ou apenas refresh para pegar dados gerados
        await self.session.refresh(db_turno)
        
        # Construir entidade manualmente para evitar lazy load trigger em db_turno.tipo
        return Turno(
            id=db_turno.id,
            telegram_user_id=db_turno.telegram_user_id,
            data_referencia=db_turno.data_referencia,
            hora_inicio=db_turno.hora_inicio,
            hora_fim=db_turno.hora_fim,
            duracao_minutos=db_turno.duracao_minutos,
            tipo=tipo_db.nome if tipo_db else turno.tipo, # Usa o objeto que já temos ou a string original
            descricao_opcional=db_turno.descricao_opcional,
            event_uid=None, # New turn has no event_uid yet until updated
            criado_em=db_turno.criado_em,
            atualizado_em=db_turno.atualizado_em,
        )

    async def buscar_por_id(self, turno_id: int, telegram_user_id: int) -> Optional[Turno]:
        stmt = select(models.Turno).options(selectinload(models.Turno.tipo)).options(selectinload(models.Turno.integracao)).where(
            models.Turno.id == turno_id,
            models.Turno.telegram_user_id == telegram_user_id
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
            select(models.Turno)
            .options(selectinload(models.Turno.tipo))
            .options(selectinload(models.Turno.integracao))
            .where(models.Turno.telegram_user_id == telegram_user_id)
            .where(models.Turno.data_referencia >= inicio)
            .where(models.Turno.data_referencia <= fim)
            .order_by(models.Turno.data_referencia, models.Turno.hora_inicio)
        )
        result = await self.session.scalars(stmt)
        return [self._to_entity(t) for t in result.all()]

    async def listar_recentes(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> List[Turno]:
        stmt = (
            select(models.Turno)
            .options(selectinload(models.Turno.tipo))
            .options(selectinload(models.Turno.integracao))
            .where(models.Turno.telegram_user_id == telegram_user_id)
            .order_by(models.Turno.criado_em.desc())
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return [self._to_entity(t) for t in result.all()]

    async def deletar(self, turno_id: int, telegram_user_id: int) -> bool:
        stmt = select(models.Turno).where(
            models.Turno.id == turno_id,
            models.Turno.telegram_user_id == telegram_user_id
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
        stmt = select(models.Turno).options(selectinload(models.Turno.tipo)).options(selectinload(models.Turno.integracao)).where(
            models.Turno.id == turno.id,
            models.Turno.telegram_user_id == turno.telegram_user_id
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
