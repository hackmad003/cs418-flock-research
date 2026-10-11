# cs418-flock-research

A CS 418 Data Science Research Project on ***Flock Safety ALPR 
(Automated License Plate Reader) cameras***: 

Where they are, 
Who operates them, 
and How they're used
Among Other Observations.


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
A 100-row sample of each raw file is committed in `data/processed/sample/`.
`notebooks/00_explore_raw.ipynb` loads each raw dataset into a polars DataFrame and shows the numbers below.

| Dataset | Role | File the notebook reads |
|---|---|---|
| OSM ALPR cameras | primary | `data/raw/Illinois_alpr.geojson` |
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

- https://overpass-turbo.eu/


**Disclaimers**

- Crowd-sourced: only cameras that volunteers have found and tagged.
- `timestamp` is the last edit, not the install date. It measures mapping activity, not deployment (see Q1).



### 2. EFF Atlas of Surveillance (secondary)

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


### 3. US Census by ZIP Code (secondary)

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
uv run python scripts/fetch_atlas.py
uv run python scripts/fetch_census.py
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
│       ├── atlas_of_surveillance_2026-09-28.csv
│       └── census/
├── notebooks/
│   ├── 00_explore_raw.ipynb         # loads each dataset into a dataframe and notes its shape
│   ├── eda.ipynb                    # unified EDA notebook (final deliverable)
│   ├── eda_aa2.ipynb                # Ahmad's EDA
│   ├── EDA_AA.md                    # summary of Ahmad's EDA
│   ├── EDA_LG.md                    # summary of Lexi's EDA
│   └── EDA_LG.ipynb                 # Lexi's EDA
│ 
├── scripts/                         # run these (fetch → data/raw/)
│   ├── fetch_alpr_cameras.py
│   ├── fetch_atlas.py
│   └── fetch_census.py
│ 
└── src/
    └── cs418_flock_research/        # import these (data/raw/ → DataFrame)
        ├── __init__.py
        ├── alpr_cameras.py          # load_alpr_cameras()
        ├── atlas.py                 # load_atlas()
        └── census.py                # load_zcta()

(Not shown: .venv/, .git/, and __pycache__/. They're generated automatically and ignored.)
```

## WORKFLOW

- Never commit directly to `main`.
- Work on your own branch: `firstname-dev`, or `firstname-feature` for a specific feature.
- Open a pull request into `main` when you're ready to merge.

## TEAM

| Name |
|---|---|
| Ahmad Awaidah
| Lexi Golley
| Naqvi, Hussain 
| Garcia Villalba, Ariana 

