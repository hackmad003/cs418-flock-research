#!/usr/bin/env python3
"""
Print every number used in docs/datasheets/DATASHEET_flock_us_historical.md.

Input (read only, nothing is written):
    data/raw/flock_osm/flock_us_historical_2026-10-30.csv      (primary)
    data/raw/flock_osm/osm_flock_us_locations_2026-10-30.csv   (ID comparison only)
    data/raw/census/*/2024/ACS*-Data.csv                       (ACS 2024 5-year)
    data/raw/elections/presidential/countypres_2000-2024.csv   (MIT Election Lab)
    data/external/census_boundaries/2024/tl_2024_<FIPS>_tract.zip
    data/external/census_boundaries/2017/tl_2017_09_tract.zip  (old Connecticut counties)
    data/external/census_boundaries/counties/tl_2024_us_county.zip

Output: printed tables only.

The Flock rule, monthly cohort columns and county assignment repeat
checkpoints/Narrative_Analysis/narrative.ipynb (cells 2, 6, 9 and 11). The
tract, ACS and vote joins use the narrative's methods from cells 17 and 23;
the narrative itself joins this file only to counties.

Usage (from the project root, takes about one minute):
    uv run python scripts/datasheet_stats_flock_us_historical.py
"""


###########
# IMPORTS #
###########
import warnings
# Used to hide GeoPandas' geographic-CRS warning for the nearest-polygon step,
# which the narrative accepts on purpose (0.03 degrees is only a cut-off).

from datetime import datetime, timezone
# Used to show file modification times in UTC.

from pathlib import Path
# Used to build file paths from the project root.

import geopandas as gpd
# Used to read the tract and county shapes and place each camera inside one.

import pandas as pd
# Only needed to combine GeoPandas tables (GeoPandas is built on pandas).

import polars as pl
# Used for every table.

from cs418_flock_research.loaders.load_osm_history import load_osm_history
# Project loader for the primary file: reads it without cleaning.

from cs418_flock_research.loaders.load_osm_locations import load_osm_locations
# Project loader for the locations file (used only to compare IDs).


#############
# CONSTANTS #
#############
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
EXTERNAL_DIR = ROOT / "data" / "external"

HISTORY_CSV = RAW_DIR / "flock_osm" / "flock_us_historical_2026-10-30.csv"
LOCATIONS_CSV = RAW_DIR / "flock_osm" / "osm_flock_us_locations_2026-10-30.csv"
POPULATION_CSV = RAW_DIR / "census" / "population" / "2024" / "ACSDT5Y2024.B01003-Data.csv"
INCOME_CSV = RAW_DIR / "census" / "median_household_income" / "2024" / "ACSDT5Y2024.B19013-Data.csv"
POVERTY_CSV = RAW_DIR / "census" / "poverty" / "2024" / "ACSST5Y2024.S1701-Data.csv"
RACE_CSV = RAW_DIR / "census" / "race_ethnicity" / "2024" / "ACSDT5Y2024.B03002-Data.csv"
ELECTIONS_CSV = RAW_DIR / "elections" / "presidential" / "countypres_2000-2024.csv"
TRACT_DIR = EXTERNAL_DIR / "census_boundaries" / "2024"
CT_TRACTS_2017_ZIP = EXTERNAL_DIR / "census_boundaries" / "2017" / "tl_2017_09_tract.zip"
COUNTIES_ZIP = EXTERNAL_DIR / "census_boundaries" / "counties" / "tl_2024_us_county.zip"

# The history file stores dates like "2025-12-11T04:26:19.000000+0000".
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%.f%z"

# The date written in the file name.
FILE_NAME_DATE = "2026-10-30"

# Start of the first month that has a first-tagged date.
SERIES_START = datetime(2024, 11, 1, tzinfo=timezone.utc)

# 50 states + DC. Anything else (Puerto Rico 72, Virgin Islands 78, ...) is outside the study area.
STATE_FIPS_50_DC = {
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
    "36", "37", "38", "39", "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
}

# Points outside every polygon go to the nearest polygon within this distance
# (degrees, about 2-3 km). Same value as the narrative notebook.
NEAREST_MAX_DEGREES = 0.03

# A changeset that first tagged this many cameras or more counts as a bulk upload (narrative cell 6).
BULK_CHANGESET_SIZE = 50

# Placeholder text values that can hide "unknown".
PLACEHOLDER_TEXT = ["", "0", "-999", "9999", "unknown", "none", "n/a"]


#################
# PRINT HEADING #
#################
def print_heading(title: str) -> None:
    """Print a visible section heading."""
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


#######################
# MANUFACTURER STATUS #
#######################
def manufacturer_status(manufacturer: str | None) -> str:
    """Classify one manufacturer value with the narrative's Flock rule (no brand column here)."""
    # Same rule as narrative.ipynb: a value naming a second vendor is
    # "ambiguous" and is not counted as a Flock camera.
    if manufacturer is None:
        return "missing"
    low = manufacturer.casefold().strip()
    if ";" in low or any(vendor in low for vendor in ("motorola", "platesmart", "genetec", "vigilant")):
        return "ambiguous"
    exact_spellings = {"flocksafety", "flock", "flockgroupinc.", "flockgroupinc", "flocksafetyinc", "flocksafetyinc."}
    if low.replace(" ", "") in exact_spellings:
        return "exact"
    if low.startswith("flock safety"):
        return "annotated"
    return "ambiguous"


###################
# ASSIGN POLYGONS #
###################
def assign_polygons(points: pl.DataFrame, polygons: gpd.GeoDataFrame, keep: list[str]) -> pl.DataFrame:
    """Give each point the polygon that contains it, else the nearest within NEAREST_MAX_DEGREES."""
    # Same method as narrative.ipynb: lon/lat used directly in the polygons'
    # coordinate system (NAD83, within about a metre of WGS 84 in the U.S.).
    point_layer = gpd.GeoDataFrame(
        points.select("osm_id").to_pandas(),
        geometry=gpd.points_from_xy(points["lon"].to_numpy(), points["lat"].to_numpy()),
        crs=polygons.crs,
    )
    polygons = polygons[keep + ["geometry"]]
    inside = gpd.sjoin(point_layer, polygons, how="inner", predicate="within").drop_duplicates("osm_id")
    rest = point_layer[~point_layer["osm_id"].isin(inside["osm_id"])]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        nearest = gpd.sjoin_nearest(rest, polygons, how="inner", max_distance=NEAREST_MAX_DEGREES).drop_duplicates("osm_id")
    inside_table = pl.from_pandas(inside[["osm_id", *keep]]).with_columns(pl.lit("within").alias("match_method"))
    nearest_table = pl.from_pandas(nearest[["osm_id", *keep]]).with_columns(pl.lit("nearest").alias("match_method"))
    return points.select("osm_id").join(pl.concat([inside_table, nearest_table]), on="osm_id", how="left")


##############
# ACS NUMBER #
##############
def acs_number(column_name: str) -> pl.Expr:
    """Convert ACS text to a number: '250,000+' -> 250001, '2,500-' -> 2499, '-' -> null."""
    # Same conversion as narrative.ipynb, so caps stay distinguishable from real values.
    text = pl.col(column_name).str.replace_all(",", "")
    return (
        pl.when(text.str.ends_with("+")).then(text.str.strip_suffix("+").cast(pl.Float64, strict=False) + 1)
        .when(text.str.ends_with("-") & (text.str.len_chars() > 1)).then(text.str.strip_suffix("-").cast(pl.Float64, strict=False) - 1)
        .otherwise(text.cast(pl.Float64, strict=False))
        .alias(column_name)
    )


############
# READ ACS #
############
def read_acs(path: Path, columns: list[str]) -> pl.DataFrame:
    """Read one ACS Data.csv: skip the label row, keep the 11-digit GEOID, convert numbers."""
    # Read as text so GEOIDs keep their leading zeros; row 0 repeats the labels.
    table = pl.read_csv(path, infer_schema_length=0, columns=["GEO_ID", *columns]).slice(1)
    table = table.with_columns(pl.col("GEO_ID").str.slice(9).alias("GEOID")).drop("GEO_ID")
    return table.with_columns([acs_number(column_name) for column_name in columns])


##############
# PRINT JOIN #
##############
def print_join(name: str, key: str, left: pl.DataFrame, right: pl.DataFrame, left_key: str, right_key: str) -> None:
    """Print left rows, right rows, matched and unmatched on both sides of a key join."""
    left_keys = left.select(pl.col(left_key).alias("_key")).drop_nulls()
    right_keys = right.select(pl.col(right_key).alias("_key")).drop_nulls().unique()
    matched_left = left_keys.join(right_keys, on="_key", how="semi").height
    unmatched_right = right_keys.join(left_keys.unique(), on="_key", how="anti").height
    print(f"JOIN {name} | key {key} | left rows {left.height:,} | right rows {right.height:,} | "
          f"left matched {matched_left:,} | left unmatched {left.height - matched_left:,} | right keys unmatched {unmatched_right:,}")


##################
# PROFILE COLUMN #
##################
def profile_column(table: pl.DataFrame, column_name: str) -> dict:
    """Return type, nulls, placeholders, unique count and min/max for one column."""
    column = table[column_name]
    profile = {"column": column_name, "type": str(column.dtype), "nulls": column.null_count(),
               "unique": column.n_unique(), "placeholders": 0, "min": None, "max": None}
    if column.dtype == pl.String:
        profile["placeholders"] = column.str.strip_chars().str.to_lowercase().is_in(PLACEHOLDER_TEXT).sum()
        lengths = column.drop_nulls().str.len_chars()
        profile["min"] = f"len {lengths.min()}" if lengths.len() else None
        profile["max"] = f"len {lengths.max()}" if lengths.len() else None
    elif column.dtype.is_numeric():
        profile["placeholders"] = column.is_in([0, -999, 9999]).sum()
        profile["min"] = column.min()
        profile["max"] = column.max()
    else:
        profile["min"] = column.min()
        profile["max"] = column.max()
    return profile


def print_profiles(table: pl.DataFrame, column_names: list[str]) -> None:
    """Print a profile table for the given columns."""
    profiles = pl.DataFrame([profile_column(table, name) for name in column_names], infer_schema_length=None)
    profiles = profiles.with_columns(pl.col("min", "max").cast(pl.String),
                                     (pl.col("nulls") / table.height * 100).round(1).alias("null_pct"))
    with pl.Config(tbl_rows=40, tbl_width_chars=170, fmt_str_lengths=34):
        print(profiles)


#####################
# PRINT INPUT FILES #
#####################
def print_input_files() -> None:
    """Print input file times and which history-script output files are present."""
    # No download log survives, so file times are the only local evidence.
    # Copying a file can change them, so they are an upper bound, not proof.
    print_heading("0. INPUT FILES (local modification time, UTC)")
    for input_path in [HISTORY_CSV, LOCATIONS_CSV, POPULATION_CSV, ELECTIONS_CSV, COUNTIES_ZIP]:
        modified_utc = datetime.fromtimestamp(input_path.stat().st_mtime, tz=timezone.utc)
        print(f"{modified_utc:%Y-%m-%d %H:%M}  {input_path.relative_to(ROOT).as_posix()}")
    # The history script writes several side files; check which survive.
    history_outputs = sorted(path.name for path in (RAW_DIR / "flock_osm").glob("flock_us_*"))
    print(f"history-script files in data/raw/flock_osm/: {history_outputs}")
    print(f"an _INCOMPLETE file is present: {any('_INCOMPLETE' in name for name in history_outputs)}")


################
# PROFILE FILE #
################
def profile_file(history: pl.DataFrame) -> pl.DataFrame:
    """Print the file profile and return the table with parsed date columns added."""
    print_heading("1. FILE PROFILE")
    print(f"rows {history.height:,} | columns {history.width}")
    print(f"columns: {history.columns}")
    print(f"unique osm_id {history['osm_id'].n_unique():,} | rows with a repeated osm_id "
          f"{history.filter(pl.col('osm_id').is_duplicated()).height:,} | fully identical rows {history.height - history.unique().height:,}")
    print("history_ok values:", history["history_ok"].value_counts().rows())
    shared_spot = history.filter(pl.struct("lat", "lon").is_duplicated())
    print(f"rows sharing exact coordinates {shared_spot.height:,} | distinct shared spots {shared_spot.select('lat', 'lon').unique().height:,} "
          f"| most rows at one spot {shared_spot.group_by('lat', 'lon').len()['len'].max()}")
    print("\nper-column profile (raw text columns, before parsing dates):")
    print_profiles(history, history.columns)
    print("manufacturer values:", history["manufacturer"].value_counts(sort=True).rows())
    user_counts = history["user"].value_counts(sort=True)
    print(f"user: {history['user'].n_unique():,} distinct | top user {user_counts['count'][0]:,} rows "
          f"| users with exactly one row {(user_counts['count'] == 1).sum():,}")
    print(f"operator: {history['operator'].n_unique():,} distinct (null counted as one)")
    print("first_insert_version values:", history["first_insert_version"].value_counts(sort=True).rows())
    print("version values:", history["version"].value_counts().sort("version").rows())
    print("first_tagged_version values:", history["first_tagged_version"].value_counts().sort("first_tagged_version").rows())

    # Parse the three date columns (this adds columns; the raw file is untouched).
    history = history.with_columns(
        pl.col("first_insert_date").str.to_datetime(DATE_FORMAT).dt.convert_time_zone("UTC").alias("inserted"),
        pl.col("first_tagged_date").str.to_datetime(DATE_FORMAT).dt.convert_time_zone("UTC").alias("tagged"),
        pl.col("last_edit").str.to_datetime(DATE_FORMAT).dt.convert_time_zone("UTC").alias("edited"),
    )
    print("\ndate columns (parsed):")
    for raw_name, parsed_name in [("first_insert_date", "inserted"), ("first_tagged_date", "tagged"), ("last_edit", "edited")]:
        print(f"{raw_name:<18} unparsed {history[parsed_name].null_count()} | min {history[parsed_name].min()} | max {history[parsed_name].max()}")
    newest = max(history["inserted"].max(), history["tagged"].max(), history["edited"].max())
    print(f"newest date in the file {newest} | rows edited after {FILE_NAME_DATE} "
          f"{history.filter(pl.col('edited') >= datetime(2026, 10, 31, tzinfo=timezone.utc)).height}")
    print(f"rows edited on the cut-off day {FILE_NAME_DATE}: {history.filter(pl.col('edited').dt.date() == pl.date(2026, 10, 30)).height:,}")

    print("\nrows per year:")
    per_year = (
        history.group_by(pl.col("inserted").dt.year().alias("year")).len("first_insert")
        .join(history.group_by(pl.col("tagged").dt.year().alias("year")).len("first_tagged"), on="year", how="full", coalesce=True)
        .join(history.group_by(pl.col("edited").dt.year().alias("year")).len("last_edit"), on="year", how="full", coalesce=True)
        .fill_null(0).sort("year")
    )
    with pl.Config(tbl_rows=30):
        print(per_year)
    per_month = history.group_by(pl.col("tagged").dt.truncate("1mo").dt.date().alias("month")).len("first_tagged").sort("month")
    all_months = pl.date_range(per_month["month"].min(), per_month["month"].max(), "1mo", eager=True)
    print(f"first-tagged months {per_month.height} | calendar months in span {all_months.len()} | empty months {all_months.len() - per_month.height}")
    print("first_tagged per month:", [(str(month), count) for month, count in per_month.rows()])
    return history


##########################
# CHECK HISTORY LOGIC #
##########################
def check_history_logic(history: pl.DataFrame) -> None:
    """Check the version-1 shortcut, the series start, and the creation-to-tag delay."""
    print_heading("2. HOW THE SCRIPT FILLED THE DATES")
    version_one = history.filter(pl.col("version") == 1)
    edited = history.filter(pl.col("version") > 1)
    print(f"version 1 (never edited, no API call) {version_one.height:,} ({version_one.height / history.height * 100:.1f}%) "
          f"| version > 1 (one API history call each) {edited.height:,}")
    all_equal = version_one.filter((pl.col("inserted") == pl.col("tagged")) & (pl.col("tagged") == pl.col("edited"))).height
    same_changeset = version_one.filter(pl.col("first_tagged_changeset") == pl.col("changeset")).height
    versions_one = version_one.filter((pl.col("first_insert_version") == 1) & (pl.col("first_tagged_version") == 1)).height
    print(f"version-1 rows with all three dates equal {all_equal:,} | first_tagged_changeset == changeset {same_changeset:,} "
          f"| both version columns == 1 {versions_one:,}")
    print(f"edited rows: tagged at version 1 {(edited['first_tagged_version'] == 1).sum():,} | tagged later {(edited['first_tagged_version'] > 1).sum():,}")

    print_heading("3. START OF THE SERIES")
    created_before = history.filter(pl.col("inserted") < SERIES_START)
    print(f"nodes created before {SERIES_START:%Y-%m-%d} {created_before.height:,} | of these first tagged at a later version "
          f"{(created_before['first_tagged_version'] > 1).sum():,}")
    print(f"earliest first_tagged {history['tagged'].min()} | earliest last_edit {history['edited'].min()} | earliest first_insert {history['inserted'].min()}")
    print("first-tagged month of the nodes created before the start:",
          created_before.group_by(pl.col("tagged").dt.truncate("1mo").dt.date().alias("month")).len().sort("month").rows())
    print("first-tagged changesets of those nodes (top 3):",
          created_before.group_by("first_tagged_changeset").len().sort("len", descending=True).head(3).rows())

    print_heading("4. TAGGED AFTER CREATION AND THE DELAY")
    retagged = history.filter(pl.col("tagged") > pl.col("inserted"))
    print(f"tagged later than created {retagged.height:,} | first_tagged_version > 1 {(history['first_tagged_version'] > 1).sum():,} "
          f"| tagged before created {history.filter(pl.col('tagged') < pl.col('inserted')).height} "
          f"| tagged after last edit {history.filter(pl.col('tagged') > pl.col('edited')).height}")
    delay_days = retagged.select(((pl.col("tagged") - pl.col("inserted")).dt.total_seconds() / 86_400).alias("days"))["days"]
    print(f"delay days: min {delay_days.min():.4f} | 25% {delay_days.quantile(0.25):.1f} | median {delay_days.median():.1f} "
          f"| 75% {delay_days.quantile(0.75):.1f} | max {delay_days.max():.1f} ({delay_days.max() / 365.25:.1f} years)")
    print(f"delay under 1 day {(delay_days < 1).sum():,} | 200-600 days {delay_days.is_between(200, 600).sum():,} "
          f"| over 365 days {(delay_days > 365).sum():,}")


##########################
# COMPARE WITH LOCATIONS #
##########################
def compare_with_locations(history: pl.DataFrame) -> None:
    """Print how the history and locations files overlap by osm_id."""
    print_heading("5. OVERLAP WITH THE LOCATIONS FILE (by osm_id)")
    locations = load_osm_locations(LOCATIONS_CSV)
    in_both = history.join(locations, on="osm_id", how="semi").height
    history_only = history.join(locations, on="osm_id", how="anti")
    locations_only = locations.join(history, on="osm_id", how="anti")
    print(f"history rows {history.height:,} | locations rows {locations.height:,} | in both {in_both:,} "
          f"| history only {history_only.height:,} | locations only {locations_only.height:,}")
    print(f"locations newest timestamp {locations['timestamp'].max()} | locations-only rows edited after the history cut-off "
          f"{locations_only.filter(pl.col('timestamp') > '2026-10-30T19:32:28Z').height:,}")
    print("history-only rows by first-tagged year:",
          history_only.group_by(pl.col("tagged").dt.year().alias("year")).len().sort("year").rows())
    shared = history.join(locations.select("osm_id", pl.col("version").alias("locations_version"),
                                           pl.col("lat").alias("locations_lat"), pl.col("lon").alias("locations_lon")),
                          on="osm_id", how="inner", validate="1:1")
    print(f"shared rows with a newer version in locations {shared.filter(pl.col('locations_version') > pl.col('version')).height:,} "
          f"| older {shared.filter(pl.col('locations_version') < pl.col('version')).height:,} "
          f"| moved {shared.filter((pl.col('lat') != pl.col('locations_lat')) | (pl.col('lon') != pl.col('locations_lon'))).height:,}")


################
# BUILD RECIPE #
################
def build_recipe(history: pl.DataFrame) -> None:
    """Apply the narrative's Flock rule and cohort columns, then every join, printing counts."""
    print_heading("6. RECIPE: FLOCK RULE AND COHORT COLUMNS (narrative cell 6)")
    pairs = history.select("manufacturer").unique()
    pairs = pairs.with_columns(pl.Series("manufacturer_status", [manufacturer_status(value) for value in pairs["manufacturer"]]))
    history = history.join(pairs, on="manufacturer", how="left", nulls_equal=True)
    print("manufacturer_status counts:", history["manufacturer_status"].value_counts(sort=True).rows())
    flock = history.filter(pl.col("manufacturer_status") != "ambiguous")
    print(f"rows before {history.height:,} | after the Flock rule {flock.height:,} | dropped {history.height - flock.height}")
    print("dropped manufacturer values:", history.filter(pl.col("manufacturer_status") == "ambiguous").group_by("manufacturer").len().sort("manufacturer").rows())
    flock = (
        flock.join(flock.group_by("first_tagged_changeset").len("changeset_size"), on="first_tagged_changeset")
        .with_columns(
            pl.col("tagged").dt.truncate("1mo").dt.date().alias("month"),
            (pl.col("first_tagged_version") > 1).alias("retag"),
            (pl.col("changeset_size") >= BULK_CHANGESET_SIZE).alias("bulk"),
        )
    )
    print(f"month: {flock['month'].min()} to {flock['month'].max()} ({flock['month'].n_unique()} months)")
    print(f"retag true {flock['retag'].sum():,} | bulk true {flock['bulk'].sum():,} | changeset_size min {flock['changeset_size'].min()} "
          f"| max {flock['changeset_size'].max()} | distinct first-tagged changesets {flock['first_tagged_changeset'].n_unique():,}")
    print("months with a bulk changeset:", flock.filter("bulk").group_by("month").len().sort("month").rows())
    print(f"first tagged in 2026 {(flock['tagged'].dt.year() == 2026).sum():,} of {flock.height:,}")

    print_heading("7. RECIPE: CAMERAS -> 2024 COUNTIES (narrative cell 11)")
    counties = gpd.read_file(COUNTIES_ZIP, columns=["STATEFP", "GEOID", "NAME", "ALAND"])
    county_match = assign_polygons(flock, counties.rename(columns={"GEOID": "county_geoid"}), ["STATEFP", "county_geoid"])
    print(f"county shapes {len(counties):,} | cameras {flock.height:,} | within {(county_match['match_method'] == 'within').sum():,} "
          f"| nearest {(county_match['match_method'] == 'nearest').sum():,} | none {county_match['county_geoid'].null_count():,}")
    print(f"counties with a camera {county_match['county_geoid'].n_unique():,} | county shapes with no camera {len(counties) - county_match['county_geoid'].n_unique():,}")
    flock = flock.join(county_match.drop("match_method"), on="osm_id", how="left")
    print("cameras outside 50 states + DC by STATEFP:",
          flock.filter(~pl.col("STATEFP").is_in(list(STATE_FIPS_50_DC))).group_by("STATEFP").len().sort("STATEFP").rows())
    print(f"STATEFP values {flock['STATEFP'].n_unique()}")

    print_heading("8. RECIPE: CAMERAS -> 2024 TRACTS -> ACS")
    tract_files = sorted(TRACT_DIR.glob("tl_2024_*_tract.zip"))
    tracts_geo = gpd.GeoDataFrame(
        pd.concat([gpd.read_file(path, columns=["GEOID", "STATEFP", "COUNTYFP", "ALAND"]) for path in tract_files], ignore_index=True),
        geometry="geometry", crs=counties.crs,
    )
    tract_match = assign_polygons(flock, tracts_geo, ["GEOID"])
    print(f"tract shapes {len(tracts_geo):,} | within {(tract_match['match_method'] == 'within').sum():,} "
          f"| nearest {(tract_match['match_method'] == 'nearest').sum():,} | none {tract_match['GEOID'].null_count():,}")
    print("cameras with no tract by STATEFP:",
          flock.join(tract_match.filter(pl.col("GEOID").is_null()).select("osm_id"), on="osm_id", how="semi")
          .group_by("STATEFP").len().sort("STATEFP").rows())
    camera_tracts = tract_match.drop_nulls("GEOID").group_by("GEOID").len("cameras")
    print(f"tracts with a camera {camera_tracts.height:,} | max cameras in one tract {camera_tracts['cameras'].max()}")

    population = read_acs(POPULATION_CSV, ["B01003_001E"]).rename({"B01003_001E": "population"})
    income = read_acs(INCOME_CSV, ["B19013_001E"]).rename({"B19013_001E": "median_income"})
    poverty = read_acs(POVERTY_CSV, ["S1701_C03_001E"]).rename({"S1701_C03_001E": "pct_poverty"})
    race = read_acs(RACE_CSV, ["B03002_001E", "B03002_003E"]).with_columns(
        (pl.col("B03002_003E") / pl.col("B03002_001E") * 100).alias("pct_nh_white")
    ).select("GEOID", "pct_nh_white")
    acs = population.join(income, on="GEOID").join(poverty, on="GEOID").join(race, on="GEOID")
    shape_table = pl.from_pandas(pd.DataFrame(tracts_geo.drop(columns="geometry")))
    print(f"ACS rows after inner-joining four tables {acs.height:,}")
    print_join("camera tracts -> tract shapes", "GEOID", camera_tracts, shape_table, "GEOID", "GEOID")
    print_join("tract shapes -> ACS", "GEOID", shape_table, acs, "GEOID", "GEOID")
    print("ACS tracts without a shape, by state FIPS:", acs.join(shape_table, on="GEOID", how="anti").group_by(pl.col("GEOID").str.slice(0, 2)).len().rows())
    print("shapes without ACS, by county:", shape_table.join(acs, on="GEOID", how="anti").group_by(pl.col("GEOID").str.slice(0, 5)).len().rows())
    tract = (
        shape_table.join(acs, on="GEOID", how="left").join(camera_tracts, on="GEOID", how="left")
        .with_columns(pl.col("cameras").fill_null(0))
        .with_columns(pl.when(pl.col("population") > 0).then(pl.col("cameras") / pl.col("population") * 10_000).alias("cameras_per_10k"))
    )
    eligible = tract.filter(pl.col("population").is_not_null() & pl.col("median_income").is_not_null() & (pl.col("population") > 0))
    print(f"tract table rows {tract.height:,} | cameras in it {tract['cameras'].sum():,} | analysed tracts {eligible.height:,} "
          f"| zero-camera {(eligible['cameras'] == 0).sum():,} | cameras in analysed tracts {eligible['cameras'].sum():,}")
    print_profiles(tract, ["cameras", "cameras_per_10k"])

    build_county_votes(flock, counties, tracts_geo, acs)


######################
# BUILD COUNTY VOTES #
######################
def build_county_votes(flock: pl.DataFrame, counties: gpd.GeoDataFrame, tracts_geo: gpd.GeoDataFrame, acs: pl.DataFrame) -> None:
    """Rebuild the narrative's county units (old Connecticut counties) and join 2024 votes."""
    print_heading("9. RECIPE: COUNTY UNITS AND 2024 VOTES (narrative cell 23 method)")
    # The election file still reports Connecticut by its 8 old counties, so
    # rebuild them from the 2017 tract file.
    connecticut_2017 = gpd.read_file(CT_TRACTS_2017_ZIP, columns=["COUNTYFP", "ALAND"])
    old_counties = connecticut_2017.dissolve("COUNTYFP", aggfunc={"ALAND": "sum"}).reset_index()
    old_counties["county_key"] = "09" + old_counties["COUNTYFP"]
    old_counties = gpd.GeoDataFrame(old_counties, geometry="geometry", crs=counties.crs)
    connecticut_cameras = assign_polygons(flock.filter(pl.col("STATEFP") == "09"), old_counties, ["county_key"])
    print(f"CT cameras {connecticut_cameras.height:,} | without an old county {connecticut_cameras['county_key'].null_count()}")
    camera_keys = (
        flock.select("osm_id", "STATEFP", "county_geoid")
        .join(connecticut_cameras.select("osm_id", pl.col("county_key").alias("ct_key")), on="osm_id", how="left")
        .with_columns(pl.when(pl.col("STATEFP") == "09").then(pl.col("ct_key")).otherwise(pl.col("county_geoid")).alias("county_key"))
    )
    county_cameras = camera_keys.drop_nulls("county_key").group_by("county_key").len("cameras")

    elections = pl.read_csv(ELECTIONS_CSV, infer_schema_length=0)
    elections_2024 = elections.filter((pl.col("year") == "2024") & pl.col("party").is_in(["REPUBLICAN", "DEMOCRAT"])).with_columns(
        pl.col("county_fips").str.zfill(5).replace({"46113": "46102", "36000": "29095"}).alias("county_key"),
        pl.col("candidatevotes").cast(pl.Int64),
    )
    has_total = elections_2024.group_by("county_key").agg((pl.col("mode") == "TOTAL").any().alias("has_total"))
    elections_2024 = elections_2024.join(has_total, on="county_key").filter(~pl.col("has_total") | (pl.col("mode") == "TOTAL"))
    votes = elections_2024.group_by("county_key").agg(
        pl.col("candidatevotes").filter(pl.col("party") == "REPUBLICAN").sum().alias("rep"),
        pl.col("candidatevotes").filter(pl.col("party") == "DEMOCRAT").sum().alias("dem"),
    ).with_columns((pl.col("rep") / (pl.col("rep") + pl.col("dem")) * 100).alias("rep_share"))

    base = pl.concat([
        pl.from_pandas(pd.DataFrame(counties.drop(columns="geometry"))).filter(pl.col("STATEFP") != "09")
        .select(pl.col("GEOID").alias("county_key"), "STATEFP"),
        pl.from_pandas(pd.DataFrame(old_counties.drop(columns="geometry"))).select("county_key", pl.lit("09").alias("STATEFP")),
    ])
    print(f"county units {base.height:,} | vote counties {votes.height:,}")
    print_join("county cameras -> county units", "county_key", county_cameras, base, "county_key", "county_key")
    print_join("county units -> 2024 votes", "county_key", base, votes, "county_key", "county_key")
    print("county units without votes, by STATEFP:", base.join(votes, on="county_key", how="anti").group_by("STATEFP").len().sort("STATEFP").rows())
    county = base.join(county_cameras, on="county_key", how="left").join(votes, on="county_key", how="left").with_columns(pl.col("cameras").fill_null(0))
    print(f"county table cameras {county['cameras'].sum():,} of {flock.height:,} | cameras in units without votes "
          f"{county.filter(pl.col('rep_share').is_null())['cameras'].sum():,} | units with a vote {county['rep_share'].is_not_null().sum():,}")


########
# MAIN #
########
def main() -> None:
    """Run every section and print the results."""
    print_input_files()
    history = load_osm_history(HISTORY_CSV)
    history = profile_file(history)
    check_history_logic(history)
    compare_with_locations(history)
    build_recipe(history)


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()

#######
# EOF #
#######
