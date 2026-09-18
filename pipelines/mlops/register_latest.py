import mlflow
from mlflow.tracking import MlflowClient

# 1. Connect to your local MLflow database
mlflow.set_tracking_uri("sqlite:///D:/nexus-ai/mlflow.db")
client = MlflowClient()

# 2. Find the latest run in the nexus_delivery_risk experiment
experiment = client.get_experiment_by_name("nexus_delivery_risk")
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["start_time DESC"],
    max_results=1,
)

if not runs:
    print("❌ No training runs found in the experiment.")
else:
    latest_run = runs[0]
    run_id = latest_run.info.run_id
    model_uri = f"runs:/{run_id}/model"
    model_name = "nexus_delivery_risk_model"

    print(f"🔍 Found latest run: {run_id}")
    print(f"📦 Registering model from run as '{model_name}'...")

    # 3. Create the registered model (if it doesn't exist) and add a version
    try:
        client.get_registered_model(model_name)
        print("   ➔ Model already exists, adding new version...")
    except mlflow.exceptions.MlflowException:
        client.create_registered_model(model_name)
        print("   ➔ Created new registered model...")

    mv = client.create_model_version(name=model_name, source=model_uri, run_id=run_id)

    print(
        f"\n🎉 SUCCESS! Model '{model_name}' is now registered as Version {mv.version}"
    )
    print("💡 You can now run: uv run python pipelines/mlops/tag_challenger.py")
