from datetime import datetime, date, time, timedelta
from typing import Iterable

from sqlalchemy import select, func
from sqlalchemy.orm import Session

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


def criar_turno(db: Session, payload: schemas.TurnoCreate) -> models.Turno:
    duracao = calcular_duracao_minutos(
        payload.data_referencia, payload.hora_inicio, payload.hora_fim
    )

    tipo_db: models.TipoTurno | None = None
    tipo_livre: str | None = None
    if payload.tipo:
        stmt_tipo = select(models.TipoTurno).where(
            func.lower(models.TipoTurno.nome) == payload.tipo.lower()
        )
        tipo_db = db.scalar(stmt_tipo)
        if not tipo_db:
            tipo_livre = payload.tipo

    turno = models.Turno(
        data_referencia=payload.data_referencia,
        hora_inicio=payload.hora_inicio,
        hora_fim=payload.hora_fim,
        duracao_minutos=duracao,
        tipo=tipo_db,
        tipo_livre=tipo_livre,
        descricao_opcional=payload.descricao_opcional,
    )
    db.add(turno)
    db.flush()

    # integração CalDAV (one-way)
    try:
        uid_existente: str | None = None
        if turno.integracao is not None:
            uid_existente = turno.integracao.event_uid
        new_uid = criar_ou_atualizar_evento(turno, uid_existente)

        if turno.integracao is None:
            integ = models.IntegracaoCalendario(
                turno_id=turno.id,
                event_uid=new_uid,
            )
            db.add(integ)
        else:
            turno.integracao.event_uid = new_uid
    except Exception:
        # não quebra o fluxo principal se a integração falhar
        pass

    db.commit()
    db.refresh(turno)
    return turno


def listar_turnos_periodo(
    db: Session,
    inicio: date,
    fim: date,
) -> list[models.Turno]:
    stmt = (
        select(models.Turno)
        .where(models.Turno.data_referencia >= inicio)
        .where(models.Turno.data_referencia <= fim)
        .order_by(models.Turno.data_referencia, models.Turno.hora_inicio)
    )
    return list(db.scalars(stmt).all())


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


def listar_turnos_recentes(db: Session, limit: int = 5) -> list[models.Turno]:
    stmt = (
        select(models.Turno)
        .order_by(models.Turno.criado_em.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def delete_turno(db: Session, turno_id: int) -> bool:
    turno = db.get(models.Turno, turno_id)
    if not turno:
        return False
    
    # Se tiver integração, tentar remover (opcional, pode falhar sem problemas)
    # Aqui só deletamos do banco local.
    # Se quisesse deletar do caldav, teria que chamar caldav_client.delete_evento(turno.integracao.event_uid)
    # Mas o caldav_client atual não expõe delete. Deixaremos assim por enquanto.
    
    db.delete(turno)
    db.commit()
    return True


# Funções CRUD para Usuario
def get_usuario_by_telegram_id(db: Session, telegram_user_id: int) -> models.Usuario | None:
    stmt = select(models.Usuario).where(
        models.Usuario.telegram_user_id == telegram_user_id
    )
    return db.scalar(stmt)


def criar_usuario(db: Session, payload: schemas.UsuarioCreate) -> models.Usuario:
    usuario = models.Usuario(
        telegram_user_id=payload.telegram_user_id,
        nome=payload.nome,
        numero_funcionario=payload.numero_funcionario,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def atualizar_usuario(
    db: Session, telegram_user_id: int, payload: schemas.UsuarioUpdate
) -> models.Usuario | None:
    usuario = get_usuario_by_telegram_id(db, telegram_user_id)
    if not usuario:
        return None
    
    if payload.nome is not None:
        usuario.nome = payload.nome
    if payload.numero_funcionario is not None:
        usuario.numero_funcionario = payload.numero_funcionario
    
    db.commit()
    db.refresh(usuario)
    return usuario


