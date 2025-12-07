"""
Testes para Repositórios e Use Cases (substituindo antigo test_crud).
"""
import pytest
from datetime import date, time, datetime
from sqlalchemy import text

from app.domain.entities.turno import Turno
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.presentation import schemas

class TestCalcularDuracaoMinutos:
    """Testes para Turno.calcular_duracao (substitui crud.calcular_duracao_minutos)."""
    
    def test_duracao_normal(self):
        """Turno de 8h às 16h = 480 minutos."""
        resultado = Turno.calcular_duracao(
            date(2024, 1, 1),
            time(8, 0),
            time(16, 0)
        )
        assert resultado == 480
    
    def test_duracao_turno_noturno(self):
        """Turno noturno passando meia-noite (22h às 6h = 480 minutos)."""
        resultado = Turno.calcular_duracao(
            date(2024, 1, 1),
            time(22, 0),
            time(6, 0)
        )
        assert resultado == 480
    
    def test_duracao_turno_curto(self):
        """Turno de 30 minutos."""
        resultado = Turno.calcular_duracao(
            date(2024, 1, 1),
            time(9, 0),
            time(9, 30)
        )
        assert resultado == 30

@pytest.mark.asyncio
class TestTurnoRepository:
    """Testes para SqlAlchemyTurnoRepository."""

    async def test_criar_turno_persistence(self, db_session_rls):
        """Testa a persistência básica de um turno via repositório."""
        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        # User ID for RLS
        user_id = 999
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))
        
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
        
        await repo.criar(t1)
        await repo.criar(t2)
        await db.flush()

        # Count
        count = await repo.contar_por_periodo(user_id, date(2024, 7, 1), date(2024, 7, 31))
        assert count == 2
        
        # Count outside
        count_out = await repo.contar_por_periodo(user_id, date(2024, 8, 1), date(2024, 8, 31))
        assert count_out == 0


    async def test_listar_turnos_periodo(self, db_session_rls):
        """Testa listar_por_periodo."""
        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        user_id = 777
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))
        
        # Create shifts
        await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,1), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="A"))
        await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,2), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="B"))
        await db.flush()
        
        turnos = await repo.listar_por_periodo(user_id, date(2024,1,1), date(2024,1,31))
        assert len(turnos) == 2
        
    async def test_listar_recentes(self, db_session_rls):
        """Testa listar_recentes."""
        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        user_id = 666
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))
        
        # Create 3 shifts
        await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,1), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="A"))
        await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,2), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="B"))
        await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,3), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="C"))
        await db.flush()
        
        recentes = await repo.listar_recentes(user_id, limit=2)
        assert len(recentes) == 2 
        # Ordering check dependent on implementation (created_em vs data_referencia, repo uses criado_em desc)

    async def test_deletar_turno(self, db_session_rls):
        """Testa deletar turno."""
        db = db_session_rls
        repo = SqlAlchemyTurnoRepository(db)
        
        user_id = 555
        await db.execute(text("BEGIN"))
        await db.execute(text(f"SELECT set_config('app.current_user_id', '{user_id}', true)"))
        
        t = await repo.criar(Turno(id=None, telegram_user_id=user_id, data_referencia=date(2024,1,1), hora_inicio=time(8,0), hora_fim=time(12,0), duracao_minutos=240, tipo="A"))
        await db.flush()
        
        assert await repo.deletar(t.id, user_id) is True
        assert await repo.deletar(t.id, user_id) is False # Already deleted


@pytest.mark.asyncio
class TestUsuarioRepository:
    """Testes para SqlAlchemyUsuarioRepository."""
    
    async def test_buscar_usuario_inexistente(self, db_session_rls):
        db = db_session_rls
        repo = SqlAlchemyUsuarioRepository(db)
        
        await db.execute(text("BEGIN"))
        
        resultado = await repo.buscar_por_telegram_id(333333)
        assert resultado is None
