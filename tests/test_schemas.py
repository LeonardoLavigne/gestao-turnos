"""
Testes para o módulo schemas (validação Pydantic).
"""
import pytest
from datetime import date, time, datetime

from app import schemas


class TestTurnoBase:
    """Testes de validação para TurnoBase/TurnoCreate."""
    
    def test_criar_turno_valido(self):
        """Criar TurnoCreate com dados válidos."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            tipo="Manhã",
            descricao_opcional="Turno teste"
        )
        
        assert turno.data_referencia == date(2024, 1, 15)
        assert turno.hora_inicio == time(8, 0)
        assert turno.hora_fim == time(16, 0)
        assert turno.tipo == "Manhã"
        assert turno.origem == "api"
    
    def test_tipo_normalizado(self):
        """Tipo com espaços é normalizado."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            tipo="  Manhã  "
        )
        
        assert turno.tipo == "Manhã"
    
    def test_tipo_vazio_vira_none(self):
        """Tipo com apenas espaços vira None."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            tipo="   "
        )
        
        assert turno.tipo is None
    
    def test_tipo_none(self):
        """Tipo None permanece None."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            tipo=None
        )
        
        assert turno.tipo is None
    
    def test_origem_default_api(self):
        """Origem padrão é 'api'."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
        )
        
        assert turno.origem == "api"
    
    def test_origem_telegram(self):
        """Origem pode ser 'telegram'."""
        turno = schemas.TurnoCreate(
            data_referencia=date(2024, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            origem="telegram"
        )
        
        assert turno.origem == "telegram"


class TestTipoTurno:
    """Testes para TipoTurno schemas."""
    
    def test_tipo_turno_create(self):
        """Criar TipoTurnoCreate."""
        tipo = schemas.TipoTurnoCreate(
            nome="Manhã",
            descricao="Turno da manhã",
            cor_calendario="#FF0000"
        )
        
        assert tipo.nome == "Manhã"
        assert tipo.descricao == "Turno da manhã"
        assert tipo.cor_calendario == "#FF0000"
    
    def test_tipo_turno_sem_opcional(self):
        """TipoTurno sem campos opcionais."""
        tipo = schemas.TipoTurnoCreate(nome="Teste")
        
        assert tipo.nome == "Teste"
        assert tipo.descricao is None
        assert tipo.cor_calendario is None


class TestRelatorioDia:
    """Testes para RelatorioDia."""
    
    def test_relatorio_dia(self):
        """Criar RelatorioDia."""
        dia = schemas.RelatorioDia(
            data=date(2024, 1, 15),
            total_minutos=480,
            por_tipo={"Manhã": 240, "Tarde": 240}
        )
        
        assert dia.data == date(2024, 1, 15)
        assert dia.total_minutos == 480
        assert len(dia.por_tipo) == 2


class TestRelatorioPeriodo:
    """Testes para RelatorioPeriodo."""
    
    def test_relatorio_periodo_vazio(self):
        """Relatório de período sem dias."""
        relatorio = schemas.RelatorioPeriodo(
            inicio=date(2024, 1, 1),
            fim=date(2024, 1, 31),
            total_minutos=0,
            dias=[]
        )
        
        assert relatorio.inicio == date(2024, 1, 1)
        assert relatorio.fim == date(2024, 1, 31)
        assert relatorio.total_minutos == 0
        assert len(relatorio.dias) == 0


class TestUsuarioSchemas:
    """Testes para Usuario schemas."""
    
    def test_usuario_create(self):
        """Criar UsuarioCreate."""
        usuario = schemas.UsuarioCreate(
            telegram_user_id=123456789,
            nome="João Silva",
            numero_funcionario="EMP001"
        )
        
        assert usuario.telegram_user_id == 123456789
        assert usuario.nome == "João Silva"
        assert usuario.numero_funcionario == "EMP001"
    
    def test_usuario_update_parcial(self):
        """UsuarioUpdate com campos parciais."""
        update = schemas.UsuarioUpdate(nome="Novo Nome")
        
        assert update.nome == "Novo Nome"
        assert update.numero_funcionario is None
    
    def test_usuario_update_vazio(self):
        """UsuarioUpdate sem nenhum campo."""
        update = schemas.UsuarioUpdate()
        
        assert update.nome is None
        assert update.numero_funcionario is None
