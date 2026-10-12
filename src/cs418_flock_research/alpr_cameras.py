##########
# LOADER #
##########
"""
Load ALPR camera GeoJSON files saved by fetch_alpr_cameras.py.

Coverage is ONLY cameras that OpenStreetMap volunteers have found and
tagged, so fewer cameras in an area may just mean fewer mappers there.

Example:
    from cs418_flock_research.alpr_cameras import load_alpr_cameras
    cams = load_alpr_cameras("Illinois_alpr.geojson")  # one row per camera
"""

###########
# IMPORTS #
###########
import json
from pathlib import Path
import polars as pl




RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


CAMERA_SCHEMA = {
    "osm_id": pl.Int64,              # the camera's unique id in OpenStreetMap
    "lon": pl.Float64,               # longitude (east/west)
    "lat": pl.Float64,               # latitude (north/south)
    "operator": pl.String,           # who runs it, e.g. a police department (often null)
    "manufacturer": pl.String,       # e.g. "Flock Safety", "Motorola Solutions"
    "direction": pl.String,          # compass direction it points, e.g. "180".
                                     # Kept as text because some cameras have
                                     # values like "0;180" or "N".
    "surveillance_type": pl.String,  # "ALPR" for all of these
    "man_made": pl.String,           # usually "surveillance"
    "timestamp": pl.String,          # when the camera was LAST edited in OSM (parsed to datetime below)
    "version": pl.Int64,             # 1 = never edited, so timestamp = when it was first added
    "all_tags": pl.String,           # every original OSM tag, as JSON text
}


##########
# LOADER #
##########
def load_alpr_cameras(path: str | Path) -> pl.DataFrame:
    """
    Load one GeoJSON file from fetch_alpr_cameras.py into a DataFrame,
    with one row per camera.
    """
    path = Path(path)

    if not path.exists():
        path = RAW_DIR / path

    with open(path, encoding="utf-8") as f:
        geojson = json.load(f)

    rows = []

    # Each "feature" is one camera. Flatten it into one simple dict (one row).
    for feature in geojson["features"]:
        # GeoJSON stores coordinates as [lon, lat] (longitude FIRST).
        # This "unpacks" the 2-item list into two variables.
        lon, lat = feature["geometry"]["coordinates"]

        # properties holds the camera info that to_geojson() pulled out.
        props = feature["properties"]

        rows.append(
            {
                "osm_id": props.get("osm_id"),
                "lon": lon,
                "lat": lat,
                "operator": props.get("operator"),
                "manufacturer": props.get("manufacturer"),
                "direction": props.get("direction"),
                "surveillance_type": props.get("surveillance_type"),
                "man_made": props.get("man_made"),
                # timestamp/version only exist in files pulled with "out meta"
                # (after 2026-09-28). Older files get null here.
                "timestamp": props.get("timestamp"),
                "version": props.get("version"),
                # all_tags is a dict with different keys for every camera,
                # which doesn't fit neatly in a table column. Store it as
                # JSON text instead. If you need a tag later, use:
                # pl.col("all_tags").str.json_path_match("$.surveillance:zone")
                "all_tags": json.dumps(props.get("all_tags", {})),
            }
        )

    # Turn the list of dicts into a polars DataFrame using our column types.
    # Then turn the timestamp text (e.g. "2025-03-14T18:22:05Z") into a real
    # datetime, so you can sort and filter by date.
    return pl.DataFrame(rows, schema=CAMERA_SCHEMA).with_columns(
        pl.col("timestamp").str.to_datetime(time_zone="UTC")
    )

#######
# EOF #
#######