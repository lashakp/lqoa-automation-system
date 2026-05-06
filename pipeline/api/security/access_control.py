import os

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader


API_KEY_NAME = "X-API-Key"

VALID_API_KEY = os.getenv(
    "API_KEY",
    "dev-secret-key"
)

api_key_header = APIKeyHeader(
    name=API_KEY_NAME,
    auto_error=False
)


def get_access_mode(

    api_key: str = Security(api_key_header)

):

    if api_key is None:

        return "demo"

    if api_key == VALID_API_KEY:

        return "full"

    raise HTTPException(

        status_code=401,

        detail="Invalid API key"
    )
