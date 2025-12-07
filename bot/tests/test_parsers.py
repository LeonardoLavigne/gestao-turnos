import pytest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from src.parsers import parse_linhas_turno, parse_mes_arg, ParsedTurno

TZ = ZoneInfo("America/Sao_Paulo")

def test_parse_simple_line():
    text = "Hospital 08:00 as 16:00"
    result = parse_linhas_turno(text, TZ)
    assert len(result) == 1
    assert result[0].tipo == "Hospital"
    assert result[0].hora_inicio == "08:00"
    assert result[0].hora_fim == "16:00"
    # Default date is today
    assert result[0].data_referencia == datetime.now(TZ).date()

def test_parse_explicit_date():
    text = "Dia 25/12/2025 - Natal 10:00 as 22:00"
    result = parse_linhas_turno(text, TZ)
    assert len(result) == 1
    assert result[0].tipo == "Natal"
    assert result[0].data_referencia == date(2025, 12, 25)
    assert result[0].hora_inicio == "10:00"
    assert result[0].hora_fim == "22:00"

def test_parse_multiple_lines():
    text = """
    Hospital 08:00 as 16:00
    Dia 01/01/2026 - Plantão 20:00 as 08:00
    """
    result = parse_linhas_turno(text, TZ)
    assert len(result) == 2
    assert result[0].tipo == "Hospital"
    assert result[1].tipo == "Plantão"
    assert result[1].data_referencia == date(2026, 1, 1)

def test_parse_invalid_format_raises_error():
    text = "Isso não é um turno"
    with pytest.raises(ValueError) as exc:
        parse_linhas_turno(text, TZ)
    assert "Linha 1 inválida" in str(exc.value)

def test_parse_invalid_date_raises_error():
    text = "Dia 99/99/2025 - Hospital 08:00 a 16:00"
    with pytest.raises(ValueError) as exc:
        parse_linhas_turno(text, TZ)
    assert "data inválida" in str(exc.value)

def test_parse_mes_arg_integers():
    assert parse_mes_arg("1") == (1, None)
    assert parse_mes_arg("12") == (12, None)

def test_parse_mes_arg_names():
    assert parse_mes_arg("jan") == (1, None)
    assert parse_mes_arg("janeiro") == (1, None)
    assert parse_mes_arg("dezembro") == (12, None)
    assert parse_mes_arg("FEVEREIRO") == (2, None)

def test_parse_mes_arg_combined():
    assert parse_mes_arg("01-2025") == (1, 2025)
    assert parse_mes_arg("12/2024") == (12, 2024)

def test_parse_mes_arg_invalid():
    with pytest.raises(ValueError):
        parse_mes_arg("batata")
    with pytest.raises(ValueError):
        parse_mes_arg("13")
