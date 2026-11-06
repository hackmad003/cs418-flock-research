# Data Documentation (Individual EDA Datasets)

**Prepared by:** Alexandra Golley  
**Project:** CS418 Flock Safety ALPR camera research  
**Files documented:** `data/raw/alpr_cameras.csv`, `data/raw/chicago_crime_2017.csv`, `data/raw/chicago_crime_2026.csv`  

## Dataset overview

| Local file | Unit of observation | Rows × columns | Missing values observed |
|---|---|---:|---|
| `alpr_cameras.csv` | One mapped ALPR camera/location record | 101,085 × 4 | No nulls in the four columns |
| `chicago_crime_2017.csv` | One reported crime record | 269,349 × 22 | Missing values in location/geography fields |
| `chicago_crime_2026.csv` | One reported crime record | 167,474 × 22 | Missing values in location/geography fields |

The row counts and missing-value counts above are for the local CSV snapshots inspected in October 2026. They are not guaranteed to match the live source websites, which may change.

# 1. `alpr_cameras.csv`

## 1.1 Motivation

The file contains mapped automated license plate reader (ALPR) camera locations, including a binary `flock` field that distinguishes records identified as Flock cameras from other ALPR cameras. The source repository, [NSM-Barii/flock-down](https://github.com/NSM-Barii/flock-down), describes its camera data as coming from OpenStreetMap (OSM), with Flock identification based on the OSM `manufacturer=Flock Safety` tag. The repository uses the data to show camera locations in a navigation/alert application. The original OSM contributors created and maintain the underlying map records; the repository republishes a snapshot for its application.

## 1.2 Composition

- **Local size:** 101,085 rows and 4 columns.
- **One row:** A camera/location record with an ID, latitude, longitude, and Flock indicator.
- **Coverage:** The file is not limited to Chicago. The sample rows include coordinates in Oslo, Norway, consistent with broad geographic coverage.
- **Completeness:** No null values were detected in `id`, `lat`, `lon`, or `flock`.
- **Important distinction:** Having no nulls does not establish that every real-world ALPR camera is represented or that every mapped location and manufacturer label is correct.
- **Class balance in this snapshot:** The prior EDA count was 75,614 records marked Flock and 25,471 marked non-Flock. These counts should be recalculated if the CSV is refreshed.

## 1.3 Collection process

The source repository states that camera locations are sourced from OpenStreetMap and that its camera database is updated periodically. OpenStreetMap is a collaborative, volunteer-maintained geographic database. Camera locations and tags may be added or edited by contributors and may be incomplete, stale, or inaccurate.

- **Source repository:** https://github.com/NSM-Barii/flock-down
- **Underlying map:** https://www.openstreetmap.org
- **OSM copyright and license information:** https://www.openstreetmap.org/copyright
- **Repository data-source description:** The repository README identifies OpenStreetMap as the camera-location source and the `manufacturer=Flock Safety` tag as the Flock-identification rule.
- **Consent:** The dataset describes mapped infrastructure rather than individual people. OSM edits are made by contributors under OSM's contribution terms; this is not a dataset collected from a survey of camera operators or people whose vehicles pass the cameras.

## 1.4 Preprocessing

The acquisition notebook reads the file with Polars:

```python
alpr = pl.read_csv("../data/raw/alpr_cameras.csv")
```

The notebook then prints the shape. It does not show a cleaning, filtering, or joining operation. The local CSV contains the columns `id`, `lat`, `lon`, and `flock`.

For the EDA, a Chicago-area subset was also examined using a geographic bounding box. The previous EDA reported 1,101 camera records in that box, of which 482 were marked Flock. This is a geographic filter, not an independently verified list of all cameras installed in Chicago. 

The upstream repository provides its own database-generation workflow, but this project’s acquisition notebook does not record the exact upstream commit or export procedure used to create this local CSV. The CSV should therefore be treated as a source snapshot, not as a fully reproducible live query.

## 1.5 Uses and inappropriate uses

**Reasonable uses**
- Describing the mapped distribution of ALPR camera records in this snapshot.
- Comparing records labeled Flock with records labeled as other manufacturers, while acknowledging label limitations.
- Selecting a geographic subset for exploratory mapping or comparing mapped camera locations with other geographic data.

**Inappropriate or unsupported uses**
- Treating the file as a complete census of all installed ALPR cameras.
- Treating a mapped point as proof that a camera is currently installed, operational, or owned by a particular agency.
- Inferring deployment dates, camera activity, or the number of vehicles scanned from these point locations alone.
- Assuming that `flock=0` means a camera is not Flock-owned in reality; it means only that the source snapshot did not label the record as Flock.
- Using mapped locations to infer an individual’s movements or identity.

## 1.6 Distribution and license

The CSV is available in the public [flock-down GitHub repository](https://github.com/NSM-Barii/flock-down). The repository describes the camera locations as sourced from OpenStreetMap. OSM data is distributed under the Open Data Commons Open Database License (ODbL); attribution and share-alike requirements may apply to database use. See https://www.openstreetmap.org/copyright and https://opendatacommons.org/licenses/odbl/.


## 1.7 Maintenance

- **Underlying data maintainer:** OpenStreetMap contributors.
- **Snapshot publisher:** NSM-Barii/flock-down GitHub repository.
- **Update information:** The repository README describes periodic updates to its camera database. The live source may change independently of this project.
- **Known limitation:** The local CSV is a snapshot and may differ from the current GitHub file or current OSM data.

# 2. `chicago_crime_2017.csv`

## 2.1 Motivation

This file contains reported crime records for Chicago with incident dates in 2017. The underlying [Crimes - 2001 to Present dataset](https://data.cityofchicago.org/Public-Safety/Crimes-2017/d62x-nvdr/about_data) is provided by the Chicago Police Department through the City of Chicago Data Portal. The portal says the records are extracted from the department’s CLEAR reporting system and are intended to provide public access to reported incidents.

## 2.2 Composition

- **Local size:** 269,349 rows and 22 columns.
- **One row:** One reported crime record. It is not necessarily one unique victim or one court-verified offense.
- **Time coverage:** The local file is intended to cover calendar year 2017. The sample rows have dates on December 31, 2017.
- **Geographic coverage:** Chicago, Illinois.
- **Missingness observed in this local snapshot:**
  - `Location Description`: 1,375 missing (about 0.5%).
  - `District`: 1 missing.
  - `Ward`: 1 missing.
  - `Community Area`: 15 missing.
  - `X Coordinate`, `Y Coordinate`, `Latitude`, `Longitude`, and `Location`: 4,413 missing each (about 1.6%).
  - The other columns had no nulls in the inspection performed.
- **Completeness:** This is a downloaded subset, not the entire live portal. Counts and classifications may change as records are updated.

## 2.3 Collection process

The City of Chicago portal states that the underlying records are extracted from the Chicago Police Department’s CLEAR system. Reports may be preliminary, classifications can change after investigation, and the city warns about possible human or mechanical errors. Addresses are shown at block level to protect privacy.

- **Publisher:** City of Chicago Data Portal; data provided by the Chicago Police Department.
- **Source dataset:** https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2
- **Underlying reporting system:** CLEAR (Citizen Law Enforcement Analysis and Reporting).
- **Local extraction date and exact filter/download query:** Not recorded in the acquisition notebook. The filename and row contents indicate a 2017 subset, but the exact download query should be verified if strict reproducibility is required.
- **Consent:** These are administrative/police reports, not data collected through informed-consent research participation. People involved in reported incidents may not have chosen to have their information included in the public dataset.

## 2.4 Preprocessing

The acquisition notebook loads the local CSV with Polars:

```python
crime_2017 = pl.read_csv("../data/raw/chicago_crime_2017.csv")
```

It prints the shape and does not show additional cleaning or joins. The local file already has 22 columns. In this inspection, the `Date` and `Updated On` columns were read as strings; any date-based analysis should parse them explicitly and document the format and timezone assumptions.

## 2.5 Uses and inappropriate uses

**Reasonable uses**
- Describing reported incidents in the local 2017 snapshot.
- Summarizing counts by recorded crime category, date, or geographic area, with appropriate caveats.
- Exploring broad spatial or temporal patterns when missing location fields and reporting limitations are disclosed.

**Inappropriate or unsupported uses**
- Treating every record as a confirmed crime, conviction, or verified account of events.
- Interpreting changes between years as changes in actual crime without accounting for reporting, data updates, and differences in collection.
- Inferring guilt, victim identity, or individual behavior.
- Geocoding block-level records to claim a specific private address. The city explicitly says mapped locations are approximate and specific addresses must not be derived.
- Making high-stakes decisions about individuals or neighborhoods from these records alone.

## 2.6 Distribution and license

The dataset is publicly downloadable from the City of Chicago Data Portal as CSV and other formats. The portal lists permissions as public and refers users to the City’s Terms of Use rather than naming a simple open-data license on the dataset page. Review the current portal terms before redistributing the file: https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html

The city’s source description and disclaimers are available on the [dataset page](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2).

## 2.7 Maintenance

- **Maintainer/publisher:** City of Chicago Data Portal; source data provided by the Chicago Police Department.
- **Update frequency:** The live source dataset is updated daily.
- **How to identify a version:** Preserve the downloaded CSV and record the date accessed, export URL/query, and file checksum if the data is refreshed.
- **Known limitation:** The local 2017 file is a static snapshot. The live dataset may contain revisions made after the local file was downloaded.

# 3. `chicago_crime_2026.csv`

## 3.1 Motivation

This file is a 2026 subset of the same Chicago crime-reporting source described above. It supports exploratory analysis of reported incidents during the portion of 2026 represented in the local snapshot. The source is the City of Chicago Data Portal’s [Crimes - 2001 to Present dataset](https://data.cityofchicago.org/Public-Safety/Crimes-2026/f6bk-yv3r/about_data), provided by the Chicago Police Department.

## 3.2 Composition

- **Local size:** 167,474 rows and 22 columns.
- **One row:** One reported crime record.
- **Time coverage:** The sample rows show incidents through September 20, 2026. This is a **partial year**, not a complete 2026 dataset.
- **Geographic coverage:** Chicago, Illinois.
- **Missingness observed in this local snapshot:**
  - `Location Description`: 758 missing (about 0.5%).
  - `Community Area`: 1 missing.
  - `X Coordinate`, `Y Coordinate`, `Latitude`, `Longitude`, and `Location`: 304 missing each (about 0.2%).
  - The other columns had no nulls in the inspection performed.
- **Type differences:** `District`, `Ward`, and `Beat` were read as integer columns in this file, while `District` and `Ward` were floating-point columns in the 2017 file because those columns contain missing values there. 

## 3.3 Collection process

The source is the Chicago Police Department’s CLEAR reporting system, published through the City of Chicago Data Portal. The portal warns that reported incidents may be preliminary, classifications can be revised, and records may contain human or mechanical errors. Addresses are displayed at block level for privacy.

- **Publisher:** City of Chicago Data Portal; data provided by the Chicago Police Department.
- **Source dataset:** https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2
- **Local snapshot evidence:** A sample record has an incident date of September 20, 2026, and an `Updated On` value of September 27, 2026. 

- **Consent:** Administrative police-report data, not consent-based research data. People named or implicated in reports may not have consented to public release.

## 3.4 Preprocessing

The acquisition notebook loads the local CSV with Polars:

```python
crime_2026 = pl.read_csv("../data/raw/chicago_crime_2026.csv")
```

It prints the shape and does not show additional cleaning or joins. In the inspection, `Date` and `Updated On` were read as strings. Date parsing, time-window selection, and removal of rows with missing coordinates should be documented if performed in analysis code.


## 3.5 Uses and inappropriate uses

**Reasonable uses**
- Describing the records in the 2026 snapshot through the observed cutoff.
- Summarizing reported crime types or locations during the covered period.
- Comparing with 2017 only when the time windows and reporting limitations are made explicit.

**Inappropriate or unsupported uses**
- Calling this a complete 2026 dataset.
- Comparing raw full-year 2017 totals with partial-year 2026 totals without adjustment.
- Treating records as verified crimes or convictions.
- Using approximate block-level locations to identify a specific address or person.
- Making individual-level judgments or high-stakes decisions from police-report records.

## 3.6 Distribution and license

The live source is publicly downloadable from the City of Chicago Data Portal. The portal refers users to its Terms of Use; check the current terms before redistributing the source file. Links: https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2

## 3.7 Maintenance

- **Maintainer/publisher:** City of Chicago Data Portal; source data provided by the Chicago Police Department.
- **Update frequency:** The live source dataset is updated daily.
- **Known limitation:** This local file is a static partial-year snapshot and may differ from later portal exports.

# 4. Scope and research questions


**Research Question 1**

What is the relationship between the geographic distribution of Flock cameras and reported crime in Chicago?

Target population: Flock Safety ALPR camera locations and criminal incidents reported to the Chicago Police Department in Chicago.

Access frame: Camera locations included in the OpenStreetMap-derived camera dataset and reported crime records available through the City of Chicago Data Portal for 2017 and 2026.

Sample: The 1,101 camera records selected by the Chicago geographic bounding-box filter, including 482 records labeled as Flock, and the available crime records for the two selected years.

Missing or underrepresented data: The camera dataset may omit cameras that are not mapped or correctly identified. Crime data excludes crimes that are not reported or recorded, and location fields may be missing.

Limitations: Geographic overlap can identify associations but cannot establish that cameras cause crime to increase or decrease. Results also depend on the completeness of camera records and the accuracy of reported crime locations.


**Research Question 2**

Are areas with more Flock cameras associated with higher or lower levels of reported crime?

Target population: Chicago geographic areas with different levels of Flock camera presence and reported crime.

Access frame: The available camera coordinates and Chicago crime records from 2017 and 2026.

Sample: Camera locations and crime reports that fall within the geographic area included in the analysis. The exact spatial unit used to count cameras and crimes must be specified by the analysis code.
Missing or underrepresented data: Areas with unmapped cameras may appear to have fewer cameras than they actually do. Unreported crimes and missing or approximate crime coordinates may also affect area-level counts.

Limitations: A higher number of reported crimes in an area with more cameras does not demonstrate that the cameras caused those crimes. Population size, traffic, land use, policing practices, reporting rates, and other factors may affect the observed relationship.


**Research Question 3**

How do crime patterns in areas with Flock cameras compare with patterns in areas without them?

Target population: Chicago areas with and without mapped Flock Safety ALPR cameras.

Access frame: The available camera-location dataset and Chicago crime reports for 2017 and 2026.

Sample: Crime reports and camera locations within the geographic area included in the analysis. The method used to classify areas as having or not having cameras must be documented in the analysis code.

Missing or underrepresented data: Areas may be incorrectly classified as having no cameras if camera locations are missing from the source data. Crimes without usable location information may not be included in spatial comparisons.

Limitations: Areas with cameras may differ from areas without cameras in population, infrastructure, commercial activity, or policing. These differences can affect reported crime patterns, so the comparison does not establish a causal effect of camera presence.


**Research Question 4**

How has the relationship between Flock camera locations and reported crime changed between 2017 and 2026?

Target population: Chicago's reported crime patterns across 2017 and 2026, in relation to Flock camera locations.

Access frame: Chicago crime reports for 2017 and the available portion of 2026, together with the available camera-location dataset.

Sample: The available crime records for both years and the mapped camera locations used in the geographic analysis.

Missing or underrepresented data: The 2026 dataset covers only part of the year. The available camera dataset may not provide historical installation dates or past camera locations.

Limitations: If the camera dataset is a current snapshot without historical records, it cannot establish which cameras were present in 2017. Therefore, this analysis can compare reported crime patterns across the two years, but it cannot reliably measure changes in the historical relationship between crime and camera placement without historical camera data. Comparisons must also account for the different lengths of the reporting periods.

# 5. Codebook

The codebook records local inferred type, units/allowed values, meaning, observed range or category constraints where verified, missing-value coding/counts, and origin. Types are those inferred by local CSV inspection. Missing counts are true nulls observed by the CSV reader; blank strings and invalid values were not separately audited.

## 5.1 `alpr_cameras.csv`

For numeric fields, the actual observed minimum/maximum and uniqueness checks were not captured in the current documentation. These are marked **not profiled** rather than inferred. Missing values are CSV-reader nulls; no nulls were observed in this snapshot.

| Column | Local type | Units, allowed values, and range | Meaning | Missing coding/count | Origin |
|---|---|---|---|---|---|
| `id` | Integer (`int64`) | Numeric identifier; observed min/max and uniqueness **not profiled** | Identifier associated with a camera record in the source snapshot. | CSV null; 0 observed | `flock-down` CSV snapshot; underlying source described as OSM |
| `lat` | Float (`float64`) | Decimal degrees; valid latitude range is −90 to 90; actual observed min/max **not profiled** | Latitude of mapped camera point. | CSV null; 0 observed | OSM-derived camera-location record |
| `lon` | Float (`float64`) | Decimal degrees; valid longitude range is −180 to 180; actual observed min/max **not profiled** | Longitude of mapped camera point. | CSV null; 0 observed | OSM-derived camera-location record |
| `flock` | Integer (`int64`) | Observed codes 0/1; full codebook/range verification **not documented** | Whether the source snapshot labels the camera as Flock; source repository describes use of OSM `manufacturer=Flock Safety` tag. | CSV null; 0 observed | Derived/source label in `flock-down` snapshot based on OSM tags; verify exact implementation upstream |

## 5.2 Crime columns shared by both CSVs

The two files share 22 column names. Local types can differ because of missingness and CSV type inference. For categorical codes, the complete allowed-value inventory was not extracted during this inspection. All fields originate from the City of Chicago crime dataset unless noted. Missing-value coding/counts below refer to CSV nulls in the 2017 / 2026 files; where the counts are not `None`, the values are actual nulls, not a special text code.

| Column | Local type (2017 / 2026) | Units, allowed values, and range | Meaning | Missing coding/count (2017 / 2026) | Origin |
|---|---|---|---|---|---|
| `ID` | Integer / integer | Numeric record identifier; min/max not profiled | Source record identifier. | Null; 0 / 0 | City of Chicago crime dataset |
| `Case Number` | String / string | Case-number format; full pattern not profiled | Police records-division case identifier. | Null; 0 / 0 | Chicago Police Department reporting record |
| `Date` | String / string | Date/time string; observed date bounds should be recomputed from the full file | Date/time the incident was reported as occurring; source notes dates may sometimes be estimates. | Null; 0 / 0 | Chicago Police Department reporting record |
| `Block` | String / string | Approximate block-address text; allowed format not exhaustively profiled | Block-level location, not a precise private address. | Null; 0 / 0 | Chicago Police Department dataset; locations are generalized by source |
| `IUCR` | String / string | IUCR code; full allowed code list not profiled | Illinois Uniform Crime Reporting offense code. | Null; 0 / 0 | Chicago Police Department; IUCR classification |
| `Primary Type` | String / string | Categorical text; full category list not profiled | Primary reported crime category. | Null; 0 / 0 | Chicago Police Department classification |
| `Description` | String / string | Categorical text; full category list not profiled | More specific description of the reported incident. | Null; 0 / 0 | Chicago Police Department classification |
| `Location Description` | String / string | Categorical text; full category list not profiled | Type of place where the incident occurred, when recorded. | Null; 1,375 / 758 | Chicago Police Department record |
| `Arrest` | Boolean / boolean | `True` / `False` in local data; exact source encoding not separately audited | Whether an arrest was recorded; not a conviction. | Null; 0 / 0 | Chicago Police Department record |
| `Domestic` | Boolean / boolean | `True` / `False` in local data; exact source encoding not separately audited | Whether incident was marked domestic-related under source definition. | Null; 0 / 0 | Chicago Police Department record |
| `Beat` | Integer / integer | Police beat identifier; valid-code list and min/max not profiled | Police beat associated with incident. | Null; 0 / 0 | Chicago Police Department geographic assignment |
| `District` | Float / integer | Police district identifier; valid-code list and min/max not profiled | Police district associated with incident. | Null; 1 / 0 | Chicago Police Department geographic assignment |
| `Ward` | Float / integer | City Council ward identifier; valid-code list and min/max not profiled | Ward associated with incident. | Null; 1 / 0 | City of Chicago geographic assignment |
| `Community Area` | Float / float | Community-area identifier; valid-code list and min/max not profiled | Chicago community area associated with incident. | Null; 15 / 1 | City of Chicago geographic assignment |
| `FBI Code` | String / string | FBI classification code; full allowed code list not profiled | FBI crime classification associated with the reported offense. | Null; 0 / 0 | Chicago Police Department classification |
| `X Coordinate` | Float / float | Projected map coordinate; coordinate system/units must be confirmed before distance calculations; min/max not profiled | X coordinate for approximate incident location. | Null; 4,413 / 304 | City of Chicago geographic data |
| `Y Coordinate` | Float / float | Projected map coordinate; coordinate system/units must be confirmed before distance calculations; min/max not profiled | Y coordinate for approximate incident location. | Null; 4,413 / 304 | City of Chicago geographic data |
| `Year` | Integer / integer | Calendar year; observed values should be validated against incident dates | Year recorded by the source. | Null; 0 / 0 | Chicago Police Department record |
| `Updated On` | String / string | Date/time string; full observed range not profiled | Timestamp indicating when the source record was last updated. | Null; 0 / 0 | City of Chicago dataset maintenance metadata |
| `Latitude` | Float / float | Decimal degrees; valid latitude range −90 to 90; actual observed min/max not profiled | Latitude of approximate incident location. | Null; 4,413 / 304 | City of Chicago geographic data |
| `Longitude` | Float / float | Decimal degrees; valid longitude range −180 to 180; actual observed min/max not profiled | Longitude of approximate incident location. | Null; 4,413 / 304 | City of Chicago geographic data |
| `Location` | String / string | Point text, commonly `POINT (longitude latitude)`; complete formatting/range validation not profiled | Text representation of approximate incident location. | Null; 4,413 / 304 | City of Chicago geographic data |

## 5.3 Derived fields, filtered subsets, and aggregates used in EDA

The fields below are confirmed by the EDA summary and code shared for the grid comparison. A derived field's exact observed range depends on the local snapshot; where the full value range was not printed, this is marked as not profiled rather than guessed.

| Derived field / analysis object | Type | Units / allowed values / range | Meaning and formula | Missing-value handling | Origin / code location |
|---|---|---|---|---|---|
| `alpr_chicago` | Polars DataFrame subset | 4 original columns; 1,101 records in the Chicago bounding box: 619 with `flock=0`, 482 with `flock=1` | Camera records selected from `alpr` using `41.64 <= lat <= 42.03` and `-87.94 <= lon <= -87.52`. This rectangular bounding box is an approximation, not the municipal boundary. | No source nulls were reported; records outside the box are excluded from this subset. | `notebooks/EDA_LG.ipynb`, cell 48; linked notebook below. |
| `flock_chicago` | Polars DataFrame subset | 4 original columns; 482 records | `alpr_chicago` filtered to `flock == 1`, retaining only Chicago-box records labeled Flock. | Inherits complete source fields; other ALPR records are excluded by the filter. | `notebooks/EDA_LG.ipynb`, cell 51. |
| `crime_2026_geo` | Polars DataFrame subset | Original crime columns; exact row count not provided in the EDA summary | 2026 records with geographic coordinates suitable for longitude/latitude plotting and grid assignment. | 304 rows in the full 2026 file have missing geographic fields; the EDA summary says such rows are excluded from geographic plots. Exact filtered row count should be printed from the notebook. | `notebooks/EDA_LG.ipynb`, geographic filtering cell. |
| `Date` after parsing | Polars datetime column | Timestamp parsed with `%m/%d/%Y %I:%M:%S %p`; no timezone conversion is shown. | Incident date/time used for monthly aggregation and time-based analysis. | No source nulls were reported; parse failures are not separately counted. | `crime_2017` and `crime_2026` are each updated in place in `notebooks/EDA_LG.ipynb` using `pl.col("Date").str.to_datetime("%m/%d/%Y %I:%M:%S %p").alias("Date")`. |
| `Month` | Integer (1–12) | Calendar month number: 1 = January through 12 = December | Derived as `Date.dt.month()` and used to group reported incidents by month. | Created after parsing `Date`; source date nulls were not reported. | `monthly_crime_2017` and `monthly_crime_2026` in `notebooks/EDA_LG.ipynb`. |
| Monthly `len` / count | Unsigned integer count | Non-negative number of reported crime rows per month | Result of `.group_by("Month").len()`; describes row counts in each month. | One row per month represented in the data. September 2026 is partial through September 20. | `monthly_crime_2017` and `monthly_crime_2026`. |
| `Crime Count` | Unsigned integer count | Positive integer number of records per `Primary Type` | Derived with `.group_by("Primary Type").agg(pl.len().alias("Crime Count"), ...)`. | Source `Primary Type` and `Arrest` had no nulls in the inspected 2026 snapshot. | `crime_type_arrest_2026` in `notebooks/EDA_LG.ipynb`. |
| `Arrest Rate` | Float | Proportion from 0 to 1; plotted as percentage by multiplying by 100 | Mean of the Boolean `Arrest` field within each `Primary Type`, equivalent to the proportion of records with `Arrest=True` when the field has no nulls. The plot multiplies this value by 100. | No nulls reported in source `Arrest`; any null behavior would affect the mean, but none were reported. | `crime_type_arrest_2026` and `top_crime_arrest_2026` in `notebooks/EDA_LG.ipynb`. |
| `percentage` | Float | Percentage from 0 to 100 | For the global ALPR dataset, derived as count for each `flock` value divided by `alpr.height` and multiplied by 100. | Not missing in displayed output. | `flock_counts` in `notebooks/EDA_LG.ipynb`. |
| `lat_grid` | Float (`f64`) | Integer-valued grid index stored as float; unitless index; actual range not profiled | `floor(latitude / 0.02)` for the relevant camera or crime latitude. | Generated only for rows entering the geographic aggregation; rows with missing coordinates are excluded upstream. | Grid aggregation code shared for Relationship 3. |
| `lon_grid` | Float (`f64`) | Integer-valued grid index stored as float; unitless index; actual range not profiled | `floor(longitude / 0.02)` for the relevant camera or crime longitude. | Generated only for rows entering the geographic aggregation; rows with missing coordinates are excluded upstream. | Grid aggregation code shared for Relationship 3. |
| `Flock Cameras` | Unsigned integer count (`u32`) | Integer count, minimum 0; observed maximum not provided | Number of rows in `flock_chicago` falling into each (`lat_grid`, `lon_grid`) cell. | After the left join, null counts are filled with 0. | `flock_grid`: group by grid keys, count rows, rename `len` to `Flock Cameras`. |
| `Reported Crimes` | Unsigned integer count (`u32`) | Positive integer count for each cell present in `crime_grid`; observed maximum not provided | Number of rows in `crime_2026_geo` falling into each (`lat_grid`, `lon_grid`) cell. | Crime cells with valid coordinates are included; the displayed join is left-sided from crime grid, so crime counts are not null in the resulting rows. | `crime_grid`: group by grid keys, count rows, rename `len` to `Reported Crimes`. |
| `camera_crime_grid` | Polars DataFrame | 206 rows × 4 columns in the output shown | Left join of crime-grid counts with Flock camera-grid counts on both grid indices. | Null `Flock Cameras` values are replaced by 0. Camera-only cells without reported crimes are not included. | Relationship 3 code shared in conversation; full code is reproduced in Section 6. |

The grid size is `0.02` degrees of latitude/longitude. This is an angular grid, not a constant distance in miles or kilometers. Because the left join starts from `crime_grid`, it only includes cells with at least one geolocated crime record. It does not include camera-only cells with no crimes in the analyzed crime data.

# 6. Raw-to-analysis recipe

This section lists the known processing steps in order and distinguishes verified code from details that are not present in the supplied output. Code files: [`notebooks/data_acquisition.ipynb`](https://github.com/hackmad003/cs418-flock-research/blob/lexi-dev/notebooks/data_acquisition.ipynb) and [`notebooks/EDA_LG.ipynb`](https://github.com/hackmad003/cs418-flock-research/blob/lexi-dev/notebooks/EDA_LG.ipynb). The repository links point to the notebook files.


## 6.1 Files and ordered steps

1. **Obtain source snapshots.** ALPR data is associated with [NSM-Barii/flock-down](https://github.com/NSM-Barii/flock-down), whose README says the camera locations come from OpenStreetMap and Flock identification uses the OSM `manufacturer=Flock Safety` tag. Crime records come from the City of Chicago's [Crimes - 2001 to Present dataset](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2), extracted from CPD's CLEAR system. The exact download query/export URL and exact access date for each local CSV are undocumented; the local snapshots were inspected in October 2026.

2. **Store the raw files** as `data/raw/alpr_cameras.csv`, `data/raw/chicago_crime_2017.csv`, and `data/raw/chicago_crime_2026.csv`. The checked-in acquisition notebook does not download the files itself; it reads local copies.

3. **Load the camera CSV** in `notebooks/data_acquisition.ipynb` with `alpr = pl.read_csv("../data/raw/alpr_cameras.csv")`.

4. **Load the 2017 crime CSV** with `crime_2017 = pl.read_csv("../data/raw/chicago_crime_2017.csv")`.

5. **Load the 2026 crime CSV** with `crime_2026 = pl.read_csv("../data/raw/chicago_crime_2026.csv")`.

6. **Inspect dataset dimensions.** The output for the local snapshots was `alpr.shape == (101085, 4)`, `crime_2017.shape == (269349, 22)`, and `crime_2026.shape == (167474, 22)`. These are snapshot counts, not guaranteed live-source counts.

7. **Filter camera records to the Chicago bounding box.** In `notebooks/EDA_LG.ipynb` cell 48, create `alpr_chicago` with `41.64 <= lat <= 42.03` and `-87.94 <= lon <= -87.52`. This produces 1,101 records: 619 labeled non-Flock (`flock=0`) and 482 labeled Flock (`flock=1`). Cell 51 then creates `flock_chicago` by filtering `alpr_chicago` to `flock == 1`, producing 482 records.

8. **Parse the incident date.** In both `crime_2017` and `crime_2026`, convert `Date` using `pl.col("Date").str.to_datetime("%m/%d/%Y %I:%M:%S %p").alias("Date")`. No timezone conversion is shown. `Updated On` remains unparsed in the shown EDA code.

9. **Prepare the 2026 geographic subset.** Create `crime_2026_geo` by retaining rows where both `Latitude` and `Longitude` are not null. The checked-in notebook output is `(167170, 22)`, meaning 304 of the 167,474 source rows are excluded from geographic plots and grid aggregation, but remain in `crime_2026`.

10. **Plot camera and crime locations.** The EDA plots `crime_2026_geo["Longitude"]` against `crime_2026_geo["Latitude"]` and overlays `flock_chicago["lon"]` against `flock_chicago["lat"]`. This plot overlays two point layers; it does not join individual crime records to individual camera records.

11. **Aggregate Flock camera counts by grid.** With `grid_size = 0.02`, calculate `lat_grid = floor(lat / grid_size)` and `lon_grid = floor(lon / grid_size)` for `flock_chicago`, group by both grid fields, count rows, and rename the count column to `Flock Cameras`. This produces `flock_grid`.

12. **Aggregate 2026 crime counts by grid.** Apply the same formula to `Latitude` and `Longitude` in `crime_2026_geo`, group by `lat_grid` and `lon_grid`, count rows, and rename the count column to `Reported Crimes`. This produces `crime_grid`.

13. **Left-join the grid summaries.** Join `crime_grid` to `flock_grid` using both `lat_grid` and `lon_grid`, with `how="left"`. Fill null `Flock Cameras` values with 0. The displayed result, `camera_crime_grid`, has 206 rows and four columns: `lat_grid`, `lon_grid`, `Reported Crimes`, and `Flock Cameras`.

14. **Plot the grid-level comparison.** Plot `Flock Cameras` on the x-axis and `Reported Crimes` on the y-axis from `camera_crime_grid`. The plot compares counts per crime-containing grid cell; it does not establish a causal relationship.

15. **Create monthly and crime-type summaries.** The notebook creates `Month` using `pl.col("Date").dt.month().alias("Month")`, groups by `Month`, and calls `.len()` for 2017 and 2026. For crime-type arrest rates, it groups `crime_2026` by `Primary Type`, computes `pl.len().alias("Crime Count")` and `pl.col("Arrest").mean().alias("Arrest Rate")`, sorts by `Crime Count` descending, and plots the top ten types after multiplying `Arrest Rate` by 100. The notebook also creates `monthly_crime_arrest_2026`, grouped by `Month`, with `Crime Count` and mean `Arrest Rate`.

## 6.2 Join keys and matched/unmatched counts

The confirmed join is a **left join** from `crime_grid` to `flock_grid` on the two-column key `[`lat_grid`, `lon_grid`]`. The join matches only exact grid-index pairs generated using `floor(coordinate / 0.02)`; it is not a nearest-neighbor join and does not use a distance buffer.

| Join item | Value |
|---|---|
| Left dataframe | `crime_grid` |
| Right dataframe | `flock_grid` |
| Join type | Left join |
| Join key | `lat_grid`, `lon_grid` together |
| Left row count before join | 206, inferred from the 206-row output because the left join preserves every left key and each grid summary has one row per key; confirm by printing `crime_grid.height` |
| Right row count before join | Not included in the supplied output; print `flock_grid.height` |
| Output row count | 206 |
| Matched left grid cells | **Not present in the supplied output; calculate using the code below** |
| Unmatched left grid cells | **Not present in the supplied output; calculate using the code below** |
| Right-side camera-only grid cells omitted by this left join | Not counted in the supplied output; calculate using the code below |



```python
# Counts of crime grid cells with and without a matching Flock-camera grid cell
matched_left_cells = camera_crime_grid.filter(
    pl.col("Flock Cameras") > 0
).height
unmatched_left_cells = camera_crime_grid.filter(
    pl.col("Flock Cameras") == 0
).height

# Camera grid cells that have no crime-grid cell are excluded by the left join
crime_keys = crime_grid.select(["lat_grid", "lon_grid"])
camera_only_cells = flock_grid.join(
    crime_keys,
    on=["lat_grid", "lon_grid"],
    how="anti"
).height

print("crime_grid rows:", crime_grid.height)
print("flock_grid rows:", flock_grid.height)
print("joined output rows:", camera_crime_grid.height)
print("matched crime grid cells:", matched_left_cells)
print("unmatched crime grid cells:", unmatched_left_cells)
print("camera-only grid cells omitted by left join:", camera_only_cells)
```

**Important interpretation:** `matched_left_cells` and `unmatched_left_cells` count grid cells, not individual crimes or individual cameras. Since `crime_grid` and `flock_grid` are each grouped to one row per key pair, a successful key match represents a shared grid cell. The `fill_null(0)` step makes unmatched crime cells appear as zero-camera cells in the final dataframe. The `camera_only_cells` anti-join count is a separate right-only count and is not part of the 206-row left-join output.

## 6.3 Missing data and dropped rows

The EDA summary states that no rows were removed from the raw files solely because of missing values. Records with missing geographic coordinates were excluded only from plots and grid analyses that require valid latitude and longitude. The full crime CSVs retain these records. 

# 7. FAIR practices


**FAIR notes:** Source links improve findability; CSV is broadly readable and preserving exact export URLs, access dates, source versions, and checksums would improve reproducibility. The local snapshot versions and exact export queries are not fully documented, so the live websites may not reproduce the same row counts.


# 8. People, representation, and potential harms

## ALPR camera data

Although this dataset directly describes infrastructure rather than people, it concerns surveillance systems that can record vehicle movements and license plates. Camera coverage may be uneven because mapping depends on volunteer activity and source tagging. A map of recorded cameras can undercount installations or overrepresent places with more mapping activity. Avoid making claims about individuals, their travel, or the actual surveillance experienced by a community based only on mapped points. Consider who benefits from the data being public, who may be affected by surveillance, and how public release could be misused.

## Chicago crime data

Crime reports concern people who may be victims, witnesses, arrested individuals, or otherwise involved in police encounters. Police-reported data can underrepresent incidents that are not reported and can reflect unequal reporting or enforcement patterns. A record is not proof of guilt, and an arrest flag is not a conviction. Block-level geography reduces address precision but does not eliminate all re-identification or stigmatization risks when combined with other data. Avoid labeling communities as inherently criminal or using these data alone to justify decisions about individuals or neighborhoods.

## Overall limitation

These sources measure different things: the ALPR file records mapped camera locations, while the crime files record reported incidents. A spatial association between cameras and crime records would not establish that cameras caused changes in crime, reduced crime, or were deployed because of crime. These claims would require a research design that addresses confounding, timing, coverage bias, and source-data limitations.

# References

1. NSM-Barii, **flock-down** GitHub repository: https://github.com/NSM-Barii/flock-down
2. OpenStreetMap copyright and license information: https://www.openstreetmap.org/copyright
3. Open Data Commons Open Database License: https://opendatacommons.org/licenses/odbl/
4. City of Chicago Data Portal, **Crimes - 2001 to Present** (source description, row unit, update frequency, CLEAR source, preliminary-data and block-level-location warnings): https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2
5. City of Chicago Data Portal Terms of Use: https://data.cityofchicago.org/terms
6. Chicago Police Department data/statistics information: https://www.chicagopolice.org/data-statistics/
