import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# current time for file naming
period_end = datetime.now()
period_start = period_end - timedelta(days=21)

# make sure directory exists
os.makedirs("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_price", exist_ok=True)

# file name with update name logic
file_name = "D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_price/gas_price_" + period_start.strftime("%Y-%m-%d") + "_to_" + period_end.strftime("%Y-%m-%d") + ".txt"

# load .env
load_dotenv()

# api key stored in .env
api_key = str(os.getenv('API_KEY'))

# base url
endpoint_url = "https://api.eia.gov/v2/natural-gas/pri/fut/data/"

params = {
    "api_key": api_key,
    "frequency": "daily",
    "data[0]": "value",
    "facets[series][]": "RNGWHHD",
    "start": period_start.strftime("%Y-%m-%d"),
    "end": period_end.strftime("%Y-%m-%d"),
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "offset": 0,
    "length": 21
}

try:
    response = requests.get(endpoint_url, params=params)
    response.raise_for_status()

    raw_data = response.json()
    data = raw_data["response"]["data"]

    pretty_data = json.dumps(data, indent=4)

    with open(file_name, "w") as f:
        f.write(pretty_data)

except requests.exceptions.HTTPError as err:
    print(f"Http Error: {err}")
except Exception as e:
    print(f"an error occurred: {e}")