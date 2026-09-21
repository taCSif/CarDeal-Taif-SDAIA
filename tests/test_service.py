from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService


class FakeModel:
    def __init__(self) -> None:
        self.called = False

    def predict(self, vehicle: Vehicle) -> float:
        self.called = True
        return 50_000


def vehicle() -> Vehicle:
    return Vehicle("Toyota Camry", 2021, 1)


def test_service_orchestrates_model_and_policy() -> None:
    model = FakeModel()
    service = PredictService(model)
    result = service.predict(vehicle(), 52_000)
    assert model.called
    assert result.decision == Decision.GOOD_DEAL
    assert service.comparables(vehicle()) == []
