from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.api.middleware import trace_id_var


def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id_var.get(),
            "data": {"error": "VALIDATION_ERROR", "details": exc.errors()},
        },
    )


def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"trace_id": trace_id_var.get(), "data": {"error": "INTERNAL_ERROR"}},
    )


def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"trace_id": trace_id_var.get(), "data": {"error": str(exc.detail)}},
    )
