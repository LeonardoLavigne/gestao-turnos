"""
Common utilities and helpers for Telegram bot handlers.
"""
import logging
from src.config import get_settings

logger = logging.getLogger(__name__)


def usuario_autorizado(user_id: int) -> bool:
    """
    Verifica se usuário está autorizado a usar o bot.
    
    Se telegram_allowed_users estiver vazio, permite todos.
    """
    settings = get_settings()
    return not settings.telegram_allowed_users or user_id in settings.telegram_allowed_users


def formatar_relatorio(relatorio: dict) -> str:
    """
    Formata um relatório para exibição em texto.
    
    Args:
        relatorio: Dicionário com dados do relatório (dias, total_minutos, etc.)
        
    Returns:
        Texto formatado para envio ao usuário
    """
    total_horas = relatorio["total_minutos"] / 60.0
    linhas = [f"Total: {total_horas:.2f}h entre {relatorio['inicio']} e {relatorio['fim']}."]
    
    for dia in relatorio["dias"]:
        horas_dia = dia["total_minutos"] / 60.0
        partes = [f"{dia['data']}: {horas_dia:.2f}h"]
        
        if dia["por_tipo"]:
            tipos_txt = ", ".join(
                f"{tipo} {mins/60.0:.2f}h" for tipo, mins in dia["por_tipo"].items()
            )
            partes.append(f"({tipos_txt})")
        
        linhas.append(" ".join(partes))
    
    return "\n".join(linhas)
