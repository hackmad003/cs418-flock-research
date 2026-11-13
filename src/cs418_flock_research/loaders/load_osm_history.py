"""Read the OSM history CSV without cleaning or filtering records.

Example:
    from cs418_flock_research.loaders.load_osm_history import load_osm_history
    history = load_osm_history()
    print(history.shape, history.schema)

Relative paths are relative to the repository root. An explicit sample path
may be supplied for testing; the default always reads the full raw dataset.
"""

###########
# IMPORTS #
###########
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parents[3]
HISTORY_FILE = ROOT / "data" / "raw" / "flock_osm" / "flock_us_historical_2026-10-30.csv"


##########
# LOADER #
##########
def load_osm_history(path: str | Path = HISTORY_FILE) -> pl.DataFrame:
    """Preserve every history row and column, with IDs and dates as strings."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise FileNotFoundError(f"OSM history CSV not found: {path}. Provide an existing raw or sample CSV path.")

    # Infer types from the whole file; keep IDs as text and dates unparsed.
    # Empty CSV fields use Polars' default null handling; no extra codes are added.
    return pl.read_csv(
        path,
        schema_overrides={"osm_id": pl.String},
        infer_schema_length=None,
        try_parse_dates=False,
    )
