from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Verifica a saúde da aplicação e conexão com o banco de dados.
    """
    try:
        # Testar conexão com DB
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        # Logar erro real em produção
        print(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
