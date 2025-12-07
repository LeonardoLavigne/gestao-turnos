from datetime import date
from typing import Optional, Dict

from app.domain.repositories.turno_repository import TurnoRepository
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.domain.repositories.assinatura_repository import AssinaturaRepository
from app.domain.services.relatorio_service import RelatorioService

class BaixarRelatorioPdfUseCase:
    """
    Use case para baixar o relatório PDF de turnos.
    Encapsula verificação de assinatura e orquestração de dados.
    """
    def __init__(
        self,
        turno_repository: TurnoRepository,
        usuario_repository: UsuarioRepository,
        assinatura_repository: AssinaturaRepository,
        relatorio_service: RelatorioService
    ):
        self.turno_repository = turno_repository
        self.usuario_repository = usuario_repository
        self.assinatura_repository = assinatura_repository
        self.relatorio_service = relatorio_service

    async def execute(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date
    ) -> Optional[bytes]:
        """
        Executa a geração do relatório.
        Retorna bytes do PDF ou None se não permitido/erro.
        Poderia levantar exceções específicas para 403/404.
        Para simplificar e manter compatibilidade com controller atual, vamos levantar aqui ou retornar None?
        
        Melhor: O UseCase deve levantar exceções de negócio.
        """
        # 1. Verificar Assinatura (Premium Check)
        assinatura = await self.assinatura_repository.get_by_user_id(telegram_user_id)
        if not assinatura or assinatura.is_free:
            # Domain Exception seria ideal, mas para manter simples agora:
            from app.domain.exceptions import AcessoNegadoException
            raise AcessoNegadoException("Funcionalidade disponível apenas para usuários Premium.")

        # 2. Buscar Dados do Usuário
        usuario = await self.usuario_repository.buscar_por_telegram_id(telegram_user_id)
        usuario_info = None
        if usuario:
            usuario_info = {
                "nome": usuario.nome,
                "numero_funcionario": usuario.numero_funcionario
            }

        # 3. Buscar Turnos
        turnos = await self.turno_repository.listar_por_periodo(telegram_user_id, inicio, fim)

        # 4. Gerar PDF (Service)
        pdf_bytes = self.relatorio_service.gerar_pdf_mes(turnos, inicio, fim, usuario_info)
        
        return pdf_bytes
