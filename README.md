

### **NOTES:**





###### **Tools:**

* PostgreSQL (DB)
* Docker container
* PGAdmin
* Python (fetch, parse, load data)
* S3 storing raw data
* Neon (hosted postgres)
* GitHub Actions (scheduled database updates)
* Power BI (visualizations)





###### **Order of Operations:**

* Data Sources

  * Henry Hub gas spot price

    * price signal: daily, weekly, national benchmark
  * Natural gas underground storage, East region (EIA API)

    * supply signal: weekly
  * population-weighted heating/cooling degree days, East region states (NOAA CPC, fixed-width text files)

    * demand driver signal: weekly



* Schema Design

  * dim\_date: one row per calendar day
  * dim\_region: one row per region
  * fact\_gas\_price, fact\_gas\_storage, fact\_degree\_days: the actual measurements

    * different grains: (daily, weekly, weekly)
    * linked back to date/region via foreign keys



* Populate dimension tables



* Ingestion

  * fetch raw data

    * web scraper
    * API
  * process raw data

    * clean data in Python
    * load parsed data into PostgreSQL using psycopg



* Move raw data to S3



* Scheduling

  * GitHub Actions
  * Switch to a hosted Postgres (Neon)



* Analysis/querying



* Power BI



&#x09;















File structure:



* data/

  * raw/

    * gas\_price/
    * gas\_storage/
    * degree\_days/
  * staging (intermediate parsed output before load to DB)



* src/

  * ingestion/

    * fetch\_gas\_price.py
    * fetch\_gas\_storage.py
    * fetch\_degree\_days.py
  * processing/

    * load\_gas\_price.py
    * load\_gas\_storage.py
    * load\_degree\_days.py

  * utils/ (shared helpers - DB connection, logging, date alignment logic)
    * file tracker (makes sure we only process raw file once)
  


* sql/

  * schema/

    * create\_dim\_date.sql
    * create\_dim\_region.sql
    * create\_facts.sql
  * queries/



* .gitHub/

  * workflows/ (GitHub Actions scheduled later)



* .env/ (local secrets - API keys, DB password; not committed)



* .gitignore/
* requirements.txt
* README.md



















