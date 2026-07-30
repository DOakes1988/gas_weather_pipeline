import re
from decimal import Decimal
from pathlib import Path
from datetime import datetime, timedelta
from utils.state_populations import STATE_POPULATIONS

def calc_weighted_average(l_list):
    weighted_sum = Decimal(0)
    total_population = 0

    for state_name, value in l_list:
        if state_name in STATE_POPULATIONS:
            population = STATE_POPULATIONS[state_name]
            weighted_sum += value * population
            total_population += population

    if total_population == 0:
        return None

    return weighted_sum / total_population

folder_path = Path("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/degree_days/jan 1, 2000.txt")

target_states = {
    "CONNECTICUT", "DELAWARE", "DISTRCT COLUMBIA",
    "FLORIDA", "GEORGIA", "MAINE", "MARYLAND", "MASSACHUSETTS",
    "NEW HAMPSHIRE", "NEW JERSEY", "NEW YORK",
    "NORTH CAROLINA", "OHIO", "PENNSYLVANIA", "RHODE ISLAND",
    "SOUTH CAROLINA", "VERMONT", "VIRGINIA", "WEST VIRGINIA"
}

temp_lines = []
line_list = []

with open(str(folder_path), "r") as f:
    for line in f:
        temp_lines.append(line.rstrip())

# File Date: remove double spaces if present
original_date = re.sub(r" {2,}", " ", temp_lines[5][-12:])

# Convert to type date
correct_date = datetime.strptime(original_date, "%b %d, %Y").date() - timedelta(days=1)


population_sum = sum(STATE_POPULATIONS.values())

# End parsing at end of state data
end_count = 0
for line in temp_lines:
    if line.strip() == "REGION":
        break
    end_count += 1

for i in range(15, end_count):
    state = temp_lines[i][:18].strip()
    storage = temp_lines[i][18:23].strip()

    if state in target_states:
        line_list.append((str(state), Decimal(storage)))

weighted_average = calc_weighted_average(line_list)

print(f"Weighted Average: {weighted_average}")

for j in range(len(line_list)):
   print(f"[{j}]: {line_list[j]}")

print(f"File Date: {correct_date}")