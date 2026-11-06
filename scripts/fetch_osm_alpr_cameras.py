
#!/usr/bin/env python3
"""
Fetch ALPR camera locations and attributes from OpenStreetMap
using the Overpass API.

Supports:
    - US state queries
    - Bounding box queries
    - Place-name queries through Nominatim
    - Nationwide US queries
    - All ALPR cameras or Flock-only cameras
    - CSV and GeoJSON output
    - Overpass metadata and all original OSM tags
    - Retry handling for temporary API errors

Examples:
    uv run python scripts/fetch_alpr_cameras.py --state Illinois
    uv run python scripts/fetch_alpr_cameras.py --state Illinois --format csv
    uv run python scripts/fetch_alpr_cameras.py --place "Orland Park, Illinois"
    uv run python scripts/fetch_alpr_cameras.py --bbox 41.6,-87.9,42.1,-87.5
    uv run python scripts/fetch_alpr_cameras.py --nationwide --flock-only --format csv

Dependencies:
    uv add requests
"""

################
# IMPORTS
################

import argparse
import csv
import json
import random
import sys
import time

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests


################
# CONFIGURATION
################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "osm"

SNAPSHOT_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

ENDPOINTS = [
    "https://overpass.deflock.org/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

HEADERS = {
    "User-Agent": "CS418-flock-research-project/1.0 (student research)",
}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

MAX_RETRIES = 3

RETRY_DELAYS = [30, 60, 120]

RETRY_STATUSES = {429, 500, 502, 503, 504}

REQUEST_TIMEOUT = 660


################
# GEOCODE PLACE
################

def geocode_place(place_name: str):
    """
    Convert a place name into a bounding box.

    Returns:
        (south, west, north, east)
    """

    print(f"Geocoding: {place_name}")

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": place_name,
            "format": "json",
            "limit": 1,
        },
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        raise RuntimeError(
            f"Nominatim found no match for: {place_name}"
        )

    result = results[0]

    south, north, west, east = map(
        float,
        result["boundingbox"],
    )

    print(f"Matched: {result['display_name']}")

    time.sleep(1)

    return south, west, north, east


################
# QUERY FILTERS
################

def camera_filters(flock_only: bool) -> str:
    """
    Build the OSM tag filters.

    Default:
        All nodes tagged surveillance:type=ALPR.

    Flock-only:
        Require man_made=surveillance,
        surveillance:type=ALPR,
        and manufacturer containing Flock.
    """

    if flock_only:
        return (
            '["man_made"="surveillance"]'
            '["surveillance:type"="ALPR"]'
            '["manufacturer"~"Flock",i]'
        )

    return '["surveillance:type"="ALPR"]'


################
# BUILD QUERY BY STATE
################

def build_query_by_state(
    state_name: str,
    flock_only: bool = False,
    timeout: int = 180,
) -> str:
    """
    Search one US state for ALPR camera nodes.
    """

    filters = camera_filters(flock_only)

    # Escape the state name for an Overpass string literal.
    safe_state = json.dumps(state_name)

    return f"""
    [out:json][timeout:{timeout}];

    area["name"={safe_state}]
        ["admin_level"="4"]->.searchArea;

    node{filters}(area.searchArea);

    out meta;
    """


################
# BUILD QUERY BY BBOX
################

def build_query_by_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
    flock_only: bool = False,
    timeout: int = 180,
) -> str:
    """
    Search a geographic bounding box.

    Bounding box order:
        south, west, north, east
    """

    filters = camera_filters(flock_only)

    bbox = f"{south},{west},{north},{east}"

    return f"""
    [out:json][timeout:{timeout}];

    node{filters}({bbox});

    out meta;
    """


################
# BUILD QUERY NATIONWIDE
################

def build_query_nationwide(
    flock_only: bool = False,
    timeout: int = 600,
) -> str:
    """
    Search the United States for ALPR camera nodes.

    Nationwide queries can be expensive and may
    exceed public Overpass server resource limits.
    """

    filters = camera_filters(flock_only)

    return f"""
    [out:json][timeout:{timeout}];

    area["ISO3166-1"="US"]->.searchArea;

    node{filters}(area.searchArea);

    out meta;
    """


################
# RETRY DELAY
################

def get_retry_delay(response, attempt: int) -> int:
    """
    Respect Retry-After when supplied by the server.
    Otherwise use exponential-style backoff.
    """

    delay = RETRY_DELAYS[attempt]

    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            delay = max(delay, int(retry_after))

        except ValueError:
            try:
                retry_date = parsedate_to_datetime(retry_after)

                if retry_date.tzinfo is None:
                    retry_date = retry_date.replace(
                        tzinfo=timezone.utc
                    )

                seconds = (
                    retry_date - datetime.now(timezone.utc)
                ).total_seconds()

                delay = max(delay, int(max(0, seconds)))

            except (TypeError, ValueError, OverflowError):
                pass

    return delay


################
# RUN QUERY
################

def run_query(query: str) -> dict:
    """
    Send an Overpass query and return its JSON response.

    Try configured endpoints sequentially, using bounded
    retries for temporary failures.
    """

    last_error = None

    for endpoint in ENDPOINTS:

        print(f"\nTrying endpoint: {endpoint}")

        for attempt in range(MAX_RETRIES):

            print(
                f"Request attempt "
                f"{attempt + 1}/{MAX_RETRIES}"
            )

            try:
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )

                if response.status_code in RETRY_STATUSES:

                    response.raise_for_status()

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    raise ValueError(
                        "Overpass returned an unexpected JSON structure."
                    )

                if "elements" not in data:
                    raise ValueError(
                        "Overpass response is missing 'elements'."
                    )

                if not isinstance(data["elements"], list):
                    raise ValueError(
                        "Overpass 'elements' is not a list."
                    )

                print("Overpass query succeeded.")

                return data

            except requests.HTTPError as exc:

                last_error = exc
                status = exc.response.status_code

                print(f"HTTP error: {status}")

                if status not in RETRY_STATUSES:
                    raise

                if attempt == MAX_RETRIES - 1:
                    break

                delay = get_retry_delay(
                    exc.response,
                    attempt,
                )

                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

            except (
                requests.Timeout,
                requests.ConnectionError,
            ) as exc:

                last_error = exc

                print(f"Network error: {exc}")

                if attempt == MAX_RETRIES - 1:
                    break

                delay = RETRY_DELAYS[attempt]

                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

            except (ValueError, requests.exceptions.JSONDecodeError) as exc:
                last_error = exc
                print(f"Invalid response: {exc}")
                break

        print("Endpoint unavailable or unable to complete query.")

        # Avoid immediately sending another expensive request.
        time.sleep(10)

    raise RuntimeError(
        f"All Overpass endpoints failed. Last error: {last_error}"
    )


################
# TO GEOJSON
################

def to_geojson(overpass_json: dict) -> dict:
    """
    Convert Overpass nodes into GeoJSON features.

    Preserve all original OSM tags and metadata.
    """

    features = []

    for el in overpass_json.get("elements", []):

        if el.get("type") != "node":
            continue

        tags = el.get("tags", {})

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    el["lon"],
                    el["lat"],
                ],
            },
            "properties": {
                "osm_type": el.get("type"),
                "osm_id": el.get("id"),
                "operator": tags.get("operator"),
                "manufacturer": (
                    tags.get("manufacturer")
                    or tags.get("brand")
                ),
                "camera_direction": tags.get("camera:direction"),
                "direction": tags.get("direction"),
                "camera_type": tags.get("camera:type"),
                "camera_mount": tags.get("camera:mount"),
                "camera_angle": tags.get("camera:angle"),
                "surveillance_zone": tags.get("surveillance:zone"),
                "surveillance_type": tags.get("surveillance:type"),
                "man_made": tags.get("man_made"),
                "timestamp": el.get("timestamp"),
                "version": el.get("version"),
                "changeset": el.get("changeset"),
                "user": el.get("user"),
                "all_tags": tags,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


################
# TO CSV
################

CSV_COLUMNS = [
    "osm_type",
    "osm_id",
    "lat",
    "lon",
    "timestamp",
    "version",
    "changeset",
    "user",
    "man_made",
    "surveillance_type",
    "manufacturer",
    "brand",
    "operator",
    "camera_direction",
    "direction",
    "camera_type",
    "camera_mount",
    "camera_angle",
    "surveillance_zone",
    "all_tags",
]


def to_csv(overpass_json: dict, output_path: Path) -> int:
    """
    Convert Overpass JSON to CSV.

    One row represents one OSM node.

    all_tags contains the original OSM tags serialized
    as JSON so no additional tags are discarded.
    """

    elements = overpass_json.get("elements", [])

    count = 0

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=CSV_COLUMNS,
        )

        writer.writeheader()

        for el in elements:

            if el.get("type") != "node":
                continue

            tags = el.get("tags", {})

            writer.writerow({
                "osm_type": el.get("type"),
                "osm_id": el.get("id"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "timestamp": el.get("timestamp"),
                "version": el.get("version"),
                "changeset": el.get("changeset"),
                "user": el.get("user"),
                "man_made": tags.get("man_made"),
                "surveillance_type": tags.get("surveillance:type"),
                "manufacturer": tags.get("manufacturer"),
                "brand": tags.get("brand"),
                "operator": tags.get("operator"),
                "camera_direction": tags.get("camera:direction"),
                "direction": tags.get("direction"),
                "camera_type": tags.get("camera:type"),
                "camera_mount": tags.get("camera:mount"),
                "camera_angle": tags.get("camera:angle"),
                "surveillance_zone": tags.get("surveillance:zone"),
                "all_tags": json.dumps(
                    tags,
                    ensure_ascii=False,
                ),
            })

            count += 1

    return count


################
# SAVE DATASET
################

def save_dataset(
    overpass_json: dict,
    output_path: Path,
    output_format: str,
) -> None:
    """
    Save CSV or GeoJSON without overwriting an
    existing dataset.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        raise FileExistsError(
            f"Output already exists: {output_path}\n"
            "Use a different filename to preserve your snapshot."
        )

    if output_format == "csv":

        count = to_csv(
            overpass_json,
            output_path,
        )

    else:

        geojson = to_geojson(overpass_json)

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                geojson,
                f,
                indent=2,
                ensure_ascii=False,
            )

        count = len(geojson["features"])

    print()
    print("Export completed successfully.")
    print(f"Saved: {output_path}")
    print(f"Camera nodes: {count:,}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


################
# MAIN
################

def main():

    parser = argparse.ArgumentParser(
        description="Fetch ALPR camera nodes from OSM/Overpass."
    )

    scope = parser.add_mutually_exclusive_group(
        required=True
    )

    scope.add_argument(
        "--state",
        help='US state name, e.g. "Illinois"',
    )

    scope.add_argument(
        "--bbox",
        help="south,west,north,east",
    )

    scope.add_argument(
        "--place",
        help='Place name, e.g. "Orland Park, Illinois"',
    )

    scope.add_argument(
        "--nationwide",
        action="store_true",
        help="Query the entire United States",
    )

    parser.add_argument(
        "--flock-only",
        action="store_true",
        help="Only nodes matching strict Flock ALPR tags",
    )

    parser.add_argument(
        "--format",
        choices=["csv", "geojson"],
        default="geojson",
        help="Output format (default: geojson)",
    )

    parser.add_argument(
        "--out",
        default=None,
        help="Output file path",
    )

    args = parser.parse_args()

    ################
    # BUILD QUERY
    ################

    if args.state:

        query = build_query_by_state(
            args.state,
            flock_only=args.flock_only,
        )

        scope_name = (
            args.state.lower()
            .replace(" ", "_")
        )

    elif args.bbox:

        try:
            parts = [
                float(value)
                for value in args.bbox.split(",")
            ]

        except ValueError:
            parser.error(
                "--bbox must contain four numeric coordinates."
            )

        if len(parts) != 4:
            parser.error(
                "--bbox must be south,west,north,east"
            )

        south, west, north, east = parts

        if not (
            -90 <= south < north <= 90
            and -180 <= west < east <= 180
        ):
            parser.error(
                "Invalid bounding box coordinates."
            )

        query = build_query_by_bbox(
            south,
            west,
            north,
            east,
            flock_only=args.flock_only,
        )

        scope_name = "bbox"

    elif args.place:

        south, west, north, east = geocode_place(
            args.place
        )

        query = build_query_by_bbox(
            south,
            west,
            north,
            east,
            flock_only=args.flock_only,
        )

        scope_name = (
            args.place.lower()
            .replace(",", "")
            .replace(" ", "_")
        )

    else:

        query = build_query_nationwide(
            flock_only=args.flock_only,
        )

        scope_name = "us"

    ################
    # OUTPUT PATH
    ################

    camera_label = (
        "flock"
        if args.flock_only
        else "alpr"
    )

    default_name = (
        f"{camera_label}_{scope_name}_"
        f"{SNAPSHOT_DATE}.{args.format}"
    )

    output_path = (
        Path(args.out)
        if args.out
        else RAW_DIR / default_name
    )

    expected_suffix = f".{args.format}"

    if output_path.suffix.lower() != expected_suffix:
        parser.error(
            f"Output filename must end in {expected_suffix}"
        )

    ################
    # EXECUTE
    ################

    print("Fetching OSM ALPR camera data...")
    print(f"Scope: {scope_name}")
    print(f"Flock only: {args.flock_only}")
    print(f"Output format: {args.format}")
    print(f"Snapshot date (UTC): {SNAPSHOT_DATE}")
    print(f"Output path: {output_path}")

    if output_path.exists():
        raise FileExistsError(
            f"Output already exists: {output_path}"
        )

    data = run_query(query)

    save_dataset(
        data,
        output_path,
        args.format,
    )


################
# ENTRY POINT
################

if __name__ == "__main__":
    main()


#######
# EOF #
#######
