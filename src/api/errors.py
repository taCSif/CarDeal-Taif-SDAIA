from typing import cast

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.api.middleware import trace_id_var

# Starlette types exception handlers as (Request, Exception) -> Response. The
# concrete exception type is narrowed with cast() so mypy --strict is satisfied
# while the handlers stay registrable with add_exception_handler.


def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    # Pydantic v2 places the original exception object in each error's "ctx" for
    # custom-validator failures, which is not JSON-serializable. Emit only the
    # safe, structured fields (and avoid echoing raw request input back).
    details = [
        {"type": error.get("type"), "loc": list(error.get("loc", [])), "msg": error.get("msg")}
        for error in validation_exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id_var.get(),
            "data": {"error": "VALIDATION_ERROR", "details": details},
        },
    )


def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"trace_id": trace_id_var.get(), "data": {"error": "INTERNAL_ERROR"}},
    )


def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(HTTPException, exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"trace_id": trace_id_var.get(), "data": {"error": str(http_exc.detail)}},
    )
