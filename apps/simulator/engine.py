"""
NEXUS Decision Simulator Engine
Pure Python simulation logic — no DB dependencies, easily testable.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass
class BaselineMetrics:
    """Current state of the business (from Gold layer in production)."""
    total_orders: int = 10000
    total_revenue: float = 2_500_000.0
    avg_order_value: float = 250.0
    delay_rate: float = 0.12  # 12% of orders delayed
    avg_delivery_days: float = 4.5
    stockout_rate: float = 0.05  # 5% of items out of stock
    expedited_shipping_cost: float = 50_000.0  # Monthly rush shipping


@dataclass
class ScenarioInputs:
    """Business user's "what-if" assumptions."""
    inventory_allocation_pct: float = 1.0  # 1.0 = no change, 1.2 = 20% more
    promotion_discount_pct: float = 0.0  # 0.0 = no discount, 0.15 = 15% off
    delivery_time_multiplier: float = 1.0  # 1.0 = normal, 1.5 = 50% slower
    marketing_spend_multiplier: float = 1.0  # 1.0 = baseline, 2.0 = 2x spend


class DecisionSimulator:
    """
    Simulates the impact of business decisions on KPIs.
    
    In production, this would read from your Gold layer (dbt marts)
    and use your ML models (delivery risk, demand forecast) to make
    more accurate projections.
    """
    
    def __init__(self, baseline: BaselineMetrics = None):
        self.baseline = baseline or BaselineMetrics()
    
    def simulate(self, scenario: ScenarioInputs) -> dict[str, float]:
        """
        Run the simulation and return projected KPIs.
        
        This is a simplified heuristic model. In production, you'd
        use your trained ML models here for more accurate predictions.
        """
        b = self.baseline
        
        # 1. Revenue Impact
        # More inventory → fewer stockouts → more sales
        stockout_reduction = (scenario.inventory_allocation_pct - 1.0) * 0.5
        new_stockout_rate = max(0, b.stockout_rate - stockout_reduction)
        
        # Promotion discount → lower price per order, but more volume
        # Price elasticity: -1.5 (10% discount → 15% more orders)
        price_elasticity = -1.5
        volume_multiplier = 1 + (-scenario.promotion_discount_pct * price_elasticity)
        marketing_boost = scenario.marketing_spend_multiplier ** 0.3  # Diminishing returns
        
        new_orders = int(b.total_orders * (1 - new_stockout_rate) * volume_multiplier * marketing_boost)
        new_avg_order_value = b.avg_order_value * (1 - scenario.promotion_discount_pct)
        new_revenue = new_orders * new_avg_order_value
        
        # 2. Delay Impact
        # Slower delivery → more delays
        # More inventory → fewer delays (items available to ship immediately)
        inventory_delay_reduction = (scenario.inventory_allocation_pct - 1.0) * 0.3
        delivery_delay_increase = (scenario.delivery_time_multiplier - 1.0) * 0.4
        
        new_delay_rate = max(0, min(1, 
            b.delay_rate - inventory_delay_reduction + delivery_delay_increase
        ))
        new_avg_delivery_days = b.avg_delivery_days * scenario.delivery_time_multiplier
        
        # 3. Cost Impact
        # More inventory → lower expedited shipping (fewer rush orders)
        new_expedited_cost = b.expedited_shipping_cost * (1 - (scenario.inventory_allocation_pct - 1.0) * 0.6)
        new_expedited_cost = max(0, new_expedited_cost)
        
        # Promotion cost (marketing spend)
        promotion_cost = b.total_revenue * scenario.promotion_discount_pct * 0.3  # 30% of discount is "cost"
        
        # 4. Calculate Total Cost Function
        delay_penalty_per_order = 25.0  # $25 penalty per delayed order (customer service, refunds)
        stockout_cost_per_order = 40.0  # $40 cost per stockout (lost customer, reputation)
        
        total_cost = (
            new_expedited_cost +
            promotion_cost +
            (new_orders * new_delay_rate * delay_penalty_per_order) +
            (new_orders * new_stockout_rate * stockout_cost_per_order)
        )
        
        # 5. Calculate Net Profit (simplified)
        gross_margin = 0.35  # 35% gross margin
        gross_profit = new_revenue * gross_margin
        net_profit = gross_profit - total_cost
        
        return {
            # Revenue KPIs
            "projected_orders": new_orders,
            "projected_revenue": new_revenue,
            "projected_avg_order_value": new_avg_order_value,
            "revenue_change_pct": ((new_revenue - b.total_revenue) / b.total_revenue) * 100,
            
            # Service KPIs
            "projected_delay_rate": new_delay_rate,
            "projected_avg_delivery_days": new_avg_delivery_days,
            "projected_stockout_rate": new_stockout_rate,
            "delay_rate_change_pct": ((new_delay_rate - b.delay_rate) / b.delay_rate) * 100,
            
            # Cost KPIs
            "projected_expedited_cost": new_expedited_cost,
            "projected_total_cost": total_cost,
            "projected_net_profit": net_profit,
            "profit_change_pct": ((net_profit - (b.total_revenue * gross_margin - b.expedited_shipping_cost)) 
                                  / (b.total_revenue * gross_margin - b.expedited_shipping_cost)) * 100,
        }
    
    def compare_scenarios(self, scenarios: dict[str, ScenarioInputs]) -> pd.DataFrame:
        """Compare multiple scenarios side-by-side."""
        results = {}
        for name, scenario in scenarios.items():
            results[name] = self.simulate(scenario)
        
        df = pd.DataFrame(results).T
        df.index.name = "Scenario"
        return df
