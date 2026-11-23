from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from support_agent.api.routes import router
from support_agent.core.config import settings
from support_agent.schemas.responses import ErrorResponse


HTTP_ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
    )
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: object,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_validation_error(exc).model_dump(),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: object,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = HTTP_ERROR_CODES.get(exc.status_code, "INTERNAL_ERROR")
        message = str(exc.detail) if exc.detail else "Request failed"
        status_code = exc.status_code if exc.status_code in HTTP_ERROR_CODES else 500
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=code, message=message).model_dump(),
        )

    return application


def _validation_error(exc: RequestValidationError) -> ErrorResponse:
    details = [
        {
            "location": ".".join(str(part) for part in error["loc"]),
            "message": str(error["msg"]),
        }
        for error in exc.errors()
    ]
    return ErrorResponse(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
    )


app = create_app()
