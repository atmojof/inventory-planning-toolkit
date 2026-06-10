import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.styles import apply_custom_css, kpi_card
from utils.demand_engine import forecast_demand

# Page Config
st.set_page_config(page_title="Demand Forecaster - Inventory Planning", page_icon="📈", layout="wide")
apply_custom_css()

# Retrieve sales data from session state
if 'sales_df' not in st.session_state:
    st.markdown("### ⚠️ Please load the homepage first to initialize data.")
    st.stop()
    
sales_df = st.session_state['sales_df']
daily_sales_series = sales_df["Sales"]

st.markdown('<div class="gradient-header">Demand Forecaster & Analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Predict future sales demand using time-series forecasting. Split historical data 80/20 into training and testing datasets to evaluate model accuracy.</div>',
    unsafe_allow_html=True
)

# Sidebar configurations
st.sidebar.markdown("### 📈 Forecaster Parameters")

method = st.sidebar.selectbox(
    "Forecasting Method",
    ["Exponential Smoothing", "Moving Average"],
    index=0,
    help="Choose between Exponential Smoothing (weighted weights) or Moving Average (flat average window)."
)

if method == "Moving Average":
    param_val = st.sidebar.slider("Window Size (Days)", 3, 30, 7, step=1, help="Number of rolling days to average.")
    engine_method = "moving_average"
else:
    param_val = st.sidebar.slider("Smoothing Factor (Alpha)", 0.05, 0.95, 0.15, step=0.05, help="Weight given to recent demand (higher = more reactive).")
    engine_method = "exponential_smoothing"

forecast_days = st.sidebar.number_input(
    "Forecast Horizon (Days)",
    min_value=7,
    max_value=90,
    value=30,
    step=1,
    help="Number of days to forecast into the future."
)

# Run forecasting engine
res = forecast_demand(
    daily_sales_series=daily_sales_series,
    forecast_days=forecast_days,
    method=engine_method,
    param=param_val
)

# Display KPI metrics
col1, col2, col3 = st.columns(3)

with col1:
    kpi_card(
        "Mean Absolute Error (MAE)",
        f"{res['mae']:.2f} Units",
        "Average forecast error magnitude",
        "neutral"
    )

with col2:
    kpi_card(
        "Root Mean Squared Error (RMSE)",
        f"{res['rmse']:.2f} Units",
        "Penalizes larger forecast errors",
        "neutral"
    )

with col3:
    future_avg = res["forecast"][0]
    kpi_card(
        "Projected Daily Demand",
        f"{future_avg:.1f} Units",
        f"Flat forecast over next {forecast_days} days",
        "neutral"
    )

# Visualizing Forecast Chart
st.markdown('<div class="gradient-subheader">Demand Forecasting Visualizer</div>', unsafe_allow_html=True)

# Construct dates for future forecast
last_date = sales_df["Date"].iloc[-1]
future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]

# Plotting
fig = go.Figure()

# Actual historical sales
fig.add_trace(go.Scatter(
    x=sales_df["Date"],
    y=sales_df["Sales"],
    name="Actual Sales",
    mode="lines",
    line=dict(color="#1f2937", width=1.5),
    opacity=0.4,
    hovertemplate="Date: %{x}<br>Actual Sales: %{y:d}<extra></extra>"
))

# Fitted values (historical model predictions)
fig.add_trace(go.Scatter(
    x=sales_df["Date"],
    y=res["fitted_values"],
    name="Model Fit / Backtest",
    mode="lines",
    line=dict(color="#14b8a6", width=2.5),
    hovertemplate="Date: %{x}<br>Fitted Sales: %{y:,.1f}<extra></extra>"
))

# Out of sample forecast
fig.add_trace(go.Scatter(
    x=future_dates,
    y=res["forecast"],
    name="Projected Forecast",
    mode="lines",
    line=dict(color="#fbbf24", width=3, dash="dash"),
    hovertemplate="Date: %{x}<br>Forecast: %{y:,.1f}<extra></extra>"
))

# Draw separator line between history and forecast
fig.add_shape(
    type="line",
    x0=last_date, y0=0,
    x1=last_date, y1=max(sales_df["Sales"].max(), res["forecast"].max()) * 1.05,
    line=dict(color="#718096", width=1.5, dash="dot")
)

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#a0aec0")),
    yaxis=dict(title="Sales Units", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#a0aec0")),
    legend=dict(orientation="h", y=-0.15, bgcolor="rgba(13,33,36,0.8)", bordercolor="rgba(255,255,255,0.05)", borderwidth=1),
    margin=dict(l=40, r=40, t=20, b=40),
    height=480
)

st.plotly_chart(fig, use_container_width=True)

# Explanations
st.markdown("---")
st.markdown("### 💡 Understanding Forecast Accuracy")
col_e1, col_e2 = st.columns(2)

with col_e1:
    st.markdown("""
    **1. MAE vs. RMSE**
    * **Mean Absolute Error (MAE):** Tells you the average absolute distance between actual sales and predictions. An MAE of 10 means your forecasts are off by 10 units on average.
    * **Root Mean Squared Error (RMSE):** Penalizes larger outlier errors more heavily. If your RMSE is much higher than your MAE, it means the model is making occasional very large errors (e.g., during promotional spikes).
    """)

with col_e2:
    st.markdown("""
    **2. Model Parameters Selection**
    * In **Exponential Smoothing**, a high $\\alpha$ (e.g., 0.8) gives heavy weight to yesterday's sales, making the model highly reactive to sudden shifts. A low $\\alpha$ (e.g., 0.1) creates a smooth forecast that ignores random spikes.
    * In **Moving Average**, longer windows (e.g. 21 days) smooth out weekly cycles but lag behind actual trend shifts.
    """)
