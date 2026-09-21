from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.domain.models import DealAssessment, Vehicle
from src.service.predict import ComparableCar


class ComparableCarsRepository:
    """Read-only historical comparable listings produced by training."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: pd.DataFrame | None = None

    def _load(self) -> pd.DataFrame:
        if self._data is None:
            if not self.path.exists():
                self._data = pd.DataFrame()
            else:
                self._data = pd.read_csv(self.path)
        return self._data

    def find_similar(self, vehicle: Vehicle, limit: int = 5) -> list[ComparableCar]:
        df = self._load()
        if df.empty or limit <= 0:
            return []

        candidates = df.copy()
        exact = candidates[candidates["Make_Model"].astype(str).str.casefold() == vehicle.make_model.casefold()]
        pool = exact if len(exact) >= limit else candidates
        pool = pool.copy()
        pool["_distance"] = (
            (pool["Year"] - vehicle.year).abs() * 3
            + (pool["Mileage"] - vehicle.mileage).abs() / 100_000
            + (pool["Make_Model"].astype(str).str.casefold() != vehicle.make_model.casefold()).astype(int) * 10
        )
        rows = pool.nsmallest(limit, "_distance")
        return [
            ComparableCar(
                make_model=str(row.Make_Model),
                year=int(row.Year),
                mileage=int(row.Mileage),
                price=float(row.Price),
            )
            for row in rows.itertuples(index=False)
        ]


class PostgresAuditRepository:
    """Minimal audit sink; stores no full vehicle request."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self) -> Any:
        import psycopg
        return psycopg.connect(self.dsn)

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS prediction_audit (
                    id BIGSERIAL PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    estimated_price DOUBLE PRECISION NOT NULL,
                    asking_price DOUBLE PRECISION NOT NULL,
                    decision TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )"""
            )
            conn.commit()

    def record(self, trace_id: str, model_version: str, assessment: DealAssessment) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO prediction_audit
                   (trace_id, model_version, estimated_price, asking_price, decision, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    trace_id, model_version, assessment.estimated_price,
                    assessment.asking_price, assessment.decision.value,
                    datetime.now(timezone.utc),
                ),
            )
            conn.commit()
