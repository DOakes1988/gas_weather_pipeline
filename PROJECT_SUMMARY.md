# Gas Price & Weather Pipeline: Project Summary

Portfolio project for data analyst roles. Tracks the relationship between natural gas prices,
underground storage, and weather-driven heating demand.

Last updated: 2026-07-30

## The core idea

Henry Hub natural gas price is the national benchmark price. It is compared against East region
gas storage levels and East region population-weighted heating degree days, to explore whether
regional cold weather (via heating demand) correlates with gas storage draws and price movement.

## Data sources

| Source | Provider | Format | History | Frequency |
|---|---|---|---|---|
| Henry Hub spot price (RNGWHHD) | EIA API | JSON | 1997-present | Daily |
| Natural gas storage, East region | EIA API | JSON | 2010-present | Weekly (Fri-ending) |
| Heating degree days, by state | NOAA CPC | Fixed-width .txt/.dat | 1997-present | Weekly (Sat-ending) |

## Key design decisions and why

- **Henry Hub (national) price, not a regional price series.** A regional hub price was
  considered, but no comparable, well-documented regional series was confidently identified
  within the available time. Henry Hub is the standard national reference price, and regional
  weather/storage events are known to influence it even though it is measured elsewhere.
  Documented limitation: local "basis" can cause a regional price to diverge from Henry Hub
  during acute regional stress.
- **East region definition**: confirmed via EIA's official state list (19 states):
  Connecticut, Delaware, District of Columbia, Florida, Georgia, Maine, Maryland,
  Massachusetts, New Hampshire, New Jersey, New York, North Carolina, Ohio, Pennsylvania,
  Rhode Island, South Carolina, Vermont, Virginia, West Virginia. This is the modern
  (post-October 2015) 5-region EIA definition, smaller than the older 3-region "East"
  definition, which included several Midwest states now split out.
- **Storage history starts at 2010**, not 1997, because EIA's 5-region storage breakdown only
  goes back to the 2015 restructuring's effective data range. Price and weather history go back
  further (1997+) and are loaded regardless, though not usable in a full three-way join before
  2010.
- **Week alignment**: gas storage and gas price weeks end Friday. NOAA degree-days weeks end
  Saturday. Fix: subtract one day from the parsed degree-days date so all three sources key off
  the same Friday-ending week.
- **Population-weighted degree days**: NOAA's data is already population-weighted within each
  state, but combining multiple states into one regional number is still a decision the project
  makes explicitly: a population-weighted average across the 19 East-region states (state
  population as the weight), not a simple average.
- **National region row**: added a `National` row to `dim_region` so `fact_gas_price` follows
  the same region-linked pattern as the other two fact tables, even though Henry Hub is not
  regional. Keeps all three fact tables structurally consistent.
- **Cooling degree days**: out of scope for now. Only heating degree days are being ingested.
  Flagged as a possible phase-2 addition, not required for the core project.

## Schema

- `dim_date`: one row per calendar day, 1997 through roughly two years past the current date.
  Includes week/month/quarter/year breakdowns, with all "start of period" columns built via
  `DATE_TRUNC`. `week_number` is a globally unique, ever-increasing identifier derived via
  `DENSE_RANK() OVER (ORDER BY start_of_week)`, not a value that resets each year. Weeks run
  Saturday to Friday (`start_of_week` is the Saturday, the week ends the following Friday).
- `dim_region`: `region_key` (SERIAL), `region_name`, `region_code`. Currently: `East`,
  `National`.
- `fact_gas_price`: daily grain. Primary key: `(date, price_region)`. Region is always
  `National` for now.
- `fact_gas_storage`: weekly grain (Friday-ending). Primary key: `(date, storage_region)`.
  Region is always `East`.
- `fact_degree_days`: weekly grain (Friday-ending, shifted from the source's Saturday-ending).
  Primary key: `(date, degree_day_region)`. Region is always `East`.

## Tech stack

- **Database**: Postgres, running in Docker locally (port 5433, to avoid a conflicting native
  Postgres install on 5432). Will migrate to Neon (a free hosted Postgres provider) once 
  scheduling is wired up. Neon was chosen over a similar option, Supabase, because it handles 
  inactive projects more gracefully for a pipeline that only runs occasionally.
- **Python**: `psycopg` (v3) for database connections, `requests` plus `BeautifulSoup` for
  scraping, `python-dotenv` for secrets, `Decimal` (not `float`) for all price and measurement
  values.
- **Loading pattern**: raw files are saved to disk untouched, parsed in memory, bulk-loaded via
  `COPY` into a temporary staging table, then merged into the real fact table with
  `INSERT ... ON CONFLICT ... DO UPDATE`. This upsert pattern means revised source data
  overwrites old values without duplicating rows.
- **File tracking**: a shared `FileTracker` class (in `utils/`) logs which raw files have
  already been processed, so backfill/fetch scripts and loaders do not reprocess the same file
  twice. It persists to a text log file, loaded into an in-memory set on startup.
- **Version control**: git and GitHub. `.env`, `.venv/`, `.idea/`, raw data, and log files are
  gitignored. `.gitkeep` placeholders preserve the empty `data/raw/` and `data/staging/` folder
  structure in the repo.

## File structure

```
gas-weather-pipeline/
├── data/
│   ├── raw/
│   │   ├── gas_price/
│   │   ├── gas_storage/
│   │   └── degree_days/
│   └── staging/
├── src/
│   ├── ingestion/      (fetch_*.py, backfill_*.py per source)
│   ├── processing/     (load_*.py: parsing and loading combined, per source)
│   └── utils/          (FileTracker, shared helpers)
├── sql/
│   └── schema/          (CREATE TABLE and populate scripts, saved as real files)
├── docs/                (reference material, e.g. EIA region map)
├── .env / .gitignore / requirements.txt / README.md
```

## Status as of last update

- Environment: Docker, Postgres, venv, and git are all working.
- Schema: all five tables are created, and `dim_date` and `dim_region` are populated.
- Gas price: backfill and fetch scripts, parsing, and loading (with upsert) are fully done,
  tested, and in git.
- Gas storage: backfill and fetch scripts, parsing, and loading are fully done.
- Degree days: the full pipeline is complete. This includes fixed-width parsing (handling 25+
  years of format drift, form-feed control characters, inconsistent whitespace, and one
  genuinely corrupted file that is skipped and logged rather than force-parsed), East-region
  state filtering, population-weighted aggregation (state population reference in
  `utils/state_populations.py`), Saturday-to-Friday date alignment, and loading via the same
  COPY-to-staging-then-upsert pattern as the other two sources. All three fact tables are now
  fully populated.

## Not started yet

- **`fetch_degree_days.py`**: the backfill script exists and has loaded full history, but there
  is no incremental fetch script yet for degree days, unlike gas price and storage, which each
  have both a `backfill_` and `fetch_` script. This is needed before scheduling can work for
  this source, since without it there is no way to pick up new weekly NOAA files after the
  initial backfill. It likely needs its own logic to check for the newest file(s) not yet in
  the tracker log, adapted from the backfill script's directory-scraping approach rather than
  the gas price/storage fetch scripts' date-range API parameters.
- Scheduling (GitHub Actions) and migration to hosted Postgres.
- Analysis and insight-finding queries.
- Power BI dashboard.

## Known open items and things to revisit if time allows

- Shared `load_data` logic across the three sources is not abstracted into one reusable
  function or class. This was a deliberate decision to skip for now given only three call
  sites, to be revisited if more sources or regions are added later.