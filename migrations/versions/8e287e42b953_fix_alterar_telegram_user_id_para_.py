"""fix: alterar telegram_user_id para BigInteger

Revision ID: 8e287e42b953
Revises: 77905a838e45
Create Date: 2025-12-03 23:48:56.812537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e287e42b953'
down_revision: Union[str, Sequence[str], None] = '77905a838e45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Step 1: Drop RLS policies temporarily (they depend on telegram_user_id) ###
    op.execute('DROP POLICY IF EXISTS usuarios_isolation ON usuarios')
    op.execute('DROP POLICY IF EXISTS turnos_isolation ON turnos')
    op.execute('DROP POLICY IF EXISTS tipos_turno_isolation ON tipos_turno')
    op.execute('DROP POLICY IF EXISTS assinaturas_isolation ON assinaturas')
    op.execute('DROP POLICY IF EXISTS integracao_calendario_isolation ON integracao_calendario')
    
    # ### Step 2: Alter column types to BigInteger ###
    op.alter_column('assinaturas', 'telegram_user_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=False)
    op.alter_column('tipos_turno', 'telegram_user_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=False)
    op.alter_column('turnos', 'telegram_user_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=False)
    op.alter_column('usuarios', 'telegram_user_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=False)
    
    # ### Step 3: Recreate RLS policies with BigInteger ###
    op.execute("""
        CREATE POLICY usuarios_isolation ON usuarios
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS BIGINT))
    """)
    
    op.execute("""
        CREATE POLICY turnos_isolation ON turnos
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS BIGINT))
    """)
    
    op.execute("""
        CREATE POLICY tipos_turno_isolation ON tipos_turno
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS BIGINT))
    """)
    
    op.execute("""
        CREATE POLICY assinaturas_isolation ON assinaturas
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS BIGINT))
    """)
    
    op.execute("""
        CREATE POLICY integracao_calendario_isolation ON integracao_calendario
        USING (
            turno_id IN (
                SELECT id FROM turnos 
                WHERE telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS BIGINT)
            )
        )
    """)


def downgrade() -> None:
    # ### Step 1: Drop RLS policies ###
    op.execute('DROP POLICY IF EXISTS usuarios_isolation ON usuarios')
    op.execute('DROP POLICY IF EXISTS turnos_isolation ON turnos')
    op.execute('DROP POLICY IF EXISTS tipos_turno_isolation ON tipos_turno')
    op.execute('DROP POLICY IF EXISTS assinaturas_isolation ON assinaturas')
    op.execute('DROP POLICY IF EXISTS integracao_calendario_isolation ON integracao_calendario')
    
    # ### Step 2: Revert column types to INTEGER ###
    op.alter_column('usuarios', 'telegram_user_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('turnos', 'telegram_user_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('tipos_turno', 'telegram_user_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('assinaturas', 'telegram_user_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    
    # ### Step 3: Recreate RLS policies with INTEGER ###
    op.execute("""
        CREATE POLICY usuarios_isolation ON usuarios
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS INTEGER))
    """)
    
    op.execute("""
        CREATE POLICY turnos_isolation ON turnos
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS INTEGER))
    """)
    
    op.execute("""
        CREATE POLICY tipos_turno_isolation ON tipos_turno
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS INTEGER))
    """)
    
    op.execute("""
        CREATE POLICY assinaturas_isolation ON assinaturas
        USING (telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS INTEGER))
    """)
    
    op.execute("""
        CREATE POLICY integracao_calendario_isolation ON integracao_calendario
        USING (
            turno_id IN (
                SELECT id FROM turnos 
                WHERE telegram_user_id = CAST(current_setting('app.current_user_id', TRUE) AS INTEGER)
            )
        )
    """)
