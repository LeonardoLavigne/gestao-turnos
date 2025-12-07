"""
Testes de isolamento RLS (Row-Level Security).

Valida que as políticas PostgreSQL garantem isolamento de dados entre usuários.
"""
import pytest
from sqlalchemy import text
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_rls_enabled_on_tables(db_session):
    """Teste: RLS está habilitado em todas as tabelas."""
    result = await db_session.execute(text("""
        SELECT tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """))
    
    tables = {row[0]: row[1] for row in result}
    
    # Verificar que RLS está habilitado nas tabelas principais
    # Note: pode falhar se não tiver populado a tabela de usuários
    # Mas assumimos que a migration já rodou
    assert tables.get('usuarios') == True, "RLS não habilitado em usuarios"
    assert tables.get('turnos') == True, "RLS não habilitado em turnos"
    # tipos_turno pode não ter RLS dependendo da estratégia, mas turnos/usuarios devem ter


@pytest.mark.asyncio
async def test_user_isolation_with_rls(db_session_rls):
    """
    Teste: Usuário A não vê dados de Usuário B.
    
    Valida que as políticas RLS isolam dados corretamente.
    Usa role não-superuser (test_rls_user) que respeita políticas RLS.
    """
    db = db_session_rls
    
    # Inserir turno para User A (111) com identificador único
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '111', true)"))
    result = await db.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (111, '2024-12-01', '08:00', '16:00', 480, NOW(), NOW())
        RETURNING id
    """))
    id_turno_a = result.scalar()
    await db.commit()
    
    # Inserir turno para User B (222) com identificador único
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '222', true)"))
    result = await db.execute(text("""
        INSERT INTO turnos (telegram_user_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
        VALUES (222, '2024-12-02', '09:00', '17:00', 480, NOW(), NOW())
        RETURNING id
    """))
    id_turno_b = result.scalar()
    await db.commit()
    
    # Teste 1: User A consegue ver seu próprio turno
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '111', true)"))
    result_a = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}"))
    row_a = result_a.first()
    await db.commit()
    assert row_a is not None, f"User A deveria ver seu próprio turno {id_turno_a}"
    
    # Teste 2: User A NÃO consegue ver turno de B (CRÍTICO para RLS)
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '111', true)"))
    result_a_ve_b = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}"))
    row_a_ve_b = result_a_ve_b.first()
    await db.commit()
    assert row_a_ve_b is None, f"VIOLAÇÃO DE SEGURANÇA: User A conseguiu ver turno {id_turno_b} de User B!"
    
    # Teste 3: User B consegue ver seu próprio turno
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '222', true)"))
    result_b = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}"))
    row_b = result_b.first()
    await db.commit()
    assert row_b is not None, f"User B deveria ver seu próprio turno {id_turno_b}"
    
    # Teste 4: User B NÃO consegue ver turno de A (CRÍTICO para RLS)
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '222', true)"))
    result_b_ve_a = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}"))
    row_b_ve_a = result_b_ve_a.first()
    await db.commit()
    assert row_b_ve_a is None, f"VIOLAÇÃO DE SEGURANÇA: User B conseguiu ver turno {id_turno_a} de User A!"
    
    # Teste 5: User C (333) não vê NENHUM dos dois turnos
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '333', true)"))
    result_c_ve_a = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_a}"))
    row_c_ve_a = result_c_ve_a.first()
    result_c_ve_b = await db.execute(text(f"SELECT id FROM turnos WHERE id = {id_turno_b}"))
    row_c_ve_b = result_c_ve_b.first()
    await db.commit()
    assert row_c_ve_a is None, f"VIOLAÇÃO: User C viu turno {id_turno_a} de User A!"
    assert row_c_ve_b is None, f"VIOLAÇÃO: User C viu turno {id_turno_b} de User B!"
    
    # Cleanup
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '111', true)"))
    await db.execute(text(f"DELETE FROM turnos WHERE id = {id_turno_a}"))
    await db.commit()
    
    await db.execute(text("BEGIN"))
    await db.execute(text("SELECT set_config('app.current_user_id', '222', true)"))
    await db.execute(text(f"DELETE FROM turnos WHERE id = {id_turno_b}"))
    await db.commit()


@pytest.mark.asyncio
async def test_rls_policies_exist(db_session):
    """Teste: Políticas RLS existem para as tabelas."""
    result = await db_session.execute(text("""
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
