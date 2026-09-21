from src.domain.models import Vehicle, Decision
from src.service.predict import PredictService

class FakeModel:
    def __init__(self): self.called = False
    def predict(self, vehicle): self.called = True; return 50_000

def test_service_orchestrates_model_and_policy():
    model = FakeModel()
    vehicle = Vehicle("Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5, "Gas", "Automatic", 1, "Riyadh")
    result = PredictService(model).predict(vehicle, 52_000)
    assert model.called
    assert result.decision == Decision.GOOD_DEAL
