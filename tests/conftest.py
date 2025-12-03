import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

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
