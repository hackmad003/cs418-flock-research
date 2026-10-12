"""
##########
# LOADER #
##########

Load US Census data by ZIP code (ZCTA) saved by scripts/fetch_census.py.

One row = one ZCTA (the Census's version of a ZIP code), with its median
household income, population, land area, and population density.

Data: ACS 5-year estimates 2020-2024 (an average over those 5 years, not a
single year) + 2024 Gazetteer land areas.

Example:
    from cs418_flock_research.census import load_zcta

    zcta = load_zcta()

VVV Sources VVV
https://www.census.gov/programs-surveys/acs/data/summary-file.html
https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html (what a ZCTA is)
https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html (negative codes = no estimate)

"""

###########
# IMPORTS #
###########
import io
import zipfile
from pathlib import Path

import polars as pl



# <repo>/data/raw/census/
CENSUS_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "census"

# In the ACS files, every ZIP code row's GEO_ID starts with this,
# e.g. "860Z200US60601" -> ZIP 60601
ZCTA_PREFIX = "860Z200US"


###########
# HELPERS #
###########
def _read_acs(file_name: str, estimate_col: str, new_name: str) -> pl.DataFrame:
    """
    Read one ACS table file, keep only ZIP code rows, and return (zcta, value).
    """
    # The .dat files are CSVs separated by | instead of commas.
    # Read as text first, because missing values are coded as -666666666.
    df = pl.read_csv(CENSUS_DIR / file_name, separator="|", infer_schema_length=0)

    return (
        df.filter(pl.col("GEO_ID").str.starts_with(ZCTA_PREFIX))  # ZIP rows only
        .select(
            # "860Z200US60601" -> "60601" (kept as text: ZIPs can start with 0)
            pl.col("GEO_ID").str.strip_prefix(ZCTA_PREFIX).alias("zcta"),
            pl.col(estimate_col).cast(pl.Int64).alias(new_name),
        )
        # Negative numbers are Census codes for "no estimate" -> null
        .with_columns(
            pl.when(pl.col(new_name) >= 0).then(pl.col(new_name)).alias(new_name)
        )
    )


##################
# READ_GAZETTEER #
##################
def _read_gazetteer() -> pl.DataFrame:
    """Read ZIP land areas from the Gazetteer zip file."""
    with zipfile.ZipFile(CENSUS_DIR / "2024_Gaz_zcta_national.zip") as z:
        raw = z.read("2024_Gaz_zcta_national.txt")

    # Tab-separated. GEOID is read as text so ZIPs like "00601" keep their 0s.
    df = pl.read_csv(io.BytesIO(raw), separator="\t", schema_overrides={"GEOID": pl.String})

    # The last column name has extra spaces at the end ("INTPTLONG      "), so strip them
    df.columns = [c.strip() for c in df.columns]

    return df.select(
        pl.col("GEOID").alias("zcta"),
        pl.col("ALAND_SQMI").alias("land_sqmi"),   # land area in square miles
        pl.col("INTPTLAT").alias("lat"),           # a point inside the ZIP
        # this column has trailing spaces in the raw file, so strip them and make it a number
        pl.col("INTPTLONG").cast(pl.String).str.strip_chars().cast(pl.Float64).alias("lon"),
    )


##########
# LOADER #
##########
def load_zcta() -> pl.DataFrame:
    """
    One row per ZIP code (ZCTA): income, population, land area, and density.
    """
    income = _read_acs("acsdt5y2024-b19013.dat", "B19013_E001", "median_household_income")
    pop = _read_acs("acsdt5y2024-b01003.dat", "B01003_E001", "population")
    area = _read_gazetteer()

    # Join the three tables on the ZIP code.
    # how="left" keeps every ZIP from the income table even if it's missing elsewhere.
    return (
        income.join(pop, on="zcta", how="left")
        .join(area, on="zcta", how="left")
        .with_columns(
            # people per square mile (null if the ZIP has no land area, to avoid dividing by 0)
            pl.when(pl.col("land_sqmi") > 0)
            .then(pl.col("population") / pl.col("land_sqmi"))
            .alias("pop_per_sqmi")
        )
    )

#######
# EOF #
#######