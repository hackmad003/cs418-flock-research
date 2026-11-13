# Datasheet: OSM Flock camera locations (`osm_flock_us_locations_2026-10-30.csv`)

Datasheet for `data/raw/flock_osm/osm_flock_us_locations_2026-10-30.csv`, the primary
dataset of locations of Flock Safety license plate reader cameras mapped in OpenStreetMap.
It follows `docs/REPRODUCIBLE_DATASHEET.md` (Checkpoint Four).

**How to read the tags.** Every answer ends with one tag:
`[publisher]` from the publisher's documentation (linked), `[code]` printed by the
statistics script, `[our note]` a decision or observation by our group, and
`[not documented by the publisher]` where the publisher says nothing.

**Statistics script.** Every number below is printed by
[`scripts/datasheet_stats_osm_flock_us_locations.py`](../scripts/datasheet_stats_osm_flock_us_locations.py).
Run it from the project root (about one minute; it writes no files):

```bash
uv run python scripts/datasheet_stats_osm_flock_us_locations.py
```

Its section numbers (0–10) are given below as "script §N".

## Summary card

| Item | Value |
|---|---|
| What one row is | One OpenStreetMap **node** (a mapped point) tagged as a Flock license plate reader camera. `[code]` |
| Rows × columns | 112,830 × 20 `[code]` (script §1) |
| Time span | Last-edit times from 2024-11-17 02:09 UTC to 2026-11-05 23:43 UTC. These are **edit** times, not install dates. `[code]` |
| Source and maintainer | OpenStreetMap volunteer contributors, downloaded through the Overpass API; OSM is supported by the OpenStreetMap Foundation. `[publisher]` |
| License | Open Database License (ODbL) 1.0, © OpenStreetMap contributors. `[publisher]` |
| Snapshot date (from the file, not only its name) | The name says 2026-10-30, but 751 rows were edited later, up to 2026-11-05 23:43:35 UTC. The file was pulled after that, most likely on 2026-11-06 around 00:10 UTC (its file time). `[code]` |
| Safe for | Describing where Flock cameras are **mapped** in OSM, and comparing mapped density per resident across tracts, counties and states. `[our note]` |
| Not safe for | Counting installed cameras, dating installations, or claiming that a place without a mapped camera has none. `[our note]` |
| Biggest limitation | It is a volunteer map: a camera is in the file only if someone mapped it and tagged `manufacturer` with "Flock", so coverage depends on where mappers are active, not only on where cameras are. `[our note]` |

Sections: [1. Datasheet](#step-1-datasheet) · [2. Scope](#step-2-scope) ·
[3. Codebook](#step-3-codebook) · [4. Recipe](#step-4-recipe) ·
[4b. Access and reuse](#step-4b-access-and-reuse-fair) · [5. People in the data](#step-5-people-in-the-data)

## Step 1: Datasheet

### 1.1 Motivation

- **Why OSM exists:** OpenStreetMap describes itself as "a free, editable map of the whole world that is being built by volunteers" ([About OpenStreetMap](https://wiki.openstreetmap.org/wiki/About_OpenStreetMap)). `[publisher]`
- **Why the camera points exist:** the OSM wiki defines `man_made=surveillance` as "A surveillance camera or other type of surveillance equipment" ([wiki](https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dsurveillance)). Why individual mappers chose to map Flock cameras is `[not documented by the publisher]`.
- **Who created it:** individual OSM contributors created the points. This CSV was made by our group with `scripts/fetch_osm_alpr_cameras.py` for this course project. `[our note]`
- **Who funds it:** "The OpenStreetMap Foundation is an organization that performs fund-raising", and "it does not control the project or 'own' the OSM data" ([About OpenStreetMap](https://wiki.openstreetmap.org/wiki/About_OpenStreetMap)). `[publisher]` Our download had no funding. `[our note]`

### 1.2 Composition

- **One row:** one OSM node. All 112,830 `osm_type` values are `node`, and all 112,830 `osm_id` values are unique. `[code]` (script §1)
- **Rows and columns:** 112,830 rows × 20 columns. `[code]`
- **Duplicates:** no row is fully identical to another. `[code]`
- **Same location:** 1,877 rows share their exact coordinates with another row, at 884 spots (at most 6 rows at one spot). Each has its own `osm_id`, so they may be several cameras on one pole or one camera mapped twice; the data cannot tell. `[code]`
- **Sample or population:** it is every OSM node that matched the query when it ran, not a random sample. It is **not** every Flock camera in the U.S. `[our note]`
- **What the tag rule keeps:** only nodes with `man_made=surveillance`, `surveillance:type=ALPR` and a `manufacturer` containing "Flock" (any case). `[code]` (`camera_filters()` in `scripts/fetch_osm_alpr_cameras.py`)
- **What the tag rule leaves out (cannot be counted from this file):**
  - cameras tagged as Flock only through `brand` or `operator`, with no Flock `manufacturer`;
  - ALPR cameras with no `manufacturer`;
  - cameras drawn as ways or areas instead of points (the query asks for nodes only; the wiki says the tag "should not be used on ways");
  - Flock cameras nobody has mapped. `[our note]`
- **Inside the file, `brand` and `operator` are rare:** `brand` is filled for 829 rows and `operator` for 13,696. `[code]`
- **Outside the 50 states + DC:** 204 rows are in Puerto Rico (146) and the U.S. Virgin Islands (58). The Overpass area `ISO3166-1=US` returned them. They have a county but no 2024 tract, because the repo's tract files cover only the 50 states + DC. `[code]` (script §4–5)
- **Almost empty columns (more than 95% null):** `camera_angle` (100.0%, 30 values), `brand` (99.3%), `camera_direction` (98.4%). `[code]`
- **Mostly empty:** `operator` is null for 99,134 rows (87.9%) and `camera_mount` for 83,810 (74.3%). `[code]`
- **Placeholders that hide missing data:**
  - `direction` is exactly `"0"` in 5,758 rows. Zero means "north", but it is also a value editors may leave unchanged; the data cannot separate the two.
  - `operator` holds a placeholder word (`unknown`, `none`, `n/a` or blank) in 15 rows.
  - `camera_direction` holds such a value in 20 rows.
  - No blank strings appear: empty CSV fields load as null. `[code]`
- **Free-text values:** `direction` holds 102,326 single numbers, 8,275 other text values (ranges like `338-23`, lists like `0;0`, letters), and 169 numbers outside 0–360. The wiki allows degrees, compass letters and ranges ("direction=67-292") ([Key:direction](https://wiki.openstreetmap.org/wiki/Key:direction)). `[code]` `[publisher]`
- **Spelling variants:** `manufacturer` has 15 distinct values for the same company (for example `Flock Safety`, `Flock Group Inc.`, `FLOCK SAFETY`). `[code]`
- **What `timestamp` means:** the OSM wiki defines `timestamp` as "Time of the last modification" ([Elements](https://wiki.openstreetmap.org/wiki/Elements)). It is the last edit, not the install date or the first mapping date. `[publisher]`
- **Last-edit years:** 960 rows in 2024, 37,493 in 2025, 74,377 in 2026. `[code]`
- **Overlap with the history file:** 112,124 `osm_id` values are also in `flock_us_historical_2026-10-30.csv`. 706 are only in this file, and all 706 were edited after the history file's cut-off (2026-10-30 19:32:28 UTC). 403 are only in the history file. `[code]` (script §2)

### 1.3 Collection process

- **How OSM data is gathered:** volunteers add and edit points with OSM editors; OSM stores "the tags, and also a full editing history of every element" ([Elements](https://wiki.openstreetmap.org/wiki/Elements)). How each mapper located each camera (street survey, imagery, public records) is `[not documented by the publisher]`.
- **How we gathered it:** one Overpass API query, built by `build_query_nationwide(flock_only=True)` in `scripts/fetch_osm_alpr_cameras.py`, asked for every matching node inside `area["ISO3166-1"="US"]`, with `out meta` (which adds version, timestamp, changeset and user). `run_query()` sends it and retries other servers on errors; `to_csv()` writes one row per node. `[code]`
- **The command, inferred:** `uv run python scripts/fetch_osm_alpr_cameras.py --nationwide --flock-only --format csv`. The file's 20 columns match `CSV_COLUMNS` in the script exactly, but the exact command was not recorded. `[our note]`
- **Time frame:** a single query. The newest edit in the file is 2026-11-05 23:43:35 UTC and the file's local modification time is 2026-11-06 00:10 UTC, so the pull happened between those two times if the file was not copied later. The script names files by the UTC run date, so the `2026-10-30` in the name was not written by this run. `[code]`
- **Overpass lag:** "It can take a couple of minutes for changes to the database to show up in the Overpass API query results" ([Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)). `[publisher]` The exact lag at our pull is `[not documented by the publisher]`.
- **Consent:**
  - Mappers agree to the [Contributor Terms](https://osmfoundation.org/wiki/Licence/Contributor_Terms), and the [Privacy Policy](https://osmfoundation.org/wiki/Privacy_Policy) says edit information is "made available to everyone via the website", including the "login name of the author of every change". `[publisher]`
  - Camera operators and people whose vehicles pass the cameras were not asked. `[our note]`

### 1.4 Preprocessing

- **By the publisher:** OSM does not clean tags. Values are whatever mappers typed, which explains the spelling variants and free-text directions above. `[our note]` A formal cleaning process is `[not documented by the publisher]`.
- **By our fetch script:**
  - keeps nodes only;
  - copies selected tags into columns (`CSV_COLUMNS`);
  - stores every tag as JSON text in `all_tags`, so no tag is lost (173 distinct tag keys). `[code]`
- **By our loader:** `load_osm_locations()` in `src/cs418_flock_research/loaders/load_osm_locations.py` reads every row, guesses types from the whole file, and keeps `osm_id` as text. It does not clean or filter. `[code]`
- **Raw data:** the full OSM history is public at openstreetmap.org. Our raw file is gitignored, so it is not in the repo; a 100-row sample is in `data/processed/samples/flock_osm/`. `[our note]`

### 1.5 Uses

- **Already used for:**
  - `checkpoints/Narrative_Analysis/narrative.ipynb` (Findings 1–3);
  - `notebooks/eda_osm_flock_us_locations.ipynb`;
  - `notebooks/dev3.ipynb`. `[our note]`
- **Other uses by the publisher:** uses of these specific OSM points outside this project are `[not documented by the publisher]`.
- **Should not be used for:**
  - counting installed cameras or ranking places by "true" surveillance;
  - dating installations: `timestamp` is the last edit;
  - drawing conclusions about places with no mapped camera;
  - identifying or targeting individual mappers through `user`;
  - treating group-level associations as facts about individuals. `[our note]`

### 1.6 Distribution

- **How OSM is published:** OSM data is "licensed under the Open Data Commons Open Database License (ODbL)" ([Copyright](https://www.openstreetmap.org/copyright)). `[publisher]`
- **How this file is shared:** the full CSV is gitignored. The repo shares the fetch script, the loader, and a 100-row sample. `[our note]`
- License details and what our processed data must carry are in [Step 4b](#step-4b-access-and-reuse-fair).

### 1.7 Maintenance

- **Who maintains OSM:** volunteers edit continuously, and the OpenStreetMap Foundation runs the servers ([About OpenStreetMap](https://wiki.openstreetmap.org/wiki/About_OpenStreetMap)). `[publisher]`
- **Is it updated:** OSM changes every minute, so a rerun returns a different map. Our file is a frozen snapshot that we do not update. `[our note]`
- **How you would know:** compare a new pull by `osm_id` with this file (script §2 shows how). A changelog for these camera tags is `[not documented by the publisher]`.

## Step 2: Scope

- **Target population:** everyone or everything a question is about.
- **Access frame:** the source we can draw from, and what it covers.
- **Sample:** the rows we actually analyze.

### RQ1: Where are mapped Flock cameras, and how has the mapping grown over time?

- **Target population:** Flock Safety ALPR cameras in the United States. `[our note]`
- **Access frame:** OSM nodes matching the Flock tag rule inside the Overpass `ISO3166-1=US` area. `[our note]`
- **Sample:** 112,823 cameras after the narrative's Flock rule drops 7 rows whose `manufacturer` or `brand` also names another vendor. 112,619 of them fall in a 2024 tract (112,613 inside one, 6 assigned to the nearest), and all 112,823 fall in a county. `[code]` (script §3–5)
- **Who or what is missing:**
  - unmapped cameras;
  - cameras tagged only by `brand` or `operator`;
  - cameras drawn as ways.
  - We can claim where cameras are **mapped**, not where they are installed.
  - This file cannot measure growth: `timestamp` is the last edit. The growth question uses `first_tagged_date` from the history file. `[our note]`

### RQ2: Is mapped camera density associated with community characteristics?

- **Target population:** U.S. communities (census tracts) and their residents. `[our note]`
- **Access frame:** 84,415 2024 TIGER/Line tracts in the 50 states + DC, with ACS 2020–2024 5-year estimates. `[code]` (script §5–6)
- **Sample:** 82,913 tracts with population above 0 and an income estimate, holding 111,382 cameras; 47,912 of them have no camera. `[code]`
- **Who or what is missing:**
  - 204 cameras in Puerto Rico and the Virgin Islands (no tract shapes);
  - 14 tract shapes with no ACS row;
  - 793 tracts with population 0;
  - 1,502 tracts with no income estimate.
  - We cannot speak for territories or for individual residents. `[code]` `[our note]`

### RQ3: Is mapped camera density associated with political voting patterns?

- **Target population:** U.S. counties and their 2024 presidential vote. `[our note]`
- **Access frame:** 3,234 county units: 2024 counties, with Connecticut as its 8 old counties because the election file still reports them. These are joined to MIT Election Lab 2024 county returns. `[code]` (script §8–10)
- **Sample:** 3,115 counties with both a vote share and residents, holding 112,602 cameras; 865 of them have no camera. `[code]`
- **Who or what is missing:**
  - 119 county units have no vote row: Alaska 27 (its election rows use 38 district codes instead), Puerto Rico 78, and Hawaii 1, American Samoa 5, Guam 1, Northern Mariana Islands 4 and the Virgin Islands 3.
  - These units hold 221 cameras.
  - County vote is a rough proxy for the politics of the agencies and businesses that buy cameras. `[code]` `[our note]`

## Step 3: Codebook

Types are Polars types after loading. Placeholder counts use `""`, `"0"`, `-999`, `9999`,
`unknown`, `none`, `n/a` for text and 0/-999/9999 for numbers. `[code]` (script §1, §7)

### 3.1 Raw columns (as loaded by `load_osm_locations()`)

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `osm_type` | String | — | OSM element type | `node` only | 0 null | Overpass `out meta` |
| `osm_id` | String | — | OSM node ID, unique per row | 112,830 unique; 8–11 digits | 0 null | Overpass; kept as text by the loader |
| `lat` | Float64 | degrees (WGS 84) | Latitude | 17.6975512 to 61.613915 | 0 null; no 0 values | Overpass |
| `lon` | Float64 | degrees (WGS 84) | Longitude | −158.1236219 to −64.6324412 | 0 null; no 0 values | Overpass |
| `timestamp` | String (ISO 8601, UTC) | date-time | Time of the node's **last** edit | 2024-11-17T02:09:40Z to 2026-11-05T23:43:35Z | 0 null | Overpass `out meta` |
| `version` | Int64 | count | Number of saved versions | 1 to 17 (12 distinct) | 0 null | Overpass `out meta` |
| `changeset` | Int64 | — | ID of the upload that made the last edit | 159,227,566 to 191,536,650 (93,481 distinct) | 0 null | Overpass `out meta` |
| `user` | String | — | Display name of the last editor (**personal data**, see Step 5) | 24,227 distinct | 0 null | Overpass `out meta` |
| `man_made` | String | — | OSM tag | `surveillance` only | 0 null | tag |
| `surveillance_type` | String | — | `surveillance:type` tag | `ALPR` only | 0 null | tag |
| `manufacturer` | String | — | Camera maker as typed by mappers | 15 distinct (note 1) | 0 null | tag |
| `brand` | String | — | Brand tag | 4 values (note 1) | 112,001 null (99.3%) | tag |
| `operator` | String | — | Who runs the camera | 1,402 values plus null | 99,134 null (87.9%); 15 placeholder words | tag |
| `camera_direction` | String | — | `camera:direction` tag | letters (`N`, `E`…) or degrees; 262 values plus null | 111,059 null (98.4%); 20 placeholders | tag |
| `direction` | String | degrees or text | Facing direction | 102,326 single numbers, 8,275 ranges/lists/letters; 169 numbers outside 0–360 | 2,229 null (2.0%); 5,758 exactly `"0"` | tag |
| `camera_type` | String | — | Camera type | 40 values plus null; `fixed` 110,953 | 1,680 null (1.5%) | tag |
| `camera_mount` | String | — | What the camera is mounted on | 354 values plus null; `pole` 22,090 | 83,810 null (74.3%); 1 placeholder | tag |
| `camera_angle` | Int64 | degrees | Tilt angle | 10 to 340 | 112,800 null (100.0%) | tag |
| `surveillance_zone` | String | — | `surveillance:zone` tag | 84 values plus null; `traffic` 96,519 | 13,676 null (12.1%) | tag |
| `all_tags` | String (JSON) | — | Every OSM tag on the node | 173 distinct keys; parses for all rows | 0 null | `to_csv()` in the fetch script |

**Note 1.**
- `manufacturer` values:
  - `Flock Safety` 112,234
  - `Flock Group Inc.` 476
  - `Flock` 57
  - `Flock Safety Inc` 44
  - `FlockSafety` 4
  - `flock` 3
  - `Flock Safety;Motorola Solutions` 2
  - `Flock Surveillance` 2
  - `Flock Safety (installation in progress)` 2
  - `Motorola Solutions;Flock Safety`, `FLOCK SAFETY`, `Flock Safety;PlateSmart/CyclopsTchnlgs`, `FLock Safety`, `Flock Safety + Clear Creek District`, `Flock safety`: 1 each
- `brand` values: `Flock Safety` 816, `Flock` 11, `Motorola Solutions` 1, `Flock safety` 1. `[code]`

### 3.2 Derived columns (cameras)

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `manufacturer_status` | String | — | Flock rule result for the `manufacturer`/`brand` pair | `exact` 112,820, `annotated` 3, `ambiguous` 7 | never null (no null `manufacturer`) | `manufacturer_status()` in narrative.ipynb cell 2; same function in the stats script |
| `is_flock` | Boolean | — | Counted as a Flock camera (`status != "ambiguous"`) | true 112,823, false 7 | never null | `add_is_flock()`, narrative cell 2 |
| `county_geoid` | String | — | 5-digit 2024 county FIPS of the county containing the point | 2,280 distinct | 0 null (all inside a county) | `assign_polygons()` with `tl_2024_us_county.zip`, narrative cell 4 |
| `STATEFP` | String | — | 2-digit state FIPS from the county | 53 values (50 states, DC, `72`, `78`) | 0 null | same as above |
| `GEOID` (tract) | String | — | 11-digit 2024 tract GEOID | 35,327 distinct tracts | 204 null (Puerto Rico 146, Virgin Islands 58) | `assign_polygons()` with 2024 tract files, narrative cell 17 |
| `county_key` | String | — | County for the vote join: `county_geoid`, or the old county for Connecticut | 2,279 distinct with a camera | 0 null | narrative cell 23 |

Note: `first_tagged_date` (first mapped as a Flock camera) is **not** in this file; it comes from
`flock_us_historical_2026-10-30.csv` and is documented with that file. `[our note]`

### 3.3 Derived columns (tract table, 84,415 rows)

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `population` | Float64 | people | ACS B01003 total population | 0 to 44,364 | 14 null (shapes with no ACS row); 793 zeros | `read_acs()`, narrative cells 2 and 4 |
| `median_income` | Float64 | 2024 dollars | ACS B19013 median household income | 2,499 to 250,001; `250,000+` → 250,001 (553), `2,500-` → 2,499 (5) | 1,502 null (`-` in ACS, or no ACS row) | `acs_number()`, narrative cell 2 |
| `pct_poverty` | Float64 | percent | ACS S1701 share below poverty | 0 to 100 | 997 null; 221 real zeros | narrative cell 17 |
| `pct_nh_white` | Float64 | percent | B03002_003E / B03002_001E × 100 (non-Hispanic white share) | 0 to 100 | 14 null; 391 real zeros | narrative cell 17 |
| `cameras` | UInt32 | count | Flock cameras in the tract | 0 to 80 | never null; 49,088 tracts have 0 (a real value) | narrative cell 17 |
| `cameras_per_10k` | Float64 | per 10,000 residents | cameras / population × 10,000 | 0 to 10,000 (tiny-population tracts) | 807 null (population 0 or missing) | narrative cell 17 |
| `land_km2` | Float64 | km² | TIGER `ALAND` / 10⁶ | 0 to 221,506.37 | 320 zeros (water-only tracts) | narrative cell 17 |

### 3.4 Derived columns (county table, 3,234 units)

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `county_key` | String | — | 5-digit county FIPS; Connecticut uses the 8 old counties | 3,234 units | never null | narrative cell 23 |
| `rep_share` | Float64 | percent | 2024 Republican votes / (Republican + Democratic) × 100 | 6.69 to 96.47 across 3,153 vote counties | 119 units null (no vote row) | narrative cell 23 |
| `cameras` (county) | UInt32 | count | Flock cameras in the unit | sums to 112,823 | 0 when none (955 units) | narrative cell 23 |

## Step 4: Recipe

Slow step: none for this file; the Overpass query is one request (timeout 600 s). The frozen
snapshot is `data/raw/flock_osm/osm_flock_us_locations_2026-10-30.csv` (gitignored), so a
stranger can skip step 1 if they have the file. `[our note]`

1. **Download.**
   - What it does: queries Overpass for every node with the Flock tag rule in the U.S. and writes a CSV.
   - Code: `main()` → `build_query_nationwide()` → `run_query()` → `to_csv()` in `scripts/fetch_osm_alpr_cameras.py`.
   - Run: `uv run python scripts/fetch_osm_alpr_cameras.py --nationwide --flock-only --format csv`.
   - Rows: 112,830. `[code]`
   - **Not reproducible:** the query reads live OSM data, so a rerun returns a different map and a file named with that day's UTC date. We keep the dated raw file instead. `[our note]`
2. **Load.**
   - What it does: reads the CSV with `osm_id` as text and every type inferred from all rows.
   - Code: `load_osm_locations()` in `src/cs418_flock_research/loaders/load_osm_locations.py`.
   - Rows: 112,830 → 112,830. `[code]`
3. **Flock rule.**
   - What it does: drops 7 rows whose `manufacturer` or `brand` also names another vendor.
   - Code: `manufacturer_status()` / `add_is_flock()` in `narrative.ipynb` cell 2, applied in cell 4.
   - Rows: 112,830 → 112,823. `[code]` (script §3)
4. **Counties.**
   - What it does: puts each camera in the 2024 county that contains it, or the nearest within 0.03°.
   - Code: `assign_polygons()`, narrative cells 2 and 4.
   - Result: 112,823 inside, 0 nearest, 0 none. `[code]` (script §4)
5. **Tracts.**
   - What it does: the same method with the 51 tract files.
   - Code: narrative cell 17.
   - Result: 112,613 inside, 6 nearest, 204 with no tract (Puerto Rico and the Virgin Islands). `[code]` (script §5)
6. **ACS.**
   - What it does: reads four ACS tables as text, converts caps and `-`, inner-joins them on `GEOID` (85,382 rows), then left-joins them to the tract shapes.
   - Code: `read_acs()` / `acs_number()`, narrative cells 2, 4 and 17.
   - Rows: 84,415 → 84,415. `[code]` (script §6)
7. **Tract counts.**
   - What it does: counts cameras per tract, fills 0, computes `cameras_per_10k`, and keeps tracts with population above 0 and an income estimate.
   - Code: narrative cell 17.
   - Rows: 84,415 → 82,913 analysed. `[code]`
8. **Connecticut.**
   - What it does: rebuilds the 8 old counties from `tl_2017_09_tract.zip`, assigns the 640 Connecticut cameras and the 884 Connecticut tracts to them.
   - Code: narrative cell 23.
   - Result: 0 cameras unassigned. `[code]` (script §8)
9. **Votes.**
   - What it does:
     - keeps 2024 Republican and Democratic rows;
     - recodes county codes 46113 → 46102 and 36000 → 29095 (2 rows each);
     - uses `TOTAL` rows where a county has them, otherwise sums the vote modes;
     - computes `rep_share`.
   - Code: narrative cell 23.
   - Rows: 94,151 (all years) → 10,372 (2024, two parties) → 3,153 counties. `[code]` (script §9)
10. **County table.**
    - What it does: joins county camera counts, county ACS sums, and votes onto 3,234 county units, then keeps units with a vote and residents.
    - Code: narrative cell 23.
    - Rows: 3,234 → 3,115 analysed. `[code]` (script §10)

**Joins** (all numbers from script §5–10):

| Join | Key | Left rows | Right rows | Matched | Unmatched (left) | Unmatched (right) | Why unmatched |
|---|---|---|---|---|---|---|---|
| Cameras → 2024 counties (spatial) | point in polygon | 112,823 cameras | 3,235 counties | 112,823 | 0 | 955 counties with no camera (incl. other territories) | Real zeros: no mapped camera there |
| Cameras → 2024 tracts (spatial) | point in polygon, else nearest ≤ 0.03° | 112,823 cameras | 84,415 tracts | 112,619 (6 by nearest) | 204 | 49,088 tracts with no camera | Left: Puerto Rico (146) and Virgin Islands (58) have no tract file in the repo. Right: real zeros |
| Tract shapes → ACS | `GEOID` | 84,415 | 85,382 | 84,401 | 14 | 981 | Left: 14 tracts in Suffolk County, NY (`36103…`) have a 2024 shape but no ACS row; why is `[not documented by the publisher]`. Right: all 981 are Puerto Rico tracts (no shapes) |
| Camera tract counts → tract table | `GEOID` | 35,327 tracts with a camera | 84,415 | 35,327 | 0 | 49,088 | Real zeros |
| County camera counts → county units | `county_key` | 2,279 | 3,234 | 2,279 | 0 | 955 | Real zeros |
| County units → county ACS | `county_key` | 3,234 | 3,221 | 3,221 | 13 | 0 | American Samoa 5, Guam 1, Northern Mariana Islands 4, Virgin Islands 3: not in the ACS files |
| County units → 2024 votes | `county_key` | 3,234 | 3,153 | 3,115 | 119 | 38 | Left: Alaska 27, Hawaii 1, Puerto Rico 78, other territories 13. Right: Alaska reports by 38 district codes (`02001`–`02040`, `02099`), not boroughs |

**Rebuild commands** (clean checkout, from the project root):

```bash
uv sync
# put the raw files at the paths in README.md "Datasets", then:
uv run python scripts/datasheet_stats_osm_flock_us_locations.py   # prints every count above
uv run jupyter lab checkpoints/Narrative_Analysis/narrative.ipynb  # run all cells to build the analysis tables
```

The statistics script was run for this datasheet and printed the numbers above. `[code]`
Running the narrative notebook rewrites `figures/finding-*.png`. `[our note]`

## Step 4b: Access and reuse (FAIR)

| Dataset | Persistent link | Version or access date | Format | License or terms | May others reuse our processed data? |
|---|---|---|---|---|---|
| OSM Flock camera locations (primary) | No DOI. Source: [openstreetmap.org](https://www.openstreetmap.org); query in `build_query_nationwide()` | Pulled after 2026-11-05 23:43:35 UTC; file time 2026-11-06 00:10 UTC `[code]` | CSV | ODbL 1.0 ([copyright](https://www.openstreetmap.org/copyright), [license](https://opendatacommons.org/licenses/odbl/1-0/)) `[publisher]` | Yes, under ODbL: attribution and share-alike (below) `[our note]` |
| ACS 2020–2024 5-year (B01003, B19013, S1701, B03002) | [data.census.gov](https://data.census.gov) (no DOI) | Local file times 2026-11-05 02:14–02:34 UTC; the exact download date was not recorded `[code]` | CSV + metadata + notes | No license named on the ACS or open-data pages `[not documented by the publisher]`; the Census Bureau states "Copyright protection is not available for any work of the United States Government" ([TIGER/Line tech doc ch. 1](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2024/TGRSHP2024_TechDoc_Ch1.pdf)) `[publisher]` | Yes; cite the Census Bureau as the source ([citation guidance](https://www.census.gov/about/policies/citation.html)) `[publisher]` |
| TIGER/Line 2024 tracts and counties; 2017 Connecticut tracts | [www2.census.gov/geo/tiger](https://www2.census.gov/geo/tiger/) | 2024 and 2017 vintages; local file times 2026-11-05 `[code]` | Zipped shapefile | Public: "you are free to reproduce census materials as you see fit", with a request to "cite the Census Bureau as the source" ([tech doc ch. 1](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2024/TGRSHP2024_TechDoc_Ch1.pdf)) `[publisher]` | Yes, with a Census citation `[publisher]` |
| MIT Election Lab County Presidential Returns 2000–2024 | [doi:10.7910/DVN/VOQCHQ](https://doi.org/10.7910/DVN/VOQCHQ) | Dataverse version 20.0 (released 2026-02-25); file `version` column `20260225` `[publisher]` `[code]` | CSV + codebook | CC0 1.0 (Dataverse record) `[publisher]` | Yes; CC0 asks nothing, but we cite the DOI `[our note]` |

**What ODbL means for our processed data** ([ODbL summary](https://opendatacommons.org/licenses/odbl/summary/), [attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)):
- **Attribution:** "You must attribute any public use of the database". Figures and maps built from the data are "Produced Works" and need a notice such as "© OpenStreetMap contributors" or "Map data from OpenStreetMap", plus a statement that the data is under the ODbL. `[publisher]`
- **Share-alike:** an adapted database we publish (for example tract or county camera counts, or the sample CSV) is a Derivative Database and "must be only under the terms of" the ODbL. `[publisher]`
- **Keep open:** if we publish a restricted version, we must "also redistribute a version without such measures". `[publisher]`
- **In this repo:**
  - The README credits OpenStreetMap and the ODbL in its Sources section.
  - The repo has no LICENSE file.
  - `data/processed/samples/flock_osm/` has no ODbL notice next to the sample.
  - A notice there is still missing. `[our note]`

**FAIR checklist**
- **Findable:**
  - Done: this datasheet, the README Datasets table, and the dated file name.
  - Missing: no DOI for our snapshot, and the file name date is wrong by about a week. `[our note]`
- **Accessible:**
  - Done: the fetch script and the 100-row sample are public in the repo.
  - Missing: the full raw file is gitignored, so others must re-query and will get a newer map. `[our note]`
- **Interoperable:**
  - Done: plain CSV, OSM IDs, WGS 84 coordinates, and standard FIPS/GEOID keys for joins.
  - Missing: `direction` stays free text. `[our note]`
- **Reusable:**
  - Done: the licenses are recorded, and the recipe and statistics script are linked.
  - Missing: the ODbL notice for derived files, and the exact pull command and time. `[our note]`

## Step 5: People in the data

- **Who is in the data directly:**
  - `user` holds the OSM display names of 24,227 mappers. It is **personal data**.
  - Some display names may be real names. 11,877 mappers made the last edit on exactly one camera, and the most active made the last edit on 2,610.
  - OSM says the name of every change's author is public, and that "we do not support anonymous contributions" ([Privacy Policy](https://osmfoundation.org/wiki/Privacy_Policy)). `[publisher]` `[code]`
  - `operator` names organisations (police departments, retailers), not people. `[code]`
  - The 100-row sample in `data/processed/samples/flock_osm/` keeps the `user` column. It is not committed yet. Dropping `user` from samples and outputs would cost the analysis nothing. `[code]` `[our note]`
- **Who is in the data indirectly:**
  - People who live near, work near or drive past the cameras. Their plates are read by the cameras themselves, not by this dataset.
  - The camera owners. `[our note]`
- **Representation:**
  - Coverage follows volunteer effort. Places with active mappers are mapped more completely, and places without them can look camera-free.
  - Mapping is also driven by people who object to the cameras, so attention may cluster where controversy is. That is an observation about volunteer maps in general, not a measured fact about this file. `[our note]`
  - Joined Census categories have their own definitions. "Non-Hispanic white" is one ACS category, and the ACS is a survey estimate with margins of error. `[our note]`
- **Who could be mis-represented or harmed:**
  - **Communities:** ranking places by mapped cameras could label a community "more surveilled" when it is only better mapped, or "less surveilled" when it is not mapped at all.
  - **Police departments and businesses:** they could be judged on where volunteers mapped, not on where they installed cameras.
  - **Mappers:** they could be singled out through their usernames.
  - **Public camera locations:** a public map can help residents know where cameras are. It could also help someone avoid or damage them. We publish no new locations beyond what OSM already shows. `[our note]`
- **CARE lens:**
  - **Collective benefit:** the data supports public debate about surveillance. Results should be shared in a form residents can read, with the "mapped, not installed" caveat. `[our note]`
  - **Authority to control:**
    - Mappers control their own edits in OSM.
    - Communities near cameras had no say in the mapping or in our analysis.
    - Operators were not consulted. `[our note]`
  - **Responsibility:** we must keep the limitations next to every finding, credit OpenStreetMap, and not republish usernames. `[our note]`
  - **Ethics:** findings describe associations between mapped cameras and place characteristics. They are not evidence of intent or targeting by any group. `[our note]`
