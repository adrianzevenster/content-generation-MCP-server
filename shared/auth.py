"""
Authentication middleware for API key validation.
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Use standard logging until structlog is configured
logger = logging.getLogger(__name__)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def load_api_key() -> Optional[str]:
    """
    Load API key from file or environment variable.

    Priority:
    1. Docker secret file at /run/secrets/api_key
    2. API_KEY_FILE environment variable pointing to a file
    3. API_KEY environment variable directly

    Returns:
        str: The API key if found, None otherwise
    """
    # Try Docker secret first (production)
    api_key_file = os.getenv("API_KEY_FILE", "/run/secrets/api_key")
    if os.path.exists(api_key_file):
        try:
            with open(api_key_file, "r") as f:
                key = f.read().strip()
                if key:
                    logger.info(f"API key loaded from file: {api_key_file}")
                    return key
        except Exception as e:
            logger.error(f"Failed to read API key file {api_key_file}: {e}")

    # Fallback to environment variable (for local dev)
    env_key = os.getenv("API_KEY")
    if env_key:
        logger.info("API key loaded from environment variable")
        return env_key.strip()

    # No API key configured - authentication disabled (log warning)
    logger.warning(
        "No API key configured. Running without authentication. "
        "Set API_KEY env var or mount secret at /run/secrets/api_key"
    )
    return None


# Load API key at module import time
EXPECTED_API_KEY = load_api_key()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    This is a FastAPI dependency that can be used to protect endpoints.
    Add it to endpoint signatures like:

        @app.post("/protected")
        async def protected_endpoint(api_key: str = Depends(verify_api_key)):
            ...

    Args:
        api_key: API key from X-API-Key header

    Returns:
        str: The validated API key

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    # If no API key is configured, skip authentication (dev mode)
    if EXPECTED_API_KEY is None:
        logger.debug("Authentication disabled - no API key configured")
        return "no-auth"

    # Check if API key was provided in request
    if api_key is None:
        logger.warning("Authentication failed: missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header in request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key matches expected value
    if api_key != EXPECTED_API_KEY:
        logger.warning("Authentication failed: invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("Authentication successful")
    return api_key
