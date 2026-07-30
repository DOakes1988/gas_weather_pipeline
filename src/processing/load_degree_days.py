import re
import psycopg
import os
import logging
from dotenv import load_dotenv
from psycopg.errors import OperationalError
from psycopg import sql
from decimal import Decimal
from pathlib import Path
from datetime import datetime, timedelta
from utils.state_populations import STATE_POPULATIONS
from utils.file_tracker import FileTracker

logging.basicConfig(
    filename='degree_days_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

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

    return (weighted_sum / total_population).quantize(Decimal(".01"))

""" Uses psycopg to connect and load the data into a PostgreSQL database """
def load_data(pair_list):
    # exit on empty list
    if not pair_list: return

    # get connection parameters from .env
    load_dotenv()

    host_ = str(os.getenv('DB_HOST'))
    db_name_ = str(os.getenv('DB_NAME'))
    user_ = str(os.getenv('USER_NAME'))
    password_ = str(os.getenv('DB_PASSWORD'))
    port_ = str(os.getenv('DB_PORT'))

    try:
        with psycopg.connect(
            host=host_,
            port=port_,
            dbname=db_name_,
            user=user_,
            password=password_,
            connect_timeout=5
        ) as conn:
                with conn.cursor() as cur:
                    # create a temp staging table for fast copying
                    cur.execute("""
                        CREATE TEMPORARY TABLE staging_temp (
                            date DATE,
                            degree_days NUMERIC(6, 2),
                            degree_day_region INTEGER
                        ) ON COMMIT DROP;
                    """)

                    copy_query = sql.SQL("COPY {} (date, degree_days, degree_day_region) FROM STDIN").format(
                        sql.Identifier("staging_temp")
                    )

                    # copy data into temp staging table
                    with cur.copy(copy_query) as copy:
                        for row in pair_list:
                            copy.write_row(row)

                    # merge data into gas price table with upserts
                    cur.execute("""
                        INSERT INTO fact_degree_days (date, degree_days, degree_day_region)
                        SELECT date, degree_days, degree_day_region FROM staging_temp
                        ON CONFLICT ON CONSTRAINT fact_degree_days_pkey
                        DO UPDATE SET degree_days = EXCLUDED.degree_days
                        WHERE fact_degree_days.degree_days IS DISTINCT FROM EXCLUDED.degree_days;
                    """)

    except OperationalError:
    # Handles connection drops, bad credentials, timeout issues
        logger.error("Database connection failure!", exc_info=True)

    except psycopg.Error as e:
    # Catches any other generic PostgreSQL/Psycopg API errors
        logger.error(f"Database error occurred: {e} | SQLSTATE: {e.sqlstate}", exc_info=True)

    except Exception:
        # Catch-all for non-database exceptions (e.g., NameError, KeyError)
        logger.critical("Unexpected non-database error", exc_info=True)

def parse_degree_days(target_file):
    #file_path_ = Path("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/degree_days/" + target_file)

    target_states = {
        "CONNECTICUT", "DELAWARE", "DISTRCT COLUMBIA",
        "FLORIDA", "GEORGIA", "MAINE", "MARYLAND", "MASSACHUSETTS",
        "NEW HAMPSHIRE", "NEW JERSEY", "NEW YORK",
        "NORTH CAROLINA", "OHIO", "PENNSYLVANIA", "RHODE ISLAND",
        "SOUTH CAROLINA", "VERMONT", "VIRGINIA", "WEST VIRGINIA"
    }

    temp_lines = []
    line_list = []

    for line in target_file:
        temp_lines.append(line.replace('\x0c', '').rstrip())

    date_count = 0
    for line in temp_lines:
        if line.strip()[:9] == "LAST DATE":
            break
        date_count += 1


    # File Date: remove double spaces if present
    original_date = re.sub(r" {2,}", " ", temp_lines[date_count][-12:].strip())

    # Convert to type date
    correct_date = datetime.strptime(original_date, "%b %d, %Y").date() - timedelta(days=1)

    start_count = 0
    for line in temp_lines:
        if line.strip()[:7] == "ALABAMA":
            break
        start_count += 1

    # End parsing at end of state data
    end_count = 0
    for line in temp_lines:
        if line.strip() == "REGION":
            break
        end_count += 1

    # Extract state and storage value from text file
    for i in range(start_count, end_count):
        state = temp_lines[i][:18].strip()
        storage = temp_lines[i][18:23].strip()

        if state in target_states:
            line_list.append((str(state), Decimal(storage)))

    weighted_average = calc_weighted_average(line_list)

    return correct_date, weighted_average, 1


tracker = FileTracker("degree_days_opened_files.log")
folder_path = Path("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/degree_days/")

degree_day_list = []

# parse all files in directory
for file_path in folder_path.iterdir():
    # make sure it's a file
    if file_path.is_file():
        file_object = tracker.open_file(file_path)
        # file hasn't been processed before
        if file_object:
            try:
                pairs = parse_degree_days(file_object)
                degree_day_list.append(pairs)
            except Exception as e:
                logger.error(f"Skipping malformed file {file_path}: {e}", exc_info=True)
                continue
            finally:
                file_object.close()

seen_dates = {}

# remove duplicate files
for row in degree_day_list:
    date_, value, region = row
    seen_dates[date_] = row

degree_day_list = list(seen_dates.values())

# filter out any files that produced no usable data
degree_day_list = [row for row in degree_day_list if row[1] is not None]

load_data(degree_day_list)