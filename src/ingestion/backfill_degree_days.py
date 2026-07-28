import os
import requests
import time
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(
    filename='logfile.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def html_parser(input_url):
    func_response = requests.get(input_url)
    if func_response.status_code == 200:
        print(f"{input_url} retrieved successfully!! \n")

        func_soup = BeautifulSoup(func_response.content, 'html.parser')
        func_links = func_soup.find_all("a")

        return func_links
    else:
        print(f"Failed to retrieve the webpage for {input_url}. Status code: {func_response.status_code}")
        return None

today = datetime.now().strftime("%Y-%m-%d")
file_name = 'D:/Data_analyst_ramp/gas_weather_pipeline/data/raw/degree_days/'

# make sure directory exists
os.makedirs(file_name, exist_ok=True)

url = 'https://ftp.cpc.ncep.noaa.gov/htdocs/products/analysis_monitoring/cdus/degree_days/archives/Heating%20degree%20Days/weekly%20states/'
links = html_parser(url)

if links:
    year = datetime.now().year
    year_links = []

    # clean year numbers for directory access
    for link in links:
        year_ = link.string
        for i in range(year - 1997 + 1):
            if year_ == str(1997 + i) + '/':
                year_links.append(link['href'])

    # access year directory
    for i in range(len(year_links)):
        year_link = html_parser(url + year_links[i])

        # year directory exists
        if year_link:
            week_links = []
            week_links_strings = []

            # access weekly tables for year directory
            for link in year_link:
                temp = str(link.string)

                # don't access unnecessary links from directory
                if (temp.casefold() != "Name".casefold()
                        and temp.casefold() != "Last Modified".casefold()
                        and temp.casefold() != "Size".casefold()
                        and temp.casefold() != "Parent Directory".casefold()):

                    # store weekly link names
                    week_links.append(link['href'])
                    temp_string = str(link.string).split(';')[0]
                    week_links_strings.append(temp_string)

            for j in range(len(week_links)):
                try:
                    response = requests.get(url + year_links[i] + week_links[j])

                    if response.status_code != 200:
                        logging.error(f"Non-200 status for {week_links_strings[j]}: {response.status_code}")
                        continue

                    text = response.text

                    # delay between downloads
                    time.sleep(1)

                    with open(file_name + week_links_strings[j], "w") as f:
                        f.write(text)
                except Exception as e:
                    logging.exception(f"Failed on {week_links_strings[j]}: {e}")
                    continue