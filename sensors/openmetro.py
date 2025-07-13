import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime


def get_openmetro_readings(start_date, end_date):

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 45.5657,
        "longitude": -122.6184,
        "hourly": ["temperature_2m", "relative_humidity_2m"],
        "start_date": start_date.split("T")[0],
        "end_date": end_date.split("T")[0],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location.
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    result = []
    for index, row in hourly_dataframe.iterrows():
        result.append(
            {
                "timestamp": datetime.fromisoformat(row["date"].isoformat()).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "historicalTemperature": (
                    float(row["temperature_2m"])
                    if pd.notna(row["temperature_2m"])
                    else None
                ),
                "historicalHumidity": (
                    float(row["relative_humidity_2m"])
                    if pd.notna(row["relative_humidity_2m"])
                    else None
                ),
            }
        )

    return result
