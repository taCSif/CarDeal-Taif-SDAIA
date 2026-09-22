from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Typed, fail-fast configuration. All values are read from environment
# variables prefixed DEAL_CHECKER_ (or a local .env file, gitignored);
# extra="forbid" means an unrecognized environment variable raises at
# startup instead of being silently ignored. database_url is optional
# because the audit repository (see adapters.repository) is itself
# optional — the service runs without PostgreSQL configured.
class Settings(BaseSettings):
    model_path: Path = Path("artifacts/price_model.joblib")
    comparables_path: Path = Path("artifacts/comparable_cars.csv")
    model_version: str = "unknown"
    database_url: str | None = None
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_prefix="DEAL_CHECKER_", env_file=".env", extra="forbid")
