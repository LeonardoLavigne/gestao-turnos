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


# Fixtures agora estão em conftest.py


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


def test_user_isolation_with_rls(db_session_rls):
    """
    Teste: Usuário A não vê dados de Usuário B.
    
    Valida que as políticas RLS isolam dados corretamente.
    Usa role não-superuser (test_rls_user) que respeita políticas RLS.
    """
    db = db_session_rls
    
    # Inserir turno para User A (111) com identificador único
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '111'"))
    result = db.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (111, '2024-12-01', '08:00', '16:00', 480, NOW(), NOW())
        RETURNING id
    """))
    id_turno_a = result.scalar()
    db.execute(text("COMMIT"))
    
    # Inserir turno para User B (222) com identificador único
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '222'"))
    result = db.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (222, '2024-12-02', '09:00', '17:00', 480, NOW(), NOW())
        RETURNING id
    """))
    id_turno_b = result.scalar()
    db.execute(text("COMMIT"))
    
    # Teste 1: User A consegue ver seu próprio turno
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '111'"))
    result_a = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}")).first()
    db.execute(text("COMMIT"))
    assert result_a is not None, f"User A deveria ver seu próprio turno {id_turno_a}"
    
    # Teste 2: User A NÃO consegue ver turno de B (CRÍTICO para RLS)
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '111'"))
    result_a_ve_b = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}")).first()
    db.execute(text("COMMIT"))
    assert result_a_ve_b is None, f"VIOLAÇÃO DE SEGURANÇA: User A conseguiu ver turno {id_turno_b} de User B!"
    
    # Teste 3: User B consegue ver seu próprio turno
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '222'"))
    result_b = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}")).first()
    db.execute(text("COMMIT"))
    assert result_b is not None, f"User B deveria ver seu próprio turno {id_turno_b}"
    
    # Teste 4: User B NÃO consegue ver turno de A (CRÍTICO para RLS)
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '222'"))
    result_b_ve_a = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}")).first()
    db.execute(text("COMMIT"))
    assert result_b_ve_a is None, f"VIOLAÇÃO DE SEGURANÇA: User B conseguiu ver turno {id_turno_a} de User A!"
    
    # Teste 5: User C (333) não vê NENHUM dos dois turnos
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '333'"))
    result_c_ve_a = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}")).first()
    result_c_ve_b = db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}")).first()
    db.execute(text("COMMIT"))
    assert result_c_ve_a is None, f"VIOLAÇÃO: User C viu turno {id_turno_a} de User A!"
    assert result_c_ve_b is None, f"VIOLAÇÃO: User C viu turno {id_turno_b} de User B!"
    
    # Cleanup: Cada user só pode deletar seus próprios dados (respeitando RLS)
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '111'"))
    db.execute(text(f"DELETE FROM turnos WHERE id = {id_turno_a}"))
    db.execute(text("COMMIT"))
    
    db.execute(text("BEGIN"))
    db.execute(text("SET LOCAL app.current_user_id = '222'"))
    db.execute(text(f"DELETE FROM turnos WHERE id = {id_turno_b}"))
    db.execute(text("COMMIT"))



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
