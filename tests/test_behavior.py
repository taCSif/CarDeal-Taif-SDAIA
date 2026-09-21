from src.api.schemas import PredictRequest
from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService


class FixedModel:
    def predict(self, vehicle: Vehicle) -> float:
        return 100_000.0


def vehicle() -> Vehicle:
    return Vehicle("Toyota Camry", 2021, 80_000)


def test_directional_behavior() -> None:
    service = PredictService(FixedModel())
    prices = [90_000, 105_000, 110_000, 115_000, 120_000]
    order = {Decision.GOOD_DEAL: 0, Decision.REVIEW: 1, Decision.POOR_DEAL: 2}
    severities = [order[service.predict(vehicle(), p).decision] for p in prices]
    assert severities == sorted(severities)


def test_metadata_trace_id_does_not_change_decision() -> None:
    service = PredictService(FixedModel())
    first = service.predict(vehicle(), 110_000, trace_id="trace-a")
    second = service.predict(vehicle(), 110_000, trace_id="trace-b")
    assert first == second


def test_api_text_normalization_is_invariant_to_outer_whitespace() -> None:
    base = {"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000, "asking_price": 72_000}
    normalized = PredictRequest(**base)
    spaced = PredictRequest(**{**base, "make_model": "  Toyota Camry  "})
    assert normalized.make_model == spaced.make_model == "Toyota Camry"
