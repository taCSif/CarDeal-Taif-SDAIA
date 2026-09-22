from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse

from src.adapters.model import SklearnPriceModel
from src.adapters.repository import ComparableCarsRepository, PostgresAuditRepository
from src.adapters.settings import Settings
from src.api.errors import generic_error_handler, http_error_handler, validation_error_handler
from src.api.middleware import TraceMiddleware, configure_logging, trace_id_var
from src.api.schemas import ComparablesQuery, PredictRequest
from src.domain.models import Vehicle
from src.service.predict import PredictService

router = APIRouter()
STATIC_DIR = Path(__file__).parent / "static"


# Shared readiness gate for every endpoint that needs a working model: if
# startup (see create_app's lifespan below) has not finished successfully,
# app.state.predict_service stays None and every dependent request gets a
# 503 with the same NOT_READY envelope /ready itself returns, instead of an
# AttributeError or a stale/partial service.
def get_service(request: Request) -> PredictService:
    service: PredictService | None = getattr(request.app.state, "predict_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="NOT_READY")
    return service


ServiceDependency = Annotated[PredictService, Depends(get_service)]


@router.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/health")
def health() -> dict[str, object]:
    return {"trace_id": trace_id_var.get(), "data": {"status": "ok"}}


@router.get("/ready")
def ready(request: Request) -> dict[str, object]:
    if not bool(getattr(request.app.state, "ready", False)):
        raise HTTPException(status_code=503, detail="NOT_READY")
    return {"trace_id": trace_id_var.get(), "data": {"status": "ready"}}


@router.post("/v1/predict")
def predict(payload: PredictRequest, service: ServiceDependency) -> dict[str, object]:
    # payload has already passed PredictRequest's validation (extra="forbid",
    # field ranges, make_model normalization) by the time FastAPI calls this
    # function; asking_price is used only here, after the estimate exists.
    vehicle = Vehicle(
        make_model=payload.make_model,
        year=payload.year,
        mileage=payload.mileage,
    )
    assessment = service.predict(
        vehicle, payload.asking_price, trace_id_var.get(), service.model_version
    )
    comparables = service.comparables(vehicle)
    data = assessment.__dict__ | {
        "decision": assessment.decision.value,
        "comparable_cars": [car.__dict__ for car in comparables],
    }
    return {"trace_id": trace_id_var.get(), "data": data}


@router.get("/v1/comparables")
def comparables(
    query: Annotated[ComparablesQuery, Query()], service: ServiceDependency
) -> dict[str, object]:
    # Query() on a pydantic model applies ComparablesQuery's own validation
    # (same extra="forbid" and ranges as PredictRequest) to the query string;
    # a failure here raises FastAPI's RequestValidationError, which
    # validation_error_handler turns into the same envelope POST /v1/predict
    # uses, so both endpoints reject bad input identically.
    vehicle = Vehicle(make_model=query.make_model, year=query.year, mileage=query.mileage)
    cars = service.comparables(vehicle)
    data = {"comparable_cars": [car.__dict__ for car in cars]}
    return {"trace_id": trace_id_var.get(), "data": data}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)

    # FastAPI lifespan: everything before `yield` runs once at startup,
    # everything after runs once at shutdown. The model is loaded and warmed
    # up here — never lazily on the first request and never at import time —
    # so that a slow or failed load is visible as a 503 from /ready rather
    # than an unpredictable delay or crash on a user's first request.
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.ready = False
        app.state.predict_service = None
        try:
            model = SklearnPriceModel.load(Path(settings.model_path))
            model.warm_up()
            comparables = ComparableCarsRepository(Path(settings.comparables_path))
            audit = None
            if settings.database_url:
                audit = PostgresAuditRepository(settings.database_url)
                audit.initialize()
            service = PredictService(
                model, comparables=comparables, audit=audit, model_version=settings.model_version
            )
            app.state.predict_service = service
            app.state.ready = True
        except Exception:
            # A missing/corrupt model artifact or an unreachable database
            # must not crash the process: the app stays alive but unready
            # (app.state.ready stays False), so /health still reports ok
            # while /ready and every model-backed endpoint report 503.
            import logging
            logging.getLogger("deal_checker").exception("startup_not_ready")
        yield
        app.state.ready = False
        app.state.predict_service = None

    app = FastAPI(title="CarDeal — Saudi Used Car Deal Checker", version="1.0.0", lifespan=lifespan)
    app.add_middleware(TraceMiddleware)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    app.include_router(router)
    return app
