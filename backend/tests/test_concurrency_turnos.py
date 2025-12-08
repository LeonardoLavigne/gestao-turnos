
import pytest
import asyncio
from datetime import date, time, datetime, UTC, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.domain.entities.usuario import Usuario
from app.domain.entities.assinatura import Assinatura, AssinaturaStatus, PlanoType
from app.core.config import get_settings
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException
from unittest.mock import MagicMock

# Force xdist to be available if needed later, but this test uses asyncio.gather
pytest_plugins = ["pytest_asyncio"]

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.infrastructure.database.session import _get_database_url

async def execute_creation(telegram_id: int, shift_date: date, session_factory):
    """
    Helper function using a specific session factory.
    """
    async with session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        # Mock dependencies
        settings = get_settings()
        settings.free_tier_max_shifts = 30 # Enforce limit
        
        calendar_mock = MagicMock()
        sync_mock = MagicMock()
        
        use_case = CriarTurnoUseCase(uow, calendar_mock, settings, sync_mock)
        
        try:
            await use_case.execute(
                telegram_id,
                data_referencia=shift_date,
                hora_inicio=time(9,0),
                hora_fim=time(18,0)
            )
            return "SUCCESS"
        except LimiteTurnosExcedidoException:
            return "LIMIT_EXCEEDED"
        except Exception as e:
            return f"ERROR: {e}"

@pytest.mark.asyncio
async def test_concorrencia_limite_free_50_turnos(db_session):
    """
    Simulates 50 concurrent requests trying to create shifts for a Free User (Limit 30).
    """
    db = db_session
    telegram_id = 99999
    
    # 1. Setup Environment 
    await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.commit()

    await db.execute(text(f"INSERT INTO usuarios (telegram_user_id, nome, numero_funcionario, criado_em, atualizado_em) VALUES ({telegram_id}, 'Concurrency User', 'CONC001', NOW(), NOW())"))
    await db.execute(text(f"""
        INSERT INTO assinaturas (telegram_user_id, stripe_customer_id, status, plano, criado_em, atualizado_em)
        VALUES ({telegram_id}, 'cust_conc', 'active', 'free', NOW(), NOW())
    """))
    await db.commit()
    
    # Create LOCAL engine to avoid 'different event loop' error with global engine
    url = _get_database_url()
    local_engine = create_async_engine(url, pool_size=10, max_overflow=20)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False, autoflush=False)

    tasks = []
    target_date = date(2025, 1, 1)
    
    for i in range(50):
        tasks.append(execute_creation(telegram_id, target_date, LocalSession))
        
    results = await asyncio.gather(*tasks)
    await local_engine.dispose()
    
    # 3. Analyze Results
    success_count = results.count("SUCCESS")
    limit_count = results.count("LIMIT_EXCEEDED")
    # ... (assertions)
    
    assert success_count == 30
    assert limit_count == 20

@pytest.mark.asyncio
async def test_carga_100_users_premium(db_session):
    """
    Load Test: 100 DISTINCT users, all PREMIUM...
    """
    db = db_session
    base_id = 80000
    count_users = 100
    
    # Setup ...
    await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id >= {base_id} AND telegram_user_id < {base_id + count_users}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id >= {base_id} AND telegram_user_id < {base_id + count_users}"))
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id >= {base_id} AND telegram_user_id < {base_id + count_users}"))
    await db.commit()

    for i in range(count_users):
        uid = base_id + i
        await db.execute(text(f"INSERT INTO usuarios (telegram_user_id, nome, numero_funcionario, criado_em, atualizado_em) VALUES ({uid}, 'Load User {i}', 'LOAD{i}', NOW(), NOW())"))
        await db.execute(text(f"""
            INSERT INTO assinaturas (telegram_user_id, stripe_customer_id, status, plano, criado_em, atualizado_em)
            VALUES ({uid}, 'cust_load_{i}', 'active', 'pro', NOW(), NOW())
        """))
    await db.commit()
    
    # Create LOCAL engine 
    url = _get_database_url()
    # Increase pool size to handle 100 or rely on queue?
    # Default stack is 10+20 = 30 connections. 
    # With 10000 tasks, we need significant time to process queue.
    # Default pool_timeout is 30s. 10k requests take >30s.
    local_engine = create_async_engine(url, pool_size=10, max_overflow=20, pool_timeout=120)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False, autoflush=False)
    
    # 2. Launch 100 * 100 = 10,000 concurrent tasks
    tasks = []
    base_date = date(2025, 1, 1)
    shifts_per_user = 100
    
    # Generate 100 shifts for each of the 100 users
    for i in range(count_users):
        uid = base_id + i
        for j in range(shifts_per_user):
            # Use different dates to make them distinct shifts
            d = base_date + timedelta(days=j)
            tasks.append(execute_creation(uid, d, LocalSession))
        
    start = datetime.now()
    results = await asyncio.gather(*tasks)
    duration = (datetime.now() - start).total_seconds()
    await local_engine.dispose()
    
    print(f"Processed {len(tasks)} requests in {duration:.2f}s")
    
    # 3. Analyze
    success_count = results.count("SUCCESS")
    failures = [r for r in results if r != "SUCCESS"]
    
    if failures:
        print(f"Failures: {failures[:5]}...")
        
    assert success_count == count_users * shifts_per_user
