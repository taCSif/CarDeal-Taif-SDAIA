from pathlib import Path


class DatasetRepository:
    """Minimal dataset access for training and comparable-car extension."""
    def __init__(self, path: Path) -> None:
        self.path = path
