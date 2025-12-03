"""enable row level security

Revision ID: 952baee58d3b
Revises: 3c68e15e6b50
Create Date: 2025-12-02 19:37:26.161744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '952baee58d3b'
down_revision: Union[str, Sequence[str], None] = '3c68e15e6b50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Habilitar Row-Level Security (RLS) para multi-tenancy.
    
    Garante que cada usuário só vê seus próprios dados baseado em telegram_user_id.
    """
    
    # ✅ Habilitar RLS na tabela usuarios
    op.execute("""
        ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
    """)
    
    # ✅ Política para usuarios: usuário só vê seu próprio perfil
    op.execute("""
        CREATE POLICY usuarios_isolation ON usuarios
        USING (telegram_user_id = current_setting('app.current_user_id', TRUE)::BIGINT);
    """)
    
    # ✅ Habilitar RLS na tabela turnos
    op.execute("""
        ALTER TABLE turnos ENABLE ROW LEVEL SECURITY;
    """)
    
    # ✅ Política para turnos: usuário só vê seus próprios turnos
    op.execute("""
        CREATE POLICY turnos_isolation ON turnos
        USING (telegram_user_id = current_setting('app.current_user_id', TRUE)::BIGINT);
    """)
    
    # ✅ Habilitar RLS na tabela tipos_turno
    op.execute("""
        ALTER TABLE tipos_turno ENABLE ROW LEVEL SECURITY;
    """)
    
    # ✅ Política para tipos_turno: usuário só vê seus próprios tipos
    op.execute("""
        CREATE POLICY tipos_turno_isolation ON tipos_turno
        USING (telegram_user_id = current_setting('app.current_user_id', TRUE)::BIGINT);
    """)
    
    # ✅ Habilitar RLS na tabela integracao_calendario
    op.execute("""
        ALTER TABLE integracao_calendario ENABLE ROW LEVEL SECURITY;
    """)
    
    # ✅ Política para integracao_calendario: isolamento via turno
    op.execute("""
        CREATE POLICY integracao_calendario_isolation ON integracao_calendario
        USING (
            turno_id IN (
                SELECT id FROM turnos 
                WHERE telegram_user_id = current_setting('app.current_user_id', TRUE)::BIGINT
            )
        );
    """)


def downgrade() -> None:
    """Remover RLS."""
    
    # Remover políticas
    op.execute("DROP POLICY IF EXISTS integracao_calendario_isolation ON integracao_calendario;")
    op.execute("DROP POLICY IF EXISTS tipos_turno_isolation ON tipos_turno;")
    op.execute("DROP POLICY IF EXISTS turnos_isolation ON turnos;")
    op.execute("DROP POLICY IF EXISTS usuarios_isolation ON usuarios;")
    
    # Desabilitar RLS
    op.execute("ALTER TABLE integracao_calendario DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tipos_turno DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE turnos DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE usuarios DISABLE ROW LEVEL SECURITY;")
