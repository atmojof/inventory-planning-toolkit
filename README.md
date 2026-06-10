# Project 20: Inventory Demand Planning Toolkit

A Streamlit-based web application that simulates inventory demand, calculates optimal Reorder Points (ROP) and Safety Stock, and visualizes the sawtooth inventory curve using synthetic logic.

## Features
- **Demand Forecaster**: Simulates daily demand with seasonality and noise, calculating lead time demand and optimal reorder points.
- **Cost Optimizer**: Calculates Economic Order Quantity (EOQ) and visualizes the total logistics cost curve to minimize holding and ordering costs.
- **Sawtooth Simulation**: Interactive Plotly charting showing the continuous depletion and replenishment cycle of inventory.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit dashboard locally:
```bash
streamlit run streamlit_app.py
```
