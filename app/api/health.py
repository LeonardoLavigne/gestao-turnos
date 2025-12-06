"""
Health check endpoint for monitoring application status.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["Monitoring"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifica a saúde da aplicação e conexão com o banco de dados.
    """
    try:
        # Testar conexão com DB
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Database connection failed")
