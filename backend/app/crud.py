from datetime import datetime, date, time, timedelta, UTC
from typing import Iterable, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas
from .caldav_client import criar_ou_atualizar_evento


def calcular_duracao_minutos(
    data_ref: date,
    inicio: time,
    fim: time,
) -> int:
    dt_inicio = datetime.combine(data_ref, inicio)
    dt_fim = datetime.combine(data_ref, fim)
    if dt_fim <= dt_inicio:
        dt_fim += timedelta(days=1)
    return int((dt_fim - dt_inicio).total_seconds() // 60)


# criar_turno function moved to CriarTurnoUseCase for better architecture.



async def listar_turnos_periodo(
    db: AsyncSession,
    inicio: date,
    fim: date,
) -> Sequence[models.Turno]:
    stmt = (
        select(models.Turno)
        .where(models.Turno.data_referencia >= inicio)
        .where(models.Turno.data_referencia <= fim)
        .order_by(models.Turno.data_referencia, models.Turno.hora_inicio)
    )
    result = await db.scalars(stmt)
    return result.all()


def _nome_tipo(turno: models.Turno) -> str | None:
    if turno.tipo is not None:
        return turno.tipo.nome
    return turno.tipo_livre


def gerar_relatorio_periodo(
    turnos: Iterable[models.Turno],
    inicio: date,
    fim: date,
) -> schemas.RelatorioPeriodo:
    por_data: dict[date, list[models.Turno]] = {}
    for turno in turnos:
        por_data.setdefault(turno.data_referencia, []).append(turno)

    dias: list[schemas.RelatorioDia] = []
    total_minutos_periodo = 0

    for dia in sorted(por_data.keys()):
        turnos_dia = por_data[dia]
        total_dia = sum(t.duracao_minutos for t in turnos_dia)
        total_minutos_periodo += total_dia

        por_tipo: dict[str, int] = {}
        for t in turnos_dia:
            nome_tipo = _nome_tipo(t) or "sem_tipo"
            por_tipo[nome_tipo] = por_tipo.get(nome_tipo, 0) + t.duracao_minutos

        dias.append(
            schemas.RelatorioDia(
                data=dia,
                total_minutos=total_dia,
                por_tipo=por_tipo,
            )
        )

    return schemas.RelatorioPeriodo(
        inicio=inicio,
        fim=fim,
        total_minutos=total_minutos_periodo,
        dias=dias,
    )


async def listar_turnos_recentes(db: AsyncSession, limit: int = 5) -> Sequence[models.Turno]:
    stmt = (
        select(models.Turno)
        .order_by(models.Turno.criado_em.desc())
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return result.all()


async def delete_turno(db: AsyncSession, turno_id: int) -> bool:
    turno = await db.get(models.Turno, turno_id)
    if not turno:
        return False
    
    await db.delete(turno)
    await db.commit()
    return True


# Funções CRUD para Usuario
async def get_usuario_by_telegram_id(db: AsyncSession, telegram_user_id: int) -> models.Usuario | None:
    stmt = select(models.Usuario).where(
        models.Usuario.telegram_user_id == telegram_user_id
    )
    return await db.scalar(stmt)


async def criar_usuario(db: AsyncSession, payload: schemas.UsuarioCreate) -> models.Usuario:
    usuario = models.Usuario(
        telegram_user_id=payload.telegram_user_id,
        nome=payload.nome,
        numero_funcionario=payload.numero_funcionario,
    )
    db.add(usuario)
    
    # 🌟 Criar assinatura TRIAL de 14 dias
    agora = datetime.now(UTC)
    fim_trial = agora + timedelta(days=14)
    
    assinatura = models.Assinatura(
        telegram_user_id=payload.telegram_user_id,
        stripe_customer_id=f"trial_{payload.telegram_user_id}",
        stripe_subscription_id=None,
        status="trialing",
        plano="pro",
        data_inicio=agora,
        data_fim=fim_trial,
    )
    db.add(assinatura)
    
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def atualizar_usuario(
    db: AsyncSession, telegram_user_id: int, payload: schemas.UsuarioUpdate
) -> models.Usuario | None:
    usuario = await get_usuario_by_telegram_id(db, telegram_user_id)
    if not usuario:
        return None
    
    if payload.nome is not None:
        usuario.nome = payload.nome
    if payload.numero_funcionario is not None:
        usuario.numero_funcionario = payload.numero_funcionario
    
    await db.commit()
    await db.refresh(usuario)
    return usuario
