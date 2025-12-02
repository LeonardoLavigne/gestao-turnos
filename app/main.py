from datetime import date
import calendar

from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import crud, schemas, models
from .infrastructure.middleware import RLSMiddleware


# ✅ Usar Alembic migrations ao invés de create_all
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestão de Turnos")

# ✅ Registrar middleware RLS
app.add_middleware(RLSMiddleware)


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
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get("/relatorios/mes/pdf")
def relatorio_mes_pdf(
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    telegram_user_id: int = Query(None),
    db: Session = Depends(get_db),
):
    from .reports import gerar_pdf_relatorio
    from fastapi.responses import Response

    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    
    # Buscar informações do usuário se telegram_user_id for fornecido
    usuario_info = None
    if telegram_user_id:
        usuario = crud.get_usuario_by_telegram_id(db, telegram_user_id)
        if usuario:
            usuario_info = {
                "nome": usuario.nome,
                "numero_funcionario": usuario.numero_funcionario
            }
    
    pdf_bytes = gerar_pdf_relatorio(turnos, inicio, fim, usuario_info)
    
    filename = f"relatorio_{ano}_{mes:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/turnos/recentes", response_model=list[schemas.TurnoRead])
def listar_recentes(
    limit: int = 5,
    db: Session = Depends(get_db),
):
    turnos = crud.listar_turnos_recentes(db, limit)
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


@app.delete("/turnos/{turno_id}", status_code=204)
def deletar_turno(turno_id: int, db: Session = Depends(get_db)):
    sucesso = crud.delete_turno(db, turno_id)
    if not sucesso:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    return None


# Endpoints de Usuario
@app.get("/usuarios/{telegram_user_id}", response_model=schemas.UsuarioRead)
def get_usuario(telegram_user_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    usuario = crud.get_usuario_by_telegram_id(db, telegram_user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@app.post("/usuarios", response_model=schemas.UsuarioRead, status_code=201)
def criar_usuario(usuario_in: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    # Verificar se já existe
    existe = crud.get_usuario_by_telegram_id(db, usuario_in.telegram_user_id)
    if existe:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    
    usuario = crud.criar_usuario(db, usuario_in)
    return usuario


@app.put("/usuarios/{telegram_user_id}", response_model=schemas.UsuarioRead)
def atualizar_usuario(
    telegram_user_id: int,
    usuario_in: schemas.UsuarioUpdate,
    db: Session = Depends(get_db)
):
    from fastapi import HTTPException
    usuario = crud.atualizar_usuario(db, telegram_user_id, usuario_in)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario



