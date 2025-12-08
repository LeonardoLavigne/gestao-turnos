from fastapi import Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db
from app.core.config import get_settings, Settings
from app.core.security import verify_token
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.domain.uow import AbstractUnitOfWork

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

# Scheme para OpenAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_current_user_id(
    request: Request, 
    token: str | None = Depends(oauth2_scheme)
) -> int:
    """
    Porteiro Bilingue:
    1. Aceita Bot com X-Internal-Secret + X-Telegram-User-ID.
    2. Aceita Web com Bearer Token (JWT).
    """
    settings = get_settings()

    # 1. Estratégia BOT
    secret = request.headers.get("X-Internal-Secret")
    if secret == settings.internal_api_key:
        user_id_header = request.headers.get("X-Telegram-User-ID")
        if user_id_header:
            return int(user_id_header)

    # 2. Estratégia WEB (JWT via Header ou Cookie)
    token_to_verify = token
    if not token_to_verify:
        token_to_verify = request.cookies.get("auth_token")

    if token_to_verify:
        payload = verify_token(token_to_verify)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                return int(user_id)

    raise HTTPException(status_code=401, detail="Não autenticado")


# Repository Providers
def get_turno_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyTurnoRepository:
    return SqlAlchemyTurnoRepository(db)

def get_usuario_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyUsuarioRepository:
    return SqlAlchemyUsuarioRepository(db)

def get_assinatura_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyAssinaturaRepository:
    return SqlAlchemyAssinaturaRepository(db)

# Service Providers
def get_calendar_service(settings: Settings = Depends(get_settings)) -> CalendarService:
    return CalDAVService(settings)

def get_relatorio_service() -> RelatorioService:
    return ReportLabPdfService()



def get_uow(db: AsyncSession = Depends(get_db)) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(db)

from app.infrastructure.background_adapter import FastAPIBackgroundTaskQueue
from fastapi import BackgroundTasks

# Ports and Adapters
from app.domain.ports.caldav_sync_port import CalDavSyncTaskPort
from app.infrastructure.services.caldav_sync_adapter import CalDavSyncTaskAdapter


# Use Case Factories
def get_caldav_sync_task_port(
    background_tasks: BackgroundTasks,
) -> CalDavSyncTaskPort:
    bg_queue = FastAPIBackgroundTaskQueue(background_tasks)
    return CalDavSyncTaskAdapter(bg_queue)


def get_criar_turno_use_case(
    uow: AbstractUnitOfWork = Depends(get_uow),
    calendar_service: CalendarService = Depends(get_calendar_service),
    settings: Settings = Depends(get_settings),
    caldav_sync_task_port: CalDavSyncTaskPort = Depends(get_caldav_sync_task_port),
) -> CriarTurnoUseCase:
    return CriarTurnoUseCase(uow, calendar_service, settings, caldav_sync_task_port)

def get_listar_turnos_periodo_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> ListarTurnosPeriodoUseCase:
    return ListarTurnosPeriodoUseCase(turno_repo)

def get_listar_turnos_recentes_use_case(
    turno_repo: SqlAlchemyTurnoRepository = Depends(get_turno_repo),
) -> ListarTurnosRecentesUseCase:
    return ListarTurnosRecentesUseCase(turno_repo)

def get_deletar_turno_use_case(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> DeletarTurnoUseCase:
    return DeletarTurnoUseCase(uow)

def get_criar_usuario_use_case(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> CriarUsuarioUseCase:
    return CriarUsuarioUseCase(uow)

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
