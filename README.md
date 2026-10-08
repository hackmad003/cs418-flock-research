# cs418-flock-research

A CS 418 Data Science Research Project on ***Flock Safety ALPR 
(Automated License Plate Reader) cameras***: Where they are, 
Who operates them, and How they're used.


## RESEARCH QUESTIONS

(We will try to narrow ALPR down to Flock*)

1 Based on OSM node creation timestamps, what's the apparent rate of new camera tagging over the past 12 months? (caveat: measures mapping activity, not necessarily deployment rate — worth stating explicitly)

2 Is camera density by ZIP code associated with median household income or population density?

3 Do ALPR-using agencies disproportionately also use other surveillance tech (facial recognition, drones) vs. non-ALPR agencies?

4 What is the density of ALPR cameras (per sq. mile or per capita) across [sample of cities]?

5 ...

6 ...

## DATASETS

Full raw files live in `data/raw/` and are **gitignored**. To get them, run the fetch commands below from the project root.
A 100-row sample of each raw file is committed in `data/processed/sample/` (made by `scripts/make_samples.py`).
`notebooks/Data_Acq_M3/00_explore_raw.ipynb` loads each raw dataset into a polars DataFrame and shows the numbers below.

| Dataset | Role | File the notebook reads |
|---|---|---|
| OSM ALPR cameras | primary | `data/raw/Illinois_alpr.geojson` |
| Eyes On Flock | primary | newest `data/raw/eyesonflock_*.json` (currently 2026-09-27) |
| EFF Atlas of Surveillance | secondary | newest `data/raw/atlas_of_surveillance_*.csv` (currently 2026-09-28) |
| US Census by ZIP code | secondary | the three files in `data/raw/census/` |


### 1. OSM ALPR Cameras (primary)

ALPR camera locations mapped by volunteers in OpenStreetMap, pulled for Illinois on 2026-09-28.

- **Rows × columns:** 8,047 × 11
- **One row =** one ALPR camera
- **Key columns:** `osm_id` (Int64), `lon` / `lat` (Float64), `manufacturer` (String), `operator` (String), `timestamp` (String, last OSM edit in UTC), `version` (Int64, 1 = never edited)
- **Time range:** last edits from 2023-05-15 to 2026-09-28
- **Geography:** Illinois (lat 37.15 to 42.50, lon -91.41 to -87.53)

Fetch: `uv run python scripts/fetch_alpr_cameras.py --state Illinois --out data/raw/Illinois_alpr.geojson`

**Sources**

- OpenStreetMap: https://www.openstreetmap.org
- Overpass API (how we query OSM): https://overpass-api.de
- DeFlock (maps ALPR cameras in OSM, runs the Overpass server we query first): https://deflock.me
- License: © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright

**Disclaimers**

- Crowd-sourced: only cameras that volunteers have found and tagged.
- `timestamp` is the last edit, not the install date. It measures mapping activity, not deployment (see Q1).


### 2. Eyes On Flock (primary)

Flock Safety transparency portal data for every agency that publishes a portal, downloaded 2026-09-27. The file holds `portals` (the table below) and `summary` (national totals).

- **Rows × columns:** 1,528 × 20
- **One row =** one agency's transparency portal
- **Key columns:** `slug` (String, agency ID), `city` / `county` / `state` / `type` (String), `total_cameras`, `total_searches`, `data_retention` (Int64), `organizations_shared_with` (List of String), `data_last_updated` (String, UTC)
- **Time range:** portals last updated from 2026-02-25 to 2026-09-23
- **Geography:** US, 45 states; 1,304 city-level agencies and 224 county-level agencies

Fetch: `uv run python scripts/fetch_eyesonflock.py`

**Sources**

- Eyes On Flock: https://eyesonflock.com
- Data endpoint (undocumented; the same one the site loads): https://eyesonflock.com/api/v1/data
- Original data: Flock Safety transparency portals: https://transparency.flocksafety.com
- License: CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/

**Disclaimers**

- Only agencies that chose to publish a portal, so this is a fraction of all Flock customers.
- The data endpoint is undocumented and may change or disappear.


### 3. EFF Atlas of Surveillance (secondary)

**How we'll use it:** For Q3, we'll **compare** agencies that have an `Automated License Plate Readers` row against agencies that don't, on how often each group also has `Face Recognition`, `Drones`, etc. rows.

Which US law enforcement agencies use which surveillance technologies, downloaded 2026-09-28.

- **Rows × columns:** 15,135 × 28
- **One row =** one (agency, technology) pair, e.g. "Rockford Police Department uses Gunshot Detection"
- **Key columns** (all String): `Agency`, `Type of LEA`, `City`, `State`, `Technology`, `Vendor`, `Link 1 Date` (date of the evidence)
- **Time range:** evidence dates from 2002-05-14 to 2026-08-14 (10,418 rows have a usable date)
- **Geography:** US, 7,762 agencies across 58 state/territory codes

Fetch: `uv run python scripts/fetch_atlas.py`

**Sources**

- Atlas of Surveillance (EFF + University of Nevada, Reno): https://atlasofsurveillance.org
- Download: https://atlasofsurveillance.org/data-library ("See Dataset (CSV)")
- License: CC BY 4.0: https://www.eff.org/copyright

**Disclaimers**

- Built from public sources. A missing row does NOT prove an agency doesn't use a technology.


### 4. US Census by ZIP Code (secondary)

**How we'll use it:** For Q2 and Q4, we'll **join** it to the OSM ALPR cameras by ZIP code: place each camera (`lat` / `lon`) inside a ZCTA, count cameras per ZCTA, then join those counts to income, population, and land area on the ZIP code. We'll then **compare** cameras per capita and per sq. mile against median household income and population density. Placing cameras inside ZCTAs needs ZCTA boundary shapes (Census TIGER/Line), which we haven't downloaded yet.

Three files, downloaded 2026-09-28: 
ACS 5-year median household income (table B19013), 
ACS 5-year total population (table B01003), 
and the 2024 Gazetteer (land area).

- **Rows × columns:** income 33,772 × 3, population 33,772 × 3, Gazetteer 33,791 × 7
- **One row =** one ZCTA (the Census's version of a ZIP code)
- **Key columns:** `GEO_ID` (String), `B19013_E001` / `B01003_E001` (Int64, the income / population estimate), `GEOID` (String, ZIP code), `ALAND_SQMI` (Float64, land area), `INTPTLAT` (Float64), `INTPTLONG` (String)
- **Time range:** ACS estimates average 2020–2024; Gazetteer is 2024
- **Geography:** every US ZCTA, 33,791 of them (ZIP 00601 to 99929, including Puerto Rico)

Fetch: `uv run python scripts/fetch_census.py`

**Sources**

- ACS Summary File (2024 5-year): https://www.census.gov/programs-surveys/acs/data/summary-file.html
- Gazetteer files: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
- License: public domain

**Disclaimers**

- ZCTAs approximate ZIP codes but don't match them exactly.
- ACS values are estimates with margins of error.


## DISCLAIMERS (whole project)

- For educational purposes only (UIC CS 418 course project).
- All data are snapshots from September 2026 and may be outdated, incomplete, or different from current official records.
- Files in `data/raw/` are raw downloads, not official records.
- If you reuse or share the data, review each source's license and terms first (ODbL for OSM, CC BY-SA 4.0 for Eyes On Flock, CC BY 4.0 for EFF, public domain for Census).


## SETUP

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python version and all packages.

1. Install uv (only once):
   ```powershell
   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   ```bash
   # Mac / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Clone the repo and install everything:
   ```bash
   git clone <repo-url>
   cd cs418-flock-research
   uv sync
   ```
3. To add a new package, use `uv add <package>` (don't edit `pyproject.toml` by hand).


## USAGE

Download every dataset (from the project root):

```bash
uv run python scripts/fetch_alpr_cameras.py --state Illinois --out data/raw/Illinois_alpr.geojson
uv run python scripts/fetch_eyesonflock.py
uv run python scripts/fetch_atlas.py
uv run python scripts/fetch_census.py
uv run python scripts/make_samples.py     # refresh data/processed/sample/
```

Other ways to pull OSM cameras:

```bash
uv run python scripts/fetch_alpr_cameras.py --place "Orland Park, Illinois" --out data/raw/orland_park_alpr.geojson
uv run python scripts/fetch_alpr_cameras.py --bbox 41.6,-87.9,42.1,-87.5 --out data/raw/chicago_alpr.geojson
```

Run `--help` to see all options. To view the results on a map, drag a `.geojson` file onto [geojson.io](https://geojson.io).



## PROJECT STRUCTURE
```
cs418-flock-research/
├── .gitignore
├── .python-version                  # Python 3.14
├── README.md
├── pyproject.toml                   # dependency list
├── uv.lock                          # pinned versions (don't edit by hand)
├── data/
│   ├── processed/                   # cleaned, analysis-ready data
│   │   └── sample/                  
│   └── raw/                         # full downloads (gitignored)
│       ├── Illinois_alpr.geojson
│       ├── eyesonflock_2026-09-27.json
│       ├── atlas_of_surveillance_2026-09-28.csv
│       └── census/
├── notebooks/
│   ├── Data_Acq_M3/
│   │   └── 00_explore_raw.ipynb     # loads each dataset into a dataframe and notes its shape
│   ├── EDA_M4/
│   │   ├── eda.ipynb                # unified EDA notebook (final deliverable)
│   │   ├── eda_aa.ipynb
│   │   ├── eda_ag.ipynb
│   │   ├── eda_avg.ipynb
│   │   └── eda_hn.ipynb
│   ├── Data_Documentation_M5/
│   ├── Narrative_Analysis_M6/
│   └── Public_Facing_Report_M7/
│ 
├── scripts/                         # run these (fetch → data/raw/)
│   ├── fetch_alpr_cameras.py
│   ├── fetch_eyesonflock.py
│   ├── fetch_atlas.py
│   ├── fetch_census.py
│   └── make_samples.py
│ 
└── src/
    └── cs418_flock_research/        # import these (data/raw/ → DataFrame)
        └── __init__.py 

(Not shown: .venv/, .git/, and __pycache__/. They're generated automatically and ignored.)
```

## WORKFLOW

- Never commit directly to `main`.
- Work on your own branch: `firstname-dev`, or `firstname-feature` for a specific feature.
- Open a pull request into `main` when you're ready to merge.

## TEAM

| Name | GitHub |
|---|---|
| Ahmad Awaidah | hackmad003 |
