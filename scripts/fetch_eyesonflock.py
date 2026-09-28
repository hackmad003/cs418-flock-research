#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
###########################
# Eyes On Flock (primary) #
###########################
Download the Eyes On Flock dataset (https://eyesonflock.com) and save it,
untouched, to data/raw/.

Eyes On Flock aggregates Flock Safety transparency portals: per-agency
camera counts, searches, data retention, and which agencies share data
with each other. Coverage is ONLY agencies that enabled a public portal.

The site has no official API docs. This uses the same JSON endpoint the
site's home page loads (/api/v1/data), so it could change without notice.
That's why we save the raw response with the date in the filename.

License: Eyes On Flock content is CC BY-SA 4.0 -- credit them, and share
anything derived from it under the same license.

Example User Usage:
    uv run python scripts/fetch_eyesonflock.py
    uv run python scripts/fetch_eyesonflock.py --out data/raw/eyesonflock_test.json

Load it afterwards with:
    from cs418_flock_research.eyesonflock import load_portals

VVV Sources VVV
https://eyesonflock.com
https://eyesonflock.com/api/v1/data (unofficial, undocumented)
https://creativecommons.org/licenses/by-sa/4.0/ (CC BY-SA 4.0)

Imports Used:
import argparse # https://docs.python.org/3/library/argparse.html
import json # https://docs.python.org/3/library/json.html
import sys # https://docs.python.org/3/library/sys.html
from datetime import date # https://docs.python.org/3/library/datetime.html
from pathlib import Path # https://docs.python.org/3/library/pathlib.html
import requests # https://requests.readthedocs.io/en/latest/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
list() https://docs.python.org/3/library/functions.html#func-list

Object Methods Used:
requests.get() https://requests.readthedocs.io/en/latest/api/#requests.get
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
Response.content (raw bytes) https://requests.readthedocs.io/en/latest/api/#requests.Response.content
json.loads() https://docs.python.org/3/library/json.html#json.loads
sys.exit() https://docs.python.org/3/library/sys.html#sys.exit
argparse.ArgumentParser() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser
.add_argument() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
.parse_args() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.parse_args
date.today() https://docs.python.org/3/library/datetime.html#datetime.date.today
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parent https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parent
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.write_bytes() https://docs.python.org/3/library/pathlib.html#pathlib.Path.write_bytes

Data Structures / Techniques Used:
dict (HEADERS, the parsed JSON) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
"in" membership test ("portals" not in data) https://docs.python.org/3/reference/expressions.html#membership-test-operations
truthiness (if not data["portals"]) https://docs.python.org/3/library/stdtypes.html#truth-value-testing
conditional expression (X if cond else Y) https://docs.python.org/3/reference/expressions.html#conditional-expressions
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
format spec (:.1f) https://docs.python.org/3/library/string.html#format-specification-mini-language
type hints (-> bytes, -> dict) https://docs.python.org/3/library/typing.html
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
User-Agent header https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
"""

###########
# IMPORTS #
###########
import argparse # https://docs.python.org/3/library/argparse.html
# reads command line arguments

import json # https://docs.python.org/3/library/json.html
# converts between JSON text and dicts

import sys # https://docs.python.org/3/library/sys.html#module-sys
# used for sys.exit()

from datetime import date # https://docs.python.org/3/library/datetime.html
# date: gives us today's date, used to put the date in the file name

from pathlib import Path # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import requests # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs


#############
# CONSTANTS #
#############
# The web address that returns ALL the data as JSON. We found it by looking
# at the site's JavaScript: the home page loads its data from here.
DATA_URL = "https://eyesonflock.com/api/v1/data"

# Headers are extra info sent with the request. "User-Agent" tells the
# server who we are, so the site owner knows it's a student project.
HEADERS = {
    "User-Agent":
    "CS418-flock-research-project/1.0 (student research, non-commercial)"
}

# Where to save the file: <repo>/data/raw/
# __file__ is the path of THIS script (scripts/fetch_eyesonflock.py).
# .resolve() turns it into a full path, e.g. D:/.../scripts/fetch_eyesonflock.py
# .parent -> the scripts/ folder
# .parent again -> the repo root folder
# / "data" / "raw" -> joins folder names onto the path
# Doing it this way means the script works no matter which folder you run it from.
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


#########
# FETCH #
#########
def fetch_data() -> bytes:
    """
    Download the full dataset in ONE request (about 16 MB) and return the
    raw bytes exactly as the server sent them.
    """
    print(f"Downloading {DATA_URL} ...") # let the user know it's working

    # Send a GET request ("give me this page") to the data URL.
    # timeout=120: give up if the server takes longer than 120 seconds.
    resp = requests.get(DATA_URL, headers=HEADERS, timeout=120)

    # If the server sent back an error code (like 404 or 500),
    # this raises an exception and stops the program here.
    resp.raise_for_status()

    # resp.content is the response as raw bytes (not decoded into text or
    # a dict). We keep it raw so the saved file is EXACTLY what the server sent.
    return resp.content


############
# VALIDATE #
############
def check_shape(raw: bytes) -> dict:
    """
    Make sure the response looks like what we expect BEFORE saving it,
    so a changed/broken API doesn't silently give us a bad file.
    """
    # Turn the raw bytes into a Python dict. If the server sent something
    # that isn't JSON (like an error web page), this line raises an error.
    data = json.loads(raw)

    # The data should have two top-level keys: "summary" (national totals)
    # and "portals" (one entry per agency). If either is missing, the site
    # probably changed, so stop and show what keys we got instead.
    if "portals" not in data or "summary" not in data:
        sys.exit(f"Unexpected response shape. Top-level keys: {list(data)}")

    # An empty list is "falsy" in Python, so "not data['portals']" is True
    # when there are 0 portals. Don't save an empty dataset.
    if not data["portals"]:
        sys.exit("Response has 0 portals -- not saving.")

    # Everything looks good. Return the dict so main() can count the portals.
    return data


###########################################################################################################################
########
# MAIN #
########
def main():
    # Set up the command line options. There's only one, and it's optional.
    p = argparse.ArgumentParser(description="Download Eyes On Flock portal data")
    p.add_argument(
        "--out",
        default=None, # stays None if the user doesn't pass --out
        help="Output JSON path (default: data/raw/eyesonflock_YYYY-MM-DD.json)",
    )
    args = p.parse_args() # read what the user typed

    # Pick where to save the file:
    # - if the user gave --out, use that path
    # - otherwise, build a default name with today's date in it,
    #   e.g. data/raw/eyesonflock_2026-09-27.json
    # Putting the date in the name means each download is a separate
    # "snapshot" and never overwrites an older one.
    # (This is a one-line if/else: X if condition else Y)
    out_path = Path(args.out) if args.out else RAW_DIR / f"eyesonflock_{date.today()}.json"

    raw = fetch_data()       # 1. download
    data = check_shape(raw)  # 2. make sure it looks right

    # 3. Create the output folder if it doesn't exist yet.
    # parents=True: also create any missing parent folders
    # exist_ok=True: don't error if the folder is already there
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 4. Save the raw bytes to the file, unchanged.
    out_path.write_bytes(raw)

    # Tell the user how it went.
    print(f"Got {len(data['portals'])} agency portals.")
    # len(raw) is the size in bytes. Divide by 1e6 (1,000,000) to get MB.
    # :.1f means "show 1 digit after the decimal point".
    print(f"Wrote {len(raw) / 1e6:.1f} MB to {out_path}")


###############
# ENTRY_POINT #
###############
# This is True only when you run the file directly
# (uv run python scripts/fetch_eyesonflock.py), not when another file imports it.
if __name__ == "__main__":
    main()

#######
# EOF #
#######