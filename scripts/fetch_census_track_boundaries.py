
##########
# FETCHER #
##########
"""
Download U.S. Census TIGER/Line census tract boundary shapefiles.

These boundaries are used to determine which census tract contains
each Flock Safety camera using its latitude and longitude.

Download 2017 and 2024 boundaries because census tract boundaries
can change between decennial censuses (2010 vs. 2020 geography).

Coverage: All 50 U.S. states and Washington, D.C.
Source: https://www2.census.gov/geo/tiger/

Example:
    python download_census_boundaries.py

Requires:
    requests
"""

###########
# IMPORTS #
###########
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import requests
import time


#############
# CONSTANTS #
#############
BASE_URL = "https://www2.census.gov/geo/tiger"

OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "external"
    / "census_boundaries"
)

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


##########
# FETCHER #
##########
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
if __name__ == "__main__":
    download_census_boundaries()


#######
# EOF #
#######
