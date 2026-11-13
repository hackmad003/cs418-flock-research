#!/usr/bin/env python3
"""
Print every number used in docs/datasheets/DATASHEET_osm_flock_us_locations.md.

Input (read only, nothing is written):
    data/raw/flock_osm/osm_flock_us_locations_2026-10-30.csv   (primary)
    data/raw/flock_osm/flock_us_historical_2026-10-30.csv      (ID overlap only)
    data/raw/census/*/2024/ACS*-Data.csv                       (ACS 2024 5-year)
    data/raw/elections/presidential/countypres_2000-2024.csv   (MIT Election Lab)
    data/external/census_boundaries/2024/tl_2024_<FIPS>_tract.zip
    data/external/census_boundaries/2017/tl_2017_09_tract.zip  (old Connecticut counties)
    data/external/census_boundaries/counties/tl_2024_us_county.zip

Output: printed tables only.

The join steps repeat the rules in
checkpoints/Narrative_Analysis/narrative.ipynb (cells 2, 4, 17 and 23), so the
counts printed here are the counts behind the narrative's analysis tables.

Usage (from the project root, takes about one minute):
    uv run python scripts/datasheet_stats_osm_flock_us_locations.py
"""


###########
# IMPORTS #
###########
import json
# Used to read the all_tags column, which stores every OSM tag as JSON text.

import warnings
# Used to hide GeoPandas' geographic-CRS warning for the nearest-polygon step,
# which the narrative accepts on purpose (0.03 degrees is only a cut-off).

from datetime import datetime, timezone
# Used to show the file's modification time in UTC.

from pathlib import Path
# Used to build file paths from the project root.

import geopandas as gpd
# Used to read the tract and county shapes and place each camera inside one.

import pandas as pd
# Only needed to combine GeoPandas tables (GeoPandas is built on pandas).

import polars as pl
# Used for every table.

from cs418_flock_research.loaders.load_osm_history import load_osm_history
# Project loader for the history file (used only to compare IDs).

from cs418_flock_research.loaders.load_osm_locations import load_osm_locations
# Project loader for the primary file: reads it without cleaning.


#############
# CONSTANTS #
#############
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
EXTERNAL_DIR = ROOT / "data" / "external"

LOCATIONS_CSV = RAW_DIR / "flock_osm" / "osm_flock_us_locations_2026-10-30.csv"
HISTORY_CSV = RAW_DIR / "flock_osm" / "flock_us_historical_2026-10-30.csv"
POPULATION_CSV = RAW_DIR / "census" / "population" / "2024" / "ACSDT5Y2024.B01003-Data.csv"
INCOME_CSV = RAW_DIR / "census" / "median_household_income" / "2024" / "ACSDT5Y2024.B19013-Data.csv"
POVERTY_CSV = RAW_DIR / "census" / "poverty" / "2024" / "ACSST5Y2024.S1701-Data.csv"
RACE_CSV = RAW_DIR / "census" / "race_ethnicity" / "2024" / "ACSDT5Y2024.B03002-Data.csv"
ELECTIONS_CSV = RAW_DIR / "elections" / "presidential" / "countypres_2000-2024.csv"
TRACT_DIR = EXTERNAL_DIR / "census_boundaries" / "2024"
CT_TRACTS_2017_ZIP = EXTERNAL_DIR / "census_boundaries" / "2017" / "tl_2017_09_tract.zip"
COUNTIES_ZIP = EXTERNAL_DIR / "census_boundaries" / "counties" / "tl_2024_us_county.zip"

# The date written in the file name.
FILE_NAME_DATE = "2026-10-30"

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

# Placeholder text values that can hide "unknown".
PLACEHOLDER_TEXT = ["", "0", "-999", "9999", "unknown", "none", "n/a"]

# Columns whose share of nulls is above this are called "almost empty".
ALMOST_EMPTY_SHARE = 0.95


##################
# PRINT HEADING #
##################
def print_heading(title: str) -> None:
    """Print a visible section heading."""
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


######################
# MANUFACTURER STATUS #
######################
def manufacturer_status(manufacturer: str | None, brand: str | None) -> str:
    """Classify one manufacturer/brand pair with the narrative's Flock rule."""
    # Same rule as narrative.ipynb: a value naming a second vendor is
    # "ambiguous" and is not counted as a Flock camera.
    if manufacturer is None:
        return "missing"
    low = manufacturer.casefold().strip()
    if ";" in low or any(vendor in low for vendor in ("motorola", "platesmart", "genetec", "vigilant")):
        return "ambiguous"
    if brand is not None and "flock" not in brand.casefold():
        return "ambiguous"
    exact_spellings = {"flocksafety", "flock", "flockgroupinc.", "flockgroupinc", "flocksafetyinc", "flocksafetyinc."}
    if low.replace(" ", "") in exact_spellings:
        return "exact"
    if low.startswith("flock safety"):
        return "annotated"
    return "ambiguous"


################
# ADD IS FLOCK #
################
def add_is_flock(cameras: pl.DataFrame) -> pl.DataFrame:
    """Add manufacturer_status and is_flock columns (status is not 'ambiguous')."""
    # Classify each distinct pair once, then join back: far faster than per row.
    pairs = cameras.select("manufacturer", "brand").unique()
    statuses = [manufacturer_status(row["manufacturer"], row["brand"]) for row in pairs.iter_rows(named=True)]
    pairs = pairs.with_columns(
        pl.Series("manufacturer_status", statuses),
    ).with_columns((pl.col("manufacturer_status") != "ambiguous").alias("is_flock"))
    return cameras.join(pairs, on=["manufacturer", "brand"], how="left", nulls_equal=True)


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


###################
# READ ACS NUMBER #
###################
def acs_number(column_name: str) -> pl.Expr:
    """Convert ACS text to a number: '250,000+' -> 250001, '2,500-' -> 2499, '-' -> null."""
    # Same conversion as narrative.ipynb. Caps become one dollar past the cap
    # so they stay distinguishable from a real value of exactly 250,000.
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


########################
# PRINT JOIN ROW COUNTS #
########################
def print_join(name: str, key: str, left: pl.DataFrame, right: pl.DataFrame, left_key: str, right_key: str) -> None:
    """Print left rows, right rows, matched and unmatched on both sides of a key join."""
    left_keys = left.select(pl.col(left_key).alias("_key")).drop_nulls()
    right_keys = right.select(pl.col(right_key).alias("_key")).drop_nulls().unique()
    matched_left = left_keys.join(right_keys, on="_key", how="semi").height
    unmatched_left = left.height - matched_left
    unmatched_right = right_keys.join(left_keys.unique(), on="_key", how="anti").height
    print(f"JOIN {name} | key {key} | left rows {left.height:,} | right rows {right.height:,} | "
          f"left matched {matched_left:,} | left unmatched {unmatched_left:,} | right keys unmatched {unmatched_right:,}")


#######################
# PROFILE COLUMN #
#######################
def profile_column(table: pl.DataFrame, column_name: str) -> dict:
    """Return type, nulls, placeholders, unique count and min/max for one column."""
    column = table[column_name]
    profile = {
        "column": column_name,
        "type": str(column.dtype),
        "nulls": column.null_count(),
        "unique": column.n_unique(),
        "placeholders": 0,
        "min": None,
        "max": None,
    }
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


################
# PROFILE FILE #
################
def profile_file(cameras: pl.DataFrame) -> None:
    """Print shape, duplicates, dates, nulls, placeholders and category lists."""
    print_heading("1. FILE PROFILE")
    print(f"rows {cameras.height:,} | columns {cameras.width}")
    print(f"columns: {cameras.columns}")
    print(f"unique osm_id {cameras['osm_id'].n_unique():,} | fully identical rows {cameras.height - cameras.unique().height:,}")
    print(f"osm_type values: {cameras['osm_type'].value_counts().rows()}")

    shared_spot = cameras.filter(pl.struct("lat", "lon").is_duplicated())
    print(f"rows sharing exact coordinates with another row {shared_spot.height:,} "
          f"| distinct shared spots {shared_spot.select('lat', 'lon').unique().height:,}")
    spot_sizes = shared_spot.group_by("lat", "lon").len("rows_at_spot")
    print(f"most rows at one spot {spot_sizes['rows_at_spot'].max()}")

    # Dates: the file name says 2026-10-30; the newest edit shows the real pull time.
    print(f"timestamp min {cameras['timestamp'].min()} | max {cameras['timestamp'].max()}")
    after_name = cameras.filter(pl.col("timestamp") > f"{FILE_NAME_DATE}T23:59:59Z")
    print(f"cameras last edited after {FILE_NAME_DATE}: {after_name.height:,}")
    print("rows per last-edit day after the file-name date:",
          after_name.group_by(pl.col("timestamp").str.slice(0, 10)).len().sort("timestamp").rows())
    modified_utc = datetime.fromtimestamp(LOCATIONS_CSV.stat().st_mtime, tz=timezone.utc)
    print(f"file modification time on this computer (UTC): {modified_utc:%Y-%m-%d %H:%M}")
    print("rows per last-edit year:", cameras.group_by(pl.col("timestamp").str.slice(0, 4).alias("year")).len().sort("year").rows())

    print("\nper-column profile (placeholders = '', '0', '-999', '9999', 'unknown', 'none', 'n/a' or numeric 0/-999/9999):")
    profiles = pl.DataFrame([profile_column(cameras, name) for name in cameras.columns], infer_schema_length=None)
    profiles = profiles.with_columns(pl.col("min", "max").cast(pl.String))
    profiles = profiles.with_columns((pl.col("nulls") / cameras.height * 100).round(1).alias("null_pct"))
    with pl.Config(tbl_rows=40, tbl_width_chars=160, fmt_str_lengths=30):
        print(profiles)
    almost_empty = profiles.filter(pl.col("nulls") / cameras.height > ALMOST_EMPTY_SHARE)["column"].to_list()
    print(f"almost empty columns (> {ALMOST_EMPTY_SHARE:.0%} null): {almost_empty}")

    # direction is free text in OSM: single degrees, ranges ("338-23"), lists ("0;0") or letters.
    direction = cameras["direction"].drop_nulls()
    direction_single = direction.filter(direction.str.contains(r"^-?\d+(\.\d+)?$"))
    direction_number = direction_single.cast(pl.Float64)
    print(f"direction: single numbers {direction_single.len():,} | other text (ranges, lists, letters) {direction.len() - direction_single.len():,} "
          f"| numbers outside 0-360 {direction_number.filter((direction_number < 0) | (direction_number > 360)).len():,} "
          f"| exactly 0 {(direction_number == 0).sum():,}")

    with pl.Config(tbl_rows=25, fmt_str_lengths=45):
        for column_name in ["manufacturer", "brand", "camera_type", "surveillance_zone", "camera_mount", "camera_direction"]:
            print(f"\n{column_name}: {cameras[column_name].n_unique()} distinct (null counted as one)")
            print(cameras[column_name].value_counts(sort=True).head(12))

    user_counts = cameras["user"].value_counts(sort=True)
    print(f"\nuser: {cameras['user'].n_unique():,} distinct mappers | top mapper {user_counts['count'][0]:,} rows "
          f"| mappers with exactly one camera {(user_counts['count'] == 1).sum():,}")
    print(f"operator: {cameras['operator'].n_unique():,} distinct values (null counted as one)")
    print(f"changeset: {cameras['changeset'].n_unique():,} distinct | min {cameras['changeset'].min()} | max {cameras['changeset'].max()}")

    # all_tags: confirm it parses and count the most common keys.
    tag_counts: dict[str, int] = {}
    for tag_text in cameras["all_tags"]:
        for key in json.loads(tag_text):
            tag_counts[key] = tag_counts.get(key, 0) + 1
    print(f"all_tags: parsed {cameras.height:,} rows | distinct tag keys {len(tag_counts):,}")
    print("top all_tags keys:", sorted(tag_counts.items(), key=lambda item: -item[1])[:12])
    print(f"rows whose all_tags has 'brand' {tag_counts.get('brand', 0):,} | 'operator' {tag_counts.get('operator', 0):,}")


################
# COMPARE FILES #
################
def compare_with_history(cameras: pl.DataFrame) -> None:
    """Print how many osm_id values the locations and history files share."""
    print_heading("2. OVERLAP WITH THE HISTORY FILE (by osm_id)")
    history = load_osm_history(HISTORY_CSV).select("osm_id", "last_edit")
    in_both = cameras.join(history, on="osm_id", how="semi").height
    locations_only = cameras.join(history, on="osm_id", how="anti")
    print(f"locations rows {cameras.height:,} | history rows {history.height:,} | in both {in_both:,} "
          f"| locations only {locations_only.height:,} | history only {history.join(cameras, on='osm_id', how='anti').height:,}")
    print(f"history newest last_edit {history['last_edit'].max()} | locations-only rows edited after it "
          f"{locations_only.filter(pl.col('timestamp') > '2026-10-30T19:32:28Z').height:,}")


#################
# BUILD RECIPE #
#################
def build_recipe(cameras: pl.DataFrame) -> None:
    """Rebuild the narrative's camera, tract and county tables and print every count."""
    print_heading("3. RECIPE: FLOCK RULE")
    cameras = add_is_flock(cameras)
    print("manufacturer_status counts:", cameras["manufacturer_status"].value_counts(sort=True).rows())
    flock = cameras.filter("is_flock")
    print(f"rows before {cameras.height:,} | after keeping is_flock {flock.height:,} | dropped {cameras.height - flock.height}")
    print("dropped manufacturer/brand values:",
          cameras.filter(~pl.col("is_flock")).group_by("manufacturer", "brand").len().sort("manufacturer").rows())

    print_heading("4. RECIPE: CAMERAS -> 2024 COUNTIES (spatial)")
    counties = gpd.read_file(COUNTIES_ZIP, columns=["STATEFP", "GEOID", "NAME", "ALAND"])
    county_match = assign_polygons(flock, counties.rename(columns={"GEOID": "county_geoid"}), ["STATEFP", "county_geoid"])
    print(f"county shapes {len(counties):,} | 50 states + DC {counties['STATEFP'].isin(STATE_FIPS_50_DC).sum():,}")
    print(f"cameras {flock.height:,} | within a county {(county_match['match_method'] == 'within').sum():,} "
          f"| nearest county within {NEAREST_MAX_DEGREES} deg {(county_match['match_method'] == 'nearest').sum():,} "
          f"| no county {county_match['county_geoid'].null_count():,}")
    print(f"counties with at least one camera {county_match['county_geoid'].n_unique():,}")
    flock = flock.join(county_match.drop("match_method"), on="osm_id", how="left")
    outside = flock.filter(~pl.col("STATEFP").is_in(list(STATE_FIPS_50_DC)))
    print("cameras outside 50 states + DC by STATEFP:", outside.group_by("STATEFP").len().sort("STATEFP").rows())
    print(f"cameras by state: {flock['STATEFP'].n_unique()} STATEFP values")

    print_heading("5. RECIPE: CAMERAS -> 2024 TRACTS (spatial)")
    tract_files = sorted(TRACT_DIR.glob("tl_2024_*_tract.zip"))
    tracts_geo = gpd.GeoDataFrame(
        pd.concat([gpd.read_file(path, columns=["GEOID", "STATEFP", "COUNTYFP", "ALAND"]) for path in tract_files], ignore_index=True),
        geometry="geometry",
        crs=counties.crs,
    )
    tract_match = assign_polygons(flock, tracts_geo, ["GEOID"])
    print(f"tract files {len(tract_files)} | tract shapes {len(tracts_geo):,}")
    print(f"cameras {flock.height:,} | within a tract {(tract_match['match_method'] == 'within').sum():,} "
          f"| nearest tract {(tract_match['match_method'] == 'nearest').sum():,} | no tract {tract_match['GEOID'].null_count():,}")
    no_tract = flock.join(tract_match.filter(pl.col("GEOID").is_null()).select("osm_id"), on="osm_id", how="semi")
    print("cameras with no tract by STATEFP:", no_tract.group_by("STATEFP").len().sort("STATEFP").rows())
    camera_tracts = tract_match.drop_nulls("GEOID").group_by("GEOID").len("cameras")
    print(f"tracts with at least one camera {camera_tracts.height:,} | max cameras in one tract {camera_tracts['cameras'].max()}")

    print_heading("6. RECIPE: TRACTS -> ACS 2024")
    population = read_acs(POPULATION_CSV, ["B01003_001E"]).rename({"B01003_001E": "population"})
    income = read_acs(INCOME_CSV, ["B19013_001E"]).rename({"B19013_001E": "median_income"})
    poverty = read_acs(POVERTY_CSV, ["S1701_C03_001E"]).rename({"S1701_C03_001E": "pct_poverty"})
    race = read_acs(RACE_CSV, ["B03002_001E", "B03002_003E"]).with_columns(
        (pl.col("B03002_003E") / pl.col("B03002_001E") * 100).alias("pct_nh_white")
    ).select("GEOID", "pct_nh_white")
    print(f"ACS rows: population {population.height:,} | income {income.height:,} | poverty {poverty.height:,} | race {race.height:,}")
    acs = population.join(income, on="GEOID").join(poverty, on="GEOID").join(race, on="GEOID")
    print(f"ACS after inner-joining the four tables on GEOID {acs.height:,}")
    shape_table = pl.from_pandas(pd.DataFrame(tracts_geo.drop(columns="geometry")))
    print_join("tract shapes -> ACS", "GEOID", shape_table, acs, "GEOID", "GEOID")
    acs_without_shape = acs.join(shape_table, on="GEOID", how="anti")
    print("ACS tracts without a shape, by state FIPS:", acs_without_shape.group_by(pl.col("GEOID").str.slice(0, 2)).len().rows())
    shapes_without_acs = shape_table.join(acs, on="GEOID", how="anti")
    print("shapes without ACS:", shapes_without_acs.select("GEOID", "ALAND").rows())
    print_join("camera tracts -> tract table", "GEOID", camera_tracts, shape_table, "GEOID", "GEOID")

    tract = (
        shape_table.join(acs, on="GEOID", how="left")
        .join(camera_tracts, on="GEOID", how="left")
        .with_columns(pl.col("cameras").fill_null(0))
        .with_columns(
            pl.when(pl.col("population") > 0).then(pl.col("cameras") / pl.col("population") * 10_000).alias("cameras_per_10k"),
            (pl.col("ALAND") / 1e6).alias("land_km2"),
        )
    )
    eligible = tract.filter(pl.col("population").is_not_null() & pl.col("median_income").is_not_null() & (pl.col("population") > 0))
    print(f"tract table rows {tract.height:,} | cameras in it {tract['cameras'].sum():,}")
    print(f"tracts with population 0 {(tract['population'] == 0).sum():,} | null income {tract['median_income'].null_count():,} "
          f"| null poverty {tract['pct_poverty'].null_count():,} | null pct_nh_white {tract['pct_nh_white'].null_count():,}")
    print(f"analysed tracts (population > 0 and income present) {eligible.height:,} | zero-camera {(eligible['cameras'] == 0).sum():,} "
          f"| cameras in analysed tracts {eligible['cameras'].sum():,}")
    print_heading("7. CODEBOOK PROFILE: TRACT TABLE")
    with pl.Config(tbl_rows=20, tbl_width_chars=160):
        print(pl.DataFrame([profile_column(tract, name) for name in
                            ["GEOID", "population", "median_income", "pct_poverty", "pct_nh_white", "cameras", "cameras_per_10k", "land_km2"]],
                           infer_schema_length=None).with_columns(pl.col("min", "max").cast(pl.String)))
    print(f"median_income at the 250,000+ cap (250001) {(tract['median_income'] == 250001).sum():,} | at the 2,500- cap (2499) {(tract['median_income'] == 2499).sum():,}")

    build_county_table(flock, counties, tracts_geo, acs)


######################
# BUILD COUNTY TABLE #
######################
def build_county_table(flock: pl.DataFrame, counties: gpd.GeoDataFrame, tracts_geo: gpd.GeoDataFrame, acs: pl.DataFrame) -> None:
    """Rebuild the narrative's county table (with old Connecticut counties) and the vote join."""
    print_heading("8. RECIPE: CONNECTICUT OLD COUNTIES")
    # The election file still reports Connecticut by its 8 old counties, but
    # the 2024 county file uses 9 planning regions. Rebuild the old counties
    # from the 2017 tract file.
    connecticut_2017 = gpd.read_file(CT_TRACTS_2017_ZIP, columns=["COUNTYFP", "ALAND"])
    old_counties = connecticut_2017.dissolve("COUNTYFP", aggfunc={"ALAND": "sum"}).reset_index()
    old_counties["county_key"] = "09" + old_counties["COUNTYFP"]
    old_counties = gpd.GeoDataFrame(old_counties, geometry="geometry", crs=counties.crs)
    connecticut_cameras = assign_polygons(flock.filter(pl.col("STATEFP") == "09"), old_counties, ["county_key"])
    print(f"old CT counties {len(old_counties)} | CT cameras {connecticut_cameras.height:,} | without an old county {connecticut_cameras['county_key'].null_count()}")
    camera_keys = (
        flock.select("osm_id", "STATEFP", "county_geoid")
        .join(connecticut_cameras.select("osm_id", pl.col("county_key").alias("ct_key")), on="osm_id", how="left")
        .with_columns(pl.when(pl.col("STATEFP") == "09").then(pl.col("ct_key")).otherwise(pl.col("county_geoid")).alias("county_key"))
    )
    county_cameras = camera_keys.drop_nulls("county_key").group_by("county_key").len("cameras")

    # Connecticut tracts -> old county by a point inside each tract.
    ct_tracts = tracts_geo[tracts_geo["STATEFP"] == "09"][["GEOID", "geometry"]].copy()
    ct_tracts["geometry"] = ct_tracts.geometry.representative_point()
    ct_map = pl.from_pandas(pd.DataFrame(gpd.sjoin(ct_tracts, old_counties[["county_key", "geometry"]], predicate="within")[["GEOID", "county_key"]]))
    print(f"CT 2024 tracts {len(ct_tracts):,} | mapped to an old county {ct_map.height:,}")
    county_acs = (
        acs.join(ct_map.rename({"county_key": "ct_key"}), on="GEOID", how="left")
        .with_columns(pl.when(pl.col("GEOID").str.starts_with("09")).then(pl.col("ct_key")).otherwise(pl.col("GEOID").str.slice(0, 5)).alias("county_key"))
        .drop_nulls("county_key")
        .group_by("county_key")
        .agg(pl.col("population").sum())
    )

    print_heading("9. RECIPE: ELECTION RETURNS (MIT Election Lab, 2024)")
    elections = pl.read_csv(ELECTIONS_CSV, infer_schema_length=0)
    print(f"election rows (all years) {elections.height:,} | years {sorted(elections['year'].unique().to_list())[:1]}..{sorted(elections['year'].unique().to_list())[-1]} "
          f"| version values {elections['version'].unique().to_list()}")
    elections_2024 = elections.filter((pl.col("year") == "2024") & pl.col("party").is_in(["REPUBLICAN", "DEMOCRAT"]))
    print(f"2024 Republican + Democrat rows {elections_2024.height:,} | null county_fips {elections_2024['county_fips'].null_count()}")
    print("2024 mode values:", elections_2024["mode"].value_counts(sort=True).rows())
    # Two county code fixes, as in the narrative: Shannon SD (46113) was renamed
    # Oglala Lakota (46102); 36000 is a Kansas City placeholder put with Jackson County MO.
    elections_2024 = elections_2024.with_columns(
        pl.col("county_fips").str.zfill(5).replace({"46113": "46102", "36000": "29095"}).alias("county_key"),
        pl.col("candidatevotes").cast(pl.Int64),
    )
    print(f"rows recoded: 46113 -> 46102 {(elections_2024['county_fips'].str.zfill(5) == '46113').sum()} "
          f"| 36000 -> 29095 {(elections_2024['county_fips'].str.zfill(5) == '36000').sum()}")
    has_total = elections_2024.group_by("county_key").agg((pl.col("mode") == "TOTAL").any().alias("has_total"))
    elections_2024 = elections_2024.join(has_total, on="county_key").filter(~pl.col("has_total") | (pl.col("mode") == "TOTAL"))
    votes = elections_2024.group_by("county_key").agg(
        pl.col("candidatevotes").filter(pl.col("party") == "REPUBLICAN").sum().alias("rep"),
        pl.col("candidatevotes").filter(pl.col("party") == "DEMOCRAT").sum().alias("dem"),
    ).with_columns((pl.col("rep") / (pl.col("rep") + pl.col("dem")) * 100).alias("rep_share"))
    print(f"vote counties {votes.height:,} | rep_share min {votes['rep_share'].min():.2f} | max {votes['rep_share'].max():.2f} "
          f"| null {votes['rep_share'].null_count()}")

    print_heading("10. RECIPE: COUNTY TABLE")
    base = pl.concat([
        pl.from_pandas(pd.DataFrame(counties.drop(columns="geometry"))).filter(pl.col("STATEFP") != "09")
        .select(pl.col("GEOID").alias("county_key"), "STATEFP", (pl.col("ALAND") / 1e6).alias("land_km2")),
        pl.from_pandas(pd.DataFrame(old_counties.drop(columns="geometry")))
        .select("county_key", pl.lit("09").alias("STATEFP"), (pl.col("ALAND") / 1e6).alias("land_km2")),
    ])
    print(f"county units {base.height:,} (2024 counties outside CT + 8 old CT counties)")
    print_join("county cameras -> county units", "county_key", county_cameras, base, "county_key", "county_key")
    print_join("county units -> county ACS", "county_key", base, county_acs, "county_key", "county_key")
    print("county units without ACS, by STATEFP:",
          base.join(county_acs, on="county_key", how="anti").group_by("STATEFP").len().sort("STATEFP").rows())
    print(f"county shapes with no camera {len(counties) - flock['county_geoid'].n_unique():,}")
    print_join("county units -> 2024 votes", "county_key", base, votes, "county_key", "county_key")
    no_votes = base.join(votes, on="county_key", how="anti")
    print("county units without votes, by STATEFP:", no_votes.group_by("STATEFP").len().sort("STATEFP").rows())
    votes_without_unit = votes.join(base, on="county_key", how="anti")
    print("vote counties without a county unit:", votes_without_unit["county_key"].sort().to_list()[:40], f"(n = {votes_without_unit.height})")

    county = (
        base.join(county_cameras, on="county_key", how="left")
        .join(county_acs, on="county_key", how="left")
        .join(votes, on="county_key", how="left")
        .with_columns(pl.col("cameras").fill_null(0))
    )
    analysed = county.filter(pl.col("rep_share").is_not_null() & (pl.col("population") > 0))
    print(f"county table cameras {county['cameras'].sum():,} of {flock.height:,}")
    print(f"analysed counties (vote + residents) {analysed.height:,} | cameras {analysed['cameras'].sum():,} "
          f"| zero-camera {(analysed['cameras'] == 0).sum():,}")
    print(f"cameras in county units without votes {county.filter(pl.col('rep_share').is_null())['cameras'].sum():,}")


#####################
# PRINT INPUT DATES #
#####################
def print_input_dates() -> None:
    """Print each input file's local modification time (UTC), the best record of when it was saved."""
    # No download dates were recorded for the manual downloads, so the file
    # times on this computer are the only evidence left. Copying a file can
    # change them, so they are an upper bound on the access date, not proof.
    print_heading("0. INPUT FILES (local modification time, UTC)")
    sample_path = ROOT / "data" / "processed" / "samples" / "flock_osm" / "osm_flock_us_locations_2026-10-30_sample.csv"
    input_paths = [LOCATIONS_CSV, HISTORY_CSV, POPULATION_CSV, INCOME_CSV, POVERTY_CSV, RACE_CSV,
                   ELECTIONS_CSV, CT_TRACTS_2017_ZIP, COUNTIES_ZIP, *sorted(TRACT_DIR.glob("tl_2024_*_tract.zip"))[:1]]
    for input_path in input_paths:
        modified_utc = datetime.fromtimestamp(input_path.stat().st_mtime, tz=timezone.utc)
        print(f"{modified_utc:%Y-%m-%d %H:%M}  {input_path.relative_to(ROOT).as_posix()}")
    if sample_path.exists():
        sample_columns = pl.read_csv(sample_path, n_rows=1).columns
        print(f"tracked sample {sample_path.relative_to(ROOT).as_posix()}: rows {pl.read_csv(sample_path, infer_schema_length=0).height} "
              f"| has 'user' column: {'user' in sample_columns}")


########
# MAIN #
########
def main() -> None:
    """Run every section and print the results."""
    print_input_dates()
    cameras = load_osm_locations(LOCATIONS_CSV)
    profile_file(cameras)
    compare_with_history(cameras)
    build_recipe(cameras)


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()

#######
# EOF #
#######
