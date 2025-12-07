from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db

# Repositories
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository

# Services
from app.infrastructure.external.caldav_service import CalDAVService
from app.infrastructure.services.pdf_service import ReportLabPdfService
from app.domain.services.calendar_service import CalendarService
from app.domain.services.relatorio_service import RelatorioService

# Use Cases
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.application.use_cases.turnos.listar_turnos import ListarTurnosPeriodoUseCase, ListarTurnosRecentesUseCase
from app.application.use_cases.turnos.deletar_turno import DeletarTurnoUseCase
from app.application.use_cases.usuarios.criar_usuario import CriarUsuarioUseCase
from app.application.use_cases.usuarios.atualizar_usuario import AtualizarUsuarioUseCase
from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase
from app.application.use_cases.relatorios.baixar_relatorio import BaixarRelatorioPdfUseCase

def get_current_user_id(request: Request) -> int:
    """Extrai o ID do usuário do Telegram do request (via Middleware ou Header)."""
    user_id = getattr(request.state, "telegram_user_id", None)
    if not user_id:
        user_id_header = request.headers.get("X-Telegram-User-ID")
        if user_id_header:
            return int(user_id_header)
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")
    return user_id

# Repository Providers
def get_turno_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyTurnoRepository:
    return SqlAlchemyTurnoRepository(db)

def get_usuario_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyUsuarioRepository:
    return SqlAlchemyUsuarioRepository(db)

def get_assinatura_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyAssinaturaRepository:
    return SqlAlchemyAssinaturaRepository(db)

# Service Providers
def get_calendar_service() -> CalendarService:
    return CalDAVService()

def get_relatorio_service() -> RelatorioService:
    return ReportLabPdfService()

# Use Case Factories
def get_criar_turno_use_case(
    db: AsyncSession = Depends(get_db),
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
    assinatura_repo: SqlAlchemyAssinaturaRepository = Depends(get_assinatura_repo),
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> CriarTurnoUseCase:
    return CriarTurnoUseCase(turno_repo, assinatura_repo, calendar_service, db)

def get_listar_turnos_periodo_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> ListarTurnosPeriodoUseCase:
    return ListarTurnosPeriodoUseCase(turno_repo)

def get_listar_turnos_recentes_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> ListarTurnosRecentesUseCase:
    return ListarTurnosRecentesUseCase(turno_repo)

def get_deletar_turno_use_case(
    db: AsyncSession = Depends(get_db),
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> DeletarTurnoUseCase:
    return DeletarTurnoUseCase(turno_repo, db)

def get_criar_usuario_use_case(
    usuario_repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
    assinatura_repo: SqlAlchemyAssinaturaRepository = Depends(get_assinatura_repo),
) -> CriarUsuarioUseCase:
    return CriarUsuarioUseCase(usuario_repo, assinatura_repo)

def get_atualizar_usuario_use_case(
    usuario_repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
) -> AtualizarUsuarioUseCase:
    return AtualizarUsuarioUseCase(usuario_repo)

def get_gerar_relatorio_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> GerarRelatorioUseCase:
    return GerarRelatorioUseCase(turno_repo)

def get_baixar_relatorio_pdf_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
    usuario_repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
    assinatura_repo: SqlAlchemyAssinaturaRepository = Depends(get_assinatura_repo),
    relatorio_service: RelatorioService = Depends(get_relatorio_service),
) -> BaixarRelatorioPdfUseCase:
    return BaixarRelatorioPdfUseCase(turno_repo, usuario_repo, assinatura_repo, relatorio_service)
