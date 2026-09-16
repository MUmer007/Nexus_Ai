import os

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="NEXUS Delivery Risk Prediction API")

model = None


@app.on_event("startup")
def load_model():
    global model
    print("📦 Loading LATEST model from MLflow registry...")

    db_path = os.path.join(os.getcwd(), "mlflow.db")
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")

    runs = mlflow.search_runs(
        experiment_names=["nexus_delivery_risk"],
        order_by=["start_time DESC"],
        max_results=1,
    )

    if runs.empty:
        raise RuntimeError("No runs found. Run training first.")

    latest_run_id = runs.iloc[0]["run_id"]
    model_uri = f"runs:/{latest_run_id}/model"

    model = mlflow.sklearn.load_model(model_uri)
    print(
        f"✅ Model loaded successfully from run: {latest_run_id} (Accuracy: {runs.iloc[0]['metrics.accuracy']:.4f})"
    )


class OrderFeatures(BaseModel):
    customer_id: int
    total_amount: float
    hour_of_day: int
    day_of_week: int


@app.post("/predict")
def predict(features: OrderFeatures):
    # 1. Feature Engineering (MUST MATCH TRAINING SCRIPT EXACTLY)
    df = pd.DataFrame([features.dict()])
    df["is_high_value"] = 1 if df["total_amount"].iloc[0] > 1000 else 0
    df["is_night_order"] = (
        1 if df["hour_of_day"].iloc[0] >= 22 or df["hour_of_day"].iloc[0] <= 5 else 0
    )
    df["is_high_risk_combo"] = (
        1
        if (df["is_high_value"].iloc[0] == 1 and df["is_night_order"].iloc[0] == 1)
        else 0
    )

    # 2. Predict
    feature_cols = [
        "customer_id",
        "total_amount",
        "hour_of_day",
        "day_of_week",
        "is_high_value",
        "is_night_order",
        "is_high_risk_combo",
    ]

    prediction = int(model.predict(df[feature_cols])[0])
    probability = float(model.predict_proba(df[feature_cols])[0][1])

    return {
        "order_id": "mock-123",
        "is_delayed": bool(prediction),
        "delay_probability": round(probability, 4),
        "risk_level": "HIGH" if probability > 0.5 else "LOW",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}
