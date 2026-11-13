#!/usr/bin/env python3
"""
########################################################
# FETCHER: OpenStreetMap ALPR / Flock Camera Locations #
########################################################

#####################
# SOURCES & LICENSE #
#####################
OpenStreetMap (OSM): https://www.openstreetmap.org/
Overpass API:        https://wiki.openstreetmap.org/wiki/Overpass_API

Queries OSM nodes (points) only. Cameras mapped as ways or relations
are not included.
License: ODbL 1.0 -- credit "(c) OpenStreetMap contributors".

###########
# PURPOSE #
###########
Download ALPR camera nodes from OSM through Overpass and save them to:
    data/raw/flock_osm/osm_flock_<scope>_locations_YYYY-MM-DD.<csv|geojson>  (--flock-only)
    data/raw/osm_alpr/osm_alpr_<scope>_locations_YYYY-MM-DD.<csv|geojson>    (all ALPR)
YYYY-MM-DD = UTC download date. One row/feature = one camera node (current version).

#############
# IMPORTANT #
#############
OSM is community-mapped, NOT a complete inventory of installed ALPR cameras.
A camera missing from OSM is not necessarily absent in reality.

#########
# USAGE #
#########
Run from the repository root:
    uv run python scripts/fetch_osm_alpr_cameras.py <OPTIONS>

Options (pick one scope; add --flock-only and/or --format csv as needed):
    --nationwide --flock-only --format csv   Flock cameras, whole U.S., CSV
    --state Illinois                         all ALPR cameras in one state (GeoJSON)
    --place "Orland Park, Illinois"          bounding-box search near a place
    --bbox 41.6,-87.9,42.1,-87.5             south,west,north,east
    --help                                   list all options

################
# DEPENDENCIES #
################
Python 3 and requests (uv add requests). Run with: uv run python <script>
"""


###########
# IMPORTS #
###########

import argparse  # https://docs.python.org/3/library/argparse.html
# reads command line arguments (--state, --bbox, --flock-only, ...)

import csv  # https://docs.python.org/3/library/csv.html
# writes the CSV output, one row per camera

import json  # https://docs.python.org/3/library/json.html
# writes GeoJSON and stores the raw OSM tags as a JSON string

import time  # https://docs.python.org/3/library/time.html
# time.sleep(): wait between retries and between geocoding requests

from datetime import datetime, timezone  # https://docs.python.org/3/library/datetime.html
# datetime/timezone: today's UTC date for the file name, and Retry-After math

from email.utils import parsedate_to_datetime  # https://docs.python.org/3/library/email.utils.html
# parses a Retry-After header that is given as an HTTP date

from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import requests  # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs


#############
# CONSTANTS #
#############
# <repo>/  (this file lives in <repo>/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Default output folders: Flock-only runs vs. all-manufacturer runs
FLOCK_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "flock_osm"
ALPR_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "osm_alpr"

# Today's UTC date, put in the file name so each download is its own snapshot
SNAPSHOT_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Public Overpass servers, tried in order until one succeeds
ENDPOINTS = [
    "https://overpass.deflock.org/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Tell the server who we are (a student project)
HEADERS = {
    "User-Agent": "CS418-flock-research-project/1.0 (student research)",
}

# OSM's geocoder: turns a place name into a bounding box (--place)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Attempts per endpoint before moving on to the next endpoint
MAX_RETRIES = 3

# Seconds to wait before retry 1, 2, 3
RETRY_DELAYS = [30, 60, 120]

# Temporary HTTP errors worth retrying (rate limit / server overload)
RETRY_STATUSES = {429, 500, 502, 503, 504}

# Client timeout in seconds; a bit longer than the 600s server-side timeout
REQUEST_TIMEOUT = 660


#################
# GEOCODE PLACE #
#################
def geocode_place(place_name: str) -> tuple[float, float, float, float]:
    """Look up a place name with Nominatim and return its bounding box (south, west, north, east)."""
    print(f"Geocoding: {place_name}")

    # limit=1 asks Nominatim for only its single best match.
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

    response.raise_for_status()  # stop on 4xx/5xx errors

    results = response.json()

    if not results:
        raise RuntimeError(
            f"Nominatim found no match for: {place_name}"
        )

    result = results[0]

    # Nominatim gives the box as strings in the order [south, north, west, east].
    # map(float, ...) converts each one to a number.
    south, north, west, east = map(
        float,
        result["boundingbox"],
    )

    print(f"Matched: {result['display_name']}")

    # Nominatim's usage policy allows at most 1 request per second
    time.sleep(1)

    return south, west, north, east


##################
# CAMERA FILTERS #
##################
def camera_filters(flock_only: bool) -> str:
    """Return the Overpass tag filters for all ALPR cameras or for Flock-only cameras."""
    # Each [...] is one required tag. ~"Flock",i is a regular expression:
    # "manufacturer contains Flock", ignoring upper/lower case.
    if flock_only:
        return (
            '["man_made"="surveillance"]'
            '["surveillance:type"="ALPR"]'
            '["manufacturer"~"Flock",i]'
        )

    return '["surveillance:type"="ALPR"]'


########################
# BUILD QUERY BY STATE #
########################
def build_query_by_state(
    state_name: str,
    flock_only: bool = False,
    timeout: int = 180,
) -> str:
    """Build an Overpass query for camera nodes inside one U.S. state."""
    filters = camera_filters(flock_only)

    # json.dumps() adds quotes and escapes, so the name is safe inside the query
    safe_state = json.dumps(state_name)

    # In the U.S., OSM tags state boundaries with admin_level=4.
    return f"""
    [out:json][timeout:{timeout}];

    area["name"={safe_state}]
        ["admin_level"="4"]->.searchArea;

    node{filters}(area.searchArea);

    out meta;
    """


#######################
# BUILD QUERY BY BBOX #
#######################
def build_query_by_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
    flock_only: bool = False,
    timeout: int = 180,
) -> str:
    """Build an Overpass query for camera nodes inside a south/west/north/east box."""
    filters = camera_filters(flock_only)

    # Overpass expects the box in this exact order: south,west,north,east.
    bbox = f"{south},{west},{north},{east}"

    return f"""
    [out:json][timeout:{timeout}];

    node{filters}({bbox});

    out meta;
    """


##########################
# BUILD QUERY NATIONWIDE #
##########################
def build_query_nationwide(
    flock_only: bool = False,
    timeout: int = 600,
) -> str:
    """Build an Overpass query for camera nodes anywhere in the United States."""
    filters = camera_filters(flock_only)

    return f"""
    [out:json][timeout:{timeout}];

    area["ISO3166-1"="US"]->.searchArea;

    node{filters}(area.searchArea);

    out meta;
    """


###################
# GET RETRY DELAY #
###################
def get_retry_delay(response: requests.Response, attempt: int) -> int:
    """Return seconds to wait before retrying, using Retry-After when it asks for longer."""

    # Start with our own schedule (30, 60, 120 seconds).
    delay = RETRY_DELAYS[attempt]

    # Retry-After is the server telling us how long to wait. It comes in
    # two forms: a number of seconds ("120") or an HTTP date
    # ("Wed, 21 Oct 2026 07:28:00 GMT"). We wait whichever is longer.
    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            delay = max(delay, int(retry_after))

        # Not a plain number, so try to read it as an HTTP date.
        except ValueError:
            try:
                retry_date = parsedate_to_datetime(retry_after)

                # A date without a time zone is assumed to be UTC, so it
                # can be subtracted from the current UTC time.
                if retry_date.tzinfo is None:
                    retry_date = retry_date.replace(
                        tzinfo=timezone.utc
                    )

                seconds = (
                    retry_date - datetime.now(timezone.utc)
                ).total_seconds()

                delay = max(delay, int(max(0, seconds)))

            # Unreadable header: keep our own delay.
            except (TypeError, ValueError, OverflowError):
                pass

    return delay


#############
# RUN QUERY #
#############
def run_query(query: str) -> dict:
    """Send the query to each Overpass endpoint in turn, retrying temporary errors, and return the JSON."""
    # Remember the most recent failure so the final error message can show it.
    last_error = None

    # Outer loop: each Overpass server. Inner loop: retries on that server.
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

                # Turn any 4xx/5xx status into an HTTPError, which the except
                # blocks below decide whether to retry. (This "if" is redundant:
                # the next line already raises for every error status. See
                # docs/BUGS.md, BUG-006.)
                if response.status_code in RETRY_STATUSES:

                    response.raise_for_status()

                response.raise_for_status()

                data = response.json()

                # Check the response has the shape we expect before using it.
                # Overpass can return valid JSON that still is not a result
                # (for example, an error object without "elements").
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

                # Permanent errors (for example 400 = bad query) will fail on
                # every server, so stop the whole run.
                if status not in RETRY_STATUSES:
                    raise

                # Out of retries on this server: move on to the next one.
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

                # Timeouts and dropped connections are usually temporary.
                print(f"Network error: {exc}")

                if attempt == MAX_RETRIES - 1:
                    break

                delay = RETRY_DELAYS[attempt]

                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

            # A malformed response will not improve on retry,
            # so move on to the next endpoint.
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


##############
# TO GEOJSON #
##############
def to_geojson(overpass_json: dict) -> dict:
    """
    Convert Overpass nodes into GeoJSON features.

    Preserve all original OSM tags and metadata.
    """

    features = []

    for el in overpass_json.get("elements", []):

        # Only nodes (points) have lat/lon; skip anything else.
        if el.get("type") != "node":
            continue

        tags = el.get("tags", {})

        features.append({
            "type": "Feature",
            # GeoJSON uses [longitude, latitude] order, the reverse of
            # how coordinates are usually written.
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
                # Falls back to "brand" when "manufacturer" is missing. The CSV
                # output does not do this (see docs/BUGS.md, BUG-004).
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


###############
# CSV COLUMNS #
###############
# Column order of the CSV output
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

##########
# TO CSV #
##########
def to_csv(overpass_json: dict, output_path: Path) -> int:
    """Write camera nodes to a CSV file and return the number of rows written."""
    elements = overpass_json.get("elements", [])

    count = 0

    # newline="" is required by the csv module; without it Windows
    # writes a blank line between every row.
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        # DictWriter writes each dict as a row, putting values under the
        # matching CSV_COLUMNS header.
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
                # Keep every original OSM tag in one column as JSON text, so no
                # tag is lost. ensure_ascii=False keeps accented letters readable.
                "all_tags": json.dumps(
                    tags,
                    ensure_ascii=False,
                ),
            })

            count += 1

    return count


################
# SAVE DATASET #
################
def save_dataset(
    overpass_json: dict,
    output_path: Path,
    output_format: str,
) -> None:
    """Save the Overpass result as CSV or GeoJSON, refusing to overwrite an existing file."""
    # Create data/raw/... if this is the first download.
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Never overwrite an earlier snapshot.
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

    # Sanity check: row count and file size show at a glance if the
    # download was empty or truncated.
    print()
    print("Export completed successfully.")
    print(f"Saved: {output_path}")
    print(f"Camera nodes: {count:,}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


########
# MAIN #
########
def main() -> None:
    """Read the command-line options, run the Overpass query, and save the dataset."""

    parser = argparse.ArgumentParser(
        description="Fetch ALPR camera nodes from OSM/Overpass."
    )

    # Exactly one of --state / --bbox / --place / --nationwide must be given.
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

    # Build the query for the chosen area. scope_name becomes part of the
    # output file name, e.g. "illinois", "bbox", "orland_park_illinois", "us".
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
            # Split "south,west,north,east" on commas and convert each piece to a float.
            parts = [
                float(value)
                for value in args.bbox.split(",")
            ]

        # parser.error() prints the message plus usage help, then exits.
        except ValueError:
            parser.error(
                "--bbox must contain four numeric coordinates."
            )

        if len(parts) != 4:
            parser.error(
                "--bbox must be south,west,north,east"
            )

        south, west, north, east = parts

        # Latitude must be within -90..90 and longitude within -180..180,
        # and south/west must be smaller than north/east.
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

    camera_label = (
        "flock"
        if args.flock_only
        else "alpr"
    )

    # Put the UTC date in the file name so each download is its own snapshot
    # e.g. osm_flock_us_locations_2026-10-30.csv
    default_name = (
        f"osm_{camera_label}_{scope_name}_locations_"
        f"{SNAPSHOT_DATE}.{args.format}"
    )

    default_dir = (
        FLOCK_RAW_DIR
        if args.flock_only
        else ALPR_RAW_DIR
    )

    output_path = (
        Path(args.out)
        if args.out
        else default_dir / default_name
    )

    # Make sure a custom --out name matches --format (no ".csv" holding GeoJSON).
    expected_suffix = f".{args.format}"

    if output_path.suffix.lower() != expected_suffix:
        parser.error(
            f"Output filename must end in {expected_suffix}"
        )

    print("Fetching OSM ALPR camera data...")
    print(f"Scope: {scope_name}")
    print(f"Flock only: {args.flock_only}")
    print(f"Output format: {args.format}")
    print(f"Snapshot date (UTC): {SNAPSHOT_DATE}")
    print(f"Output path: {output_path}")

    # Check before downloading, so a nationwide query is not wasted.
    # save_dataset() checks again right before writing.
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


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######
