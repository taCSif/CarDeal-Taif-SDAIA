from src.domain.decisions import assess_deal
from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService


class FixedModel:
    def predict(self, vehicle: Vehicle) -> float:
        return 100_000.0


def test_directional_behavior():
    service = PredictService(FixedModel())
    vehicle = Vehicle("Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5, "Gas", "Automatic", 80_000, "Riyadh")
    prices = [90_000, 105_000, 110_000, 115_000, 120_000]
    order = {Decision.GOOD_DEAL: 0, Decision.REVIEW: 1, Decision.POOR_DEAL: 2}
    severities = [order[service.predict(vehicle, p).decision] for p in prices]
    assert severities == sorted(severities)


def test_invariance_to_vehicle_copy():
    service = PredictService(FixedModel())
    a = Vehicle("Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5, "Gas", "Automatic", 80_000, "Riyadh")
    b = Vehicle(**a.__dict__)
    assert service.predict(a, 110_000) == service.predict(b, 110_000)
