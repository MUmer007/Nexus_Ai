
from feast import FeatureStore

# Initialize the feature store
store = FeatureStore(repo_path="../../nexus_features/feature_repo")

# Fetch features for specific orders from the ONLINE store (sub-ms latency)
# This is what your FastAPI will do in production
entity_rows = [
    {"order_id": 1},
    {"order_id": 5},
    {"order_id": 99},
]

features = store.get_online_features(
    features=[
        "order_features:total_amount",
        "order_features:is_high_value",
        "order_features:is_night_order",
        "order_features:is_high_risk_combo",
    ],
    entity_rows=entity_rows,
).to_df()

print("🎯 Features served from ONLINE store (real-time serving):")
print(features)
print("\n⚡ This is sub-millisecond latency - perfect for real-time ML inference!")
print(f"✅ Retrieved {len(features)} feature rows")
