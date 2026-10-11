"""
##########
# LOADER #
##########

Load the EFF Atlas of Surveillance CSV saved by scripts/fetch_atlas.py.

One row = one (agency, technology) pair, e.g. "Rockford Police Department
uses Gunshot Detection". An agency that uses 3 technologies has 3 rows.
"""

###########
# IMPORTS #
###########
from datetime import date
from pathlib import Path
import polars as pl


RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# The raw CSV has 28 columns. These are the ones useful for analysis,
# renamed to simple snake_case names. (The rest are extra source links.)
RENAME = {
    "AOSNUMBER": "aos_id",                 # unique row id, e.g. "AOS000001"
    "NEWAOSNUMBER (ORI9)": "ori_tech_id",  # agency ORI code + technology code
    "Agency": "agency",
    "Type of LEA": "agency_type",          # Police, Sheriff, ...
    "Type of Juris": "jurisdiction_type",  # Municipal, County, State, ...
    "City": "city",
    "County": "county",
    "State": "state",                      # 2-letter code
    "Technology": "technology",            # ALPR, Drones, Face Recognition, ...
    "Vendor": "vendor",                    # e.g. "Flock Safety"
    "Summary": "summary",                  # one-sentence description
    "Link 1": "source_url",                # first evidence link
    "Link 1 Date": "source_date",          # date of that evidence (parsed below)
}


###########
# HELPERS #
###########
def latest_raw_file() -> Path:
    """Return the newest data/raw/atlas_of_surveillance_*.csv snapshot."""
    files = sorted(RAW_DIR.glob("atlas_of_surveillance_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No atlas_of_surveillance_*.csv in {RAW_DIR}. "
            "Run: uv run python scripts/fetch_atlas.py"
        )
    return files[-1] # names end in YYYY-MM-DD, so the last one is newest


##########
# LOADER #
##########
def load_atlas(path: str | Path | None = None) -> pl.DataFrame:
    """
    One row per (agency, technology). Uses the newest snapshot unless a path is given.
    """
    path = Path(path) if path else latest_raw_file()

    # infer_schema_length=0 reads every column as text. Safer for a messy
    # hand-made CSV; we convert the columns we need ourselves below.
    df = pl.read_csv(path, infer_schema_length=0).select(RENAME.keys()).rename(RENAME)

    return df.with_columns(
        # The CSV uses "" for missing values. Turn those into real nulls.
        pl.col(pl.String).replace("", None),
    ).with_columns(
        # "FRT" is a duplicate spelling of "Face Recognition" (6 rows)
        pl.col("technology").replace("FRT", "Face Recognition"),
        # Dates look like "10/06/2018". strict=False turns bad ones into null.
        # A few have typo years (e.g. 0005, 3023), so keep only 1990-today.
        pl.col("source_date").str.to_date("%m/%d/%Y", strict=False),
    ).with_columns(
        pl.when(pl.col("source_date").is_between(pl.date(1990, 1, 1), pl.lit(date.today())))
        .then(pl.col("source_date"))
        .otherwise(None)
        .alias("source_date")
    )


#######
# EOF #
#######