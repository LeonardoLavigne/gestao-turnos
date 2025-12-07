import calendar
from datetime import date
from fastapi import APIRouter, Depends, Request, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.presentation import schemas
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository
from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase
from app.application.use_cases.relatorios.baixar_relatorio import BaixarRelatorioPdfUseCase
from app.infrastructure.services.pdf_service import ReportLabPdfService

router = APIRouter()

@router.get(
    "/periodo",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório por período customizado",
)
async def relatorio_periodo(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para um período customizado."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)
    
    return await use_case.execute(telegram_user_id, inicio, fim)


@router.get(
    "/semana",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório semanal",
)
async def relatorio_semana(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    semana: int = Query(..., ge=1, le=53),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para uma semana específica."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    inicio = date.fromisocalendar(ano, semana, 1)
    fim = date.fromisocalendar(ano, semana, 7)

    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)

    return await use_case.execute(telegram_user_id, inicio, fim)


@router.get(
    "/mes",
    response_model=schemas.RelatorioPeriodo,
    summary="Relatório mensal",
)
async def relatorio_mes(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para um mês específico."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)

    return await use_case.execute(telegram_user_id, inicio, fim)


@router.get(
    "/mes/pdf",
    summary="Relatório mensal em PDF",
)
async def relatorio_mes_pdf(
    ano: int,
    mes: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório em PDF dos turnos do mês."""
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    # Validar mês
    try:
        last_day = calendar.monthrange(ano, mes)[1]
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, last_day)
    except Exception:
        raise HTTPException(status_code=400, detail="Data inválida")
    
    turno_repo = SqlAlchemyTurnoRepository(db)
    usuario_repo = SqlAlchemyUsuarioRepository(db)
    assinatura_repo = SqlAlchemyAssinaturaRepository(db)
    pdf_service = ReportLabPdfService() # Concrete implementation
    
    use_case = BaixarRelatorioPdfUseCase(
        turno_repository=turno_repo,
        usuario_repository=usuario_repo,
        assinatura_repository=assinatura_repo,
        relatorio_service=pdf_service
    )
    
    try:
        pdf_bytes = await use_case.execute(telegram_user_id, inicio, fim)
        if not pdf_bytes:
             # Caso raro onde passou checks mas gerou None
             raise HTTPException(status_code=500, detail="Erro ao gerar PDF")
             
        filename = f"relatorio_{ano}_{mes:02d}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        # Generic fallback
        print(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
