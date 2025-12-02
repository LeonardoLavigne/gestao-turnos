"""
Testes de isolamento RLS (Row-Level Security).

Valida que as políticas PostgreSQL garantem isolamento de dados entre usuários.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date, time

from app.config import get_settings
from app.models import Base, Usuario, Turno


@pytest.fixture
def db_engine():
    """Engine do banco de dados."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Sessão do banco de dados."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


def test_rls_enabled_on_tables(db_session):
    """Teste: RLS está habilitado em todas as tabelas."""
    result = db_session.execute(text("""
        SELECT tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """))
    
    tables = {row[0]: row[1] for row in result}
    
    # Verificar que RLS está habilitado nas tabelas principais
    assert tables.get('usuarios') == True, "RLS não habilitado em usuarios"
    assert tables.get('turnos') == True, "RLS não habilitado em turnos"
    assert tables.get('tipos_turno') == True, "RLS não habilitado em tipos_turno"


def test_user_isolation_with_rls(db_session):
    """
    Teste: Usuário A não vê dados de Usuário B.
    
    Valida que as políticas RLS isolam dados corretamente.
    """
    # Configurar contexto para User A (telegram_user_id=111)
    db_session.execute(text("SET LOCAL app.current_user_id = '111'"))
    
    # Inserir turno para User A
    db_session.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos)
        VALUES (111, '2024-01-01', '08:00', '16:00', 480)
    """))
    db_session.commit()
    
    # Consultar turnos (deve ver apenas do User A)
    result_a = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    assert result_a == 1, f"User A deveria ver 1 turno, viu {result_a}"
    
    # Mudar contexto para User B (telegram_user_id=222)
    db_session.execute(text("SET LOCAL app.current_user_id = '222'"))
    
    # Consultar turnos (NÃO deve ver turnos de User A)
    result_b = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    assert result_b == 0, f"User B não deveria ver turnos de User A, viu {result_b}"
    
    # Inserir turno para User B
    db_session.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos)
        VALUES (222, '2024-01-02', '09:00', '17:00', 480)
    """))
    db_session.commit()
    
    # User B deve ver apenas seu próprio turno
    result_b2 = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    assert result_b2 == 1, f"User B deveria ver 1 turno, viu {result_b2}"
    
    # Voltar para User A e verificar que ainda vê apenas 1
    db_session.execute(text("SET LOCAL app.current_user_id = '111'"))
    result_a2 = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    assert result_a2 == 1, f"User A deveria continuar vendo 1 turno, viu {result_a2}"
    
    # Cleanup
    db_session.execute(text("DELETE FROM turnos WHERE telegram_user_id IN (111, 222)"))
    db_session.commit()


def test_rls_policies_exist(db_session):
    """Teste: Políticas RLS existem para as tabelas."""
    result = db_session.execute(text("""
        SELECT tablename, policyname 
        FROM pg_policies 
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname
    """))
    
    policies = [(row[0], row[1]) for row in result]
    
    # Verificar que políticas foram criadas
    policy_names = [p[1] for p in policies]
    
    assert 'usuarios_isolation' in policy_names or 'turnos_isolation' in policy_names, \
        f"Políticas de isolamento não encontradas. Políticas existentes: {policy_names}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
