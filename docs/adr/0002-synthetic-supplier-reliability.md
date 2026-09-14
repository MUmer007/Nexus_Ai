# ADR 0002: Synthetic Supplier Reliability Scores

## Status
Accepted (Temporary simplification)

## Context
Our pitch requires identifying "unreliable suppliers." In a mature system, this score is dynamically calculated by comparing the `promised_date` vs `actual_arrival_date` on historical `purchase_orders`. However, in Phase 1 and 2, we have not yet built the purchasing/replenishment pipeline.

## Decision
For now, the `reliability_score` (0.0 to 1.0) in the `suppliers` table will be a static, seeded/synthetic value. 

## Consequences
- **Pros:** Allows us to immediately build and test downstream ML models (like delivery risk) that rely on supplier reliability as a feature, without waiting for the purchasing pipeline to be finished.
- **Cons:** The score does not reflect real-time reality. 
- **Future Action:** In Phase 3+, once `purchase_orders` and `receiving_events` are implemented, this static column must be dropped and replaced with a dynamically calculated metric in the dbt Gold layer.