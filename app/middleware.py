
import hmac
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Validates API keys for private application endpoints.

    Public endpoint:
        GET /health

    All other routes require:
        X-Api-Key: configured-secret
    """

    PUBLIC_PATHS = {
        "/health",
    }

    async def dispatch(self, request: Request, call_next):

        # Allow explicitly public endpoints.
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        configured_key = settings.API_KEY_SECRET

        # Reject requests if server configuration is missing.
        if not configured_key:
            logger.error(
                "API authentication rejected: API_KEY_SECRET is not configured."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "API authentication is not configured."
                },
            )

        # Read incoming API key.
        incoming_key = request.headers.get("X-Api-Key")

        if not incoming_key or not hmac.compare_digest(
            incoming_key,
            configured_key,
        ):
            logger.warning(
                "Unauthorized API request: invalid or missing API key."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or missing API key."
                },
            )

        # Authentication successful.
        return await call_next(request)
