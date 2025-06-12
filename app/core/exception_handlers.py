from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "path": request.url.path,
                "method": request.method
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Интеграция с Sentry
        if settings.SENTRY_DSN:
            from sentry_sdk import capture_exception
            capture_exception(exc)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "type": type(exc).__name__,
                "details": str(exc)
            }
        ) 