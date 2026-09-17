"""
NEXUS Decision Simulator — Interactive Web UI
Run with: uv run streamlit run apps/simulator/app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Add simulator to path
sys.path.insert(0, str(Path(__file__).parent))
from engine import DecisionSimulator, ScenarioInputs, BaselineMetrics

# Page config
st.set_page_config(
    page_title="NEXUS Decision Simulator",
    page_icon="🎯",
    layout="wide",
)

# Title
st.title("🎯 NEXUS Decision Simulator")
st.markdown("""
**What-if analysis for supply chain decisions.** 
Adjust the sliders below to see how different scenarios impact revenue, delay rates, and profitability.
""")

# Initialize simulator
sim = DecisionSimulator()

# --- Handle Preset Scenarios (Transient Trigger Pattern) ---
# This avoids the "WidgetAlreadyInstantiated" error by setting defaults 
# at the top of the script *before* the widgets are drawn.
preset = st.session_state.get("preset_scenario", "baseline")
if preset != "baseline":
    if preset == "aggressive":
        def_inv, def_promo, def_del, def_mkt = 1.3, 0.15, 1.0, 1.5
    elif preset == "disruption":
        def_inv, def_promo, def_del, def_mkt = 1.0, 0.0, 1.5, 1.0
    elif preset == "cost_opt":
        def_inv, def_promo, def_del, def_mkt = 1.2, 0.0, 1.0, 0.8
    else:
        def_inv, def_promo, def_del, def_mkt = 1.0, 0.0, 1.0, 1.0
    
    # Clear the preset so manual slider moves work normally on the next run
    del st.session_state.preset_scenario
else:
    def_inv, def_promo, def_del, def_mkt = 1.0, 0.0, 1.0, 1.0

# Sidebar: Scenario Inputs
st.sidebar.header("🎛️ Scenario Inputs")

inventory_allocation = st.sidebar.slider(
    "Inventory Allocation",
    min_value=0.5,
    max_value=2.0,
    value=def_inv,
    step=0.05,
    help="Multiplier on current inventory levels. 1.0 = no change, 1.2 = 20% more inventory.",
)

promotion_discount = st.sidebar.slider(
    "Promotion Discount",
    min_value=0.0,
    max_value=0.5,
    value=def_promo,
    step=0.01,
    format="%.0f%%",
    help="Percentage discount on all orders. 0.15 = 15% off.",
)

delivery_time = st.sidebar.slider(
    "Delivery Time Multiplier",
    min_value=0.5,
    max_value=2.0,
    value=def_del,
    step=0.05,
    help="Multiplier on delivery times. 1.5 = 50% slower (e.g., due to weather, disruptions).",
)

marketing_spend = st.sidebar.slider(
    "Marketing Spend",
    min_value=0.5,
    max_value=3.0,
    value=def_mkt,
    step=0.1,
    help="Multiplier on marketing budget. 2.0 = double the spend.",
)

# Run simulation
scenario = ScenarioInputs(
    inventory_allocation_pct=inventory_allocation,
    promotion_discount_pct=promotion_discount,
    delivery_time_multiplier=delivery_time,
    marketing_spend_multiplier=marketing_spend,
)

result = sim.simulate(scenario)
baseline = sim.baseline

# Main dashboard
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="📦 Projected Revenue",
        value=f"${result['projected_revenue']:,.0f}",
        delta=f"{result['revenue_change_pct']:+.1f}%",
    )

with col2:
    # A negative change in delay rate is GOOD, so we invert the sign for the delta display
    delay_improvement = -result['delay_rate_change_pct']
    st.metric(
        label="⏱️ Delay Rate",
        value=f"{result['projected_delay_rate']:.1%}",
        delta=f"{delay_improvement:+.1f}% improvement",
    )

with col3:
    st.metric(
        label="💰 Net Profit",
        value=f"${result['projected_net_profit']:,.0f}",
        delta=f"{result['profit_change_pct']:+.1f}%",
    )

# Detailed breakdown
st.markdown("---")
st.subheader("📊 Detailed KPI Breakdown")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### Revenue & Orders")
    df_revenue = pd.DataFrame({
        "Metric": ["Total Orders", "Avg Order Value", "Total Revenue"],
        "Baseline": [
            f"{baseline.total_orders:,}",
            f"${baseline.avg_order_value:.2f}",
            f"${baseline.total_revenue:,.0f}",
        ],
        "Projected": [
            f"{result['projected_orders']:,}",
            f"${result['projected_avg_order_value']:.2f}",
            f"${result['projected_revenue']:,.0f}",
        ],
    })
    st.dataframe(df_revenue, hide_index=True, width="stretch")

with col_right:
    st.markdown("#### Service & Cost")
    df_service = pd.DataFrame({
        "Metric": ["Delay Rate", "Avg Delivery Days", "Stockout Rate", "Total Cost"],
        "Baseline": [
            f"{baseline.delay_rate:.1%}",
            f"{baseline.avg_delivery_days:.1f} days",
            f"{baseline.stockout_rate:.1%}",
            f"${baseline.expedited_shipping_cost:,.0f}",
        ],
        "Projected": [
            f"{result['projected_delay_rate']:.1%}",
            f"{result['projected_avg_delivery_days']:.1f} days",
            f"{result['projected_stockout_rate']:.1%}",
            f"${result['projected_total_cost']:,.0f}",
        ],
    })
    st.dataframe(df_service, hide_index=True, width="stretch")

# Visualization: Revenue vs Delay Rate tradeoff
st.markdown("---")
st.subheader("📈 Revenue vs. Delay Rate Tradeoff")

scenarios_chart = []
for inv_mult in [0.8, 1.0, 1.2, 1.5]:
    for promo in [0.0, 0.1, 0.2]:
        scenario = ScenarioInputs(
            inventory_allocation_pct=inv_mult,
            promotion_discount_pct=promo,
        )
        res = sim.simulate(scenario)
        scenarios_chart.append({
            "Inventory": f"{inv_mult:.0%}",
            "Promotion": f"{promo:.0%}",
            "Revenue": res["projected_revenue"],
            "Delay Rate": res["projected_delay_rate"],
        })

df_chart = pd.DataFrame(scenarios_chart)

fig = px.scatter(
    df_chart,
    x="Delay Rate",
    y="Revenue",
    color="Inventory",
    symbol="Promotion",
    size="Revenue",
    size_max=30,
    title="Explore the tradeoff: more inventory reduces delays, promotions increase revenue",
    labels={"Delay Rate": "Delay Rate", "Revenue": "Projected Revenue ($)"},
)
fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
fig.update_layout(xaxis_tickformat='.1%', yaxis_tickformat='$,.0f')

st.plotly_chart(fig, width="stretch")

# Preset scenarios
st.markdown("---")
st.subheader("🎯 Preset Scenarios")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 Aggressive Growth", width="stretch"):
        st.session_state.preset_scenario = "aggressive"
        st.rerun()

with col2:
    if st.button("⚠️ Supply Chain Disruption", width="stretch"):
        st.session_state.preset_scenario = "disruption"
        st.rerun()

with col3:
    if st.button("💰 Cost Optimization", width="stretch"):
        st.session_state.preset_scenario = "cost_opt"
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
**Built with:** Streamlit, Plotly, Pure Python simulation engine  
**Data source:** NEXUS Gold Layer (dbt marts) + ML models (delivery risk, demand forecast)  
**Next steps:** Connect to real-time Feature Store for live KPI baselines
""")
