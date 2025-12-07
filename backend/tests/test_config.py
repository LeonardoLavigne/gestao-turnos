"""
Testes para o módulo config.
"""
import pytest
import os


class TestSettings:
    """Testes para configurações da aplicação."""
    
    def test_database_url_from_settings(self):
        """Verificar que database_url pode ser lida das settings."""
        from app.config import get_settings
        
        settings = get_settings()
        
        # Deve ter database_url (pode ser None se não configurado)
        assert hasattr(settings, 'database_url')
    
    def test_telegram_allowed_users_parsing(self):
        """Verificar parsing de telegram_allowed_users."""
        from app.config import get_settings
        
        settings = get_settings()
        
        # Deve ser uma lista (mesmo se vazia)
        assert hasattr(settings, 'telegram_allowed_users')
        assert isinstance(settings.telegram_allowed_users, list)
    
    def test_timezone(self):
        """Verificar timezone padrão."""
        from app.config import get_settings
        
        settings = get_settings()
        
        # Deve ter um timezone válido (campo é 'timezone', não 'app_timezone')
        assert hasattr(settings, 'timezone')
        assert settings.timezone is not None
    
    def test_stripe_keys_optional(self):
        """Verificar que chaves Stripe são opcionais."""
        from app.config import get_settings
        
        settings = get_settings()
        
        # Campo real é stripe_api_key
        assert hasattr(settings, 'stripe_api_key')
        assert hasattr(settings, 'stripe_webhook_secret')


class TestDatabaseUrl:
    """Testes para database_url."""
    
    def test_database_url_configured(self):
        """database_url está configurada."""
        from app.config import get_settings
        
        settings = get_settings()
        
        # Em ambiente Docker, deve ter PostgreSQL
        assert settings.database_url is not None
        assert 'postgresql' in settings.database_url or 'sqlite' in settings.database_url

