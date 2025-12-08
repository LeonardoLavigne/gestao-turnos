import hashlib
import hmac
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.security import create_access_token
from app.api.deps import get_usuario_repo, get_criar_usuario_use_case
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from fastapi import Depends

router = APIRouter()

class TelegramAuthSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str

from fastapi import Response

@router.post("/login", summary="Login via Telegram Login Widget")
async def login_telegram(
    response: Response,
    auth_data: TelegramAuthSchema,
    usuario_repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
    criar_usuario_use_case = Depends(get_criar_usuario_use_case)
):
    """
    Validates Telegram Login data and returns a JWT Access Token via HttpOnly Cookie.
    1. Validates the hash provided by Telegram.
    2. Checks if data is recent (prevent replay attacks).
    3. Issues JWT for the user.
    """
    settings = get_settings()
    
    # 1. Validation Logic
    # Construct data-check-string
    data_dict = auth_data.model_dump(exclude={"hash"}, exclude_none=True)
    # Telegram sends data sorted alphabetically by key
    # "key=value" pairs joined by \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    
    # Compute HMAC-SHA256
    secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if computed_hash != auth_data.hash:
        raise HTTPException(status_code=401, detail="Invalid Telegram authentication")
        
    # 2. Freshness Check (e.g., 24h)
    if time.time() - auth_data.auth_date > 86400:
        raise HTTPException(status_code=401, detail="Authentication data is outdated")

    # 3. Create/Update User
    existing_user = await usuario_repo.buscar_por_telegram_id(auth_data.id)
    if not existing_user:
        # Create new user
        from app.presentation.schemas import UsuarioCreate
        new_user_in = UsuarioCreate(
            telegram_user_id=auth_data.id,
            nome=f"{auth_data.first_name} {auth_data.last_name or ''}".strip(),
            username=auth_data.username,
            # Generate temporary employee number if needed or optional
            numero_funcionario=str(auth_data.id) 
        )
        # Execute creation
        await criar_usuario_use_case.execute(new_user_in)

    access_token = create_access_token(subject=auth_data.id)
    
    # Set HttpOnly Cookie
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=False, # Set to True in Production (TLS)
        samesite="lax",
        max_age=60 * 60 * 24 * 7 # 7 days
    )
    
    return {
        "message": "Login successful",
        "user": {
            "id": auth_data.id,
            "first_name": auth_data.first_name,
            "username": auth_data.username
        }
    }
