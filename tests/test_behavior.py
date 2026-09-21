from src.api.schemas import PredictRequest
from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService


class FixedModel:
    def predict(self, vehicle: Vehicle) -> float:
        return 100_000.0


def vehicle() -> Vehicle:
    return Vehicle(
        "Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5,
        "Gas", "Automatic", 80_000, "Riyadh",
    )


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
    base = {
        "make": "Toyota", "type": "Camry", "year": 2021, "origin": "Saudi",
        "color": "White", "options": "Full",
        "engine_size": 2.5, "fuel_type": "Gas", "gear_type": "Automatic",
        "mileage": 80_000, "region": "Riyadh", "asking_price": 72_000,
    }
    normalized = PredictRequest(**base)
    spaced = PredictRequest(**{**base, "make": " Toyota ", "type": " Camry "})
    assert normalized.make == spaced.make == "Toyota"
    assert normalized.type == spaced.type == "Camry"
