# Datasheet: OSM Flock camera mapping history (`flock_us_historical_2026-10-30.csv`)

Datasheet for `data/raw/flock_osm/flock_us_historical_2026-10-30.csv`, the primary dataset
used for the timeline of Flock license plate reader cameras mapped in OpenStreetMap (OSM).
It follows `docs/REPRODUCIBLE_DATASHEET.md` (Checkpoint Four). The companion datasheet for
the locations file is [`DATASHEET_osm_flock_us_locations.md`](DATASHEET_osm_flock_us_locations.md).

**This file is built by our own script, not published as-is by OSM.** OSM publishes the
camera points and each point's version history; `scripts/fetch_osm_flock_history.py`
downloads both and **computes** a one-row summary per camera. Columns our script computes
are marked `[our note]` in the codebook.

**How to read the tags.** Every answer ends with one tag:
`[publisher]` from the publisher's documentation (linked), `[code]` printed by a script in
the repo, `[our note]` a decision or observation by our group, and
`[not documented by the publisher]` where the publisher says nothing.

**Statistics script.** Every number below is printed by
[`scripts/datasheet_stats_flock_us_historical.py`](../scripts/datasheet_stats_flock_us_historical.py).
Run it from the project root (about one minute; it writes no files):

```bash
uv run python scripts/datasheet_stats_flock_us_historical.py
```

Its section numbers (0–9) are given below as "script §N".

## Summary card

| Item | Value |
|---|---|
| What one row is | One OSM **node** (mapped point) tagged as a Flock ALPR camera, with a summary of its edit history: when the point was created, when it first matched the Flock tag rule, and when it was last edited. `[code]` |
| Rows × columns | 112,527 × 15 `[code]` (script §1) |
| Time span | Point creation 2007-09-05 to 2026-10-30; **first tagged as Flock 2024-11-03 to 2026-10-30**; last edit 2024-11-17 to 2026-10-30. All are mapping dates, not install dates. `[code]` |
| Source and maintainer | OpenStreetMap contributors (Overpass API for the current points, OSM API v0.6 for each point's history); summary columns computed by our script. `[publisher]` `[our note]` |
| License | Open Database License (ODbL) 1.0, © OpenStreetMap contributors. `[publisher]` |
| Snapshot date (from the file, not only its name) | The newest date in all three date columns is 2026-10-30 19:32:28 UTC, which matches the name. No row is dated after 2026-10-30. `[code]` |
| Safe for | Describing how the OSM map of Flock cameras grew, in cameras and in places reached, from November 2024 on. `[our note]` |
| Not safe for | Dating installations, describing mapping before November 2024, or counting cameras deleted from OSM. `[our note]` |
| Biggest limitation | `first_tagged_date` is when a point first matched our tag rule, so the series cannot start before 2024-11-03 even though 657 points are older. The growth it shows is volunteer mapping activity, not deployment. `[code]` `[our note]` |

Sections: [1. Datasheet](#step-1-datasheet) · [2. Scope](#step-2-scope) ·
[3. Codebook](#step-3-codebook) · [4. Recipe](#step-4-recipe) ·
[4b. Access and reuse](#step-4b-access-and-reuse-fair) · [5. People in the data](#step-5-people-in-the-data)

## Step 1: Datasheet

### 1.1 Motivation

- **Why OSM exists:** OSM is "a free, editable map of the whole world that is being built by volunteers" ([About OpenStreetMap](https://wiki.openstreetmap.org/wiki/About_OpenStreetMap)). `[publisher]`
- **Why OSM keeps history:** OSM stores "the tags, and also a full editing history of every element" ([Elements](https://wiki.openstreetmap.org/wiki/Elements)). `[publisher]`
- **Why this file was created:** our group needed a date for when each camera entered the map, to answer how mapping grew (research question 1). The locations file only has the last edit. `[our note]`
- **Who created it:** OSM contributors created the points and versions. Our group wrote and ran `scripts/fetch_osm_flock_history.py` to build the summary. `[our note]`
- **Who funds it:** "The OpenStreetMap Foundation is an organization that performs fund-raising", and it "does not control the project or 'own' the OSM data" ([About OpenStreetMap](https://wiki.openstreetmap.org/wiki/About_OpenStreetMap)). `[publisher]` Our download had no funding. `[our note]`

### 1.2 Composition

- **One row is one camera:**
  - All 112,527 `osm_id` values are unique; 0 rows repeat an ID, and 0 rows are fully identical.
  - So the file holds no per-version or per-edit rows. Each camera's history is summarised into one row. `[code]` (script §1)
- **Rows and columns:** 112,527 rows × 15 columns. `[code]`
- **Sample or population:** every node that matched the Flock tag rule in the Overpass pull, not a random sample. It is not every Flock camera in the U.S., and it has no cameras deleted from OSM before the pull. `[our note]`
- **The tag rule:**
  - A node counts when `man_made=surveillance`, `surveillance:type=ALPR` (any case), and `manufacturer` contains "flock" (any case).
  - The script applies it twice: in the Overpass query, and to each old version through `is_flock_alpr()`.
  - It leaves out cameras tagged only by `brand` or `operator`, ALPRs with no `manufacturer`, and cameras drawn as ways. `[code]`
- **History lookups:** `history_ok` is true for all 112,527 rows, so no lookup failed and this is the final file, not an `_INCOMPLETE` one. `[code]`
- **Same location:** 1,865 rows share exact coordinates with another row, at 880 spots (at most 6 rows at one spot). Each has its own ID. `[code]`
- **Outside the 50 states + DC:** 199 cameras are in Puerto Rico (141) and the U.S. Virgin Islands (58). `[code]` (script §7)
- **Missing values:** only `operator` has nulls: 98,711 rows (87.7%), plus 15 placeholder words (`unknown`, `none` or similar). Every date and version column is complete. `[code]`
- **Spelling variants:** `manufacturer` has 14 distinct values for the same company. `[code]`
- **Never-edited points:** 88,391 rows (78.6%) are version 1. For these the three dates are copied, not looked up (see 1.3). `[code]`
- **Points that became Flock cameras later:**
  - 3,876 cameras were tagged as Flock after their point was created (`first_tagged_version` above 1). These are existing points later changed into Flock cameras.
  - No camera is tagged before its creation or after its last edit. `[code]` (script §4)
- **Delay from creation to Flock tag (those 3,876):**
  - Median 154.8 days; middle half 4.9 to 429.3 days; longest 6,943.5 days (19.0 years).
  - The distribution has two peaks: 720 were tagged within a day of creation, and 1,321 between 200 and 600 days later.
  - 1,268 waited more than a year. `[code]`
- **Start of the series:**
  - 657 points were created before 2024-11-01, all of them first tagged as Flock in a later version.
  - No camera has a `first_tagged_date` before 2024-11-03 or a `last_edit` before 2024-11-17. See [1.3](#13-collection-process) for what this means. `[code]` (script §3)
- **One gap in an early history:** one camera's history starts at version 3, not 1, so its `first_insert_date` may be later than its real creation. `[code]`
  - OSM's Data Working Group can redact versions, and "Changesets that have been redacted are still listed in the history, but object information is absent" ([Data Working Group](https://wiki.openstreetmap.org/wiki/Data_Working_Group)). Whether that happened here is `[not documented by the publisher]`.
- **Relationship to the locations file** (`osm_flock_us_locations_2026-10-30.csv`), compared by `osm_id` (script §5):
  - **In both:** 112,124 cameras. `[code]`
  - **History only:** 403 cameras (first tagged 2024: 1, 2025: 112, 2026: 290). They were on the map at the history pull but not at the later locations pull: deleted, retagged off the rule, or replaced. Which one is not recorded. `[code]` `[our note]`
  - **Locations only:** 706 cameras, all edited after this file's cut-off (2026-10-30 19:32:28 UTC). The locations file's newest edit is 2026-11-05 23:43:35 UTC, so the two pulls are about a week apart. `[code]`
  - **Changed between pulls:** of the shared cameras, 136 have a newer version in the locations file (0 older), and 70 moved. `[code]`

### 1.3 Collection process

- **Step A, current points:**
  - `download_current_cameras()` sends one Overpass query to `https://overpass-api.de/api/interpreter` for nodes matching the tag rule in `area["ISO3166-1"="US"]`, with `out meta`.
  - It checks for duplicate IDs and null IDs/versions/coordinates (`validate_snapshot()`), and compares the row count with an expected 111,128 (±10%).
  - It caches the result as `flock_us_current.csv`, and later runs reuse that cache. `[code]`
  - Overpass "is a read-only API that serves up custom selected parts of the OSM map data", and "It can take a couple of minutes for changes to the database to show up" ([Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)). `[publisher]`
- **Step B, history per point:**
  - **Version-1 points:** the script makes **no API call**. It copies the snapshot `timestamp` into `first_insert_date` and `first_tagged_date`, sets both version columns to 1, and copies `changeset` into `first_tagged_changeset`.
    - This is correct: a version-1 point has only one version.
    - The file confirms it: for all 88,391 version-1 rows, the three dates are equal, both version columns are 1, and `first_tagged_changeset` equals `changeset`. `[code]` (script §2)
  - **Edited points (24,136 rows):** `get_node_history()` calls `https://api.openstreetmap.org/api/0.6/node/<id>/history.json`.
    - `extract_history()` takes `first_insert_*` from the earliest returned version.
    - It takes `first_tagged_*` from the earliest **visible** version that passes `is_flock_alpr()`.
    - The OSM wiki lists the history call among the calls that support JSON ([API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6)). `[code]` `[publisher]`
    - It waits 1 second after each request (`REQUEST_DELAY`) and retries status 429/500/502/503/504/509 up to 5 times.
    - It saves progress to `flock_us_history_checkpoint.jsonl`, so an interrupted run can resume. `[code]`
- **Step C, export:**
  - `build_final_dataset()` joins the snapshot with the history results.
  - If any history is missing (`report_completeness()`), it writes `..._INCOMPLETE.csv` instead of the final name and lists the failures in `flock_us_history_unresolved.csv`.
  - Our file has the final name, `history_ok` is true for every row, and no `_INCOMPLETE` file is present. `[code]` (script §0–1)
- **Why the series starts in November 2024:**
  - `first_tagged_date` is the first version that matched **all three** tags, including a `manufacturer` containing "Flock".
  - A point mapped earlier with other tags, for example only `brand`, a different `surveillance:type`, or no `manufacturer`, counts only from the version where the rule first holds.
  - The 657 older points became Flock cameras gradually, not in one edit: their first-tagged months spread over all 24 months, with only 7 in November 2024. `[code]`
  - Why no surviving point matched the rule before 2024-11-03, and none was last edited before 2024-11-17, cannot be told from this file: it keeps no old tags. It could reflect a change in tagging practice or older points being deleted and re-added. `[our note]`
  - So the timeline shows mapping **under this rule**, and nothing about mapping before November 2024. `[our note]`
- **Time frame:**
  - The newest date in the file, 2026-10-30 19:32:28 UTC, is the snapshot cut-off. On that day 64 cameras were last edited. `[code]`
  - The history lookups ran after that. The file's local time is 2026-11-03 23:09 UTC, which fits the hours-long API step, but the run log was not kept. `[code]` `[our note]`
- **Slow step:** one API call per edited point. With 24,136 edited points and a 1-second pause after each, Step B spends at least 24,136 seconds (about 6.7 hours) just waiting, plus the request time. `[code]` `[our note]`
- **API rules:**
  - The OSM API policy asks for a "Valid User-Agent identifying application and version" and says "Large or frequent data users must use the download service" ([API usage policy](https://operations.osmfoundation.org/policies/api/)). `[publisher]`
  - Whether about 24,000 history calls count as "large" use is `[not documented by the publisher]`.
- **Consent:**
  - Mappers agree to the [Contributor Terms](https://osmfoundation.org/wiki/Licence/Contributor_Terms).
  - The [Privacy Policy](https://osmfoundation.org/wiki/Privacy_Policy) says the "login name of the author of every change" is made "available to everyone". `[publisher]`
  - Camera operators and people whose vehicles pass the cameras were not asked. `[our note]`

### 1.4 Preprocessing

- **By OSM:** none. Tags are what mappers typed. A formal cleaning process is `[not documented by the publisher]`.
- **By our fetch script** (all `[our note]`):
  - computes the five `first_*` columns and `history_ok`;
  - renames the snapshot's `id`/`timestamp` to `osm_id`/`last_edit`;
  - parses dates as UTC and writes them as `YYYY-MM-DDTHH:MM:SS.ffffff+0000`;
  - keeps only `manufacturer` and `operator` among the tags (no `brand`, no `all_tags`).
- **By our loader:** `load_osm_history()` in `src/cs418_flock_research/loaders/load_osm_history.py` reads every row, keeps `osm_id` as text and leaves dates as text. It does not clean or filter. `[code]`
- **Raw data:** the full OSM history stays public at openstreetmap.org. Our cache, checkpoint and raw file are gitignored; only the final CSV survives locally (script §0), and a sample is in `data/processed/samples/flock_osm/`. `[code]` `[our note]`

### 1.5 Uses

- **Already used for:**
  - Finding One in `checkpoints/Narrative_Analysis/narrative.ipynb`: monthly growth, county spread, bulk-upload and retag checks;
  - `notebooks/eda_flock_us_historical.ipynb`;
  - `notebooks/dev3.ipynb`. `[our note]`
- **Should not be used for:**
  - install dates, or a "deployment curve";
  - mapping before November 2024;
  - counting cameras removed from OSM;
  - treating monthly spikes as installs (they are mapping activity);
  - identifying or ranking individual mappers. `[our note]`

### 1.6 Distribution

- OSM data is "licensed under the Open Data Commons Open Database License (ODbL)" ([Copyright](https://www.openstreetmap.org/copyright)). `[publisher]`
- This file is gitignored. The repo shares the fetch script, the loader, and a sample. `[our note]`
- License details are in [Step 4b](#step-4b-access-and-reuse-fair).

### 1.7 Maintenance

- **OSM:** maintained by volunteers, with servers run by the OpenStreetMap Foundation. `[publisher]`
- **This file:** a frozen snapshot that we do not update. `[our note]`
  - A rerun downloads a new snapshot and names the file with that day's UTC date. That date is computed at import time (`SNAPSHOT_DATE`), so a rerun never overwrites this file.
  - A same-day rerun would overwrite that day's output (logged as BUG-003 in `docs/BUGS.md`). `[code]`
- **How you would know of changes:** compare a new file by `osm_id` (script §5 shows how). `[our note]`

## Step 2: Scope

- **Target population:** everyone or everything a question is about.
- **Access frame:** the source we can draw from, and what it covers.
- **Sample:** the rows we actually analyze.

### RQ1: Where are mapped Flock cameras, and how has the mapping grown over time?

- **Target population:** Flock ALPR cameras in the U.S. and the history of their appearance on the map. `[our note]`
- **Access frame:** OSM nodes matching the tag rule at the 2026-10-30 pull, with their version histories. `[our note]`
- **Sample:** 112,522 cameras after the narrative's Flock rule drops 5 rows whose `manufacturer` names a second vendor.
  - All 112,522 fall in a 2024 county, across 2,279 counties.
  - 68,899 were first tagged in 2026. `[code]` (script §6–7)
- **Who or what is missing:**
  - cameras deleted from OSM before the pull;
  - cameras that never matched the rule;
  - all mapping before 2024-11-03.
  - We can describe growth of the **current map** under this rule, not deployment, and not the map as it looked in the past. `[code]` `[our note]`

### RQ2: Is mapped camera density associated with community characteristics?

- **Target population:** U.S. census tracts and their residents. `[our note]`
- **Access frame:** 84,415 2024 TIGER/Line tracts (50 states + DC) with ACS 2020–2024 estimates. `[code]` (script §8)
- **Sample:** 82,913 tracts with residents and an income estimate, holding 111,088 of these cameras; 47,901 of the tracts have none.
  - The narrative uses the locations file for this question; this file supports period splits by `first_tagged_date` (as in the EDA notebook). `[code]` `[our note]`
- **Who or what is missing:**
  - 199 cameras in Puerto Rico and the Virgin Islands (no tract shapes);
  - 14 tracts in Suffolk County, NY with no ACS row;
  - tracts with no residents or no income estimate. `[code]`

### RQ3: Is mapped camera density associated with political voting patterns?

- **Target population:** U.S. counties and their 2024 presidential vote. `[our note]`
- **Access frame:** 3,234 county units (2024 counties, with Connecticut's 8 old counties), joined to MIT Election Lab 2024 returns. `[code]` (script §9)
- **Sample:** 3,115 county units with a vote. The narrative answers this question with the locations file; this file is not joined to votes in any analysis yet. `[code]` `[our note]`
- **Who or what is missing:**
  - 119 county units with no vote row: Alaska 27, Hawaii 1, Puerto Rico 78, and other territories 13.
  - These units hold 216 of these cameras.
  - County vote is a rough proxy for the buyers' politics. `[code]` `[our note]`

## Step 3: Codebook

Types are Polars types after `load_osm_history()`. Placeholder counts use `""`, `"0"`, `-999`,
`9999`, `unknown`, `none`, `n/a` for text and 0/-999/9999 for numbers. `[code]` (script §1, §6)

### 3.1 Columns in the file

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `osm_id` | String | — | OSM node ID, one per row | 112,527 unique; 8–11 digits | 0 null | OSM (Overpass); text by our loader |
| `lat` | Float64 | degrees (WGS 84) | Latitude | 17.6975512 to 61.613915 | 0 null; no 0 values | OSM (Overpass) |
| `lon` | Float64 | degrees (WGS 84) | Longitude | −158.1236219 to −64.6324412 | 0 null; no 0 values | OSM (Overpass) |
| `manufacturer` | String | — | Maker tag, current version | 14 distinct (note 1) | 0 null | OSM tag |
| `operator` | String | — | Operator tag, current version | 1,403 values plus null | 98,711 null (87.7%); 15 placeholder words | OSM tag |
| `version` | Int64 | count | Current version number | 1 to 17 (note 2) | 0 null | OSM `out meta` |
| `last_edit` | String (date-time, UTC) | date-time | Time of the last edit ("Time of the last modification", [Elements](https://wiki.openstreetmap.org/wiki/Elements)) | 2024-11-17 02:09:40 to 2026-10-30 19:32:28 | 0 null | OSM `timestamp`, renamed by our script |
| `changeset` | Int64 | — | Upload that made the last edit (links to a mapper, Step 5) | 159,227,566 to 191,252,765 (93,061 distinct) | 0 null | OSM `out meta` |
| `user` | String | — | Display name of the last editor (**personal data**) | 24,192 distinct | 0 null | OSM `out meta` |
| `history_ok` | Boolean | — | A history result exists for this row | `true` for all 112,527 | 0 null | **computed by our script** `[our note]` |
| `first_insert_date` | String (date-time, UTC) | date-time | When the point was created (earliest returned version) | 2007-09-05 12:27:31 to 2026-10-30 19:32:28 | 0 null | **computed by our script** `[our note]` |
| `first_insert_version` | Int64 | count | Version number of that earliest version | 1 (112,526 rows) or 3 (1 row) | 0 null | **computed by our script** `[our note]` |
| `first_tagged_date` | String (date-time, UTC) | date-time | First version matching the Flock tag rule | 2024-11-03 03:04:15 to 2026-10-30 19:32:28 | 0 null | **computed by our script** `[our note]` |
| `first_tagged_version` | Int64 | count | Version number of that version | 1 to 16 (note 2) | 0 null | **computed by our script** `[our note]` |
| `first_tagged_changeset` | Int64 | — | Upload that first made it a Flock camera | 158,683,616 to 191,252,765 (94,928 distinct) | 0 null | **computed by our script** `[our note]` |

**Note 1.**
- `manufacturer` values:
  - `Flock Safety` 111,931
  - `Flock Group Inc.` 477
  - `Flock` 57
  - `Flock Safety Inc` 44
  - `FlockSafety` 4
  - `flock` 3
  - `Flock Safety;Motorola Solutions` 2
  - `Flock Surveillance` 2
  - `Flock Safety (installation in progress)` 2
  - `FLOCK SAFETY`, `Flock Safety;PlateSmart/CyclopsTchnlgs`, `FLock Safety`, `Flock Safety + Clear Creek District`, `Flock safety`: 1 each. `[code]`

**Note 2.**
- `version`: 1 = 88,391; 2 = 17,553; 3 = 4,703; 4 = 1,303; 5 = 401; 6 = 113; 7 = 35; 8 = 12; 9 = 7; 10 = 6; 12 = 2; 17 = 1.
- `first_tagged_version`: 1 = 108,651; 2 = 2,889; 3 = 717; 4 = 204; 5 = 44; 6 = 16; 7 = 3; 8 = 2; 16 = 1. `[code]`

### 3.2 Derived columns (narrative cells 6 and 11; same code in the stats script)

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|
| `inserted`, `tagged`, `edited` | Datetime (UTC) | date-time | Parsed `first_insert_date`, `first_tagged_date`, `last_edit` | as in 3.1 | 0 unparsed | `str.to_datetime("%Y-%m-%dT%H:%M:%S%.f%z")`, narrative cell 6 (it overwrites the original names) |
| `manufacturer_status` | String | — | Narrative Flock rule result | `exact` 112,519, `annotated` 3, `ambiguous` 5 | never null | `manufacturer_status()`, narrative cell 2 |
| `month` | Date | month | First day of the first-tagged month | 2024-11-01 to 2026-10-01 (24 months, none empty) | never null | `dt.truncate("1mo")`, narrative cell 6 |
| `retag` | Boolean | — | `first_tagged_version > 1` (an existing point that became a Flock camera) | true 3,876 | never null | narrative cell 6 |
| `changeset_size` | UInt32 | cameras | Cameras in this file sharing the same `first_tagged_changeset` | 1 to 430 | never null | narrative cell 6 |
| `bulk` | Boolean | — | `changeset_size >= 50` (bulk upload) | true 1,234, in 7 months (note 3) | never null | narrative cell 6 |
| `county_geoid` | String | — | 2024 county containing the point | 2,279 distinct | 0 null | `assign_polygons()`, narrative cell 11 |
| `STATEFP` | String | — | State FIPS from the county | 53 values (50 states, DC, `72`, `78`) | 0 null | stats script §7 (narrative cell 4 method) |
| `GEOID` (tract) | String | — | 2024 tract containing the point (or nearest within 0.03°) | 35,337 distinct | 199 null (Puerto Rico 141, Virgin Islands 58) | stats script §8 (narrative cell 17 method) |
| `period` | String | — | Before 2026 vs. 2026 by `first_tagged_date` | `Nov 2024 - Dec 2025`, `Jan - Oct 2026` | never null | `notebooks/eda_flock_us_historical.ipynb` join setup cell |
| `cameras` (tract) | UInt32 | count | Cameras per tract, zero-camera tracts kept | 0 to 76; 49,078 tracts have 0 | never null | stats script §8 |
| `cameras_per_10k` (tract) | Float64 | per 10,000 residents | cameras / population × 10,000 | 0 to 10,000 | 807 null (no residents or no ACS row) | stats script §8 |

**Note 3.** Months with a changeset of 50 or more cameras:
- 2024-11: 430
- 2025-02: 291
- 2025-05: 59
- 2025-06: 101
- 2025-09: 178
- 2025-10: 69
- 2026-04: 106 `[code]`

The ACS columns (`population`, `median_income`, `pct_poverty`, `pct_nh_white`) and the county
`rep_share` are the same as in the locations datasheet's codebook (3.3–3.4), built by the same code. `[our note]`

## Step 4: Recipe

**Slow step:** Step 1b (one OSM API call per edited point; the pauses alone add up to about 6.7 hours). The frozen
file is `data/raw/flock_osm/flock_us_historical_2026-10-30.csv` (gitignored); with it, skip
step 1 entirely. `[our note]`

1. **Build the file.**
   - Code: `main()` in `scripts/fetch_osm_flock_history.py`. Run: `uv run python scripts/fetch_osm_flock_history.py` (set the `OSM_CONTACT` environment variable first).
   - **1a. Snapshot:** `download_current_cameras()` → `validate_snapshot()`.
   - **1b. History:** `process_cameras()` → `extract_history()` for edited points, or the copy shortcut for version 1.
   - **1c. Export:** `report_completeness()` → `build_final_dataset()`. It writes `_INCOMPLETE.csv` if any lookup failed.
   - Rows: 112,527 in the final file, `history_ok` all true. `[code]`
   - **Not reproducible:** both APIs serve live data, so a rerun gives a newer map, newer histories and a new file name. We keep the dated file. `[our note]`
2. **Load.**
   - What it does: reads the file with `osm_id` as text and dates as text.
   - Code: `load_osm_history()`.
   - Rows: 112,527 → 112,527. `[code]`
3. **Parse dates and apply the Flock rule.**
   - What it does: drops 5 rows whose `manufacturer` names a second vendor.
   - Code: narrative cell 6 with `add_is_flock()` from cell 2.
   - Rows: 112,527 → 112,522. `[code]` (script §6)
4. **Cohort columns.**
   - What it does: adds `month`, `retag`, `changeset_size` and `bulk`.
   - Code: narrative cell 6.
   - Rows: 112,522 → 112,522. `[code]`
5. **Counties.**
   - What it does: puts each camera in a 2024 county, or the nearest within 0.03°.
   - Code: `assign_polygons()`, narrative cell 11.
   - Result: 112,522 inside, 0 nearest, 0 none. `[code]` (script §7)
6. **Tracts and ACS.**
   - What it does: the same method with the 51 tract files, then a left join of the ACS tables on `GEOID`.
   - Code: method from narrative cell 17; for this file, the stats script §8 and the EDA notebook.
   - Result: 112,317 inside, 6 nearest, 199 none. `[code]`
7. **County units and votes.**
   - What it does: rebuilds Connecticut's old counties, recodes 2 county codes, and keeps `TOTAL` vote rows.
   - Code: method from narrative cell 23; for this file, the stats script §9.
   - Rows: 3,234 county units → 3,115 with a vote. `[code]`

**Joins** (all numbers from the stats script):

| Join | Key | Left rows | Right rows | Matched | Unmatched (left) | Unmatched (right) | Why unmatched |
|---|---|---|---|---|---|---|---|
| History → locations file (comparison only) | `osm_id` | 112,527 | 112,830 | 112,124 | 403 | 706 | Separate pulls about a week apart: 706 were edited after this file's cut-off; 403 left the map between pulls |
| Cameras → 2024 counties (spatial) | point in polygon | 112,522 | 3,235 | 112,522 | 0 | 956 counties with no camera | Real zeros |
| Cameras → 2024 tracts (spatial) | point in polygon, else nearest ≤ 0.03° | 112,522 | 84,415 | 112,323 (6 by nearest) | 199 | 49,078 tracts with no camera | Left: Puerto Rico (141) and Virgin Islands (58) have no tract file. Right: real zeros |
| Tract shapes → ACS | `GEOID` | 84,415 | 85,382 | 84,401 | 14 | 981 | Left: 14 Suffolk County, NY (`36103`) tracts have a shape but no ACS row (cause `[not documented by the publisher]`). Right: all 981 are Puerto Rico tracts |
| County camera counts → county units | `county_key` | 2,278 | 3,234 | 2,278 | 0 | 956 | Real zeros |
| County units → 2024 votes | `county_key` | 3,234 | 3,153 | 3,115 | 119 | 38 | Left: Alaska 27, Hawaii 1, Puerto Rico 78, American Samoa 5, Guam 1, Northern Mariana Islands 4, Virgin Islands 3. Right: Alaska reports by 38 district codes |

**Rebuild commands** (clean checkout, from the project root):

```bash
uv sync
# put the raw files at the paths in README.md "Datasets", then:
uv run python scripts/datasheet_stats_flock_us_historical.py        # prints every count above
uv run jupyter lab checkpoints/Narrative_Analysis/narrative.ipynb    # Finding One uses this file
```

The statistics script was run for this datasheet. `[code]`

## Step 4b: Access and reuse (FAIR)

| Dataset | Persistent link | Version or access date | Format | License or terms | May others reuse our processed data? |
|---|---|---|---|---|---|
| OSM Flock camera history (primary, built by our script) | No DOI. Sources: [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API), [OSM API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6) history calls; recipe in `scripts/fetch_osm_flock_history.py` | Snapshot cut-off 2026-10-30 19:32:28 UTC; local file time 2026-11-03 23:09 UTC `[code]` | CSV | ODbL 1.0 ([copyright](https://www.openstreetmap.org/copyright), [license](https://opendatacommons.org/licenses/odbl/1-0/)) `[publisher]` | Yes, under ODbL: attribution and share-alike (below) `[our note]` |
| ACS 2020–2024 5-year (B01003, B19013, S1701, B03002) | [data.census.gov](https://data.census.gov) | Local file times 2026-11-05; download date not recorded `[code]` | CSV | No license named on the ACS pages `[not documented by the publisher]`; "Copyright protection is not available for any work of the United States Government" ([TIGER/Line tech doc ch. 1](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2024/TGRSHP2024_TechDoc_Ch1.pdf)) `[publisher]` | Yes; cite the Census Bureau ([citation guidance](https://www.census.gov/about/policies/citation.html)) `[publisher]` |
| TIGER/Line 2024 tracts and counties; 2017 Connecticut tracts | [www2.census.gov/geo/tiger](https://www2.census.gov/geo/tiger/) | 2024 and 2017 vintages `[code]` | Zipped shapefile | "you are free to reproduce census materials as you see fit", with a request to cite the Census Bureau ([tech doc ch. 1](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2024/TGRSHP2024_TechDoc_Ch1.pdf)) `[publisher]` | Yes, with a Census citation `[publisher]` |
| MIT Election Lab County Presidential Returns 2000–2024 | [doi:10.7910/DVN/VOQCHQ](https://doi.org/10.7910/DVN/VOQCHQ) | Dataverse version 20.0, released 2026-02-25 `[publisher]` | CSV + codebook | CC0 1.0 `[publisher]` | Yes; we cite the DOI `[our note]` |

**What ODbL means for our processed data** ([ODbL summary](https://opendatacommons.org/licenses/odbl/summary/), [attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)):
- **This file is a Derivative Database:** it is built from OSM data. If we publish it, or anything built from it such as monthly counts or the sample, it "must be only under the terms of" the ODbL. `[publisher]`
- **Attribution:** "You must attribute any public use of the database". Figures such as `figures/finding-one.png` need "© OpenStreetMap contributors" (or "Map data from OpenStreetMap") and a statement that the data is under the ODbL. The narrative's figure caption credits "OpenStreetMap contributors". `[publisher]` `[code]`
- **Keep open:** a restricted copy must come with "a version without such measures". `[publisher]`
- **Gap:** the repo has no LICENSE file and no ODbL notice next to the sample in `data/processed/samples/flock_osm/`. `[our note]`

**FAIR checklist**
- **Findable:**
  - Done: this datasheet and the dated file name, which matches the cut-off.
  - Missing: no DOI. `[our note]`
- **Accessible:**
  - Done: the fetch script and the sample are in the repo.
  - Missing: the full file is gitignored, and rebuilding it takes hours and gives a newer map. `[our note]`
- **Interoperable:**
  - Done: CSV, ISO 8601 UTC dates, and OSM IDs that join to the locations file and to openstreetmap.org. `[our note]`
- **Reusable:**
  - Done: the method is documented in the script's docstring and in this datasheet.
  - Missing: the run log (exact run time and the expected-count check result) was not kept, and the ODbL notice for derived files. `[our note]`

## Step 5: People in the data

- **Who is in the data directly:**
  - `user` holds the display names of 24,192 mappers who made each camera's last edit. It is **personal data**.
  - 11,867 of them appear on exactly one row, and the most active on 2,612. `[code]`
  - `changeset` and `first_tagged_changeset` are also personal data in effect. Each changeset ID can be looked up on openstreetmap.org to show who made it and when, including who **first** mapped each camera, which the file does not store by name. `[our note]`
  - OSM's Privacy Policy says the "user id and login name of the author of every change" is public, and "we do not support anonymous contributions" ([Privacy Policy](https://osmfoundation.org/wiki/Privacy_Policy)). `[publisher]`
  - Combined with dates, these columns show when and where a mapper was active. Dropping `user` and the changeset columns from published outputs would not affect the analysis. `[our note]`
- **Who is in the data indirectly:**
  - people living near or driving past the cameras;
  - the camera owners named in `operator` (police departments, retailers). `[our note]`
- **Representation:**
  - **Volunteer effort:** the timeline follows volunteer effort, not deployment.
    - Bursts can come from a few active people or a campaign.
    - Most cameras came in small uploads: only 1,234 cameras came in changesets of 50 or more. `[code]`
  - **Who maps:** places with active mappers are mapped earlier and more completely. People who map in order to document or oppose cameras may be over-represented among contributors. That is a general feature of volunteer maps, not a measured fact about this file. `[our note]`
  - **Survivorship:** the file shows only cameras still on the map at the pull, so places where cameras were removed look like they never had any. `[our note]`
- **Who could be mis-represented or harmed:**
  - A community could be shown as "surveilled sooner" only because it was mapped sooner.
  - Mappers could be singled out through `user` or changeset IDs.
  - Public camera locations help residents know where cameras are, but could also help someone avoid or damage them. We add no locations beyond what OSM already shows.
  - Agencies and businesses could be judged on mapping dates that are not their installation dates. `[our note]`
- **CARE lens:**
  - **Collective benefit:** a public timeline of mapping supports public discussion, if it carries the "mapping, not installation" warning. `[our note]`
  - **Authority to control:**
    - Mappers control their own edits.
    - Residents and operators had no say in the mapping or in our use of it. `[our note]`
  - **Responsibility:** we must credit OpenStreetMap under the ODbL, avoid republishing usernames and changeset IDs, and keep the November 2024 start limit next to every timeline. `[our note]`
  - **Ethics:** the timeline describes mapping activity and associations. It is not evidence of when or why any group installed cameras. `[our note]`
