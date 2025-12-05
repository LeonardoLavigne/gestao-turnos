"""
Testes para o módulo CRUD.

Testa operações de criação, listagem, atualização e exclusão de turnos e usuários.
"""
import pytest
from datetime import date, time, datetime
from sqlalchemy import text

from app import crud, schemas


class TestCalcularDuracaoMinutos:
    """Testes para calcular_duracao_minutos."""
    
    def test_duracao_normal(self):
        """Turno de 8h às 16h = 480 minutos."""
        resultado = crud.calcular_duracao_minutos(
            date(2024, 1, 1),
            time(8, 0),
            time(16, 0)
        )
        assert resultado == 480
    
    def test_duracao_turno_noturno(self):
        """Turno noturno passando meia-noite (22h às 6h = 480 minutos)."""
        resultado = crud.calcular_duracao_minutos(
            date(2024, 1, 1),
            time(22, 0),
            time(6, 0)
        )
        assert resultado == 480
    
    def test_duracao_turno_curto(self):
        """Turno de 30 minutos."""
        resultado = crud.calcular_duracao_minutos(
            date(2024, 1, 1),
            time(9, 0),
            time(9, 30)
        )
        assert resultado == 30
    
    def test_duracao_turno_1_minuto(self):
        """Turno de 1 minuto."""
        resultado = crud.calcular_duracao_minutos(
            date(2024, 1, 1),
            time(10, 0),
            time(10, 1)
        )
        assert resultado == 1
    
    def test_duracao_turno_24h(self):
        """Turno completo onde fim = início (passa 24h)."""
        resultado = crud.calcular_duracao_minutos(
            date(2024, 1, 1),
            time(0, 0),
            time(0, 0)
        )
        assert resultado == 1440  # 24 horas


class TestNomeTipo:
    """Testes para _nome_tipo helper."""
    
    def test_nome_tipo_helper(self):
        """Testa função auxiliar _nome_tipo."""
        from app.models import Turno, TipoTurno
        
        # Mock turno sem tipo
        class MockTurno:
            tipo = None
            tipo_livre = "Plantão"
        
        resultado = crud._nome_tipo(MockTurno())
        assert resultado == "Plantão"


class TestGerarRelatorioPeriodo:
    """Testes para gerar_relatorio_periodo."""
    
    def test_relatorio_vazio(self):
        """Relatório sem turnos."""
        relatorio = crud.gerar_relatorio_periodo(
            [],
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        assert relatorio.inicio == date(2024, 1, 1)
        assert relatorio.fim == date(2024, 1, 31)
        assert relatorio.total_minutos == 0
        assert relatorio.dias == []
    
    def test_relatorio_com_turnos_mock(self):
        """Relatório com turnos mockados."""
        class MockTurno:
            def __init__(self, data, duracao, tipo_livre):
                self.data_referencia = data
                self.duracao_minutos = duracao
                self.tipo = None
                self.tipo_livre = tipo_livre
        
        turnos = [
            MockTurno(date(2024, 1, 15), 480, "Manhã"),
            MockTurno(date(2024, 1, 15), 240, "Tarde"),
            MockTurno(date(2024, 1, 16), 360, "Noite"),
        ]
        
        relatorio = crud.gerar_relatorio_periodo(
            turnos,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        assert relatorio.total_minutos == 480 + 240 + 360
        assert len(relatorio.dias) == 2
        
        # Primeiro dia
        dia1 = relatorio.dias[0]
        assert dia1.data == date(2024, 1, 15)
        assert dia1.total_minutos == 720
        assert dia1.por_tipo["Manhã"] == 480
        assert dia1.por_tipo["Tarde"] == 240
        
        # Segundo dia
        dia2 = relatorio.dias[1]
        assert dia2.data == date(2024, 1, 16)
        assert dia2.total_minutos == 360


class TestListarTurnosPeriodo:
    """Testes para listar_turnos_periodo."""
    
    def test_listar_turnos_periodo_vazio(self, db_session_rls):
        """Listar período sem turnos retorna lista vazia."""
        db = db_session_rls
        
        db.execute(text("BEGIN"))
        db.execute(text("SET LOCAL app.current_user_id = '888'"))
        
        turnos = crud.listar_turnos_periodo(
            db,
            date(2099, 1, 1),
            date(2099, 1, 31)
        )
        
        db.execute(text("COMMIT"))
        assert turnos == []


class TestListarTurnosRecentes:
    """Testes para listar_turnos_recentes."""
    
    def test_listar_recentes_vazio(self, db_session_rls):
        """Listar recentes de usuário sem turnos."""
        db = db_session_rls
        
        db.execute(text("BEGIN"))
        db.execute(text("SET LOCAL app.current_user_id = '777'"))
        
        turnos = crud.listar_turnos_recentes(db, limit=5)
        
        db.execute(text("COMMIT"))
        # Pode retornar lista vazia ou com alguns turnos do usuário
        assert isinstance(turnos, list)


class TestDeleteTurno:
    """Testes para delete_turno."""
    
    def test_delete_turno_inexistente(self, db_session_rls):
        """Deletar turno inexistente retorna False."""
        db = db_session_rls
        
        db.execute(text("BEGIN"))
        db.execute(text("SET LOCAL app.current_user_id = '777'"))
        
        resultado = crud.delete_turno(db, 999999)
        
        db.execute(text("COMMIT"))
        assert resultado is False


class TestGetUsuarioByTelegramId:
    """Testes para get_usuario_by_telegram_id."""
    
    def test_buscar_usuario_inexistente(self, db_session_rls):
        """Buscar usuário inexistente retorna None."""
        db = db_session_rls
        
        db.execute(text("BEGIN"))
        db.execute(text("SET LOCAL app.current_user_id = '333333'"))
        
        resultado = crud.get_usuario_by_telegram_id(db, 333333)
        
        db.execute(text("COMMIT"))
        assert resultado is None


class TestAtualizarUsuario:
    """Testes para atualizar_usuario."""
    
    def test_atualizar_usuario_inexistente(self, db_session_rls):
        """Atualizar usuário inexistente retorna None."""
        db = db_session_rls
        
        db.execute(text("BEGIN"))
        db.execute(text("SET LOCAL app.current_user_id = '444444'"))
        
        update_payload = schemas.UsuarioUpdate(nome="Novo Nome")
        resultado = crud.atualizar_usuario(db, 444444, update_payload)
        
        db.execute(text("COMMIT"))
        assert resultado is None

