import calendar
from datetime import date
from fastapi import APIRouter, Depends, Query, Response, HTTPException

from app.presentation import schemas
from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase
from app.application.use_cases.relatorios.baixar_relatorio import BaixarRelatorioPdfUseCase
from app.api.deps import (
    get_current_user_id,
    get_gerar_relatorio_use_case,
    get_baixar_relatorio_pdf_use_case
)

router = APIRouter()

@router.get(
    "/periodo",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório por período customizado",
)
async def relatorio_periodo(
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    user_id: int = Depends(get_current_user_id),
    use_case: GerarRelatorioUseCase = Depends(get_gerar_relatorio_use_case),
):
    """Gera relatório de turnos para um período customizado."""
    return await use_case.execute(user_id, inicio, fim)


@router.get(
    "/semana",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório semanal",
)
async def relatorio_semana(
    ano: int = Query(..., ge=2000, le=2100),
    semana: int = Query(..., ge=1, le=53),
    user_id: int = Depends(get_current_user_id),
    use_case: GerarRelatorioUseCase = Depends(get_gerar_relatorio_use_case),
):
    """Gera relatório de turnos para uma semana específica."""
    inicio = date.fromisocalendar(ano, semana, 1)
    fim = date.fromisocalendar(ano, semana, 7)

    return await use_case.execute(user_id, inicio, fim)


@router.get(
    "/mes",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório mensal",
)
async def relatorio_mes(
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    user_id: int = Depends(get_current_user_id),
    use_case: GerarRelatorioUseCase = Depends(get_gerar_relatorio_use_case),
):
    """Gera relatório de turnos para um mês específico."""
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    return await use_case.execute(user_id, inicio, fim)


@router.get(
    "/mes/pdf",
    summary="Relatório mensal em PDF",
)
async def relatorio_mes_pdf(
    ano: int,
    mes: int,
    user_id: int = Depends(get_current_user_id),
    use_case: BaixarRelatorioPdfUseCase = Depends(get_baixar_relatorio_pdf_use_case),
):
    """Gera relatório em PDF dos turnos do mês."""
    # Validar mês
    try:
        last_day = calendar.monthrange(ano, mes)[1]
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, last_day)
    except Exception:
        raise HTTPException(status_code=400, detail="Data inválida")
    
    pdf_bytes = await use_case.execute(user_id, inicio, fim)
    if not pdf_bytes:
            # Caso raro onde passou checks mas gerou None
            raise HTTPException(status_code=500, detail="Erro ao gerar PDF")
            
    filename = f"relatorio_{ano}_{mes:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
