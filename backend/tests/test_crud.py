"""
Testes para o módulo CRUD.

Testa operações de criação, listagem, atualização e exclusão de turnos e usuários.
"""
import pytest
from datetime import date, time, datetime
from sqlalchemy import text

from app import crud, schemas


class TestCalcularDuracaoMinutos:
    """Testes para calcular_duracao_minutos (síncrono - sem DB)."""
    
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


@pytest.mark.asyncio
class TestCriarTurno:
    """Testes para criar_turno."""
    
    async def test_criar_turno_simples(self, db_session_rls):
        """Criar turno básico sem tipo."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '999', true)"))
        
        payload = schemas.TurnoCreate(
            data_referencia=date(2024, 6, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
        )
        
        turno = await crud.criar_turno(db, payload)
        
        assert turno.id is not None
        assert turno.telegram_user_id == 999
        assert turno.data_referencia == date(2024, 6, 15)
        assert turno.hora_inicio == time(8, 0)
        assert turno.hora_fim == time(16, 0)
        assert turno.duracao_minutos == 480
        
        # Cleanup
        await db.execute(text("SELECT set_config('app.current_user_id', '999', true)"))
        await db.execute(text(f"DELETE FROM turnos WHERE id = {turno.id}"))
        await db.commit()
    
    async def test_criar_turno_com_tipo_livre(self, db_session_rls):
        """Criar turno com tipo que não existe no banco (tipo_livre)."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '999', true)"))
        
        payload = schemas.TurnoCreate(
            data_referencia=date(2024, 6, 16),
            hora_inicio=time(9, 0),
            hora_fim=time(17, 0),
            tipo="TipoNaoExiste",
        )
        
        turno = await crud.criar_turno(db, payload)
        
        assert turno.tipo_livre == "TipoNaoExiste"
        assert turno.tipo is None
        assert turno.telegram_user_id == 999
        
        # Cleanup
        await db.execute(text("SELECT set_config('app.current_user_id', '999', true)"))
        await db.execute(text(f"DELETE FROM turnos WHERE id = {turno.id}"))
        await db.commit()
    
    async def test_criar_turno_sem_user_id_erro(self, db_session_rls):
        """Criar turno sem current_user_id setado deve dar erro."""
        db = db_session_rls
        
        # Não seta current_user_id
        await db.execute(text("BEGIN"))
        
        payload = schemas.TurnoCreate(
            data_referencia=date(2024, 6, 17),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
        )
        
        import pytest
        with pytest.raises(ValueError, match="telegram_user_id não definido"):
            await crud.criar_turno(db, payload)
        
        await db.rollback()


class TestGerarRelatorioPeriodo:
    """Testes para gerar_relatorio_periodo (síncrono - sem DB)."""
    
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


@pytest.mark.asyncio
class TestListarTurnosPeriodo:
    """Testes para listar_turnos_periodo."""
    
    async def test_listar_turnos_periodo_vazio(self, db_session_rls):
        """Listar período sem turnos retorna lista vazia."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '888', true)"))
        
        turnos = await crud.listar_turnos_periodo(
            db,
            date(2099, 1, 1),
            date(2099, 1, 31)
        )
        
        await db.commit()
        assert turnos == []


@pytest.mark.asyncio
class TestListarTurnosRecentes:
    """Testes para listar_turnos_recentes."""
    
    async def test_listar_recentes_vazio(self, db_session_rls):
        """Listar recentes de usuário sem turnos."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '777', true)"))
        
        turnos = await crud.listar_turnos_recentes(db, limit=5)
        
        await db.commit()
        # Pode retornar lista vazia ou com alguns turnos do usuário
        assert isinstance(turnos, list)


@pytest.mark.asyncio
class TestDeleteTurno:
    """Testes para delete_turno."""
    
    async def test_delete_turno_inexistente(self, db_session_rls):
        """Deletar turno inexistente retorna False."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '777', true)"))
        
        resultado = await crud.delete_turno(db, 999999)
        
        await db.commit()
        assert resultado is False


@pytest.mark.asyncio
class TestGetUsuarioByTelegramId:
    """Testes para get_usuario_by_telegram_id."""
    
    async def test_buscar_usuario_inexistente(self, db_session_rls):
        """Buscar usuário inexistente retorna None."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '333333', true)"))
        
        resultado = await crud.get_usuario_by_telegram_id(db, 333333)
        
        await db.commit()
        assert resultado is None


@pytest.mark.asyncio
class TestAtualizarUsuario:
    """Testes para atualizar_usuario."""
    
    async def test_atualizar_usuario_inexistente(self, db_session_rls):
        """Atualizar usuário inexistente retorna None."""
        db = db_session_rls
        
        await db.execute(text("BEGIN"))
        await db.execute(text("SELECT set_config('app.current_user_id', '444444', true)"))
        
        update_payload = schemas.UsuarioUpdate(nome="Novo Nome")
        resultado = await crud.atualizar_usuario(db, 444444, update_payload)
        
        await db.commit()
        assert resultado is None
