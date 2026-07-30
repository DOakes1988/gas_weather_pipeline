# Gas Price & Weather Pipeline — Project Summary

Portfolio project for data analyst roles. Tracks the relationship between natural gas prices,
underground storage, and weather-driven heating demand.

Last updated: 2026-07-29

## The core idea

Henry Hub natural gas price is the national benchmark price. It's compared against East region
gas storage levels and East region population-weighted heating degree days, to explore whether
regional cold weather (via heating demand) correlates with gas storage draws and price movement.

## Data sources

| Source | Provider | Format | History | Frequency |
|---|---|---|---|---|
| Henry Hub spot price (RNGWHHD) | EIA API | JSON | 1997–present | Daily |
| Natural gas storage, East region | EIA API | JSON | 2010–present | Weekly (Fri-ending) |
| Heating degree days, by state | NOAA CPC | Fixed-width .txt/.dat | 1997–present | Weekly (Sat-ending) |

## Key design decisions (and why)

- **Henry Hub (national) price, not a regional price series.** Considered switching to a
  regional hub price, but no comparable, well-documented regional series was confidently
  identified within the time available. Henry Hub is the standard national reference price;
  regional weather/storage events are known to influence it even though it's measured
  elsewhere. Documented limitation: local "basis" can cause a regional price to diverge from
  Henry Hub during acute regional stress.
- **East region definition**: confirmed via EIA's official state list (19 states) —
  Connecticut, Delaware, District of Columbia, Florida, Georgia, Maine, Maryland,
  Massachusetts, New Hampshire, New Jersey, New York, North Carolina, Ohio, Pennsylvania,
  Rhode Island, South Carolina, Vermont, Virginia, West Virginia. This is the *modern*
  (post-October 2015) 5-region EIA definition — smaller than the older 3-region "East"
  definition, which included several Midwest states now split out.
- **Storage history starts at 2010**, not 1997, because EIA's 5-region storage breakdown only
  goes back to the 2015 restructuring's effective data range. Price and weather history go back
  further (1997+) and are loaded regardless — just not usable in a full 3-way join before 2010.
- **Week alignment**: gas storage and gas price weeks end Friday. NOAA degree-days weeks end
  Saturday. Fix: subtract 1 day from the parsed degree-days date so all three sources key off
  the same Friday-ending week.
- **Population-weighted degree days**: NOAA's data is already population-weighted *within* each
  state, but combining multiple states into one regional number is still a decision the project
  makes explicitly — a population-weighted average across the 19 East-region states (state
  population as the weight), not a simple average. (In progress.)
- **National region row**: added a `National` row to `dim_region` so `fact_gas_price` follows
  the same region-linked pattern as the other two fact tables, even though Henry Hub isn't
  regional. Keeps all three fact tables structurally consistent.
- **Cooling degree days**: out of scope for now. Only heating degree days are being ingested.
  Flagged as a possible phase-2 addition, not required for the core project.

## Schema

- `dim_date` — one row per calendar day, 1997 through ~2 years past current date. Includes
  week/month/quarter/year breakdowns, all "start of period" columns via `DATE_TRUNC`.
  `week_number` is a globally unique, ever-increasing identifier derived via
  `DENSE_RANK() OVER (ORDER BY start_of_week)` — not a "resets every year" week number.
  Weeks run Saturday-to-Friday (`start_of_week` = the Saturday, week ends the following Friday).
- `dim_region` — `region_key` (SERIAL), `region_name`, `region_code`. Currently: `East`,
  `National`.
- `fact_gas_price` — daily grain. PK: `(date, price_region)`. Region is always `National`
  for now.
- `fact_gas_storage` — weekly grain (Friday-ending). PK: `(date, storage_region)`. Region is
  always `East`.
- `fact_degree_days` — weekly grain (Friday-ending, shifted from source's Saturday-ending).
  PK: `(date, degree_day_region)`. Region is always `East`. (Loading not yet complete.)

## Tech stack

- **Database**: Postgres, running in Docker locally (port 5433, to avoid a conflicting native
  Postgres install on 5432). Will migrate to a hosted free-tier instance (Neon, chosen over
  Supabase for its scale-to-zero/auto-resume behavior vs. Supabase's harder weekly pause) once
  scheduling is wired up.
- **Python**: `psycopg` (v3) for DB connections, `requests` + `BeautifulSoup` for scraping,
  `python-dotenv` for secrets, `Decimal` (not `float`) for all price/measurement values.
- **Loading pattern**: raw files saved to disk untouched → parsed in memory → bulk-loaded via
  `COPY` into a temporary staging table → merged into the real fact table with
  `INSERT ... ON CONFLICT ... DO UPDATE` (upsert, so revised source data overwrites old values
  without duplicating rows).
- **File tracking**: a shared `FileTracker` class (in `utils/`) logs which raw files have
  already been processed, so backfill/fetch scripts and loaders don't reprocess the same file
  twice. Persists to a text log file, loaded into an in-memory set on startup.
- **Version control**: git + GitHub. `.env`, `.venv/`, `.idea/`, raw data, and log files are
  gitignored. `.gitkeep` placeholders preserve empty `data/raw/` and `data/staging/` folder
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
│   ├── processing/      (load_*.py — parsing + loading combined, per source)
│   └── utils/           (FileTracker, shared helpers)
├── sql/
│   └── schema/          (CREATE TABLE + populate scripts, saved as real files)
├── docs/                (reference material, e.g. EIA region map)
├── .env / .gitignore / requirements.txt / README.md
```

## Status as of last update

- ✅ Environment: Docker, Postgres, venv, git — all working
- ✅ Schema: all 5 tables created, `dim_date` and `dim_region` populated
- ✅ Gas price: backfill + fetch scripts, parsing, loading (with upsert) — fully done, tested, in git
- ✅ Gas storage: backfill + fetch scripts, parsing, loading — fully done
- 🔄 Degree days: raw backfill done (full history downloaded). Fixed-width parser built and
  tested across 20+ sample files, including 1997 `.dat` files and inconsistent early-year
  layouts (state block length varies by year — using "stop at REGION line" instead of a fixed
  line count to handle this). Date parsing solved (including the leading-zero/double-space
  quirk). State-list filtering and population-weighted aggregation are done. Friday-shift
  logic is done. Still to do: the actual load-to-Postgres step (Copy to temp table, loading with upsert).

## Not started yet

- Scheduling (GitHub Actions) + migration to hosted Postgres
- Analysis / insight-finding queries
- Power BI dashboard

## Known open items / things to revisit if time allows

- Shared `load_data` logic across the three sources isn't abstracted into one reusable
  function/class yet — deliberate decision to skip for now given only 3 call sites, revisit if
  more sources/regions are added later.
- Population-weighting for degree days uses a static state population reference — needs a
  source and a decision on whether it lives in Postgres or as a hardcoded Python dict.
