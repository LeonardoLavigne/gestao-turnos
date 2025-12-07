from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from app.core.config import get_settings

ALGORITHM = "HS256"

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Creates a JWT access token.
    :param subject: Main identifier (e.g., user_id)
    :param expires_delta: Optional expiration time
    :return: Encoded JWT string
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict | None:
    """
    Decodes and verifies a JWT token.
    :param token: JWT string
    :return: Payload dict if valid, None otherwise
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
