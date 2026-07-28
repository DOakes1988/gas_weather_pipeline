

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
  * parse raw data

    * clean data
  * load parsed data into PostgreSQL



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
  * parsing/

    * parse\_gas\_price.py
    * parse\_gas\_storage.py
    * parse\_degree\_days.py
  * load/

    * load\_to\_postgres.py
  * utils/ (shared helpers - DB connection, logging, date alignment logic)



* sql/

  * schema/

    * create\_dim\_date.sql
    * create\_dim\_region.sql
    * create\_facts.sql
  * queries/



* .gitHub/

  * workflows/ (GitHub Actions scheduled later)



* .env/ (local secrets - API keys, DB password; NEVER COMMITTED)



* .gitignore/
* requirements.txt
* README.md



















