from __future__ import annotations

import re
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette_csrf import CSRFMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings

# Instancia global del limitador de tasa (en memoria por defecto para desarrollo)
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade cabeceras HTTP recomendadas para mejorar la seguridad.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS en producción para forzar HTTPS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response


def setup_security(app: FastAPI) -> None:
    """
    Registra los manejadores de excepciones de rate limiting y añade
    los middlewares de seguridad y protección CSRF a la aplicación FastAPI.
    """
    # Manejador de excepciones para límite de tasa superado
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middleware de cabeceras de seguridad
    app.add_middleware(SecurityHeadersMiddleware)

    # Middleware de protección CSRF para peticiones administrativas
    # Excluye la ruta de votación pública (/voter/vote y /v/{token}/vote)
    app.add_middleware(
        CSRFMiddleware,
        secret=settings.JWT_SECRET,
        cookie_name="csrftoken",
        header_name="x-csrftoken",
        cookie_samesite="lax",
        cookie_secure=settings.ENVIRONMENT == "production",
        exempt_urls=[
            re.compile(r"^/voter/vote$"),
            re.compile(r"^/v/[a-zA-Z0-9_\-]+/vote$"),
        ],
    )
