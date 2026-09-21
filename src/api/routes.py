from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from src.adapters.model import SklearnPriceModel
from src.adapters.repository import ComparableCarsRepository, PostgresAuditRepository
from src.adapters.settings import Settings
from src.api.errors import generic_error_handler, http_error_handler, validation_error_handler
from src.api.middleware import TraceMiddleware, configure_logging, trace_id_var
from src.api.schemas import PredictRequest
from src.domain.models import Vehicle
from src.service.predict import PredictService

router = APIRouter()


def get_service(request: Request) -> PredictService:
    service = getattr(request.app.state, "predict_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="NOT_READY")
    return service


@router.get("/health")
def health() -> dict[str, object]:
    return {"trace_id": trace_id_var.get(), "data": {"status": "ok"}}


@router.get("/ready")
def ready(request: Request) -> dict[str, object]:
    if not bool(getattr(request.app.state, "ready", False)):
        raise HTTPException(status_code=503, detail="NOT_READY")
    return {"trace_id": trace_id_var.get(), "data": {"status": "ready"}}


@router.post("/v1/predict")
def predict(
    payload: PredictRequest, service: PredictService = Depends(get_service)
) -> dict[str, object]:
    vehicle = Vehicle(
        make=payload.make, type=payload.type, year=payload.year, origin=payload.origin,
        color=payload.color, options=payload.options, engine_size=payload.engine_size,
        fuel_type=payload.fuel_type, gear_type=payload.gear_type, mileage=payload.mileage,
        region=payload.region,
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


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
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
            __import__("logging").getLogger("deal_checker").exception("startup_not_ready")
        yield
        app.state.ready = False
        app.state.predict_service = None

    app = FastAPI(title="Saudi Used Car Deal Checker", version="0.2.0", lifespan=lifespan)
    app.add_middleware(TraceMiddleware)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    app.include_router(router)
    return app
