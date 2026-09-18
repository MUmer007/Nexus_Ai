"""
NEXUS MLOps: Tag the latest trained model as 'challenger'
Run this before the promotion script to set up the test.
"""

import os

import mlflow
from mlflow.tracking import MlflowClient

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.path.join(PROJECT_ROOT, "mlflow.db")
mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")
client = MlflowClient()

MODEL_NAME = "nexus_delivery_risk_model"


def tag_latest_as_challenger():
    """Find the most recent model version and tag it as 'challenger'."""
    print(f"🔍 Looking for registered model: {MODEL_NAME}")

    # Check if the model is registered
    try:
        client.get_registered_model(MODEL_NAME)
    except mlflow.exceptions.MlflowException:
        print(f"❌ Model '{MODEL_NAME}' is not registered yet.")
        print(
            "💡 Run your training script first: "
            "uv run python pipelines/ml/train_delivery_risk.py"
        )
        return

    # Find the latest model version
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        print("❌ No model versions found in the registry.")
        return

    # Sort by creation time to get the latest
    latest = max(versions, key=lambda v: v.creation_timestamp)
    print(f"📦 Found latest model version: {latest.version} (Run: {latest.run_id})")

    # Tag it as 'challenger'
    client.set_registered_model_alias(
        name=MODEL_NAME, alias="challenger", version=latest.version
    )
    print(f"🥊 Version {latest.version} is now tagged as 'challenger'!")
    print(
        "\n🚀 Next step: Run the promotion script:\n"
        "   uv run python pipelines/mlops/promote_model.py"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🏷️  NEXUS MLOps: Tag Latest Model as Challenger")
    print("=" * 60)
    tag_latest_as_challenger()
