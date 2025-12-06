"""
Parsers for Telegram bot message parsing.

Handles parsing of shift (turno) messages in various formats.
"""
import re
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Tuple, NamedTuple


class ParsedTurno(NamedTuple):
    """Represents a parsed shift entry."""
    tipo: str
    data_referencia: date
    hora_inicio: str
    hora_fim: str


# Regex para parsing de linhas de turno
# Suporta formatos como:
# - "Hospital 08:00 as 16:00"
# - "Dia 29/11/2025 - Casino 15:00 as 03:00"
LINHA_REGEX = re.compile(
    r"^(?:dia\s+(?P<data>\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*[-–—:]?\s*)?"
    r"(?P<tipo>[^\s\-–—:]+)\s*(?:[-–—:]\s*)?"
    r"(?P<h1>\d{1,2}:\d{2})\s*(?:as|às|a|ate)\s*(?P<h2>\d{1,2}:\d{2})$",
    re.IGNORECASE,
)


def parse_data_token(token: str) -> date:
    """
    Converte uma string de data no formato DD/MM/YYYY ou DD-MM-YYYY para date.
    """
    token = token.replace("-", "/")
    return datetime.strptime(token, "%d/%m/%Y").date()


def parse_linhas_turno(text: str, tz: ZoneInfo) -> list[ParsedTurno]:
    """
    Parseia texto com uma ou mais linhas de turno.
    
    Args:
        text: Texto da mensagem (pode ter múltiplas linhas)
        tz: Timezone para data padrão (hoje)
        
    Returns:
        Lista de ParsedTurno com os dados extraídos
        
    Raises:
        ValueError: Se o texto estiver vazio ou tiver linhas inválidas
    """
    linhas = [linha.strip() for linha in text.splitlines() if linha.strip()]
    if not linhas:
        raise ValueError(
            "Mensagem vazia. Use algo como: REN 08:00 as 16:00 ou "
            "Dia 29/11/2025 - Casino 15:00 as 03:00"
        )

    agora = datetime.now(tz=tz)
    resultados: list[ParsedTurno] = []
    erros: list[str] = []

    for idx, linha in enumerate(linhas, start=1):
        m = LINHA_REGEX.match(linha)
        if not m:
            erros.append(
                f"Linha {idx} inválida. Exemplo válido: "
                "Dia 29/11/2025 - Casino 15:00 as 03:00"
            )
            continue

        data_token = m.group("data")
        try:
            data_ref = (
                parse_data_token(data_token) if data_token else agora.date()
            )
        except ValueError:
            erros.append(
                f"Linha {idx}: data inválida '{data_token}'. Use dd/mm/aaaa."
            )
            continue

        resultados.append(
            ParsedTurno(
                tipo=m.group("tipo"),
                data_referencia=data_ref,
                hora_inicio=m.group("h1"),
                hora_fim=m.group("h2"),
            )
        )

    if erros:
        raise ValueError("\n".join(erros))

    return resultados


def parse_mes_arg(arg: str) -> tuple[int, int | None]:
    """
    Parseia argumento de mês em diversos formatos.
    
    Retorna (mes, ano). Ano pode ser None se não especificado.
    
    Formatos suportados:
    - 1..12 (número do mês)
    - janeiro..dezembro (nome, case insensitive, prefixos de 3 letras)
    - mm-yyyy ou mm/yyyy
    """
    arg = arg.lower().strip()
    
    # Check for mm-yyyy or mm/yyyy
    if "-" in arg:
        parts = arg.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    if "/" in arg:
        parts = arg.split("/")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])

    # Map month names
    meses = {
        "jan": 1, "janeiro": 1,
        "fev": 2, "fevereiro": 2,
        "mar": 3, "marco": 3, "março": 3,
        "abr": 4, "abril": 4,
        "mai": 5, "maio": 5,
        "jun": 6, "junho": 6,
        "jul": 7, "julho": 7,
        "ago": 8, "agosto": 8,
        "set": 9, "setembro": 9,
        "out": 10, "outubro": 10,
        "nov": 11, "novembro": 11,
        "dez": 12, "dezembro": 12
    }
    
    # Check if it is a name
    for name, num in meses.items():
        if arg == name or (len(arg) >= 3 and name.startswith(arg)):
            return num, None
            
    # Try integer
    if arg.isdigit():
        return int(arg), None
        
    raise ValueError(f"Mês inválido: {arg}")
