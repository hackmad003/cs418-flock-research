#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
###################################################
# Census TIGER/Line Roads (Primary and Secondary) #
###################################################


#####################
# SOURCES & LICENSE #
#####################
U.S. Census Bureau, TIGER/Line Shapefiles:
    https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html

Files are downloaded from the Census Bureau's TIGER/Line folder:
    https://www2.census.gov/geo/tiger/TIGER2024/

License: not stated by this script. Check the Census Bureau's terms before
redistributing, and record them in the datasheet.

Example User Usage (from the repository root):
    uv run python scripts/fetch_census_roads.py --download

###########
# PURPOSE #
###########
Download the 2024 TIGER/Line road lines that carry most traffic:
one national primary-roads file and one primary-and-secondary-roads
file for each of the 50 states and DC. Files are saved unchanged to
data/external/census_boundaries/roads/2024/ (original Census file names).

One feature = one road segment (a line). The files hold geometry and
road names/types only. They do NOT hold traffic counts.

By default the script only checks file sizes and stops. Nothing is
downloaded until you add --download.


#############
# IMPORTANT #
#############
This script does NOT download the per-county "all roads" layer (about
3,200 files, mostly local streets). Puerto Rico and the territories are
skipped, to match the 50-state + DC tract files.

File names follow the TIGER 2024 folder layout (PRIMARYROADS/ and
PRISECROADS/). If the size check reports a 404, open the folder in a
browser and confirm the names.


#########
# USAGE #
#########
Run commands from the repository root.

Check file sizes only (no download):

    uv run python scripts/fetch_census_roads.py

Download every missing file (existing files are skipped, never overwritten):

    uv run python scripts/fetch_census_roads.py --download

Display available command-line arguments:

    uv run python scripts/fetch_census_roads.py --help


################
# DEPENDENCIES #
################
Python 3 and requests (already used by fetch_osm_alpr_cameras.py).

    uv run python scripts/fetch_census_roads.py [OPTIONS]
"""


###########
# IMPORTS #
###########

import argparse
# reads the --download command line flag

import zipfile  # https://docs.python.org/3/library/zipfile.html
# zipfile.is_zipfile(): checks that a download is a real zip file, not an error page

from pathlib import Path
# Path: builds file paths that work on any operating system

import requests
# sends the HTTP requests (size check and download)


#############
# CONSTANTS #
#############
# <repo>/  (this file lives in <repo>/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# TIGER vintage. It appears in the folder name and in every file name.
TIGER_YEAR = 2024

# Census Bureau folder that holds every TIGER/Line layer for that year
BASE_URL = f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}"

# Where the raw road files are saved (not committed to git)
OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "external" / "census_boundaries" / "roads" / str(TIGER_YEAR)
)

# FIPS codes of the 50 states and DC, as text so leading zeros stay ("01")
STATE_FIPS = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55",
    "56",
]

# Tell the server who we are (a student project)
HEADERS = {
    "User-Agent": "CS418-flock-research-project/1.0 (student research)",
}

# Seconds to wait for a response (size check and download)
REQUEST_TIMEOUT = 120

# Download in 1 MB pieces so a large file never sits fully in memory
CHUNK_SIZE = 1024 * 1024


###################
# BUILD FILE LIST #
###################
def build_file_list() -> list[tuple[str, str]]:
    """Return (file_name, url) for the national primary roads and each state's primary/secondary roads."""
    files = []

    # One national file with only the primary roads (interstates and major highways)
    national_name = f"tl_{TIGER_YEAR}_us_primaryroads.zip"
    files.append((national_name, f"{BASE_URL}/PRIMARYROADS/{national_name}"))

    # One file per state with primary AND secondary roads (adds state and
    # county highways, which is where many cameras sit)
    for state_fips in STATE_FIPS:
        state_name = f"tl_{TIGER_YEAR}_{state_fips}_prisecroads.zip"
        files.append((state_name, f"{BASE_URL}/PRISECROADS/{state_name}"))

    return files


###################
# GET REMOTE SIZE #
###################
def get_remote_size(url: str) -> int | None:
    """Ask the server how big a file is, without downloading it. Returns bytes, or None if unknown."""
    # A HEAD request returns only the headers, so it is fast and downloads nothing.
    response = requests.head(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )

    # A missing file (404) means our assumed file name is wrong, so say so clearly.
    if response.status_code == 404:
        raise RuntimeError(
            f"File not found (404): {url}\n"
            "Open the TIGER folder in a browser and confirm the file names."
        )

    response.raise_for_status()  # stop on any other 4xx/5xx error

    content_length = response.headers.get("Content-Length")

    if content_length is None:
        return None

    return int(content_length)


###############
# CHECK SIZES #
###############
def check_sizes(files: list[tuple[str, str]]) -> int:
    """Print the size of every file still to download and return the total bytes."""
    total_bytes = 0
    unknown_count = 0
    missing_count = 0

    for position, (file_name, url) in enumerate(files, start=1):
        output_path = OUTPUT_DIR / file_name

        # Files we already have are skipped, so they add nothing to the total.
        if output_path.exists():
            print(f"[{position}/{len(files)}] {file_name}: already downloaded")
            continue

        missing_count += 1
        size_bytes = get_remote_size(url)

        if size_bytes is None:
            unknown_count += 1
            print(f"[{position}/{len(files)}] {file_name}: size unknown")
            continue

        total_bytes += size_bytes
        print(f"[{position}/{len(files)}] {file_name}: {size_bytes / 1e6:.1f} MB")

    print(f"\nFiles still to download: {missing_count}")
    print(f"Total size of files with a known size: {total_bytes / 1e9:.2f} GB")

    if unknown_count > 0:
        print(f"Files with an unknown size (not in the total): {unknown_count}")

    return total_bytes


#################
# DOWNLOAD FILE #
#################
def download_file(url: str, output_path: Path) -> None:
    """Download one file to output_path. Refuses to overwrite and checks the result is a zip."""
    # Never overwrite a file we already have.
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary ".part" file first. If the download stops halfway,
    # the real file name never exists, so a rerun cleanly starts that file again.
    temp_path = output_path.with_name(output_path.name + ".part")

    # stream=True reads the file in pieces instead of all at once.
    with requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        stream=True,
    ) as response:
        response.raise_for_status()  # stop on 4xx/5xx errors

        with open(temp_path, "wb") as temp_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                temp_file.write(chunk)

    # Sanity check: an error page saved as ".zip" would break later steps.
    if not zipfile.is_zipfile(temp_path):
        temp_path.unlink()
        raise RuntimeError(f"Download is not a valid zip file: {url}")

    temp_path.rename(output_path)


########
# MAIN #
########
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check sizes of, and optionally download, Census TIGER/Line primary and secondary roads."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="download the missing files (without this flag, only sizes are checked)",
    )
    args = parser.parse_args()

    files = build_file_list()
    print(f"TIGER {TIGER_YEAR} roads: {len(files)} files -> {OUTPUT_DIR}\n")

    check_sizes(files)

    # Stop here by default so the total size can be reviewed before downloading.
    if not args.download:
        print("\nSize check only. Re-run with --download to download.")
        return

    downloaded_count = 0

    for position, (file_name, url) in enumerate(files, start=1):
        output_path = OUTPUT_DIR / file_name

        if output_path.exists():
            continue

        print(f"Downloading [{position}/{len(files)}] {file_name}")
        download_file(url, output_path)
        downloaded_count += 1

    print(f"\nDone. Files downloaded this run: {downloaded_count}")


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######