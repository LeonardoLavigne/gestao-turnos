from datetime import date
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.presentation import schemas
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository
from app.infrastructure.external.caldav_service import CalDAVService
from app.application.use_cases.turnos.listar_turnos import ListarTurnosPeriodoUseCase, ListarTurnosRecentesUseCase
from app.application.use_cases.turnos.deletar_turno import DeletarTurnoUseCase

router = APIRouter()

@router.post(
    "",
    response_model=schemas.TurnoRead,
    summary="Criar novo turno",
)
async def criar_turno(
    request: Request,
    turno_in: schemas.TurnoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo turno de trabalho para o usuário autenticado via RLS."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None)
    if not telegram_user_id:
         # Fallback: tentar header diretamente se middleware falhar
         user_id_header = request.headers.get("X-Telegram-User-ID")
         if user_id_header:
             telegram_user_id = int(user_id_header)
         else:
             raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")
             
    repo = SqlAlchemyTurnoRepository(db)
    assinatura_repo = SqlAlchemyAssinaturaRepository(db)
    calendar_service = CalDAVService()
    
    use_case = CriarTurnoUseCase(repo, assinatura_repo, calendar_service, db)
    
    turno_entity = await use_case.execute(
        telegram_user_id=telegram_user_id,
        data_referencia=turno_in.data_referencia,
        hora_inicio=turno_in.hora_inicio,
        hora_fim=turno_in.hora_fim,
        tipo=turno_in.tipo,
        descricao_opcional=turno_in.descricao_opcional,
    )
    
    return schemas.TurnoRead.model_validate(turno_entity)


@router.get(
    "",
    response_model=list[schemas.TurnoRead],
    summary="Listar turnos por período",
)
async def listar_turnos(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Lista turnos do usuário dentro do período especificado."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    repo = SqlAlchemyTurnoRepository(db)
    use_case = ListarTurnosPeriodoUseCase(repo)
    
    turnos = await use_case.execute(telegram_user_id, inicio, fim)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@router.get(
    "/recentes",
    response_model=list[schemas.TurnoRead],
    summary="Listar turnos recentes",
)
async def listar_recentes(
    request: Request,
    limit: int = Query(5, ge=1, le=50, description="Número máximo de turnos"),
    db: AsyncSession = Depends(get_db),
):
    """Lista os turnos mais recentes do usuário."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    repo = SqlAlchemyTurnoRepository(db)
    use_case = ListarTurnosRecentesUseCase(repo)

    turnos = await use_case.execute(telegram_user_id, limit)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@router.delete(
    "/{turno_id}",
    status_code=204,
    summary="Deletar turno",
)
async def deletar_turno(
    request: Request,
    turno_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deleta um turno do usuário."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    repo = SqlAlchemyTurnoRepository(db)
    use_case = DeletarTurnoUseCase(repo, db)

    sucesso = await use_case.execute(turno_id, telegram_user_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    return None
