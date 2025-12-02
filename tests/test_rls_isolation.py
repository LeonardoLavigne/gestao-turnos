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
    # Preparar: Inserir dados para dois usuários diferentes
    # Usar BEGIN...COMMIT manual para garantir transação correta
    
    # Inserir turno para User A (111)
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '111'"))
    db_session.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (111, '2024-01-01', '08:00', '16:00', 480, NOW(), NOW())
    """))
    db_session.execute(text("COMMIT"))
    
    # Inserir turno para User B (222)
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '222'"))
    db_session.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (222, '2024-01-02', '09:00', '17:00', 480, NOW(), NOW())
    """))
    db_session.execute(text("COMMIT"))
    
    # Teste 1: User A deve ver apenas seu turno
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '111'"))
    result_a = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    db_session.execute(text("COMMIT"))
    assert result_a == 1, f"User A deveria ver 1 turno, viu {result_a}"
    
    # Teste 2: User B deve ver apenas seu turno (NÃO deve ver de A)
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '222'"))
    result_b = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    db_session.execute(text("COMMIT"))
    assert result_b == 1, f"User B deveria ver 1 turno, viu {result_b}"
    
    # Teste 3: User C (333) não deve ver nada
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '333'"))
    result_c = db_session.execute(text("SELECT COUNT(*) FROM turnos")).scalar()
    db_session.execute(text("COMMIT"))
    assert result_c == 0, f"User C não deveria ver nenhum turno, viu {result_c}"
    
    # Cleanup: Deletar o que foi criado (respeitando RLS)
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '111'"))
    db_session.execute(text("DELETE FROM turnos"))
    db_session.execute(text("COMMIT"))
    
    db_session.execute(text("BEGIN"))
    db_session.execute(text("SET LOCAL app.current_user_id = '222'"))
    db_session.execute(text("DELETE FROM turnos"))
    db_session.execute(text("COMMIT"))


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
