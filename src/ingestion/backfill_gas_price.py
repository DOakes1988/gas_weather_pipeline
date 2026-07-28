import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

today_date = datetime.now()

# make sure directory exists
os.makedirs("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_price", exist_ok=True)

# file name with update name logic
file_name = "D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_price/gas_price_backfill_1997-01-07_to_" + today_date.strftime("%Y-%m-%d") + ".txt"

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
    "start": "1997-01-07",
    "end": today_date.strftime("%Y-%m-%d"),
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "offset": 0,
    "length": 5000
}

all_records = []
offset = 0
limit = 5000

try:
    while True:
        params["offset"] = offset
        response = requests.get(endpoint_url, params=params)
        response.raise_for_status()

        raw_data = response.json()
        data = raw_data["response"]["data"]

        if not data:
            break

        all_records.extend(data)
        offset += limit

    pretty_data = json.dumps(all_records, indent=4)

    with open(file_name, "w") as f:
        f.write(pretty_data)

except requests.exceptions.HTTPError as err:
    print(f"Http Error: {err}")
except Exception as e:
    print(f"an error occurred: {e}")