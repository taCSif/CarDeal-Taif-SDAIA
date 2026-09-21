from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_path: Path = Path("artifacts/price_model.joblib")
    comparables_path: Path = Path("artifacts/comparable_cars.csv")
    model_version: str = "unknown"
    database_url: str | None = None
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_prefix="DEAL_CHECKER_", env_file=".env", extra="ignore")
