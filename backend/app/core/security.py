"""Admin authentication dependency."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


async def get_current_admin(api_key: str | None = Security(_api_key_header)) -> str:
    """Verify the X-Admin-API-Key header.

    Returns the key on success, raises 401 on missing or invalid key.
    """
    if not api_key or api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
