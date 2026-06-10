import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.styles import apply_custom_css, kpi_card
from utils.demand_engine import generate_mock_sales_data, calculate_rop_and_safety_stock, simulate_sawtooth_inventory

# Page Config
st.set_page_config(
    page_title="Inventory Demand Planning Toolkit",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS Styling
apply_custom_css()

# App Header
st.markdown('<div class="gradient-header">Inventory Demand Planning Toolkit</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">A supply chain analytics workspace to compute safety stocks, define reorder points (ROP), calculate Economic Order Quantity (EOQ), and simulate daily inventory sawtooth replenishment cycles.</div>',
    unsafe_allow_html=True
)

# Generate mock sales data (180 days)
if 'sales_df' not in st.session_state:
    st.session_state['sales_df'] = generate_mock_sales_data(days=180)

sales_df = st.session_state['sales_df']
daily_sales_series = sales_df["Sales"]

# Sidebar parameters
st.sidebar.markdown("### ⚙️ Inventory Parameters")

lead_time = st.sidebar.number_input(
    "Lead Time (Days)",
    min_value=1.0,
    max_value=30.0,
    value=5.0,
    step=1.0,
    help="Days between placing a purchase order and receiving stock."
)

service_level = st.sidebar.selectbox(
    "Target Service Level (%)",
    [90.0, 95.0, 99.0],
    index=1,
    help="Desired probability of not stocking out during a lead time period."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 Operational Inputs")

init_stock = st.sidebar.number_input(
    "Starting Stock Level (Units)",
    min_value=0.0,
    value=450.0,
    step=10.0,
    help="Initial inventory in the warehouse at Day 1."
)

order_quantity = st.sidebar.number_input(
    "Order Quantity (Q)",
    min_value=10.0,
    value=350.0,
    step=10.0,
    help="Replenishment order size placed when inventory hits ROP."
)

# Calculate ROP and Safety Stock based on historical sales
rop_results = calculate_rop_and_safety_stock(
    daily_sales_series=daily_sales_series,
    lead_time_days=lead_time,
    service_level_pct=service_level
)

avg_demand = rop_results["avg_demand"]
std_demand = rop_results["std_demand"]
safety_stock = rop_results["safety_stock"]
reorder_point = rop_results["reorder_point"]

# Run daily inventory simulation for the last 90 days of sales
simulation_days = 90
sim_sales = daily_sales_series.tail(simulation_days).values
sim_dates = sales_df["Date"].tail(simulation_days).values

sim_df = simulate_sawtooth_inventory(
    initial_stock=init_stock,
    daily_sales=sim_sales,
    dates=sim_dates,
    rop=reorder_point,
    order_qty=order_quantity,
    lead_time_days=int(lead_time)
)

# Stock status tag determination
current_stock = sim_df["Stock After"].iloc[-1]
if current_stock <= reorder_point:
    status_str = "⚠️ REORDER TRIGGERED"
    status_trend = "negative"
elif current_stock <= safety_stock:
    status_str = "❌ LOW STOCK / SAFETY"
    status_trend = "negative"
else:
    status_str = "✓ OPTIMAL STOCK"
    status_trend = "positive"

# Display KPI Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card(
        "Average Daily Demand",
        f"{avg_demand:.1f} Units",
        f"Demand Std Dev: {std_demand:.1f} units",
        "neutral"
    )

with col2:
    kpi_card(
        "Safety Stock Requirement",
        f"{safety_stock:,.0f} Units",
        f"Service Level: {service_level:.0f}% (Z: {rop_results['z_score']:.3f})",
        "neutral"
    )

with col3:
    kpi_card(
        "Reorder Point (ROP)",
        f"{reorder_point:,.0f} Units",
        f"Daily lead demand: {avg_demand * lead_time:.1f} units",
        "neutral"
    )

with col4:
    kpi_card(
        "Ending Stock Status",
        f"{current_stock:,.0f} Units",
        status_str,
        status_trend
    )

# Main Grid Layout
col_left, col_right = st.columns([7, 3])

with col_left:
    st.markdown('<div class="gradient-subheader">Inventory Level saw-tooth Simulation</div>', unsafe_allow_html=True)
    st.write("Daily stock levels tracked over a 90-day simulation. Reorder orders are placed when stock hits ROP, arriving after the lead time:")
    
    # Plotly Sawtooth Chart
    fig = go.Figure()
    
    # Stock After
    fig.add_trace(go.Scatter(
        x=sim_df["Date"],
        y=sim_df["Stock After"],
        name="Inventory Level",
        mode="lines",
        line=dict(color="#14b8a6", width=3),
        hovertemplate="Date: %{x}<br>Stock Level: %{y:,.0f}<extra></extra>"
    ))
    
    # ROP line
    fig.add_trace(go.Scatter(
        x=sim_df["Date"],
        y=np.full(len(sim_df), reorder_point),
        name="Reorder Point (ROP)",
        mode="lines",
        line=dict(color="#fbbf24", width=2, dash="dash"),
        hovertemplate="ROP: " + f"{reorder_point:,.0f}<extra></extra>"
    ))
    
    # Safety Stock line
    fig.add_trace(go.Scatter(
        x=sim_df["Date"],
        y=np.full(len(sim_df), safety_stock),
        name="Safety Stock",
        mode="lines",
        line=dict(color="#f43f5e", width=2, dash="dot"),
        hovertemplate="Safety Stock: " + f"{safety_stock:,.0f}<extra></extra>"
    ))
    
    # Reorders Placed
    placed_df = sim_df[sim_df["Reorder Placed"] == True]
    if not placed_df.empty:
        fig.add_trace(go.Scatter(
            x=placed_df["Date"],
            y=placed_df["Stock After"],
            name="Order Placed",
            mode="markers",
            marker=dict(color="#fbbf24", size=12, symbol="triangle-down"),
            hovertemplate="<b>Reorder Placed</b><br>Date: %{x}<br>Stock: %{y:,.0f}<extra></extra>"
        ))
        
    # Reorders Arrived
    arrived_df = sim_df[sim_df["Reorder Arrived"] == True]
    if not arrived_df.empty:
        fig.add_trace(go.Scatter(
            x=arrived_df["Date"],
            y=arrived_df["Stock After"],
            name="Order Arrived (Q)",
            mode="markers",
            marker=dict(color="#22d3ee", size=12, symbol="triangle-up"),
            hovertemplate="<b>Order Arrived</b><br>Date: %{x}<br>Stock: %{y:,.0f}<extra></extra>"
        ))
        
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#a0aec0")),
        yaxis=dict(title="Stock Units", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#a0aec0")),
        legend=dict(orientation="h", y=-0.15, bgcolor="rgba(13,33,36,0.8)", bordercolor="rgba(255,255,255,0.05)", borderwidth=1),
        margin=dict(l=40, r=40, t=20, b=40),
        height=480
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown('<div class="gradient-subheader">Simulation Summary</div>', unsafe_allow_html=True)
    
    # Statistics calculations
    total_orders = int(sim_df["Reorder Placed"].sum())
    stockout_days = int(sim_df["Stockout"].sum())
    max_stock = int(sim_df["Stock After"].max())
    avg_stock = int(sim_df["Stock After"].mean())
    
    with st.container():
        st.markdown('<div class="premium-container">', unsafe_allow_html=True)
        st.write("#### 📈 Key Operations Metrics")
        
        st.metric("Orders Placed (Q)", f"{total_orders} Orders")
        st.metric("Stockout Days", f"{stockout_days} Days", delta=f"{stockout_days} stockout events" if stockout_days > 0 else "No stockouts", delta_color="inverse")
        st.metric("Average Stock Level", f"{avg_stock:,.0f} Units")
        st.metric("Max Stock Peak", f"{max_stock:,.0f} Units")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    with st.container():
        st.markdown('<div class="premium-container">', unsafe_allow_html=True)
        st.write("#### 📐 Operations Formulas")
        st.markdown("""
        * **Safety Stock ($SS$):**
          $$SS = Z \\times \\sigma_d \\times \\sqrt{L}$$
          *Where $Z$ is service level multiplier, $\\sigma_d$ is demand variance, and $L$ is lead time.*
        * **Reorder Point ($ROP$):**
          $$ROP = (d \\times L) + SS$$
          *Where $d$ is average daily demand.*
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Navigation guidelines
st.markdown("---")
st.markdown("### 🔍 Dashboard Navigation")
col_n1, col_n2 = st.columns(2)

with col_n1:
    st.markdown("""
    **📈 [Demand Forecaster](Demand_Forecaster)**
    Explore the time-series forecasting engine. Run moving averages and exponential smoothing on historical transactions, view accuracy metrics (MAE, RMSE), and forecast future demand.
    """)

with col_n2:
    st.markdown("""
    **💰 [Logistics Cost Optimizer](Cost_Optimizer)**
    Configure ordering costs and annual unit holding rates. Plot economic order quantity (EOQ) curves to minimize logistics expenses and compare optimal policy against current practice.
    """)
