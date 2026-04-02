import pandas as pd
from scipy.stats import skew, kurtosis

from dataclasses import dataclass

@dataclass
class Quantiles:
    q95: float
    q99: float
    q05: float

def calculate_corr(df: pd.DataFrame, col1: str, df2: pd.DataFrame, col2: str):
    s1 = df[col1]
    s2 = df2[col2]

    if len(s1) != len(s2):
        raise ValueError("Columns must have the same length")

    return s1.corr(s2)

def summary_statistics(df: pd.DataFrame, col1: str):
    s1 = df[col1].dropna()

    mean_val = s1.mean()
    std_val = s1.std()

    stats = {
        "Mean": mean_val,
        "Max": s1.max(),
        "Min": s1.min(),
        "Std": std_val,
        "Coef_of_Var": std_val / mean_val,
        "Skewness": skew(s1),
        "Kurtosis": kurtosis(s1),
    }

    return stats

def calculate_quantiles(df: pd.DataFrame, col: str) -> Quantiles:
    s1 = df[col].dropna()
    qs = Quantiles(
        s1.quantile(0.95),
        s1.quantile(0.99),
        s1.quantile(0.05)
        )

    return qs

def calculate_intermarket_spread(df: pd.DataFrame):
    required_cols = {"DAM_price", "IDM_price"}

    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols}")

    temp = df.copy()
    temp['dam_idm_spread'] = df['DAM_price'] - df['IDM_price']
    return temp

def calculate_intramarket_spread(df: pd.DataFrame):
    return