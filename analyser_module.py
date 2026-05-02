import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis


def calculate_corr(df: pd.DataFrame, col1: str, df2: pd.DataFrame, col2: str):
    s1 = df[col1]
    s2 = df2[col2]

    if len(s1) != len(s2):
        raise ValueError("Columns must have the same length")

    return s1.corr(s2)

def price_summary_statistics(df: pd.DataFrame):

    prices = df['price'].dropna()

    mean_val = prices.mean()
    std_val = prices.std()

    stats = {
        "Počet": len(prices),
        "Priemer": mean_val,
        "Medián": prices.median(),
        "Maximum": prices.max(),
        "Minimum": prices.min(),
        "Rozsah": prices.max() - prices.min(),
        "Štandardná odchýlka": std_val,
        "Koeficient variability": std_val / mean_val,
        "Šikmosť": skew(prices),
        "Špicatosť": kurtosis(prices, fisher=False),
    }

    return stats

def calculate_quantiles(data, column:str):
    prices = data[column].dropna()
    quantiles = {
        "0.95 kvantil": prices.quantile(0.95),
        "0.75 kvantil": prices.quantile(0.75),
        "0.25 kvantil": prices.quantile(0.25),
        "0.05 kvantil": prices.quantile(0.05),
    }
    return quantiles


def price_diff_summary_statistics(df: pd.DataFrame):
    r = df['price_diff'].dropna()
    return {
        "mean price diff": r.mean(),
        "std price diff": r.std(),
        "mean abs price diff": np.abs(r).mean(),
        "Max abs price diff": np.abs(r).max(),
        "q99 abs price diff": np.quantile(np.abs(r), 0.99),
        "q95 abs price diff": np.quantile(np.abs(r), 0.95),
        "Skewness price diff": skew(r),
        "Kurtosis price diff": kurtosis(r, fisher=False),

    }

def avg_daily_max_spread_by_weekday(df: pd.DataFrame):
    df = df.copy()

    daily_spread = (
        df.groupby('deliveryDay')['price']
        .agg(lambda x: x.max() - x.min())
        .rename('spread')
    )

    weekday_map = (
        df.drop_duplicates('deliveryDay')
        .set_index('deliveryDay')['weekday']
    )

    daily_spread = daily_spread.to_frame().join(weekday_map)

    result = (
        daily_spread.groupby('weekday')['spread']
        .mean()
        .sort_index()
    )

    return result

def calculate_battery_arbitrage(
        df: pd.DataFrame,
        max_soc_units:int = 2,
        power:float = 0.5,
        efficiency:float = 0.90,
        distribution_cost:float = 50.00,
        mtu:int = 60

):
    df = df.reset_index(drop=True).copy()
    prices = df['price']
    periods = len(df['price'])

    unit_size = power * 0.25 if mtu == 15 else power

    profits = np.full((periods + 1, max_soc_units + 1), -np.inf)
    parent = np.full((periods + 1, max_soc_units + 1), -1, dtype=int)

    profits[0][0] = 0

    for t in range(periods):
        for s in range(max_soc_units + 1):
            if profits[t][s] == -np.inf:
                continue

            if np.isnan(prices[t]):
                profits[t + 1][s] = profits[t][s]
                parent[t + 1][s] = s
                continue

            # IDLE
            if profits[t][s] > profits[t + 1][s]:
                profits[t + 1][s] = profits[t][s]
                parent[t + 1][s] = s

            # CHARGE
            if s < max_soc_units:
                cost = (prices[t] + distribution_cost) * unit_size
                if profits[t][s] - cost > profits[t + 1][s + 1]:
                    profits[t + 1][s + 1] = profits[t][s] - cost
                    parent[t + 1][s + 1] = s

            # DISCHARGE
            if s > 0:
                revenue = prices[t] * unit_size * efficiency
                if profits[t][s] + revenue > profits[t + 1][s - 1]:
                    profits[t + 1][s - 1] = profits[t][s] + revenue
                    parent[t + 1][s - 1] = s

    soc_path = []
    current_soc = 0
    for t in range(periods, 0, -1):
        soc_path.append(current_soc)
        current_soc = parent[t][current_soc]
    soc_path.append(current_soc)
    soc_path.reverse()

    action_points = []
    for t in range(periods):
        curr = soc_path[t]
        nxt = soc_path[t + 1]
        if nxt > curr:
            action_points.append((t, prices[t], "charge"))
        elif nxt < curr:
            action_points.append((t, prices[t], "discharge"))

    return {
        "df": df,
        "soc_path": soc_path,
        "action_points": action_points,
        "profit": profits[periods][0],
        "unit_size": unit_size,
        "max_soc_units": max_soc_units,
    }

def calculate_time_summary(df: pd.DataFrame, quarter:bool, column:str):
    group_cols = ['hour', 'quarterHour'] if quarter else ['hour']
    summary = (
        df
        .groupby(group_cols)[column]
        .agg(
            mean='mean',
            median='median',
            std='std',
            min='min',
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
            max='max'
        )
        .reset_index()
    )

    return summary