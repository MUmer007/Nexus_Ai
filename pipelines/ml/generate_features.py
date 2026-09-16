from datetime import UTC, datetime

import numpy as np
import pandas as pd

# Use UTC timestamps to avoid timezone issues with Feast
now_utc = datetime.now(UTC)

# Customer features
n_customers = 200
customer_df = pd.DataFrame(
    {
        "customer_id": range(1, n_customers + 1),
        "total_orders": np.random.randint(1, 50, n_customers),
        "total_spend": np.random.uniform(100, 50000, n_customers).round(2),
        "avg_order_value": np.random.uniform(50, 2000, n_customers).round(2),
        "region": np.random.choice(["North", "South", "East", "West"], n_customers),
        "tier": np.random.choice(
            ["premium", "standard", "basic"], n_customers, p=[0.2, 0.5, 0.3]
        ),
        "event_timestamp": [now_utc] * n_customers,
        "created": [now_utc] * n_customers,
    }
)
customer_df.to_parquet("data/features/customer_features.parquet")
print(f"✅ Generated {len(customer_df)} customer feature rows (UTC)")

# Order features
n_orders = 1000
order_df = pd.DataFrame(
    {
        "order_id": range(1, n_orders + 1),
        "total_amount": np.random.uniform(10, 5000, n_orders).round(2),
        "hour_of_day": np.random.randint(0, 24, n_orders),
        "day_of_week": np.random.randint(0, 7, n_orders),
        "is_high_value": (np.random.uniform(10, 5000, n_orders) > 1000).astype(int),
        "is_night_order": (
            (np.random.randint(0, 24, n_orders) >= 22)
            | (np.random.randint(0, 24, n_orders) <= 5)
        ).astype(int),
        "is_high_risk_combo": 0,
        "event_timestamp": [now_utc] * n_orders,
        "created": [now_utc] * n_orders,
    }
)
order_df["is_high_risk_combo"] = (
    (order_df["is_high_value"] == 1) & (order_df["is_night_order"] == 1)
).astype(int)
order_df.to_parquet("data/features/order_features.parquet")
print(f"✅ Generated {len(order_df)} order feature rows (UTC)")
