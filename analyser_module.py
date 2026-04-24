import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def calculate_corr(df: pd.DataFrame, col1: str, df2: pd.DataFrame, col2: str):
    s1 = df[col1]
    s2 = df2[col2]

    if len(s1) != len(s2):
        raise ValueError("Columns must have the same length")

    return s1.corr(s2)

def price_summary_statistics(data):

    prices = data['price'].dropna()

    mean_val = prices.mean()
    std_val = prices.std()

    stats = {
        "count": len(prices),
        "Mean": mean_val,
        "Median": prices.median(),
        "Max": prices.max(),
        "Min": prices.min(),
        "Range": prices.max() - prices.min(),
        "Std": std_val,
        "Coef_of_Var": std_val / mean_val,
        "Skewness": skew(prices),
        "Kurtosis": kurtosis(prices, fisher=False),
    }

    return stats

def calculate_quantiles(data, column:str):
    prices = data[column].dropna()
    quantiles = {
        "95 quantile": prices.quantile(0.95),
        "75 quantile": prices.quantile(0.75),
        "25 quantile": prices.quantile(0.25),
        "05 quantile": prices.quantile(0.05),
    }
    return quantiles

def calculate_price_diff(data):
    data['price_diff'] = data['price'].diff()
    df = data.dropna(subset=['price_diff'])
    return df

def price_diff_summary_statistics(data):
    r = data['price_diff'].dropna()
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


def weekday_statistics(df: pd.DataFrame, value_col: str) -> pd.DataFrame:

    df = df.groupby('weekday')[value_col]
    return df

def calculate_intermarket_spread(df: pd.DataFrame):
    required_cols = {"DAM_price", "IDM_price"}

    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols}")

    temp = df.copy()
    temp['dam_idm_spread'] = df['DAM_price'] - df['IDM_price']
    return temp



def calculate_battery_dp(df, max_soc_units=2, unit_size=0.5, efficiency=0.90, distribution_cost=0.00):
    df = df.reset_index(drop=True).copy()
    prices = df['price']
    periods = len(df['price'])

    dp = np.full((periods + 1, max_soc_units + 1), -np.inf)
    parent = np.full((periods + 1, max_soc_units + 1), -1, dtype=int)

    dp[0][0] = 0

    for t in range(periods):
        for s in range(max_soc_units + 1):
            if dp[t][s] == -np.inf:
                continue

            # IDLE
            if dp[t][s] > dp[t + 1][s]:
                dp[t + 1][s] = dp[t][s]
                parent[t + 1][s] = s

            # CHARGE
            if s < max_soc_units:
                cost = (prices[t] + distribution_cost) * unit_size
                if dp[t][s] - cost > dp[t + 1][s + 1]:
                    dp[t + 1][s + 1] = dp[t][s] - cost
                    parent[t + 1][s + 1] = s

            # DISCHARGE
            if s > 0:
                revenue = (prices[t] - distribution_cost) * unit_size * efficiency
                if dp[t][s] + revenue > dp[t + 1][s - 1]:
                    dp[t + 1][s - 1] = dp[t][s] + revenue
                    parent[t + 1][s - 1] = s

    soc_path = []
    current_soc = 0
    for t in range(periods, 0, -1):
        soc_path.append(current_soc)
        current_soc = parent[t][current_soc]
    soc_path.append(current_soc)
    soc_path.reverse()

    action_points = []
    for t, (curr, nxt) in enumerate(zip(soc_path[:-1], soc_path[1:])):
        if nxt > curr:
            action_points.append((t, prices[t], "charge"))
        elif nxt < curr:
            action_points.append((t, prices[t], "discharge"))

    return {
        "df": df,
        "dp": dp,
        "parent": parent,
        "soc_path": soc_path,
        "action_points": action_points,
        "profit": dp[periods][0],
        "unit_size": unit_size,
        "max_soc_units": max_soc_units,
    }