import pandas as pd
import requests, json, calendar
from pathlib import Path
import time
from datetime import datetime, date

from entsoe import EntsoePandasClient

from data_manager import convert_to_datetime

MARKET_URLS = {
    "DAM": "https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom={start}&deliveryDayTo={end}",
    "IDM60": "https://isot.okte.sk/api/v1/idm/results?deliveryDayFrom={start}&deliveryDayTo={end}&productType=60",
    "IDM15": "https://isot.okte.sk/api/v1/idm/results?deliveryDayFrom={start}&deliveryDayTo={end}&productType=15",
}

def fetch_data(url: str, retries: int = 3, timeout: int = 20):
    for attempt in range(1,retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except requests.Timeout as e:
            if attempt == retries:
                raise TimeoutError("Request timed out") from e

        except requests.ConnectionError as e:
            if attempt == retries:
                raise ConnectionError("Connection failed") from e

        except requests.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            raise RuntimeError(f"HTTP error: {status}") from e

        except ValueError as e:
            raise ValueError("Response was not valid JSON") from e

        except requests.RequestException as e:
            raise RuntimeError("Unexpected request error") from e

        if attempt < retries:
            time.sleep(attempt)

    raise RuntimeError("Failed to fetch data after retries")

def cache_path(source:str, year, month, unique_identifier: str = ""):
    if unique_identifier != "":
        return Path("cache") / source / unique_identifier / str(year) / f"{unique_identifier}-{year}-{month:02d}.parquet"
    else:
        return Path("cache") / source / f"{year}-{month:02d}.parquet"


def months_between(startDate: datetime, endDate: datetime):
    months= []

    year = startDate.year
    month = startDate.month

    while(year, month) <= (endDate.year, endDate.month):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1

    return months

def check_valid_date_range(startDate: datetime, endDate: datetime):
    if startDate > endDate:
        raise ValueError("startDate must be before endDate")

    if (endDate - startDate).days > 365:
        raise ValueError("Date range cannot be longer than one year")

def build_okte_url(marketType, startDate: datetime, endDate: datetime):
    last_day = calendar.monthrange(endDate.year, endDate.month)[1]

    start = f"{startDate.year}-{startDate.month:02d}-{startDate.day:02d}"
    end = f"{endDate.year}-{endDate.month:02d}-{last_day:02d}"
    return MARKET_URLS[marketType].format(start=start, end=end)

def get_okte_data_simple(marketType: str, startDate: datetime, endDate: datetime):

    check_valid_date_range(startDate, endDate)

    if marketType not in MARKET_URLS:
        raise ValueError("marketType doesnt exist")

    months = months_between(startDate, endDate)

    frames = []

    for month in months:
        dp = cache_path("OKTE", month.year, month.month, marketType)
        if not dp.is_file():
            url = build_okte_url(marketType, month, month)
            json_data = fetch_data(url)
            df = pd.DataFrame(json_data)
            save_data(df, dp)
        else:
            df = load_data(dp)

        df['market'] = marketType
        frames.append(df)

    final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if not final.empty:
        convert_to_datetime(final, ["deliveryStart"])
        startDate = pd.Timestamp(startDate, tz="UTC")
        endDate = pd.Timestamp(endDate, tz="UTC")
        final = final[
            (final["deliveryStart"] >= startDate) &
            (final["deliveryStart"] <= endDate)
            ]

    return final

def get_entsoe_data(startDate: datetime, endDate: datetime, country_code: str, apiKey: str):
    check_valid_date_range(startDate, endDate)

    client = EntsoePandasClient(api_key=apiKey)
    country_code = country_code.upper()

    months = months_between(startDate, endDate)
    frames = []
    for month in months:
        dp = cache_path("ENTSOE", month.year, month.month, country_code)
        if not dp.is_file():
            start = pd.Timestamp(month, tz='UTC')
            end = pd.Timestamp(month + pd.offsets.MonthEnd(0), tz='UTC')
            temp = client.query_wind_and_solar_forecast(country_code, start=start, end=end)
            df = pd.DataFrame(temp)
            df = df.reset_index(names="date")
            save_data(df, dp)
        else:
            df = load_data(dp)

        frames.append(df)

    final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    final['Wind_Total'] = final['Wind Onshore'] + final['Wind Offshore']

    return final


def save_data(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

def load_data(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)































    # def get_okte_data(marketType: str, startDate: datetime, endDate: datetime):
    #     if startDate > endDate:
    #         raise ValueError("startDate must be before endDate")
    #
    #     if marketType not in MARKET_URLS.keys():
    #         raise ValueError("marketType doesnt exist")
    #
    #     url_template = MARKET_URLS[marketType]
    #
    #     months = months_between(startDate, endDate)
    #     rangess = required_ranges(marketType, months)
    #
    #     data = pd.DataFrame()
    #
    #     for ranges in rangess:
    #         startDay = ranges[0]
    #         endDay = ranges[-1]
    #
    #         last_day = calendar.monthrange(endDay.year, endDay.month)[1]
    #
    #         start = f"{startDay.year}-{startDay.month:02d}-{startDay.day:02d}"
    #         end = f"{endDay.year}-{endDay.month:02d}-{last_day:02d}"
    #         url = url_template.format(start=start, end=end)
    #         json_data = fetch_data(url)
    #         df = pd.DataFrame(json_data)
    #         data = pd.concat([data, df], ignore_index=True)
    #         dm.convert_to_datetime(data, ['deliveryStart', 'deliveryEnd','deliveryDay'])
    #
    #     for _, df_month in data.groupby(pd.Grouper(key="deliveryStart", freq="MS")):
    #         save_data(df_month)

    # def required_ranges(marketType: str, months: list[date]):
    #     ranges = []
    #     temp = []
    #     for month in months:
    #         if not data_path(marketType,month.year, month.month).is_file():
    #             temp.append(month)
    #         elif len(temp) > 0:
    #             ranges.append(temp)
    #             temp = []
    #
    #     if len(temp) > 0:
    #         ranges.append(temp)
    #     return ranges