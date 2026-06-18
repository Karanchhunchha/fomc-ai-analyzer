import os
import hmac
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    # If no key configured (local dev), skip check
    if not INTERNAL_API_KEY:
        return True
    if not api_key or not hmac.compare_digest(api_key, INTERNAL_API_KEY):
        raise HTTPException(
            status_code=403,
            detail={"error": "UNAUTHORIZED", "message": "Valid X-API-Key header required"}
        )
    return True
