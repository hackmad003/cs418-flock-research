#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
########################################################
# U.S. Census TIGER/Line Tract Boundaries (2017, 2024) #
########################################################


Download U.S. Census TIGER/Line census tract boundary shapefiles and save
them, untouched, to
data/external/census_boundaries/<year>/tl_<year>_<state FIPS>_tract.zip

One ZIP = one state's tract boundaries for one year (51 jurisdictions x
2 years = 102 files). Used to spatially join each Flock camera's
latitude/longitude to the census tract that contains it.

Source:  https://www2.census.gov/geo/tiger/  (TIGER/Line Shapefiles)
License: U.S. Census Bureau data is a U.S. Government work (public domain).

Example User Usage (from the repository root):
    uv run python scripts/fetch_census_track_boundaries.py

PURPOSE
-------
These boundaries are used to determine which census tract contains
each Flock Safety camera using its latitude and longitude (spatial join).

WHY 2017 AND 2024?
------------------
This script downloads two selected years, NOT every year from 2017
through 2024.

Census tract boundaries can change, especially after the decennial
census (conducted every 10 years).

- 2017 boundaries: Based on 2010 Census tract geography.
  Used with ACS 2013-2017 5-year demographic estimates.

- 2024 boundaries: Based on 2020 Census tract geography.
  Used with ACS 2020-2024 5-year demographic estimates.

Using matching geographic vintages helps ensure that camera locations
are assigned to the correct census tracts when joining demographic data.

WHY NOT 2025 OR 2026?
---------------------
Newer boundaries are not automatically better.

The project's demographic comparisons use ACS 2017 and ACS 2024
5-year estimates, so the corresponding TIGER/Line tract boundaries
are appropriate.

Cameras first mapped in OSM during 2025 or 2026 can still be
assigned to 2024 Census tracts. The camera's mapping date and
the Census boundary year represent different things.

Downloading 2026 boundaries would not provide 2026 demographic data
and is unnecessary for the current analysis.

NOTE ON HISTORICAL ANALYSIS
---------------------------
For descriptive geographic comparisons, ACS 2024 demographics can
be joined to cameras mapped in 2025 or 2026.

For historical predictive modeling, demographic data must have been
publicly available at the prediction date to avoid data leakage.
ACS 2020-2024 5-year estimates were released in January 2026,
so they must not be used as predictors for 2025 forecasts.

COVERAGE
--------
All 50 U.S. states and Washington, D.C. (51 jurisdictions).
U.S. territories are excluded.

SOURCE
------
U.S. Census Bureau TIGER/Line Shapefiles:
https://www2.census.gov/geo/tiger/

OUTPUT
------
data/external/census_boundaries/<year>/tl_<year>_<state FIPS>_tract.zip

This script does NOT download the national county boundary file:
data/external/census_boundaries/counties/tl_2024_us_county.zip

That file was obtained manually.

USAGE
-----
Run from the repository root:

    uv run python scripts/fetch_census_track_boundaries.py

DEPENDENCIES
------------
requests

VVV Sources VVV
https://www2.census.gov/geo/tiger/
https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
https://www.census.gov/library/reference/code-lists/ansi.html (state FIPS codes)

Imports Used:
from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
from zipfile import ZipFile, BadZipFile  # https://docs.python.org/3/library/zipfile.html
import requests  # https://requests.readthedocs.io/en/latest/
import time  # https://docs.python.org/3/library/time.html

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
range() https://docs.python.org/3/library/stdtypes.html#range
str() https://docs.python.org/3/library/stdtypes.html#str
open() https://docs.python.org/3/library/functions.html#open
ValueError https://docs.python.org/3/library/exceptions.html#ValueError
OSError https://docs.python.org/3/library/exceptions.html#OSError

Object Methods Used:
requests.get(stream=True) https://requests.readthedocs.io/en/latest/api/#requests.get
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
.iter_content() https://requests.readthedocs.io/en/latest/api/#requests.Response.iter_content
requests.RequestException https://requests.readthedocs.io/en/latest/api/#requests.RequestException
ZipFile() https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
.testzip() https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.testzip
BadZipFile https://docs.python.org/3/library/zipfile.html#zipfile.BadZipFile
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parents https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parents
.exists() https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.with_suffix() https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.with_suffix
.replace() https://docs.python.org/3/library/pathlib.html#pathlib.Path.replace
.unlink(missing_ok=True) https://docs.python.org/3/library/pathlib.html#pathlib.Path.unlink
.write() (file) https://docs.python.org/3/library/io.html#io.BufferedIOBase.write
.append() https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
time.sleep() https://docs.python.org/3/library/time.html#time.sleep

Data Structures / Techniques Used:
list (YEARS, STATE_FIPS) https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
tuple ((year, state) failures) https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences
with statement (context managers) https://docs.python.org/3/reference/compound_stmts.html#the-with-statement
try / except https://docs.python.org/3/tutorial/errors.html#handling-exceptions
streaming downloads https://requests.readthedocs.io/en/latest/user/advanced/#body-content-workflow
temp file + rename (atomic save) https://docs.python.org/3/library/pathlib.html#pathlib.Path.replace
type hints (-> bool) https://docs.python.org/3/library/typing.html
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
"""


###########
# IMPORTS #
###########
from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

from zipfile import ZipFile, BadZipFile  # https://docs.python.org/3/library/zipfile.html
# ZipFile: opens .zip files so we can check they are not corrupted
# BadZipFile: the error raised when a file is not a valid ZIP

import requests  # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs

import time  # https://docs.python.org/3/library/time.html
# time.sleep(): wait a few seconds between retries


#############
# CONSTANTS #
#############
# Root folder of the Census TIGER/Line download site
BASE_URL = "https://www2.census.gov/geo/tiger"

# This file lives in <repo>/scripts/, so parents[1] is the repository root.
# (parents[2] pointed one directory ABOVE the repository.)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "census_boundaries"
)

# Boundary years to download (see WHY 2017 AND 2024? above)
YEARS = [2017, 2024]

# Two-digit FIPS codes identify each state.
# Includes Washington, D.C. (11), but excludes U.S. territories.
STATE_FIPS = [
    "01", "02", "04", "05", "06", "08", "09", "10",
    "11", "12", "13", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35",
    "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
]

# Try each file up to 3 times; give up on a request after 120 seconds
RETRIES = 3
TIMEOUT = 120


#############
# VALIDATOR #
#############
def valid_zip(path: Path) -> bool:
    """
    Check whether a downloaded ZIP file exists and is readable.
    """
    if not path.exists():
        return False

    try:
        with ZipFile(path) as z:
            # testzip() checks the CRC of every file inside the ZIP.
            # None means no corrupted members were found.
            return z.testzip() is None

    except (BadZipFile, OSError):
        return False


##############
# DOWNLOADER #
##############
def download_tract(year: int, state: str) -> bool:
    """
    Download one state's census tract boundaries for a given year.

    Example:
        download_tract(2024, "17")  # Illinois
    """
    filename = f"tl_{year}_{state}_tract.zip"

    url = f"{BASE_URL}/TIGER{year}/TRACT/{filename}"

    # Save each year's shapefiles in its own folder.
    folder = OUTPUT_DIR / str(year)
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / filename

    # Avoid downloading files we already have.
    if valid_zip(path):
        print(f"[SKIP] {filename} already downloaded")
        return True

    # Retry if the Census server is temporarily unavailable.
    for attempt in range(1, RETRIES + 1):
        try:
            print(f"[GET] {filename} (attempt {attempt})")

            # Stream the response so large ZIP files are not
            # loaded entirely into memory.
            with requests.get(
                url, stream=True, timeout=TIMEOUT
            ) as response:
                response.raise_for_status()

                # Download to a temporary file first.
                # This prevents interrupted downloads from
                # being mistaken for completed ZIP files.
                temp_path = path.with_suffix(".zip.part")

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            f.write(chunk)

            # Verify the downloaded ZIP before saving it.
            if not valid_zip(temp_path):
                raise ValueError("Downloaded ZIP is corrupted")

            temp_path.replace(path)

            print(f"[OK] {filename}")
            return True

        except (requests.RequestException, OSError, ValueError) as e:
            print(f"[ERROR] {filename}: {e}")

            # Remove incomplete downloads.
            temp_path = path.with_suffix(".zip.part")
            temp_path.unlink(missing_ok=True)

            if attempt < RETRIES:
                time.sleep(2 * attempt)

    print(f"[FAILED] {filename}")
    return False


###########
# FETCHER #
###########
def download_census_boundaries() -> None:
    """
    Download census tract boundaries for every state and year.
    """
    total = len(YEARS) * len(STATE_FIPS)
    completed = 0
    failed = []

    print(f"Downloading {total} Census tract shapefiles...\n")

    for year in YEARS:
        for state in STATE_FIPS:
            success = download_tract(year, state)

            if success:
                completed += 1
            else:
                failed.append((year, state))

    print(f"\nCompleted: {completed}/{total}")

    if failed:
        print(f"Failed downloads: {failed}")
    else:
        print("All Census tract boundaries downloaded successfully!")


########
# MAIN #
########
def main() -> None:
    """Download every Census tract boundary file."""
    download_census_boundaries()


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######
