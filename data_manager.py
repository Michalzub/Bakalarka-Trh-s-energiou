from datetime import datetime

import pandas as pd
import data_access_module as da

OKTE_FLOW_COLS = ["flowSkCz", "flowCzSk", "flowSkPl", "flowPlSk", "flowSkPlc", "flowPlcSk", "flowSkHu", "flowHuSk",
             "flowHuRo", "flowRoHu"]
OKTE_ATC_COLS = ["atcSkCz", "atcCzSk", "atcSkPl", "atcPlSk", "atcSkPlc", "atcPlcSk", "atcSkHu", "atcHuSk", "atcHuRo",
            "atcRoHu"]
OKTE_OTHER_COLS = ['saleUnsuccessfulVolume',"publicationStatus", "purchaseUnsuccessfulVolume",
    "SaleTotalVolume",
    "priceRo", "priceHu", "priceCz"]
OKTE_IDM_COLS = ['purchaseSuccessfulVolume','purchaseTotalVolume', 'saleTotalVolume', 'saleSuccessfulVolume','successfulVolumeDifference', 'priceAverage', 'simpleOrdersSuccessfulVolume',
       'simpleOrdersPriceWeightedAverage',
       'lastPrice']

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

def add_ba_timestamp(df: pd.DataFrame):
    df['deliveryStartBA'] = df['deliveryStart']
    df['deliveryEndBA'] = df['deliveryEnd']
    change_timezone(df, ['deliveryStartBA', 'deliveryEndBA'], timezone="Europe/Bratislava")
    df['deliveryDayBA'] = df['deliveryStartBA'].dt.date

def add_ba_time_features(df: pd.DataFrame):
    df['quarterHourBA'] = df['deliveryStartBA'].dt.minute // 15
    df['hourBA'] = df['deliveryStartBA'].dt.hour

def prep_okte_data(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    cols = OKTE_FLOW_COLS + OKTE_ATC_COLS + OKTE_OTHER_COLS + OKTE_IDM_COLS
    temp = temp.drop(columns=cols, errors="ignore")
    convert_to_datetime(temp, ['deliveryStart', 'deliveryEnd'])
    add_ba_timestamp(temp)
    add_ba_time_features(temp)
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
        df_dam[['deliveryStartBA', 'price']],
        df_idm[['deliveryStartBA', 'priceWeightedAverage']],
        on='deliveryStartBA',
        how='inner'
    ).rename(columns={'price': 'DAM_price', 'priceWeightedAverage': 'IDM_price'})

    return temp

def aggregate_hourly(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    hourly = (
        df
        .set_index('deliveryStartBA')
        .resample('1h')[value_col]
        .mean()
        .reset_index()
    )
    return hourly

def concat_dam_idm(df_dam: pd.DataFrame, df_idm: pd.DataFrame) -> pd.DataFrame:
    temp_idm = df_idm.copy()

    temp_idm = temp_idm.rename(columns={"priceWeightedAverage": "price"})

    combined = pd.concat([df_dam, temp_idm], ignore_index=True)
    combined.drop(columns=["successfulVolume", "minimalPrice", "maximalPrice"], inplace=True)
    return combined

