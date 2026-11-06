#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
#####################################
# US Census by ZIP Code (secondary) #
#####################################

Download US Census data by ZIP code (ZCTA) and save it, untouched, to data/raw/census/.
Used for research questions 2 and 4 (income, population, density).

Downloads 3 files (no API key needed):
  1. ACS 5-year 2020-2024, table B19013: median household income
  2. ACS 5-year 2020-2024, table B01003: total population
  3. 2024 Gazetteer ZCTA file: land area of each ZIP code (for density)

The ACS files cover EVERY geography (states, counties, ZIPs, ...). The loader
keeps only the ZIP code rows.

Note: a ZCTA ("ZIP Code Tabulation Area") is the Census's version of a ZIP
code. They match real ZIP codes closely, but not perfectly.

Source:  https://www.census.gov/programs-surveys/acs/data/summary-file.html
         https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
License: US Census data is public domain.

Example User Usage:
    uv run python scripts/fetch_census.py

Load it afterwards with:
    from cs418_flock_research.census import load_zcta

VVV Sources VVV
https://www.census.gov/programs-surveys/acs/data/summary-file.html
https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html (what a ZCTA is)

Imports Used:
from pathlib import Path # https://docs.python.org/3/library/pathlib.html
import requests # https://requests.readthedocs.io/en/latest/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len

Object Methods Used:
requests.get() https://requests.readthedocs.io/en/latest/api/#requests.get
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
Response.content (raw bytes) https://requests.readthedocs.io/en/latest/api/#requests.Response.content
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parent https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parent
.name https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.name
.exists() https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.write_bytes() https://docs.python.org/3/library/pathlib.html#pathlib.Path.write_bytes
.items() https://docs.python.org/3/library/stdtypes.html#dict.items

Data Structures / Techniques Used:
dict (FILES: file name -> URL) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
continue (skip files already downloaded) https://docs.python.org/3/tutorial/controlflow.html#break-and-continue-statements
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
format spec (:.1f) https://docs.python.org/3/library/string.html#format-specification-mini-language
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
User-Agent header https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
"""

###########
# IMPORTS #
###########
from pathlib import Path # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import requests # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs


#############
# CONSTANTS #
#############
ACS_BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData"
GAZ_BASE = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer"


#########
# FILES #
#########
FILES = {
    "acsdt5y2024-b19013.dat": f"{ACS_BASE}/acsdt5y2024-b19013.dat", # median household income
    "acsdt5y2024-b01003.dat": f"{ACS_BASE}/acsdt5y2024-b01003.dat", # total population
    "2024_Gaz_zcta_national.zip": f"{GAZ_BASE}/2024_Gaz_zcta_national.zip", # land area
}

###########
# HEADERS #
###########
HEADERS = {
    "User-Agent":
    "CS418-flock-research-project/1.0 (student research, non-commercial)"
}

# <repo>/data/raw/census/
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "census"


###########################################################################################################################
########
# MAIN #
########
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in FILES.items():
        out_path = OUT_DIR / name

        # These files only change once a year, so skip ones we already have
        if out_path.exists():
            print(f"Already have {out_path.name}, skipping.")
            continue

        print(f"Downloading {url} ...")
        resp = requests.get(url, headers=HEADERS, timeout=300)
        resp.raise_for_status()
        out_path.write_bytes(resp.content) # save the raw bytes, unchanged
        print(f"  wrote {len(resp.content) / 1e6:.1f} MB to {out_path}")


###############
# ENTRY_POINT #
###############
if __name__ == "__main__":
    main()

#######
# EOF #
#######