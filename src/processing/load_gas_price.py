import psycopg
import json
import os
import logging
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from psycopg.errors import UniqueViolation, OperationalError
from psycopg import sql
from pathlib import Path
from utils.file_tracker import FileTracker

logging.basicConfig(
    filename='gas_price_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

""" Parses raw data and transforms into list of tuples (date, decimal) """
def parse_gas_price(target_file):
    # loads json file and returns a Python Object
    data = json.load(target_file)
    pair_list = []

    # loop through raw data and only extract the date and price(value)
    for item in data:
        # don't include blank/None values
        if not item["period"] or not item["value"]:
            continue

        pair_list.append((datetime.strptime(item["period"], "%Y-%m-%d").date(), Decimal(item["value"]), 2))

    return pair_list

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
                            gas_price NUMERIC,
                            price_region INTEGER
                        ) ON COMMIT DROP;
                    """)

                    copy_query = sql.SQL("COPY {} (date, gas_price, price_region) FROM STDIN").format(
                        sql.Identifier("staging_temp")
                    )

                    # copy data into temp staging table
                    with cur.copy(copy_query) as copy:
                        for row in pair_list:
                            copy.write_row(row)

                    # merge data into gas price table with upserts
                    cur.execute("""
                        INSERT INTO fact_gas_price (date, gas_price, price_region)
                        SELECT date, gas_price, price_region FROM staging_temp
                        ON CONFLICT ON CONSTRAINT fact_gas_price_pkey
                        DO UPDATE SET gas_price = EXCLUDED.gas_price
                        WHERE fact_gas_price.gas_price IS DISTINCT FROM EXCLUDED.gas_price;
                    """)

                    # template for a single row placeholder
                    """row_template = sql.SQL("({}, {}, {})").format(sql.Placeholder(), sql.Placeholder(), sql.Placeholder())

                    # join templates by commas
                    values_block = sql.SQL(", ").join(row_template for _ in pair_list)

                    # SQL query
                    query = sql.SQL("""
                        #INSERT INTO fact_gas_price (date, gas_price, price_region)
                        #VALUES {values}
                        #ON CONFLICT ON CONSTRAINT fact_gas_price_pkey
                        #DO UPDATE SET gas_price = EXCLUDED.gas_price
                        #WHERE fact_gas_price.gas_price IS DISTINCT FROM EXCLUDED.gas_price;
                    """).format(values=values_block)

                    flat_args = [val for pair in pair_list for val in pair]

                    cur.execute(query, flat_args)
                    """
    except OperationalError:
    # Handles connection drops, bad credentials, timeout issues
        logger.error("Database connection failure!", exc_info=True)

    except psycopg.Error as e:
    # Catches any other generic PostgreSQL/Psycopg API errors
        logger.error(f"Database error occurred: {e} | SQLSTATE: {e.sqlstate}", exc_info=True)

    except Exception:
        # Catch-all for non-database exceptions (e.g., NameError, KeyError)
        logger.critical("Unexpected non-database error", exc_info=True)


tracker = FileTracker("gas_price_opened_files.log")

folder_path = Path("D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/gas_price/")

# parse all files in directory
for file_path in folder_path.iterdir():
    # make sure it's a file
    if file_path.is_file():
        file_object = tracker.open_file(file_path)
        # file hasn't been processed before
        if file_object:
            try:
                pairs = parse_gas_price(file_object)
                load_data(pairs)
            except Exception as e:
                logger.error(f"Failed processing {file_path}", exc_info=True)
            finally:
                file_object.close()