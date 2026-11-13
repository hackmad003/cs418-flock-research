"""Read the OSM locations CSV without cleaning or filtering records.

Example:
    from cs418_flock_research.loaders.load_osm_locations import load_osm_locations
    locations = load_osm_locations()
    print(locations.shape, locations.schema)

Relative paths are relative to the repository root. An explicit sample path
may be supplied for testing; the default always reads the full raw dataset.
"""

###########
# IMPORTS #
###########
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parents[3]
LOCATIONS_FILE = ROOT / "data" / "raw" / "flock_osm" / "osm_flock_us_locations_2026-10-30.csv"


##########
# LOADER #
##########
def load_osm_locations(path: str | Path = LOCATIONS_FILE) -> pl.DataFrame:
    """Preserve every locations row and column, with IDs and dates as strings."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise FileNotFoundError(f"OSM locations CSV not found: {path}. Provide an existing raw or sample CSV path.")

    # Infer types from the whole file; keep IDs as text and dates unparsed.
    # Empty CSV fields use Polars' default null handling; no extra codes are added.
    return pl.read_csv(
        path,
        schema_overrides={"osm_id": pl.String},
        infer_schema_length=None,
        try_parse_dates=False,
    )
