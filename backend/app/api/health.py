"""
Health check endpoint for monitoring application status.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["Monitoring"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Verifica a saúde da aplicação e conexão com o banco de dados.
    """
    try:
        # Testar conexão com DB
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Database connection failed")
