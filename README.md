# cs418-flockers
A CS 418 Data Science Research Project on ***Flock Safety***: 

## RESEARCH QUESTIONS
**1 Where are mapped Flock cameras, and how has the mapping grown over time?**
**2 Is mapped camera density associated with community characteristics?**
**3 Is mapped camera density associated with political voting patterns?**

## DATASETS

Primary datasets describe Flock cameras. Secondary datasets provide supporting context for the analysis.

### Primary: Flock camera datasets

- **OpenStreetMap (OSM):** Camera locations, attributes, and OSM mapping history collected through Overpass and the OSM API. Stored in `data/raw/flock_osm/`.
- **Finding Flock:** City and state camera summaries, including Flock counts, plus city geographic data. Stored in `data/raw/finding_flock/`.

**Limitations:** Mapped cameras may not represent all installed cameras. OSM history dates describe mapping activity, not installation dates. Finding Flock summaries include other manufacturers, so use the Flock-specific counts when analyzing Flock cameras.

### Secondary: Supporting datasets

- **U.S. Census:** 2017 and 2024 income, population, poverty, and race/ethnicity tables for studying community characteristics. Stored in `data/raw/census/`.
- **Census TIGER/Line boundaries:** Tract and county boundaries for matching camera locations to geographic areas. Stored in `data/external/census_boundaries/`.
- **Presidential election returns:** County-level results from 2000-2024 for studying voting patterns. Stored in `data/raw/elections/presidential/`; the included codebook documents the data and sources.

**Limitations:** Match geographic areas and time periods carefully when combining datasets. Associations do not establish causation.

## SOURCES

- **OSM camera data:** [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), accessed through [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) and the OSM API.
- **Finding Flock summaries:** [Finding Flock](https://www.findingflock.com/stats).
- **Census tables:** [U.S. Census Bureau, American Community Survey](https://www.census.gov/programs-surveys/acs/data.html).
- **Geographic boundaries:** [U.S. Census Bureau, TIGER/Line downloads](https://www2.census.gov/geo/tiger/).
- **Election results:** [MIT Election Data and Science Lab, County Presidential Election Returns 2000-2024](https://doi.org/10.7910/DVN/VOQCHQ).

## DISCLAIMERS (whole project)
- For educational purposes only (UIC CS 418 course project).

## PROJECT STRUCTURE
```
cs418-flock-research/
|-- .gitignore
|-- .python-version
|-- README.md
|-- pyproject.toml                   # dependencies
|-- uv.lock                          # pinned dependency versions
|-- checkpoints/
|   |-- Data_Acquisition/
|   |   `-- 00_explore_raw.ipynb
|   |-- Data_Documentation/
|   |   `-- DATASHEET.md
|   |-- Exploratory_Analysis/
|   |   |-- EDA_AA.ipynb
|   |   |-- EDA_AA.md
|   |   |-- EDA_LG.ipynb
|   |   |-- EDA_LG.md
|   |   `-- eda_findingflock.ipynb
|   |-- Narrative_Analysis/
|   |-- Presentation/
|   `-- Public_Facing_Report/
|-- data/
|   |-- external/
|   |   |-- census_boundaries/
|   |   |   |-- 2017/                # state tract boundary ZIPs
|   |   |   |-- 2024/                # state tract boundary ZIPs
|   |   |   `-- counties/
|   |   |       `-- tl_2024_us_county.zip
|   |   `-- chicago/
|   |       |-- chicago-city.geojson
|   |       |-- chicago-ward-income.csv
|   |       `-- chicago-wards.geojson
|   |-- processed/
|   |   `-- samples/
|   |       |-- census/
|   |       |   |-- median_household_income/
|   |       |   |   |-- 2017/
|   |       |   |   `-- 2024/
|   |       |   |-- population/
|   |       |   |   |-- 2017/
|   |       |   |   `-- 2024/
|   |       |   |-- poverty/
|   |       |   |   |-- 2017/
|   |       |   |   `-- 2024/
|   |       |   `-- race_ethnicity/
|   |       |       |-- 2017/
|   |       |       `-- 2024/
|   |       |-- elections/
|   |       |   `-- presidential/
|   |       |       |-- County Presidential Returns 2000-2024.md
|   |       |       |-- countypres_2000-2024_sample.csv
|   |       |       `-- sources-president_sample.csv
|   |       |-- finding_flock/
|   |       |   |-- findingflock-cameras-by-city_sample.csv
|   |       |   |-- findingflock-cameras-by-city_sample.geojson
|   |       |   `-- findingflock-cameras-by-state_sample.csv
|   |       `-- flock_osm/
|   |           |-- flock_us_historical_2026-10-30_sample.csv
|   |           `-- osm_flock_us_with_history_2026-10-30_sample.csv
|   `-- raw/                        # datasets are gitignored
|       |-- atlas_of_surveillance/
|       |   `-- atlas_of_surveillance_2026-09-28.csv
|       |-- census/
|       |   |-- median_household_income/
|       |   |   |-- 2017/
|       |   |   `-- 2024/
|       |   |-- population/
|       |   |   |-- 2017/
|       |   |   `-- 2024/
|       |   |-- poverty/
|       |   |   |-- 2017/
|       |   |   `-- 2024/
|       |   `-- race_ethnicity/
|       |       |-- 2017/
|       |       `-- 2024/
|       |-- elections/
|       |   `-- presidential/
|       |       |-- County Presidential Returns 2000-2024.md
|       |       |-- countypres_2000-2024.csv
|       |       `-- sources-president.csv
|       |-- finding_flock/
|       |   |-- findingflock-cameras-by-city.csv
|       |   |-- findingflock-cameras-by-city.geojson
|       |   `-- findingflock-cameras-by-state.csv
|       `-- flock_osm/
|           |-- flock_us_historical_2026-10-30.csv
|           `-- osm_flock_us_with_history_2026-10-30.csv
|-- docs/
|   |-- data_acq_goal.pdf
|   |-- data_documentation.md
|   |-- data_documentation.pdf
|   |-- eda.pdf
|   |-- exploratory_analysis.md
|   |-- narrative analysis.pdf
|   `-- narrative_analysis.md
|-- figures/                        # currently empty
|-- notebooks/
|   |-- personal_notebooks/
|   |   |-- dev.ipynb
|   |   `-- dev2.ipynb
|   `-- reset/
|       `-- dev.ipynb
|-- reports/                        # currently empty
|-- scripts/
|   |-- create_dataset_samples.py
|   |-- fetch_atlas.py
|   |-- fetch_census_legacy.py
|   |-- fetch_census_track_boundaries.py
|   |-- fetch_osm_alpr_cameras.py
|   |-- fetch_osm_alpr_cameras_legacy.py
|   `-- fetch_osm_flock_history.py
`-- src/
    `-- cs418_flock_research/
        |-- __init__.py
        |-- alpr_cameras.py
        |-- atlas_of_surveillance.py
        |-- census_zcta.py
        |-- loaders/                # currently empty
        `-- processing/             # currently empty

Not shown: .git/, .venv/, __pycache__/, and .gitkeep placeholders.
Raw Census year folders contain data CSVs, column metadata CSVs, and table notes.
Sample Census year folders contain _sample.csv files and copied table notes.
```
