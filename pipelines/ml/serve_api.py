from contextlib import asynccontextmanager
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI
from feast import FeatureStore
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

# Calculate project root dynamically (D:\nexus-ai)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_PATH = str(PROJECT_ROOT / "nexus_features" / "feature_repo")
MLFLOW_DB_PATH = str(PROJECT_ROOT / "mlflow.db")

model = None
feature_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, feature_store

    # 1. Load model from MLflow
    print("📦 Loading model from MLflow registry...")
    mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB_PATH}")

    runs = mlflow.search_runs(
        experiment_names=["nexus_delivery_risk"],
        order_by=["start_time DESC"],
        max_results=1,
    )
    latest_run_id = runs.iloc[0]["run_id"]
    model = mlflow.sklearn.load_model(f"runs:/{latest_run_id}/model")
    print(f"✅ Model loaded from run: {latest_run_id}")

    # 2. Initialize Feature Store
    print("🔧 Initializing Feature Store...")
    print(f"   Looking for repo at: {REPO_PATH}")
    feature_store = FeatureStore(repo_path=REPO_PATH)
    print("✅ Feature Store ready")

    yield  # Application runs here

    # Cleanup on shutdown (if needed)
    print("🛑 Shutting down API...")


# 1. Create the app FIRST
app = FastAPI(title="NEXUS Delivery Risk Prediction API", lifespan=lifespan)

# 2. Instrument the app SECOND (This exposes the /metrics endpoint!)
Instrumentator().instrument(app).expose(app)


class OrderPredictionRequest(BaseModel):
    order_id: int


@app.post("/predict")
def predict(request: OrderPredictionRequest):
    # 1. Fetch features from the Feature Store (Online Store - sub-ms latency)
    feature_vector = feature_store.get_online_features(
        features=[
            "order_features:total_amount",
            "order_features:hour_of_day",
            "order_features:day_of_week",
            "order_features:is_high_value",
            "order_features:is_night_order",
            "order_features:is_high_risk_combo",
        ],
        entity_rows=[{"order_id": request.order_id}],
    ).to_dict()

    # 2. Build the feature DataFrame (matches training schema EXACTLY)
    features_df = pd.DataFrame(
        [
            {
                "customer_id": 1,  # Mocked for this demo
                "total_amount": float(feature_vector["total_amount"][0]),
                "hour_of_day": int(feature_vector["hour_of_day"][0]),
                "day_of_week": int(feature_vector["day_of_week"][0]),
                "is_high_value": int(feature_vector["is_high_value"][0]),
                "is_night_order": int(feature_vector["is_night_order"][0]),
                "is_high_risk_combo": int(feature_vector["is_high_risk_combo"][0]),
            }
        ]
    )

    # 3. Predict
    feature_cols = [
        "customer_id",
        "total_amount",
        "hour_of_day",
        "day_of_week",
        "is_high_value",
        "is_night_order",
        "is_high_risk_combo",
    ]

    prediction = int(model.predict(features_df[feature_cols])[0])
    probability = float(model.predict_proba(features_df[feature_cols])[0][1])

    return {
        "order_id": request.order_id,
        "is_delayed": bool(prediction),
        "delay_probability": round(probability, 4),
        "risk_level": "HIGH" if probability > 0.5 else "LOW",
        "features_served_from": "feast_online_store",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "feature_store_loaded": feature_store is not None,
    }