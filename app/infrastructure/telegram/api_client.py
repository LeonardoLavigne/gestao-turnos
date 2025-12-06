"""
API client for Telegram bot to communicate with the FastAPI backend.
"""
import logging
from datetime import date
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Base URL for API calls
API_BASE_URL = "http://localhost:8000"


class TurnoAPIClient:
    """Client for interacting with Turno API endpoints."""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
    
    async def criar_turno(
        self,
        tipo: str,
        data_ref: date,
        hora_inicio: str,
        hora_fim: str,
        telegram_user_id: int,
    ) -> dict:
        """
        Cria um novo turno via API.
        
        Args:
            tipo: Tipo/local do turno
            data_ref: Data de referência
            hora_inicio: Hora de início (HH:MM)
            hora_fim: Hora de fim (HH:MM)
            telegram_user_id: ID do usuário do Telegram
            
        Returns:
            Dicionário com dados do turno criado
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/turnos",
                json={
                    "data_referencia": data_ref.isoformat(),
                    "hora_inicio": hora_inicio,
                    "hora_fim": hora_fim,
                    "tipo": tipo,
                    "origem": "telegram",
                },
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
    
    async def listar_turnos_recentes(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> list[dict]:
        """Lista os turnos mais recentes do usuário."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/turnos/recentes",
                params={"limit": limit},
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
    
    async def deletar_turno(
        self,
        turno_id: int,
        telegram_user_id: int,
    ) -> bool:
        """
        Deleta um turno.
        
        Returns:
            True se deletado, False se não encontrado
        """
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/turnos/{turno_id}",
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            return True


class RelatorioAPIClient:
    """Client for interacting with Relatório API endpoints."""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
    
    async def relatorio_semana(
        self,
        ano: int,
        semana: int,
        telegram_user_id: int,
    ) -> dict:
        """Busca relatório semanal."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/relatorios/semana",
                params={"ano": ano, "semana": semana},
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
    
    async def relatorio_mes(
        self,
        ano: int,
        mes: int,
        telegram_user_id: int,
    ) -> dict:
        """Busca relatório mensal."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/relatorios/mes",
                params={"ano": ano, "mes": mes},
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
    
    async def relatorio_periodo(
        self,
        inicio: date,
        fim: date,
        telegram_user_id: int,
    ) -> dict:
        """Busca relatório de período customizado."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/relatorios/periodo",
                params={
                    "inicio": inicio.isoformat(),
                    "fim": fim.isoformat(),
                },
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
    
    async def relatorio_mes_pdf(
        self,
        ano: int,
        mes: int,
        telegram_user_id: int,
    ) -> bytes:
        """Busca relatório mensal em PDF."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/relatorios/mes/pdf",
                params={
                    "ano": ano,
                    "mes": mes,
                    "telegram_user_id": telegram_user_id,
                },
                headers={"X-Telegram-User-ID": str(telegram_user_id)},
                timeout=30.0,  # PDF pode demorar mais
            )
            resp.raise_for_status()
            return resp.content


class UsuarioAPIClient:
    """Client for interacting with Usuario API endpoints."""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
    
    async def buscar_usuario(self, telegram_user_id: int) -> Optional[dict]:
        """
        Busca usuário por telegram_user_id.
        
        Returns:
            Dados do usuário ou None se não encontrado
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/usuarios/{telegram_user_id}",
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    return resp.json()
                return None
        except Exception as e:
            logger.error(
                "Erro ao buscar usuário",
                extra={"telegram_user_id": telegram_user_id, "error": str(e)}
            )
            return None
    
    async def criar_usuario(
        self,
        telegram_user_id: int,
        nome: str,
        numero_funcionario: str,
    ) -> dict:
        """
        Cria novo usuário.
        
        Raises:
            httpx.HTTPStatusError: Se houver erro (ex: 400 para usuário duplicado)
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/usuarios",
                json={
                    "telegram_user_id": telegram_user_id,
                    "nome": nome,
                    "numero_funcionario": numero_funcionario,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()


# Singleton instances for convenience
turno_client = TurnoAPIClient()
relatorio_client = RelatorioAPIClient()
usuario_client = UsuarioAPIClient()
