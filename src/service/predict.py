from dataclasses import dataclass
from typing import Protocol

from src.domain.decisions import assess_deal
from src.domain.models import DealAssessment, Vehicle


class PriceModel(Protocol):
    def predict(self, vehicle: Vehicle) -> float: ...


@dataclass(frozen=True)
class ComparableCar:
    make: str
    type: str
    year: int
    mileage: int
    region: str
    price: float


class ComparableRepository(Protocol):
    def find_similar(self, vehicle: Vehicle, limit: int = 5) -> list[ComparableCar]: ...


class AuditRepository(Protocol):
    def record(self, trace_id: str, model_version: str, assessment: DealAssessment) -> None: ...


class PredictService:
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
        if self._audit is not None:
            self._audit.record(trace_id, model_version or self.model_version, assessment)
        return assessment

    def comparables(self, vehicle: Vehicle) -> list[ComparableCar]:
        return self._comparables.find_similar(vehicle, 5) if self._comparables else []
