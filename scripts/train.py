from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = ["Make", "Type", "Year", "Origin", "Color", "Options", "Engine_Size", "Fuel_Type", "Gear_Type", "Mileage", "Region"]
CATEGORICAL = ["Make", "Type", "Origin", "Color", "Options", "Fuel_Type", "Gear_Type", "Region"]
NUMERIC = ["Year", "Engine_Size", "Mileage"]
TARGET = "Price"


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = set(FEATURES + [TARGET])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df = df[FEATURES + [TARGET]].copy()
    for col in NUMERIC + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=FEATURES + [TARGET])
    df = df[(df["Price"] >= 5_000) & (df["Mileage"] <= 700_000)]
    df = df[(df["Year"] >= 1950) & (df["Year"] <= 2025) & (df["Engine_Size"] > 0)]
    for col in CATEGORICAL:
        df[col] = df[col].astype(str).str.strip()
    return df.reset_index(drop=True)


def build_pipeline() -> Pipeline:
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=2, sparse_output=False), CATEGORICAL),
        ("num", "passthrough", NUMERIC),
    ])
    return Pipeline([
        ("preprocess", prep),
        ("model", HistGradientBoostingRegressor(max_iter=250, learning_rate=0.06, l2_regularization=1.0, random_state=42)),
    ])


def main() -> None:
    data_path = Path("data/raw/saudi_used_cars.csv")
    artifact = Path("artifacts/price_model.joblib")
    if not data_path.exists():
        raise SystemExit(f"Dataset not found: {data_path}. Download the Kaggle dataset into data/raw/saudi_used_cars.csv")
    df = load_and_clean(data_path)
    X_train, X_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42)
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)
    metrics = {
        "rows_after_cleaning": len(df),
        "test_rows": len(y_test),
        "MAE_SAR": round(mean_absolute_error(y_test, pred), 2),
        "RMSE_SAR": round(mean_squared_error(y_test, pred) ** 0.5, 2),
        "R2": round(r2_score(y_test, pred), 4),
    }
    artifact.parent.mkdir(exist_ok=True)
    joblib.dump(pipeline, artifact)
    Path("artifacts/metrics.json").write_text(__import__("json").dumps(metrics, indent=2), encoding="utf-8")
    print(metrics)


if __name__ == "__main__":
    main()
