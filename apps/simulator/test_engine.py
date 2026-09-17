"""Quick test of the simulation engine."""
import sys
sys.path.insert(0, "apps/simulator")

from engine import DecisionSimulator, ScenarioInputs, BaselineMetrics

sim = DecisionSimulator()

# Scenario 1: Baseline (no changes)
baseline_result = sim.simulate(ScenarioInputs())
print("📊 BASELINE:")
print(f"   Revenue: ${baseline_result['projected_revenue']:,.0f}")
print(f"   Delay Rate: {baseline_result['projected_delay_rate']:.1%}")
print(f"   Net Profit: ${baseline_result['projected_net_profit']:,.0f}")

# Scenario 2: Aggressive promotion + more inventory
aggressive = ScenarioInputs(
    inventory_allocation_pct=1.3,  # 30% more inventory
    promotion_discount_pct=0.15,   # 15% discount
    marketing_spend_multiplier=1.5,
)
aggressive_result = sim.simulate(aggressive)
print("\n🚀 AGGRESSIVE SCENARIO:")
print(f"   Revenue: ${aggressive_result['projected_revenue']:,.0f} ({aggressive_result['revenue_change_pct']:+.1f}%)")
print(f"   Delay Rate: {aggressive_result['projected_delay_rate']:.1%} ({aggressive_result['delay_rate_change_pct']:+.1f}%)")
print(f"   Net Profit: ${aggressive_result['projected_net_profit']:,.0f} ({aggressive_result['profit_change_pct']:+.1f}%)")

# Scenario 3: Supply chain disruption (slower delivery)
disruption = ScenarioInputs(
    delivery_time_multiplier=1.5,  # 50% slower
)
disruption_result = sim.simulate(disruption)
print("\n⚠️  DISRUPTION SCENARIO:")
print(f"   Revenue: ${disruption_result['projected_revenue']:,.0f} ({disruption_result['revenue_change_pct']:+.1f}%)")
print(f"   Delay Rate: {disruption_result['projected_delay_rate']:.1%} ({disruption_result['delay_rate_change_pct']:+.1f}%)")
print(f"   Net Profit: ${disruption_result['projected_net_profit']:,.0f} ({disruption_result['profit_change_pct']:+.1f}%)")
