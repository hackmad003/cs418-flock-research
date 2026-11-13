#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
########################################################################
# LEHD LODES8 Workplace Area Characteristics (WAC), one file per state #
########################################################################


#####################
# SOURCES & LICENSE #
#####################
U.S. Census Bureau, LEHD Origin-Destination Employment Statistics (LODES8):
    https://lehd.ces.census.gov/data/lodes/LODES8/

License: not stated by this script. Check the Census Bureau's terms before
redistributing, and record them in the datasheet.

Example User Usage (from the repository root):
    uv run python scripts/fetch_lehd_lodes.py --download

###########
# PURPOSE #
###########
Download the Workplace Area Characteristics (WAC) file for each of the
50 states and DC, for all workers (S000) and all jobs (JT00). Files are
saved unchanged to:
    data/raw/lehd_lodes/wac/<st>_wac_S000_JT00_<YEAR>.csv.gz

By default the script only checks file sizes and stops. Nothing is
downloaded until you add --download.


#############
# IMPORTANT #
#############
Not every state has a file for the latest year. For each state the script
tries LATEST_YEAR first and then each earlier year down to OLDEST_YEAR,
and uses the newest year it finds. States that fall back are flagged in
the size check, so the years can differ between states.

Existing files are skipped, never overwritten.


#########
# USAGE #
#########
Run commands from the repository root.

Check file sizes only (no download):

    uv run python scripts/fetch_lehd_lodes.py

Download every missing file (existing files are skipped, never overwritten):

    uv run python scripts/fetch_lehd_lodes.py --download

Display available command-line arguments:

    uv run python scripts/fetch_lehd_lodes.py --help


################
# DEPENDENCIES #
################
Python 3 and requests (already used by fetch_osm_alpr_cameras.py).

    uv run python scripts/fetch_lehd_lodes.py [OPTIONS]
"""


###########
# IMPORTS #
###########

import argparse
# reads the --download command line flag

from pathlib import Path
# Path: builds file paths that work on any operating system

import requests
# sends the HTTP requests (size check and download)


#############
# CONSTANTS #
#############
# <repo>/  (this file lives in <repo>/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Where the raw WAC files are saved (not committed to git)
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "lehd_lodes" / "wac"

# Census Bureau folder that holds every LODES8 file
BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8"

# Worker segment: S000 = all workers
SEGMENT = "S000"

# Job type: JT00 = all jobs
JOB_TYPE = "JT00"

# Newest year to try first for each state
LATEST_YEAR = 2023

# Oldest year to fall back to for a state with no LATEST_YEAR file
OLDEST_YEAR = 2015

# Postal codes of the 50 states and DC, lowercase as in the LODES folder names
STATES = [
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "dc", "fl", "ga", "hi",
    "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn",
    "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh",
    "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa",
    "wv", "wi", "wy",
]

# Tell the server who we are (a student project)
HEADERS = {
    "User-Agent": "cs418-flock-research (academic course project)",
}

# Seconds to wait for a response (size check and download)
REQUEST_TIMEOUT = 120

# Download in 1 MB pieces so a large file never sits fully in memory
CHUNK_SIZE = 1024 * 1024


#############
# BUILD URL #
#############
def build_url(state: str, year: int) -> tuple[str, str]:
    """Return (url, file_name) of the WAC file for one state and year."""
    # e.g. il_wac_S000_JT00_2023.csv.gz
    name = f"{state}_wac_{SEGMENT}_{JOB_TYPE}_{year}.csv.gz"

    return f"{BASE_URL}/{state}/wac/{name}", name


###############
# FIND LATEST #
###############
def find_latest(state: str) -> tuple[str, str, int, int] | None:
    """Return (url, file_name, year, size_bytes) of the newest WAC file for a state, or None if none exists."""
    # Try LATEST_YEAR first, then each earlier year down to OLDEST_YEAR.
    # range(start, stop, -1) counts down and stops before "stop", hence the - 1.
    for year in range(LATEST_YEAR, OLDEST_YEAR - 1, -1):
        url, name = build_url(state, year)

        # A HEAD request returns only the headers, so it is fast and downloads nothing.
        response = requests.head(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code == 200:
            # A missing Content-Length header counts as 0 bytes in the total.
            size = int(response.headers.get("Content-Length", 0))
            return url, name, year, size

        # 404 only means "no file for this year", so try the year before.
        # Any other error status stops the run.
        if response.status_code != 404:
            response.raise_for_status()

    return None


#################
# DOWNLOAD FILE #
#################
def download_file(url: str, output_path: Path) -> None:
    """Download one file to output_path. Skips an existing file and checks the result is gzip."""
    # Never overwrite a file we already have.
    if output_path.exists():
        print(f"  Skip (exists): {output_path.name}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary ".part" file first. If the download stops halfway,
    # the real file name never exists, so a rerun cleanly starts that file again.
    # e.g. il_wac_S000_JT00_2023.csv.gz -> il_wac_S000_JT00_2023.csv.gz.part
    temp_path = output_path.with_suffix(output_path.suffix + ".part")

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

    # Sanity check: an error page saved as ".csv.gz" would break later steps.
    # A real gzip file always starts with the two bytes 1f 8b.
    with open(temp_path, "rb") as temp_file:
        if temp_file.read(2) != b"\x1f\x8b":
            temp_path.unlink()
            raise ValueError(f"{output_path.name} is not a gzip file")

    temp_path.rename(output_path)
    print(f"  Saved: {output_path.name}")


########
# MAIN #
########
def main() -> None:
    """Read the --download flag, check every state's file size, and download the missing files if asked."""
    parser = argparse.ArgumentParser(
        description="Check sizes of, and optionally download, LEHD LODES8 WAC files for the 50 states and DC."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="download missing files",
    )
    args = parser.parse_args()

    found = []  # (url, file_name) of each state with a file
    missing = []  # states with no file between OLDEST_YEAR and LATEST_YEAR
    total = 0  # bytes across all found files

    for state in STATES:
        result = find_latest(state)

        if result is None:
            missing.append(state)
            continue

        url, name, year, size = result
        found.append((url, name))
        total += size

        # Flag states that fell back to an older year.
        if year == LATEST_YEAR:
            year_note = ""
        else:
            year_note = f"  (latest available: {year})"

        print(f"{name}: {size / 1e6:.1f} MB{year_note}")

    print(f"\nFound {len(found)} of {len(STATES)} states, {total / 1e6:.0f} MB total")

    if missing:
        print(f"No file found for: {', '.join(missing)}")

    # Stop here by default so the total size can be reviewed before downloading.
    if not args.download:
        print("Size check only. Re-run with --download to fetch.")
        return

    for url, name in found:
        download_file(url, OUTPUT_DIR / name)


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######