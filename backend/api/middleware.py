import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.utils.exceptions import FridayError
from backend.utils.logger import LogContext, get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        with LogContext(request_id=request_id, path=request.url.path, method=request.method):
            try:
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response
            except Exception as e:
                logger.exception("unhandled_request_exception", error=str(e))
                raise


def setup_middlewares(app: FastAPI) -> None:
    """Register all middlewares and exception handlers."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID & Logging Context
    app.add_middleware(RequestContextMiddleware)

    # Global Exception Handlers
    @app.exception_handler(FridayError)
    async def friday_error_handler(request: Request, exc: FridayError) -> JSONResponse:
        logger.error("api_friday_error", error_code=exc.error_code, message=exc.message)
        
        status_code = 400
        if "RESOURCE_EXHAUSTED" in exc.message or "429" in exc.message or exc.error_code == "GEMINI_API_ERROR":
            status_code = 429
            
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("api_unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": str(exc),
            },
        )
