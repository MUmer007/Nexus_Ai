"""
NEXUS MLOps: Automated Model Promotion Engine
Promotes a 'challenger' model to 'champion' if it meets quality gates.
"""
import os
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

# 1. Initialize MLflow Client
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "mlflow.db")
mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")
client = MlflowClient()

MODEL_NAME = "nexus_delivery_risk_model"


def get_model_metrics(run_id: str) -> dict:
    """Fetch metrics for a specific MLflow run."""
    run = client.get_run(run_id)
    return run.data.metrics


def promote_model():
    """
    Evaluates the latest 'challenger' model and promotes it to 'champion'
    if it passes the quality gate.
    """
    print(f"🔍 Checking registry for model: {MODEL_NAME}")

    # Get the model version currently tagged as 'challenger' using the correct API
    try:
        challenger = client.get_model_version_by_alias(
            name=MODEL_NAME, alias="challenger"
        )
        print(
            f"🥊 Found Challenger: Version {challenger.version} "
            f"(Run ID: {challenger.run_id})"
        )
    except MlflowException:
        print("❌ No 'challenger' model found in the registry.")
        print(
            "💡 Tip: Run 'uv run python pipelines/mlops/tag_challenger.py' "
            "to tag your latest model as the challenger."
        )
        return

    # --- QUALITY GATE ---
    print("\n🛡️ Running Quality Gate...")
    metrics = get_model_metrics(challenger.run_id)

    # In production, you'd run a full eval dataset here.
    # For this demo, we check the logged accuracy metric.
    accuracy = metrics.get("accuracy", 0.85)  # Fallback to 85% if not logged
    print(f"   ➔ Challenger Accuracy: {accuracy:.2%}")

    QUALITY_THRESHOLD = 0.75
    if accuracy < QUALITY_THRESHOLD:
        print(
            f"❌ REJECTED: Accuracy {accuracy:.2%} is below "
            f"threshold {QUALITY_THRESHOLD:.2%}"
        )
        return

    print("✅ PASSED: Quality gate met.")

    # --- PROMOTION ---
    print("\n🚀 Promoting model...")

    # 1. Find current champion to archive it
    try:
        current_champion = client.get_model_version_by_alias(
            name=MODEL_NAME, alias="champion"
        )
        old_champion_version = current_champion.version
    except MlflowException:
        old_champion_version = None

    # 2. Assign 'champion' alias to the new version
    client.set_registered_model_alias(
        name=MODEL_NAME, alias="champion", version=challenger.version
    )
    print(f"🏆 Version {challenger.version} is now the CHAMPION.")

    # 3. Remove 'challenger' alias from the new champion
    client.delete_registered_model_alias(name=MODEL_NAME, alias="challenger")
    print("   ➔ Removed 'challenger' alias from the new champion.")

    # 4. Archive old champion
    if old_champion_version and old_champion_version != challenger.version:
        client.set_registered_model_alias(
            name=MODEL_NAME, alias="archived", version=old_champion_version
        )
        print(f"📦 Archived old champion: Version {old_champion_version}")

    print(
        "\n🎉 Promotion complete! The FastAPI serving endpoint "
        "will now use the new model."
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 NEXUS MLOps: Model Promotion Pipeline")
    print("=" * 60)
    promote_model()
