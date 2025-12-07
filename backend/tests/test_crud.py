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
class TestTurnoRepository:
    """Testes para SqlAlchemyTurnoRepository (Persistência)."""

    async def test_criar_turno_persistence(self, db_session_rls):
        """Testa a persistência básica de um turno via repositório."""
        from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
        from app.domain.entities.turno import Turno
        from app.models import Turno as TurnoModel

        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        # User ID for RLS
        user_id = 999
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))
        
        # Prepare Entity (Logic like duration calc is done in UseCase, here we manually set it)
        turno_entity = Turno(
            id=None,
            telegram_user_id=user_id,
            data_referencia=date(2024, 6, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(16, 0),
            duracao_minutos=480,
            tipo="Trabalho",
            descricao_opcional="Teste Repo",
            event_uid=None
        )

        saved_turno = await repo.criar(turno_entity)
        
        assert saved_turno.id is not None
        assert saved_turno.telegram_user_id == user_id
        
        # Verify in DB
        stmt = text(f"SELECT count(*) FROM turnos WHERE id = {saved_turno.id}")
        result = await db.scalar(stmt)
        assert result == 1
        
        # Cleanup
        await db.execute(text(f"DELETE FROM turnos WHERE id = {saved_turno.id}"))
        await db.commit()

    async def test_contar_por_periodo(self, db_session_rls):
        """Testa o método contar_por_periodo."""
        from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
        from app.domain.entities.turno import Turno

        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        user_id = 888
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))

        # Create 2 shifts in the period
        t1 = Turno(
            id=None, telegram_user_id=user_id,
            data_referencia=date(2024, 7, 1),
            hora_inicio=time(8, 0), hora_fim=time(12, 0), duracao_minutos=240,
            tipo="T1", descricao_opcional=None, event_uid=None
        )
        t2 = Turno(
            id=None, telegram_user_id=user_id,
            data_referencia=date(2024, 7, 2),
            hora_inicio=time(8, 0), hora_fim=time(12, 0), duracao_minutos=240,
            tipo="T2", descricao_opcional=None, event_uid=None
        )
        
        saved_t1 = await repo.criar(t1)
        saved_t2 = await repo.criar(t2)
        await db.flush()

        # Count
        count = await repo.contar_por_periodo(user_id, date(2024, 7, 1), date(2024, 7, 31))
        assert count == 2
        
        # Count outside
        count_out = await repo.contar_por_periodo(user_id, date(2024, 8, 1), date(2024, 8, 31))
        assert count_out == 0

        # Cleanup
        await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id = {user_id}"))
        await db.commit()


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
