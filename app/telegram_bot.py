"""
Telegram Bot Module - Backward Compatibility Re-export.

This module re-exports build_application from the new modular location
for backward compatibility with existing code.

The actual implementation is now in:
    app/infrastructure/telegram/bot.py

Handler modules are in:
    app/infrastructure/telegram/handlers/
"""
from app.infrastructure.telegram.bot import build_application

__all__ = ["build_application"]
