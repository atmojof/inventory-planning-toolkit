import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.styles import apply_custom_css, kpi_card
from utils.demand_engine import calculate_eoq

# Page Config
st.set_page_config(page_title="Cost Optimizer (EOQ) - Inventory Planning", page_icon="💰", layout="wide")
apply_custom_css()

# Retrieve sales data from session state
if 'sales_df' not in st.session_state:
    st.markdown("### ⚠️ Please load the homepage first to initialize data.")
    st.stop()
    
sales_df = st.session_state['sales_df']
daily_sales_series = sales_df["Sales"]
currency_symbol = st.session_state.get("currency_symbol", "Rp")

# Extrapolate annual demand D from historical daily sales
num_days = len(sales_df)
total_sales_history = daily_sales_series.sum()
annual_demand = total_sales_history * (365.25 / num_days)

st.markdown('<div class="gradient-header">Economic Order Quantity (EOQ) Cost Optimizer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Logistics management seeks to minimize total annual cost by balancing order setup costs (placing orders) and holding costs (storing inventory). Calculate the mathematically optimal order quantity.</div>',
    unsafe_allow_html=True
)

# Sidebar configurations
st.sidebar.markdown("### 💸 Cost Parameters")

if currency_symbol == "Rp":
    def_price = 10000.0
    def_setup = 200000.0
    step_price = 1000.0
    step_setup = 10000.0
else:
    def_price = 10.0
    def_setup = 20.0
    step_price = 1.0
    step_setup = 1.0

unit_price = st.sidebar.number_input(
    f"Unit Purchase Price ({currency_symbol})",
    min_value=0.1,
    value=def_price,
    step=step_price,
    help="Purchase cost of a single inventory item."
)

holding_rate = st.sidebar.slider(
    "Annual Holding Cost Rate (%)",
    5, 100, 20,
    step=5,
    help="Yearly carrying cost expressed as a percentage of the unit price (covers warehouse space, insurance, capital costs)."
)

order_cost = st.sidebar.number_input(
    f"Order Setup Cost ({currency_symbol}/Order)",
    min_value=1.0,
    value=def_setup,
    step=step_setup,
    help="Cost to place, process, and receive a single replenishment shipment."
)

# Calculated annual holding cost H per unit
holding_cost_unit_year = unit_price * (holding_rate / 100.0)

# Calculate optimal EOQ values
eoq_res = calculate_eoq(
    annual_demand=annual_demand,
    order_cost=order_cost,
    holding_cost_per_unit_year=holding_cost_unit_year
)

# Display KPI Row
col1, col2, col3, col4 = st.columns(4)

# Format currency helper
def format_curr(value, symbol):
    if symbol == "Rp":
        return f"Rp {value:,.0f}"
    return f"${value:,.2f}"

with col1:
    kpi_card(
        "Optimal Order Quantity (EOQ)",
        f"{eoq_res['eoq']:,.0f} Units",
        f"Annual Demand: {annual_demand:,.0f} units",
        "neutral"
    )

with col2:
    kpi_card(
        "Orders per Year",
        f"{eoq_res['orders_per_year']:.1f} Orders",
        f"Order every {eoq_res['order_interval_days']:.1f} days",
        "neutral"
    )

with col3:
    kpi_card(
        "Min Total Annual Cost",
        format_curr(eoq_res['total_logistics_cost'], currency_symbol),
        f"Hold: {format_curr(eoq_res['annual_holding_cost'], currency_symbol)} | Setup: {format_curr(eoq_res['annual_ordering_cost'], currency_symbol)}",
        "neutral"
    )

with col4:
    # Savings calculation compared to a custom user policy
    q_current = st.session_state.get("order_quantity", 350.0)
    
    # Calculate current costs
    curr_orders_yr = annual_demand / q_current
    curr_setup_cost = curr_orders_yr * order_cost
    curr_hold_cost = (q_current / 2.0) * holding_cost_unit_year
    curr_total_cost = curr_setup_cost + curr_hold_cost
    
    savings = curr_total_cost - eoq_res['total_logistics_cost']
    trend_savings = "positive" if savings > 0 else "neutral"
    
    kpi_card(
        "Potential Annual Savings",
        format_curr(max(0, savings), currency_symbol),
        f"Compared to ordering {q_current:,.0f} units",
        trend_savings
    )

# Main Grid Layout
col_left, col_right = st.columns([6, 4])

with col_left:
    st.markdown('<div class="gradient-subheader">Logistics Total Cost Curves</div>', unsafe_allow_html=True)
    st.write("Visualizing annual logistics costs across a range of replenishment order sizes. The minimum of the Total Cost curve marks the EOQ point:")
    
    # Generate data series for the cost curves
    q_vals = np.linspace(max(10.0, eoq_res["eoq"] * 0.2), eoq_res["eoq"] * 2.2, 100)
    ordering_costs = (annual_demand / q_vals) * order_cost
    holding_costs = (q_vals / 2.0) * holding_cost_unit_year
    total_costs = ordering_costs + holding_costs
    
    fig = go.Figure()
    
    # Ordering Cost (descending)
    fig.add_trace(go.Scatter(
        x=q_vals, y=ordering_costs, name="Annual Ordering Cost", mode="lines",
        line=dict(color="#f43f5e", width=2, dash="dash"),
        hovertemplate="Order Qty: %{x:,.0f}<br>Ordering Cost: " + currency_symbol + " %{y:,.0f}<extra></extra>"
    ))
    
    # Holding Cost (ascending)
    fig.add_trace(go.Scatter(
        x=q_vals, y=holding_costs, name="Annual Holding Cost", mode="lines",
        line=dict(color="#22d3ee", width=2, dash="dash"),
        hovertemplate="Order Qty: %{x:,.0f}<br>Holding Cost: " + currency_symbol + " %{y:,.0f}<extra></extra>"
    ))
    
    # Total Cost (U-curve)
    fig.add_trace(go.Scatter(
        x=q_vals, y=total_costs, name="Total Annual Cost", mode="lines",
        line=dict(color="#14b8a6", width=4),
        hovertemplate="Order Qty: %{x:,.0f}<br>Total Cost: " + currency_symbol + " %{y:,.0f}<extra></extra>"
    ))
    
    # Mark the EOQ optimal point
    fig.add_trace(go.Scatter(
        x=[eoq_res["eoq"]],
        y=[eoq_res["total_logistics_cost"]],
        name="Optimal EOQ Point",
        mode="markers",
        marker=dict(color="#fbbf24", size=14, symbol="star", line=dict(color="#ffffff", width=2)),
        hovertemplate="<b>Optimal EOQ</b><br>Order Size: %{x:,.0f} units<br>Min Cost: " + currency_symbol + " %{y:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Order Quantity (Units)", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#a0aec0")),
        yaxis=dict(title=f"Annual Cost ({currency_symbol})", gridcolor="rgba(255,255,255,0.05)", tickformat=",d", tickfont=dict(color="#a0aec0")),
        legend=dict(orientation="h", y=-0.15, bgcolor="rgba(13,33,36,0.8)", bordercolor="rgba(255,255,255,0.05)", borderwidth=1),
        margin=dict(l=40, r=40, t=20, b=40),
        height=450
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown('<div class="gradient-subheader">Policy Comparison Metrics</div>', unsafe_allow_html=True)
    st.write(f"Compare your current operational configuration against the Economic Order Quantity (EOQ) model:")
    
    # Prepare comparison dataframe
    comp_data = {
        "Cost Element": [
            "Order Size (Units)",
            "Orders per Year",
            "Order Frequency (Days)",
            "Annual Ordering Costs",
            "Annual Holding Costs",
            "Total Logistics Cost"
        ],
        "Current Policy": [
            f"{q_current:,.0f}",
            f"{curr_orders_yr:.1f}",
            f"{365.25 / curr_orders_yr:.1f} days",
            format_curr(curr_setup_cost, currency_symbol),
            format_curr(curr_hold_cost, currency_symbol),
            format_curr(curr_total_cost, currency_symbol)
        ],
        "Optimal EOQ Policy": [
            f"{eoq_res['eoq']:,.0f}",
            f"{eoq_res['orders_per_year']:.1f}",
            f"{eoq_res['order_interval_days']:.1f} days",
            format_curr(eoq_res['annual_ordering_cost'], currency_symbol),
            format_curr(eoq_res['annual_holding_cost'], currency_symbol),
            format_curr(eoq_res['total_logistics_cost'], currency_symbol)
        ]
    }
    
    df_comp = pd.DataFrame(comp_data)
    st.table(df_comp.set_index("Cost Element"))
    
    # Analysis summary block
    st.markdown('<div class="premium-container">', unsafe_allow_html=True)
    st.write("#### 🛡️ Supply Chain Insights")
    st.markdown(f"""
    * **Cost Tradeoffs:** Ordering in very small quantities decreases carrying holding costs, but raises setup shipping frequencies, increasing setup overheads. 
    * **Minimum Point:** At the exact optimal EOQ order quantity, the **Annual Ordering Cost** matches the **Annual Holding Cost** exactly.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
