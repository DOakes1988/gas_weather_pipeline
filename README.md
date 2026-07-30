# Gas Price & Weather Pipeline

A data pipeline examining how natural gas prices relate to gas storage levels and
weather-driven heating demand in the U.S. This project was built to practice the full lifecycle
of a real data project: pulling from live sources, cleaning genuinely messy historical data,
designing a proper database schema, and working toward real analysis and a dashboard.

## What this project does

Cold weather drives heating demand, and heating demand affects gas prices. That relationship is
the focus of this project, using three historical sources:

- **Henry Hub natural gas spot price**: the U.S. national benchmark price, from the EIA
- **Natural gas underground storage**: weekly storage levels for the U.S. East region, also EIA
- **Heating degree days**: a proxy for regional heating demand, built from 19 East-region
  states' weekly data (NOAA's Climate Prediction Center), weighted by state population

Gas price and weather data go back to 1997. Storage data starts in 2010, since that's as far
back as EIA's current regional breakdown goes. That still provides over a decade of historical
winters to analyze.

## Architecture

Raw ingestion, parsing and transformation, PostgreSQL, analysis, and finally a dashboard.

- **Ingestion**: Python scripts call EIA's API directly and scrape NOAA's archive of historical
  text reports. Every raw file is saved to disk untouched before any further processing, so
  there is always a clean copy to fall back on.
- **Parsing**: each source has its own parsing logic to turn raw files into clean, typed rows.
  The most involved part was the NOAA data: 25+ years of fixed-width text files with format
  drift, stray control characters, and inconsistent spacing, along with the weighting
  calculation that combines 19 individual state values into one regional number.
- **Loading**: rows are bulk-loaded into a temporary staging table using `COPY`, then merged
  into the real fact tables with an upsert (`INSERT ... ON CONFLICT ... DO UPDATE`). This means
  re-running the pipeline, or loading a date range that overlaps with existing data, does not
  create duplicates or fail.
- **Database**: PostgreSQL, modeled as a star schema. Three fact tables (price, storage, degree
  days) sit at their own natural grain (daily, weekly, weekly) and connect through shared date
  and region dimension tables.

## Tech stack

- **Python**: `requests`, `BeautifulSoup` (scraping), `psycopg` (PostgreSQL), `python-dotenv`
- **PostgreSQL**, containerized with **Docker**
- **Git/GitHub** for version control
- **Power BI** for the analysis dashboard (in progress)

## A few decisions worth explaining

- **National price paired with regional data**: Henry Hub is a national benchmark, not a
  regional price point. It was used deliberately because it is the standard reference price the
  market watches. Regional demand shocks are known to move this national price, even though
  Henry Hub itself is priced in Louisiana, far from the East region. This is a simplification,
  and it is worth stating plainly rather than glossing over. See `PROJECT_SUMMARY.md` for the
  full reasoning.
- **Week alignment**: gas storage and price data report weeks ending on Friday. NOAA's weather
  data reports weeks ending on Saturday. Weather dates are shifted back one day during parsing
  so all three sources align to the same week.
- **Population-weighted regional aggregation**: rather than averaging the 19 East-region states'
  weekly degree-day values equally, each state is weighted by population, so a cold snap in New
  York counts for more than one in Delaware. This more closely reflects how heating demand is
  actually distributed.
- **Parsing that does not assume too much**: the NOAA files span 25+ years, and the formatting
  is not consistent. There are different file extensions in 1997, inconsistent capitalization,
  stray control characters, and at least one file that is genuinely corrupted. Rather than
  hardcoding line numbers, the parser looks for known text markers to determine structure, and
  any file that still cannot be parsed is skipped and logged instead of stopping the run.

## Where things stand

Ingestion, parsing, and loading are complete for all three sources, and the database schema is
built and populated. The pipeline currently runs manually. Scheduled automation via GitHub
Actions, along with a migration to a hosted Postgres instance to support that, is the next
infrastructure step. In parallel, the project is moving into analysis: identifying real
relationships in the data before building anything in Power BI.

`PROJECT_SUMMARY.md` contains a full history of decisions and changes for more detail than what
is covered here.

## Project structure

```
├── data/               # raw source files (gitignored) + folder structure preserved via .gitkeep
├── src/
│   ├── ingestion/      # backfill + incremental fetch scripts per source
│   ├── processing/     # parsing + loading scripts per source
│   └── utils/          # shared helpers (file tracking, reference data)
├── sql/schema/         # CREATE TABLE and population scripts
├── docs/               # reference material (e.g. region definitions)
```