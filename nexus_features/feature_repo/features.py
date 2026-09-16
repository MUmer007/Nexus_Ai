import os
from datetime import timedelta

from feast import Entity, FeatureService, FeatureView, Field, FileSource, ValueType
from feast.types import Float64, Int64, String

# Use absolute paths to avoid relative path issues
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Define Entities
customer = Entity(
    name="customer_id",
    description="Unique identifier for a customer",
    join_keys=["customer_id"],
    value_type=ValueType.INT64,
)

order = Entity(
    name="order_id",
    description="Unique identifier for an order",
    join_keys=["order_id"],
    value_type=ValueType.INT64,
)

# 2. Define Feature Views with absolute paths
customer_features = FeatureView(
    name="customer_features",
    entities=[customer],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_orders", dtype=Int64),
        Field(name="total_spend", dtype=Float64),
        Field(name="avg_order_value", dtype=Float64),
        Field(name="region", dtype=String),
        Field(name="tier", dtype=String),
    ],
    source=FileSource(
        path=os.path.join(BASE_DIR, "data/features/customer_features.parquet"),
        timestamp_field="event_timestamp",
    ),
    tags={"team": "nexus-ml"},
)

order_features = FeatureView(
    name="order_features",
    entities=[order],
    ttl=timedelta(hours=1),
    schema=[
        Field(name="total_amount", dtype=Float64),
        Field(name="hour_of_day", dtype=Int64),
        Field(name="day_of_week", dtype=Int64),
        Field(name="is_high_value", dtype=Int64),
        Field(name="is_night_order", dtype=Int64),
        Field(name="is_high_risk_combo", dtype=Int64),
    ],
    source=FileSource(
        path=os.path.join(BASE_DIR, "data/features/order_features.parquet"),
        timestamp_field="event_timestamp",
    ),
    tags={"team": "nexus-ml"},
)

# 3. Define a Feature Service
delivery_risk_features = FeatureService(
    name="delivery_risk_features",
    features=[order_features],
    description="Features used by the delivery risk prediction model",
)
