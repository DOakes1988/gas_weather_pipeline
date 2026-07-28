import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

today_date = datetime.now()

# make sure directory exists
os.makedirs("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_storage", exist_ok=True)

# file name with update name logic
file_name = "D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_storage/gas_storage_backfill_2010-01-01_to_" + today_date.strftime("%Y-%m-%d") + ".txt"

# load .env
load_dotenv()

# api key stored in .env
api_key = str(os.getenv('API_KEY'))

# base url
endpoint_url = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"

params = {
    "api_key": api_key,
    "frequency": "weekly",
    "data[0]": "value",
    "facets[series][]": "NW2_EPG0_SWO_R31_BCF",
    "start": "2010-01-01",
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