import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_sales_data(days: int = 180):
    """Generates synthetic daily sales data with trend, seasonality, and random noise.
    
    Includes reproducible random seed.
    """
    np.random.seed(42)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    
    # Base trend (slowly increasing)
    base_sales = np.linspace(40.0, 55.0, days)
    
    # Weekly seasonality (higher sales on Fri, Sat, Sun)
    weekly_season = []
    for d in date_range:
        day_of_week = d.weekday()  # 0=Mon, ..., 6=Sun
        if day_of_week in [4, 5]:  # Fri, Sat
            weekly_season.append(15.0)
        elif day_of_week == 6:  # Sun
            weekly_season.append(10.0)
        else:
            weekly_season.append(0.0)
            
    weekly_season = np.array(weekly_season)
    
    # Random noise (standard deviation = 8)
    noise = np.random.normal(0, 8, days)
    
    # Generate daily sales
    sales = base_sales + weekly_season + noise
    
    # Insert a few promotional spike events (double sales)
    promo_indices = np.random.choice(days, 5, replace=False)
    for idx in promo_indices:
        sales[idx] += np.random.uniform(30.0, 50.0)
        
    # Cast to integers and ensure no negative values
    sales = np.clip(sales, 0, None)
    sales = np.round(sales).astype(int)
    
    df = pd.DataFrame({
        "Date": date_range,
        "Sales": sales
    })
    
    return df

def calculate_rop_and_safety_stock(daily_sales_series: pd.Series, lead_time_days: float, service_level_pct: float):
    """Calculates average demand, standard deviation, safety stock, and Reorder Point (ROP)."""
    avg_demand = daily_sales_series.mean()
    std_demand = daily_sales_series.std()
    
    # Hurdle service level Z-score mapping fallback
    z_map = {90: 1.282, 95: 1.645, 99: 2.326}
    
    try:
        from scipy.stats import norm
        z = norm.ppf(service_level_pct / 100.0)
    except Exception:
        # Fallback mapping if scipy import fails
        z = z_map.get(int(service_level_pct), 1.645)
        
    # Safety Stock formula: Z * std_d * sqrt(LeadTime)
    safety_stock = z * std_demand * np.sqrt(lead_time_days)
    
    # Reorder Point formula: (avg_d * LeadTime) + Safety Stock
    reorder_point = (avg_demand * lead_time_days) + safety_stock
    
    return {
        "avg_demand": avg_demand,
        "std_demand": std_demand,
        "z_score": z,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point
    }

def calculate_eoq(annual_demand: float, order_cost: float, holding_cost_per_unit_year: float):
    """Calculates Economic Order Quantity (EOQ) and associated logistics cost items."""
    if holding_cost_per_unit_year <= 0:
        return {
            "eoq": annual_demand,
            "orders_per_year": 1.0,
            "order_interval_days": 365.25,
            "annual_ordering_cost": order_cost,
            "annual_holding_cost": 0.0,
            "total_logistics_cost": order_cost,
            "feasible": False
        }
        
    # EOQ Formula = sqrt((2 * D * S) / H)
    eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit_year)
    orders_per_year = annual_demand / eoq
    order_interval = 365.25 / orders_per_year
    
    ann_ordering = orders_per_year * order_cost
    ann_holding = (eoq / 2.0) * holding_cost_per_unit_year
    total_cost = ann_ordering + ann_holding
    
    return {
        "eoq": eoq,
        "orders_per_year": orders_per_year,
        "order_interval_days": order_interval,
        "annual_ordering_cost": ann_ordering,
        "annual_holding_cost": ann_holding,
        "total_logistics_cost": total_cost,
        "feasible": True
    }

def simulate_sawtooth_inventory(
    initial_stock: float,
    daily_sales: list,
    dates: list,
    rop: float,
    order_qty: float,
    lead_time_days: int
):
    """Simulates inventory levels day-by-day to create a visual sawtooth pattern.
    
    Triggers reorders when stock <= ROP, arriving after lead time.
    """
    inventory_level = initial_stock
    inventory_history = []
    
    order_placed = False
    days_until_arrival = 0
    
    for idx, sale in enumerate(daily_sales):
        date_item = dates[idx]
        
        # Deduct sales at start of day
        inventory_before = inventory_level
        inventory_level -= sale
        
        # Check stockouts
        stockout = False
        if inventory_level <= 0:
            inventory_level = 0
            stockout = True
            
        reorder_placed_today = False
        reorder_arrived_today = False
        
        # Check reorder trigger
        if inventory_level <= rop and not order_placed:
            order_placed = True
            days_until_arrival = lead_time_days
            reorder_placed_today = True
            
        # Check arrival trigger
        if order_placed:
            days_until_arrival -= 1
            if days_until_arrival == 0:
                inventory_level += order_qty
                order_placed = False
                reorder_arrived_today = True
                
        inventory_history.append({
            "Day": idx + 1,
            "Date": date_item,
            "Sales": sale,
            "Stock Before": inventory_before,
            "Stock After": inventory_level,
            "Reorder Placed": reorder_placed_today,
            "Reorder Arrived": reorder_arrived_today,
            "Stockout": stockout
        })
        
    return pd.DataFrame(inventory_history)

def forecast_demand(daily_sales_series: pd.Series, forecast_days: int = 30, method: str = "exponential_smoothing", param: float = 7.0):
    """Generates demand forecasts using moving averages or single exponential smoothing.
    
    Evaluates forecast accuracy on an 80/20 train/test split.
    """
    n = len(daily_sales_series)
    split_idx = int(n * 0.8)
    
    train = daily_sales_series.iloc[:split_idx].values
    test = daily_sales_series.iloc[split_idx:].values
    
    # Perform forecast based on method
    if method == "moving_average":
        window = int(param)
        # Train fit (rolling mean)
        fitted = pd.Series(train).rolling(window=window).mean().fillna(train.mean()).values
        # Predict on test (flat average of last train window)
        last_window_val = train[-window:].mean()
        predictions = np.full(len(test), last_window_val)
        # Out-of-sample forecast
        future_forecast = np.full(forecast_days, last_window_val)
    else:
        # Exponential Smoothing
        alpha = param  # e.g., 0.15
        fitted = np.zeros(len(train))
        fitted[0] = train[0]
        for t in range(1, len(train)):
            fitted[t] = alpha * train[t] + (1.0 - alpha) * fitted[t - 1]
            
        last_smoothed = fitted[-1]
        predictions = np.full(len(test), last_smoothed)
        future_forecast = np.full(forecast_days, last_smoothed)
        
    # Evaluate accuracy on test set
    mae = np.mean(np.abs(test - predictions))
    rmse = np.sqrt(np.mean((test - predictions) ** 2))
    
    # Create complete series for plotting
    historical_fitted = np.concatenate([fitted, predictions])
    
    return {
        "fitted_values": historical_fitted,
        "forecast": future_forecast,
        "mae": mae,
        "rmse": rmse
    }
