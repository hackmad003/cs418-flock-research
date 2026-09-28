#!/usr/bin/env python3
"""
Save a small sample (first 100 rows) of each RAW dataset to data/processed/sample/.

The full raw files are gitignored (too big for GitHub). The samples ARE
committed, so anyone can see what the data looks like without downloading it.
Each dataset is loaded exactly the way notebooks/00_explore_raw.ipynb loads it,
so the sample columns match the notebook and the README.

Run AFTER the fetch scripts:
    uv run python scripts/make_samples.py

VVV Sources VVV
https://docs.pola.rs/user-guide/io/csv/ (writing CSV with polars)

Imports Used:
import io # https://docs.python.org/3/library/io.html
import json # https://docs.python.org/3/library/json.html
import zipfile # https://docs.python.org/3/library/zipfile.html
from pathlib import Path # https://docs.python.org/3/library/pathlib.html
import polars as pl # https://docs.pola.rs/api/python/stable/reference/index.html

Built-In Functions Used:
open() https://docs.python.org/3/library/functions.html#open
print() https://docs.python.org/3/library/functions.html#print
sorted() https://docs.python.org/3/library/functions.html#sorted

Object Methods Used:
json.load() https://docs.python.org/3/library/json.html#json.load
zipfile.ZipFile() https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
io.BytesIO() https://docs.python.org/3/library/io.html#io.BytesIO
Path.glob() https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.strip() https://docs.python.org/3/library/stdtypes.html#str.strip
.items() https://docs.python.org/3/library/stdtypes.html#dict.items

Polars Used:
pl.DataFrame() https://docs.pola.rs/api/python/stable/reference/dataframe/index.html
pl.read_csv() https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html
.filter() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.filter.html
.str.starts_with() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.str.starts_with.html
.head() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.head.html
.with_columns() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.with_columns.html
.struct.json_encode() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.struct.json_encode.html
.list.join() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.list.join.html
.write_csv() https://docs.pola.rs/api/python/stable/reference/api/polars.DataFrame.write_csv.html

Data Structures / Techniques Used:
dict (datasets: name -> DataFrame) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
list comprehension ([col.strip() for col in ...]) https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
"""

###########
# IMPORTS #
###########
import io
import json
import zipfile
from pathlib import Path

import polars as pl


#############
# CONSTANTS #
#############
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CENSUS = RAW / "census"
SAMPLE_DIR = ROOT / "data" / "processed" / "sample"
N_ROWS = 100
ZIP_PREFIX = "860Z200US"  # ACS rows whose GEO_ID starts with this are ZIP codes


###########
# LOADERS #
###########
# Same loading code as notebooks/00_explore_raw.ipynb.

def load_cameras() -> pl.DataFrame:
    """One row per camera: [lon, lat] from geometry plus every property."""
    with open(RAW / "Illinois_alpr.geojson", encoding="utf-8") as f:
        geojson = json.load(f)

    rows = []
    for feature in geojson["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        rows.append({"lon": lon, "lat": lat, **feature["properties"]})
    return pl.DataFrame(rows)


def load_portals() -> pl.DataFrame:
    """One row per agency portal, from the newest Eyes On Flock snapshot."""
    with open(sorted(RAW.glob("eyesonflock_*.json"))[-1], encoding="utf-8") as f:
        return pl.DataFrame(json.load(f)["portals"])


def load_atlas() -> pl.DataFrame:
    """One row per (agency, technology) pair, from the newest Atlas snapshot."""
    return pl.read_csv(sorted(RAW.glob("atlas_of_surveillance_*.csv"))[-1])


def load_acs(file_name: str) -> pl.DataFrame:
    """One ACS table (separated by |), ZIP code rows only."""
    df = pl.read_csv(CENSUS / file_name, separator="|")
    return df.filter(pl.col("GEO_ID").str.starts_with(ZIP_PREFIX))


def load_gazetteer() -> pl.DataFrame:
    """ZIP land areas. GEOID is read as text so ZIPs like "00601" keep their leading zeros."""
    with zipfile.ZipFile(CENSUS / "2024_Gaz_zcta_national.zip") as z:
        df = pl.read_csv(io.BytesIO(z.read(z.namelist()[0])), separator="\t", schema_overrides={"GEOID": pl.String})
    # The last column name has trailing spaces ("INTPTLONG      "), so strip every column name
    df.columns = [col.strip() for col in df.columns]
    return df


########
# MAIN #
########
def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    datasets = {
        "osm_alpr_cameras_illinois": load_cameras(),
        "eyesonflock_portals": load_portals(),
        "atlas_of_surveillance": load_atlas(),
        "census_income_zcta": load_acs("acsdt5y2024-b19013.dat"),
        "census_population_zcta": load_acs("acsdt5y2024-b01003.dat"),
        "census_gazetteer": load_gazetteer(),
    }

    for name, df in datasets.items():
        sample = df.head(N_ROWS).with_columns(
            # CSV can't store nested values, so turn them into text:
            # dicts (all_tags) become JSON text, lists become "a; b; c"
            pl.col(pl.Struct).struct.json_encode(),
            pl.col(pl.List(pl.String)).list.join("; "),
        )
        out_path = SAMPLE_DIR / f"{name}_sample.csv"
        sample.write_csv(out_path)
        print(f"Wrote {sample.height} rows x {sample.width} columns to {out_path}")


###############
# ENTRY_POINT #
###############
if __name__ == "__main__":
    main()

#######
# EOF #
#######
