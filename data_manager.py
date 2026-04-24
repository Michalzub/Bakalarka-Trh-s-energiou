from datetime import datetime

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
    df['weekday'] = df['deliveryStart'].dt.dayofweek
    df['quarterHour'] = df['deliveryStart'].dt.minute // 15
    df['hour'] = df['deliveryStart'].dt.hour

def prep_okte_data(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    if temp['market'].iloc[0] == "DAM":
        temp = temp.loc[:,MAIN_DAM_COLS]
    else:
        temp = temp.loc[:,MAIN_IDM_COLS]
    convert_to_datetime(temp, ['deliveryStart', 'deliveryEnd']) #TEORETICKY DUPLIKATNE VOLANIE ALE NECHAM PRE ISTOTU
    change_timezone(temp,['deliveryStart', 'deliveryEnd'], timezone="Europe/Bratislava")
    add_time_features(temp)
    return temp

def prep_entsoe_data(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp.rename(columns={
        "Solar": "solar",
        "Wind Onshore": "windOnshore",
        "Wind Offshore": "windOffshore"
    }, inplace=True)
    temp['windTotal'] = temp['windOnshore'] + temp['windOffshore']
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


def concat_dam_idm(df_dam: pd.DataFrame, df_idm: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([df_dam, df_idm], ignore_index=True)
    combined.drop(columns=['purchaseSuccessfulVolume','saleSuccessfulVolume',"successfulVolume"], inplace=True)
    return combined

