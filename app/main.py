from datetime import date
import calendar

from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import crud, schemas, models


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestão de Turnos")


@app.post("/turnos", response_model=schemas.TurnoRead)
def criar_turno(turno_in: schemas.TurnoCreate, db: Session = Depends(get_db)):
    turno = crud.criar_turno(db, turno_in)
    tipo_nome = turno.tipo.nome if turno.tipo is not None else turno.tipo_livre
    return schemas.TurnoRead(
        id=turno.id,
        data_referencia=turno.data_referencia,
        hora_inicio=turno.hora_inicio,
        hora_fim=turno.hora_fim,
        duracao_minutos=turno.duracao_minutos,
        tipo=tipo_nome,
        descricao_opcional=turno.descricao_opcional,
        criado_em=turno.criado_em,
        atualizado_em=turno.atualizado_em,
    )


@app.get("/turnos", response_model=list[schemas.TurnoRead])
def listar_turnos(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Session = Depends(get_db),
):
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    resultado: list[schemas.TurnoRead] = []
    for t in turnos:
        tipo_nome = t.tipo.nome if t.tipo is not None else t.tipo_livre
        resultado.append(
            schemas.TurnoRead(
                id=t.id,
                data_referencia=t.data_referencia,
                hora_inicio=t.hora_inicio,
                hora_fim=t.hora_fim,
                duracao_minutos=t.duracao_minutos,
                tipo=tipo_nome,
                descricao_opcional=t.descricao_opcional,
                criado_em=t.criado_em,
                atualizado_em=t.atualizado_em,
            )
        )
    return resultado


@app.get("/relatorios/periodo", response_model=schemas.RelatorioPeriodo)
def relatorio_periodo(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Session = Depends(get_db),
):
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get("/relatorios/semana", response_model=schemas.RelatorioPeriodo)
def relatorio_semana(
    ano: int = Query(..., ge=2000, le=2100),
    semana: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    inicio = date.fromisocalendar(ano, semana, 1)
    fim = date.fromisocalendar(ano, semana, 7)
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get("/relatorios/mes", response_model=schemas.RelatorioPeriodo)
def relatorio_mes(
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


