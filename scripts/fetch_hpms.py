#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
#####################################################################
# FHWA HPMS 2024 Spatial All Sections (road geometry + AADT counts) #
#####################################################################


#####################
# SOURCES & LICENSE #
#####################
Federal Highway Administration (FHWA), Highway Performance Monitoring
System (HPMS), published on data.transportation.gov:
    https://data.transportation.gov/api/views/42um-tgh5
    (HPMS Spatial All Sections - 2024, GeoJSON, ARNOLD geometry)

License: not stated by this script. Check the publisher's terms before
redistributing, and record them in the datasheet.

Example User Usage (from the repository root):
    uv run python scripts/fetch_hpms.py --download

###########
# PURPOSE #
###########
Download the 2024 HPMS spatial sections as one GeoJSON file, saved
unchanged to:
    data/external/hpms/2024/hpms_spatial_all_sections_2024.geojson

By default the script only checks the file size and stops. Nothing is
downloaded until you add --download.


#############
# IMPORTANT #
#############
The older FHWA page (fhwa.dot.gov/policyinformation/hpms/shapefiles.cfm)
only lists the 2018 public release. Use 2024 to match the 2024 OSM snapshot.

Use --url to point at a different export (e.g. a BTS NTAD shapefile zip),
and --name to give it a matching file name.

An existing file is never overwritten.


#########
# USAGE #
#########
Run commands from the repository root.

Check the file size only (no download):

    uv run python scripts/fetch_hpms.py

Download the file (an existing file is never overwritten):

    uv run python scripts/fetch_hpms.py --download

Download a different export under its own name:

    uv run python scripts/fetch_hpms.py --download --url <URL> --name <FILE NAME>

Display available command-line arguments:

    uv run python scripts/fetch_hpms.py --help


################
# DEPENDENCIES #
################
Python 3 and requests (already used by fetch_osm_alpr_cameras.py).

    uv run python scripts/fetch_hpms.py [OPTIONS]
"""


###########
# IMPORTS #
###########

import argparse
# reads the --download, --url and --name command line options

from pathlib import Path
# Path: builds file paths that work on any operating system

import requests
# sends the HTTP requests (size check and download)


#############
# CONSTANTS #
#############
# <repo>/  (this file lives in <repo>/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Where the HPMS file is saved (not committed to git)
OUTPUT_DIR = PROJECT_ROOT / "data" / "external" / "hpms" / "2024"

# GeoJSON export of the 2024 HPMS dataset (override with --url)
DEFAULT_URL = (
    "https://data.transportation.gov/api/v3/views/42um-tgh5/"
    "query.geojson?accessType=DOWNLOAD"
)

# Output file name (override with --name)
DEFAULT_NAME = "hpms_spatial_all_sections_2024.geojson"

# Tell the server who we are (a student project)
HEADERS = {
    "User-Agent": "cs418-flock-research (academic course project)",
}

# Seconds to wait for a response; longer than the other fetchers because
# the export can be large
REQUEST_TIMEOUT = 300

# Download in 8 MB pieces so the large file never sits fully in memory
CHUNK_SIZE = 8 * 1024 * 1024


###################
# GET REMOTE SIZE #
###################
def get_remote_size(url: str) -> int | None:
    """Ask the server how big the file is, without downloading it. Returns bytes, or None if unknown."""
    # A HEAD request returns only the headers, so it is fast and downloads nothing.
    response = requests.head(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )

    # A missing file (404) means the URL is wrong, so say so clearly.
    if response.status_code == 404:
        raise FileNotFoundError(f"404 Not Found: {url}")

    response.raise_for_status()  # stop on any other 4xx/5xx error

    # An export built on demand may not report its size. An empty header
    # counts as unknown too.
    length = response.headers.get("Content-Length")

    if not length:
        return None

    return int(length)


#################
# DOWNLOAD FILE #
#################
def download_file(url: str, output_path: Path) -> None:
    """Download one file to output_path, printing progress. Skips an existing file."""
    # Never overwrite a file we already have.
    if output_path.exists():
        print(f"Refusing to overwrite: {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary ".part" file first. If the download stops halfway,
    # the real file name never exists, so a rerun cleanly starts again.
    # e.g. hpms_spatial_all_sections_2024.geojson -> ...2024.geojson.part
    temp_path = output_path.with_suffix(output_path.suffix + ".part")

    written = 0  # bytes downloaded so far

    # stream=True reads the file in pieces instead of all at once.
    with requests.get(
        url,
        headers=HEADERS,
        stream=True,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        response.raise_for_status()  # stop on 4xx/5xx errors

        with open(temp_path, "wb") as temp_file:
            for chunk in response.iter_content(CHUNK_SIZE):
                temp_file.write(chunk)
                written += len(chunk)

                # "\r" moves back to the start of the line, so each update
                # overwrites the last one instead of printing a new line.
                print(f"\r  {written / 1e9:.2f} GB", end="", flush=True)

    print()  # end the progress line

    temp_path.rename(output_path)
    print(f"Saved: {output_path}")


########
# MAIN #
########
def main() -> None:
    """Read the command-line options, check the file size, and download the file if asked."""
    parser = argparse.ArgumentParser(
        description="Check the size of, and optionally download, the FHWA HPMS 2024 spatial sections."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="download the file",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="alternate export URL",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help="output file name",
    )
    args = parser.parse_args()

    size = get_remote_size(args.url)

    if size is None:
        print("Server did not report a size (the export may be generated on demand).")
    else:
        print(f"{args.name}: {size / 1e9:.2f} GB")

    # Stop here by default so the size can be reviewed before downloading.
    if not args.download:
        print("Size check only. Re-run with --download to fetch.")
        return

    download_file(args.url, OUTPUT_DIR / args.name)


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######