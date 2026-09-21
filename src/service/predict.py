from typing import Protocol

from src.domain.decisions import assess_deal
from src.domain.models import DealAssessment, Vehicle


class PriceModel(Protocol):
    def predict(self, vehicle: Vehicle) -> float: ...


class PredictService:
    def __init__(self, model: PriceModel) -> None:
        self._model = model

    def predict(self, vehicle: Vehicle, asking_price: float) -> DealAssessment:
        estimated = self._model.predict(vehicle)
        return assess_deal(estimated, asking_price)
