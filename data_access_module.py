import pandas as pd
import requests, calendar
from pathlib import Path
import time
from datetime import datetime, date

from data_processor import convert_to_datetime

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

def cache_path(source:str, year:int, month:int, unique_identifier: str = ""):
    if unique_identifier != "":
        return Path("cache") / source / unique_identifier / str(year) / f"{unique_identifier}-{year}-{month:02d}.parquet"
    else:
        return Path("cache") / source / f"{year}-{month:02d}.parquet"


def months_between(start_date: datetime, end_date: datetime):
    months= []

    year = start_date.year
    month = start_date.month

    while(year, month) <= (end_date.year, end_date.month):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1

    return months

def check_valid_date_range(start_date: datetime, end_date: datetime):
    if start_date > end_date:
        raise ValueError("startDate must be before endDate")

    if (end_date - start_date).days > 365:
        raise ValueError("Date range cannot be longer than one year")

def build_okte_url(market_type:str, start_date: datetime, end_date: datetime):
    last_day = calendar.monthrange(end_date.year, end_date.month)[1]

    start = f"{start_date.year}-{start_date.month:02d}-{start_date.day:02d}"
    end = f"{end_date.year}-{end_date.month:02d}-{last_day:02d}"
    return MARKET_URLS[market_type].format(start=start, end=end)

def get_okte_data_simple(market_type: str, start_date: datetime, end_date: datetime):

    check_valid_date_range(start_date, end_date)

    if market_type not in MARKET_URLS:
        raise ValueError("marketType doesnt exist")


    months = months_between(start_date, end_date)

    frames = []

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    for month in months:
        is_current_month = (month.year == current_year and month.month == current_month)
        dp = cache_path("OKTE", month.year, month.month, market_type)
        if not dp.is_file() or is_current_month:
            url = build_okte_url(market_type, month, month)
            json_data = fetch_data(url)
            df = pd.DataFrame(json_data)
            save_data(df, dp)
        else:
            df = load_data(dp)

        df['market'] = market_type
        frames.append(df)

    final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if not final.empty:
        convert_to_datetime(final, ["deliveryStart"])
        start_date = pd.Timestamp(start_date).tz_localize("Europe/Bratislava")
        end_date = pd.Timestamp(end_date).replace(hour=23, minute=45, second=00).tz_localize("Europe/Bratislava")
        final = final[
            (final["deliveryStart"] >= start_date) &
            (final["deliveryStart"] <= end_date)
            ]
        final = final.rename(columns={"priceWeightedAverage": "price"})
        return final
    else:
        raise ValueError("No data found")


def save_data(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

def load_data(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)