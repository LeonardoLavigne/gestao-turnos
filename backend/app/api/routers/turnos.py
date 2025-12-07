from datetime import date
from fastapi import APIRouter, Depends, Query

from app.presentation import schemas
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.application.use_cases.turnos.listar_turnos import ListarTurnosPeriodoUseCase, ListarTurnosRecentesUseCase
from app.application.use_cases.turnos.deletar_turno import DeletarTurnoUseCase
from app.api.deps import (
    get_current_user_id,
    get_criar_turno_use_case,
    get_listar_turnos_periodo_use_case,
    get_listar_turnos_recentes_use_case,
    get_deletar_turno_use_case
)

router = APIRouter()

@router.post(
    "",
    response_model=schemas.TurnoRead,
    summary="Criar novo turno",
)
async def criar_turno(
    turno_in: schemas.TurnoCreate,
    user_id: int = Depends(get_current_user_id),
    use_case: CriarTurnoUseCase = Depends(get_criar_turno_use_case),
):
    """Cria um novo turno de trabalho para o usuário autenticado via RLS."""
    turno_entity = await use_case.execute(
        telegram_user_id=user_id,
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
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    user_id: int = Depends(get_current_user_id),
    use_case: ListarTurnosPeriodoUseCase = Depends(get_listar_turnos_periodo_use_case),
):
    """Lista turnos do usuário dentro do período especificado."""
    turnos = await use_case.execute(user_id, inicio, fim)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@router.get(
    "/recentes",
    response_model=list[schemas.TurnoRead],
    summary="Listar turnos recentes",
)
async def listar_recentes(
    limit: int = Query(5, ge=1, le=50, description="Número máximo de turnos"),
    user_id: int = Depends(get_current_user_id),
    use_case: ListarTurnosRecentesUseCase = Depends(get_listar_turnos_recentes_use_case),
):
    """Lista os turnos mais recentes do usuário."""
    turnos = await use_case.execute(user_id, limit)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@router.delete(
    "/{turno_id}",
    status_code=204,
    summary="Deletar turno",
)
async def deletar_turno(
    turno_id: int,
    user_id: int = Depends(get_current_user_id),
    use_case: DeletarTurnoUseCase = Depends(get_deletar_turno_use_case),
):
    """Deleta um turno do usuário."""
    sucesso = await use_case.execute(turno_id, user_id)
    # Exceção de "Turno não encontrado" deveria vir do UseCase
    # Mas mantendo consistência com anterior:
    if not sucesso:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    return None
