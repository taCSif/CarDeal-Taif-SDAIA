from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RAW_FEATURES = ["Make", "Type", "Year", "Mileage"]
FEATURES = ["Make_Model", "Year", "Mileage"]
TARGET = "Price"
SEED = 42


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = set(RAW_FEATURES + [TARGET])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df = df[RAW_FEATURES + [TARGET]].copy()
    for col in ["Year", "Mileage", TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=RAW_FEATURES + [TARGET])
    df = df[(df["Price"] >= 5_000) & (df["Mileage"] <= 700_000)]
    df = df[(df["Year"] >= 1950) & (df["Year"] <= 2025)]
    for col in ["Make", "Type"]:
        df[col] = df[col].astype(str).str.strip()
    df = df[(df[["Make", "Type"]] != "").all(axis=1)]
    df["Make_Model"] = df["Make"] + " " + df["Type"]
    return df[["Make_Model", "Year", "Mileage", TARGET]].reset_index(drop=True)


def build_pipeline() -> Pipeline:
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=2, sparse_output=False), ["Make_Model"]),
        ("num", "passthrough", ["Year", "Mileage"]),
    ])
    return Pipeline([
        ("preprocess", prep),
        ("model", HistGradientBoostingRegressor(
            max_iter=250, learning_rate=0.06, l2_regularization=1.0, random_state=SEED,
        )),
    ])


def main() -> None:
    data_path = Path("data/raw/saudi_used_cars.csv")
    artifact_dir = Path("artifacts")
    artifact = artifact_dir / "price_model.joblib"
    if not data_path.exists():
        raise SystemExit(f"Dataset not found: {data_path}")
    raw = pd.read_csv(data_path)
    df = load_and_clean(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df[TARGET], test_size=0.2, random_state=SEED,
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)
    metrics = {
        "source_rows": int(len(raw)),
        "rows_after_cleaning": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "MAE_SAR": round(float(mean_absolute_error(y_test, pred)), 2),
        "RMSE_SAR": round(float(mean_squared_error(y_test, pred) ** 0.5), 2),
        "R2": round(float(r2_score(y_test, pred)), 4),
        "random_seed": SEED,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact)
    df.to_csv(artifact_dir / "comparable_cars.csv", index=False)
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (artifact_dir / "model_metadata.json").write_text(json.dumps({
        "features": FEATURES,
        "public_inputs": ["make_model", "year", "mileage", "asking_price"],
        "target": TARGET,
        "model": "HistGradientBoostingRegressor",
        "training_seed": SEED,
        "dataset_warning": (
            "2021 historical Syarah listings; predictions are estimates, "
            "not current-market guarantees."
        ),
    }, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
