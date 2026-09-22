from dataclasses import dataclass
from typing import Protocol

from src.domain.decisions import assess_deal
from src.domain.models import DealAssessment, Vehicle


# Protocols define the service's dependencies as structural interfaces rather
# than concrete classes. This is the dependency-injection boundary described
# in DECISIONS.md #4: PredictService depends only on these shapes, so the
# sklearn-backed adapter, the CSV-backed repository, and the Postgres sink
# can each be swapped or stubbed in tests without changing this module.
class PriceModel(Protocol):
    def predict(self, vehicle: Vehicle) -> float: ...


@dataclass(frozen=True)
class ComparableCar:
    make_model: str
    year: int
    mileage: int
    price: float


class ComparableRepository(Protocol):
    def find_similar(self, vehicle: Vehicle, limit: int = 5) -> list[ComparableCar]: ...


class AuditRepository(Protocol):
    def record(self, trace_id: str, model_version: str, assessment: DealAssessment) -> None: ...


class PredictService:
    """Orchestrates a single prediction: get an estimate from the model,
    apply the deal policy, and optionally persist an audit record. Contains
    no ML or HTTP concerns of its own — those live in adapters and api.
    """

    def __init__(
        self,
        model: PriceModel,
        comparables: ComparableRepository | None = None,
        audit: AuditRepository | None = None,
        model_version: str = "unknown",
    ) -> None:
        self._model = model
        self._comparables = comparables
        self._audit = audit
        self.model_version = model_version

    def predict(
        self,
        vehicle: Vehicle,
        asking_price: float,
        trace_id: str = "-",
        model_version: str | None = None,
    ) -> DealAssessment:
        estimated = self._model.predict(vehicle)
        assessment = assess_deal(estimated, asking_price)
        # Audit persistence is best-effort context (trace_id, prices,
        # decision) for observability, not a source of truth the response
        # depends on; a missing audit repository simply skips this step.
        if self._audit is not None:
            self._audit.record(trace_id, model_version or self.model_version, assessment)
        return assessment

    def comparables(self, vehicle: Vehicle) -> list[ComparableCar]:
        # Fixed limit of 5: this is what both POST /v1/predict's embedded
        # comparables field and GET /v1/comparables expose to callers.
        return self._comparables.find_similar(vehicle, 5) if self._comparables else []
