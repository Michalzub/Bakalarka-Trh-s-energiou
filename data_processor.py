import pandas as pd

MAIN_DAM_COLS = ['price','purchaseSuccessfulVolume','saleSuccessfulVolume','deliveryDay','period','deliveryStart','deliveryEnd','market']
MAIN_IDM_COLS = ['price','successfulVolume','deliveryDay','period','deliveryStart','deliveryEnd','market']

def convert_to_datetime(df: pd.DataFrame, columns: list[str]):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

def localize_datetime(df: pd.DataFrame, columns: list[str], timezone: str):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].dt.tz_localize(timezone)

def change_timezone(df: pd.DataFrame, columns: list[str], timezone: str):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].dt.tz_convert(timezone)


def add_time_features(df: pd.DataFrame):
    temp= df.copy()
    temp['weekday'] = temp['deliveryStart'].dt.dayofweek
    temp['quarterHour'] = temp['deliveryStart'].dt.minute // 15
    temp['hour'] = temp['deliveryStart'].dt.hour
    return temp

def prep_okte_data(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    if temp['market'].iloc[0] == "DAM":
        temp = temp.loc[:,MAIN_DAM_COLS]
    else:
        temp = temp.loc[:,MAIN_IDM_COLS]
    convert_to_datetime(temp, ['deliveryStart', 'deliveryEnd']) #TEORETICKY DUPLIKATNE VOLANIE ALE NECHAM PRE ISTOTU
    change_timezone(temp,['deliveryStart', 'deliveryEnd'], timezone="Europe/Bratislava")
    temp = add_time_features(temp)
    temp = calculate_price_diff(temp)
    return temp

def merge_dam_idm_prices(df_dam: pd.DataFrame, df_idm: pd.DataFrame) -> pd.DataFrame:
    temp = pd.merge(
        df_dam[['deliveryStart', 'price']].rename(columns={'price': 'DAM_price'}),
        df_idm[['deliveryStart', 'price']].rename(columns={'price': 'IDM_price'}),
        on='deliveryStart',
        how='inner'
    )
    return temp

def aggregate_hour(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    hourly = (
        df
        .set_index('deliveryStart')
        .resample('1h')[value_col]
        .mean()
        .reset_index()
    )
    return hourly

def replicate_hour_to_quarter(df: pd.DataFrame) -> pd.DataFrame:
    temp = df[['price', 'deliveryStart']].set_index('deliveryStart')
    temp = temp.resample('15min').ffill()
    temp = temp.reset_index()
    return temp

def calculate_price_diff(df: pd.DataFrame):
    temp = df.copy()
    temp['price_diff'] = temp['price'].diff()
    return temp

def calculate_intermarket_spread(df: pd.DataFrame):
    required_cols = {"DAM_price", "IDM_price"}

    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols}")

    temp = df.copy()
    temp['spread'] = df['DAM_price'] - df['IDM_price']
    return temp

def remove_nonstandard_days(df: pd.DataFrame) -> pd.DataFrame:
    max_periods = df.groupby("deliveryDay")["period"].max()
    normal_period_count = max_periods.mode().iloc[0]

    valid_days = max_periods[max_periods == normal_period_count].index

    return df[df["deliveryDay"].isin(valid_days)].copy()

def groupby_period_mean(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    temp = (
        df
        .groupby("period", as_index=False)[value_col]
        .mean()
        .sort_values("period")
        .reset_index(drop=True)
    )

    return temp

def groupby_weekday_mean(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    df = df.groupby('weekday')[value_col].mean()
    return df

def combine_datasets(df1, df2):
    combined_df = pd.concat([df1, df2])
    combined_df = combined_df.sort_index()
    return combined_df
