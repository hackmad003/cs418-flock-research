#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
#########################################
# EFF Atlas of Surveillance (secondary) #
#########################################


Download the EFF Atlas of Surveillance dataset and save it, untouched, to data/raw/.

The Atlas is a database of which US law enforcement agencies use which
surveillance technologies (ALPR, face recognition, drones, body cams, ...).
One row = one (agency, technology) pair. Used for research question 3.

Source:  https://atlasofsurveillance.org/data-library  ("See Dataset (CSV)")
License: EFF original material is CC BY 4.0 -- credit EFF.

Example User Usage:
    uv run python scripts/fetch_atlas.py

Load it afterwards with:
    from cs418_flock_research.atlas import load_atlas

VVV Sources VVV
https://atlasofsurveillance.org/data-library
https://atlasofsurveillance.org/download.csv
https://creativecommons.org/licenses/by/4.0/ (CC BY 4.0)

Imports Used:
import argparse # https://docs.python.org/3/library/argparse.html
from datetime import date # https://docs.python.org/3/library/datetime.html
from pathlib import Path # https://docs.python.org/3/library/pathlib.html
import requests # https://requests.readthedocs.io/en/latest/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
SystemExit https://docs.python.org/3/library/exceptions.html#SystemExit

Object Methods Used:
requests.get() https://requests.readthedocs.io/en/latest/api/#requests.get
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
Response.content (raw bytes) https://requests.readthedocs.io/en/latest/api/#requests.Response.content
argparse.ArgumentParser() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser
.add_argument() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
.parse_args() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.parse_args
date.today() https://docs.python.org/3/library/datetime.html#datetime.date.today
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parent https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parent
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.write_bytes() https://docs.python.org/3/library/pathlib.html#pathlib.Path.write_bytes
.startswith() (bytes) https://docs.python.org/3/library/stdtypes.html#bytes.startswith

Data Structures / Techniques Used:
dict (HEADERS) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
bytes literal (b'"AOSNUMBER"') https://docs.python.org/3/library/stdtypes.html#bytes-objects
conditional expression (X if cond else Y) https://docs.python.org/3/reference/expressions.html#conditional-expressions
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
format spec (:.1f) https://docs.python.org/3/library/string.html#format-specification-mini-language
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
User-Agent header https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
"""

###########
# IMPORTS #
###########
import argparse # https://docs.python.org/3/library/argparse.html
# reads command line arguments

from datetime import date # https://docs.python.org/3/library/datetime.html
# date: gives us today's date, used to put the date in the file name

from pathlib import Path # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import requests # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs


#############
# CONSTANTS #
#############
# The official CSV download link from the Atlas's "Data Library" page
DATA_URL = "https://atlasofsurveillance.org/download.csv"

# Tell the server who we are (a student project)
HEADERS = {
    "User-Agent":
    "CS418-flock-research-project/1.0 (student research, non-commercial)"
}

# <repo>/data/raw/  (this file lives in scripts/, so go up 2 levels)
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


###########################################################################################################################
########
# MAIN #
########
def main():
    p = argparse.ArgumentParser(description="Download EFF Atlas of Surveillance CSV")
    p.add_argument(
        "--out",
        default=None,
        help="Output CSV path (default: data/raw/atlas_of_surveillance_YYYY-MM-DD.csv)",
    )
    args = p.parse_args()

    # Put today's date in the file name so each download is its own snapshot
    out_path = Path(args.out) if args.out else RAW_DIR / f"atlas_of_surveillance_{date.today()}.csv"

    print(f"Downloading {DATA_URL} ...")
    resp = requests.get(DATA_URL, headers=HEADERS, timeout=120)
    resp.raise_for_status() # stop on 4xx/5xx errors

    # Quick check: a real CSV starts with the header row. If we got a web
    # page instead (e.g. an error page), don't save it.
    if not resp.content.startswith(b'"AOSNUMBER"'):
       raise SystemExit("Response doesn't look like the Atlas CSV -- not saving.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(resp.content) # save the raw bytes, unchanged

    print(f"Wrote {len(resp.content) / 1e6:.1f} MB to {out_path}")


###############
# ENTRY_POINT #
###############
if __name__ == "__main__":
    main()
