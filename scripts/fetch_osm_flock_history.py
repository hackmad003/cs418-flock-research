#!/usr/bin/env python3
"""
###########
# FETCHER #
###########
######################################
# OpenStreetMap Flock Camera History #
######################################


Download the current Flock ALPR camera nodes from OpenStreetMap (OSM),
look up each node's OSM edit history, and save the result to
data/raw/flock_osm/flock_<scope>_historical_YYYY-MM-DD.csv
(YYYY-MM-DD = UTC run date).

One row = one OSM camera node, with the dates it was first mapped and
first tagged as Flock. These are MAPPING dates, not installation dates.

Source:  https://www.openstreetmap.org/  (Overpass API + OSM API v0.6)
License: OSM data is ODbL 1.0 -- credit "(c) OpenStreetMap contributors".

Example User Usage (from the repository root):
    uv run python scripts/fetch_osm_flock_history.py

PURPOSE
-------
This script retrieves the current set of OSM nodes tagged as Flock
Safety ALPR cameras, then looks up each node's OSM edit history to
add historical mapping dates.

For the CS418 Flock Safety research project, this dataset is used to:

1. Examine how the number of MAPPED Flock cameras grew over time.
2. Distinguish when a node was created from when it was first
   identified as a Flock ALPR camera.
3. Support time-based comparisons across states, counties, and
   regions, subject to the limitations described below.

IMPORTANT:
OSM contains community-mapped cameras, NOT a complete inventory
of all physically installed ALPR cameras in the United States.

The dates produced here describe OSM MAPPING activity, NOT
physical camera installation.


DATA SOURCES
------------
Overpass API (current camera snapshot):
    https://overpass-api.de/api/interpreter

OSM API v0.6 (per-node edit history):
    https://api.openstreetmap.org/api/0.6/node/<id>/history.json

Overpass returns the current version of every matching node.
The OSM API returns every historical version of a single node,
which is used to find its creation and first Flock tagging.

Only OSM nodes (point features) are queried. Cameras represented
as ways or relations are not included.


CAMERA FILTERING
----------------
A node is treated as a Flock ALPR camera when all three hold:

    man_made=surveillance
    surveillance:type=ALPR
    manufacturer matching "Flock" (case-insensitive)

The same rule is applied in two places:

    - The Overpass query (current snapshot).
    - is_flock_alpr() (each historical version).

This is not an exact manufacturer="Flock Safety" comparison.
Cameras with missing or alternative manufacturer tags may be
excluded even if they are physically Flock cameras.


GEOGRAPHIC SCOPE
----------------
The scope is set with the SCOPE constant, not a command-line flag.

    "us"       Nationwide, using the OSM area ISO3166-1=US.
    "chicago"  City of Chicago, admin_level=8 boundary.

Each scope gets its own cache, checkpoint, and output files,
so switching scopes never mixes data.


HOW THE OVERPASS QUERY WORKS
----------------------------
Example nationwide query:

    [out:csv(::id, ::lat, ::lon, ::timestamp, ::version,
             ::changeset, ::user, "man_made",
             "surveillance:type", "manufacturer",
             "operator"; true)][timeout:600];

    area["ISO3166-1"="US"]->.scope;

    node["man_made"="surveillance"]
        ["surveillance:type"="ALPR"]
        ["manufacturer"~"Flock",i]
        (area.scope);

    out meta;

Explanation:

    [out:csv(...; true)]
        Return tab-separated rows with the listed metadata
        and tag columns, including a header row.

    [timeout:600]
        Allow up to 600 seconds for server-side execution.

    (area.scope)
        Restrict results to the selected geographic area.

    out meta
        Include version, timestamp, changeset, and user.

The downloaded snapshot is validated (no duplicate IDs, no null
id/version/lat/lon, and a rough row-count check) before it is
cached. A cached snapshot is reused on later runs.


HOW HISTORY IS RECONSTRUCTED
----------------------------
1. Version-1 nodes have never been edited, so their creation date,
   first-tagged date, and last edit are all the snapshot timestamp.
   No API request is needed.

2. Edited nodes (version > 1) require one OSM API history request.

   first_insert_*  comes from the earliest version.
   first_tagged_*  comes from the earliest visible version whose
                   tags satisfy is_flock_alpr().

Only edited nodes are saved to the checkpoint file, so an
interrupted run resumes without repeating completed lookups.


WHAT THE DATE COLUMNS MEAN (and do NOT mean)
--------------------------------------------
    first_insert_date:
        When the OSM node was originally created.

    first_tagged_date:
        When an OSM version first identified the node as a
        Flock ALPR camera. Can be later than first_insert_date.

    last_edit:
        When the node was most recently edited in OSM.

IMPORTANT DISTINCTIONS:

- None of these is the date a physical camera was installed.
- A camera installed in 2022 may only have been mapped in 2025.
- A camera deleted and re-added as a new node gets new dates.
- Analyses built on these columns describe growth in MAPPED
  cameras, not deployment.


OUTPUT COLUMNS
--------------
The final CSV contains one row per camera node:

    osm_id
    lat
    lon
    manufacturer
    operator
    version
    last_edit
    changeset
    user
    history_ok
    first_insert_date
    first_insert_version
    first_tagged_date
    first_tagged_version
    first_tagged_changeset

history_ok is False when no history result exists for the node.

Date columns are parsed as UTC datetimes.


OUTPUT FILES
------------
All files are saved in data/raw/flock_osm/ (gitignored):

    flock_<scope>_historical_<YYYY-MM-DD>.csv
        Final dataset, e.g. flock_us_historical_2026-10-30.csv

    flock_<scope>_historical_<YYYY-MM-DD>_INCOMPLETE.csv
        Written instead if any history lookup is missing.

    flock_<scope>_current.csv
        Cached Overpass snapshot (reused on later runs).

    flock_<scope>_current_UNVERIFIED.csv
        Fresh snapshot that failed the count check. Never reused.

    flock_<scope>_history_checkpoint.jsonl
        Resumable API progress.

    flock_<scope>_history_unresolved.csv
        Edited nodes still missing history.

In sample mode, the historical, checkpoint, and unresolved
filenames receive a "_sample" suffix.

The date is the UTC calendar date when the script runs.

The history file is a separate Overpass pull from
osm_flock_us_locations_*.csv, so the two files differ slightly
in rows.


SAMPLE MODE
-----------
Set SAMPLE_SIZE to an integer (e.g. 200) to process a random
sample of edited nodes, selected with SAMPLE_SEED.

Sample mode prints the average time per lookup and a runtime
projection for the full run.

Set SAMPLE_SIZE = None to process every camera in the scope.


API RELIABILITY AND RETRIES
---------------------------
Overpass:
    A single request is sent. HTTP errors are raised immediately.

OSM API history requests:
    Each node is attempted up to MAX_RETRIES times.

    Retried statuses:

        HTTP 429: Too Many Requests
        HTTP 500: Internal Server Error
        HTTP 502: Bad Gateway
        HTTP 503: Service Unavailable
        HTTP 504: Gateway Timeout
        HTTP 509: Bandwidth Limit Exceeded

    The Retry-After header is respected (clamped to 1-120 seconds);
    otherwise an exponential backoff is used.

    If 429/509 persists through every retry, the whole run stops
    rather than continuing to hammer a rate-limited API.

    Other 4xx responses are not retried.

    REQUEST_DELAY seconds are waited after every history request.

Pressing Ctrl-C stops the run; completed lookups remain in the
checkpoint and the partial dataset is still exported.


RESEARCH LIMITATIONS
--------------------
1. OSM coverage is incomplete and geographically uneven.

2. Camera records are community-contributed and may contain
   incorrect, missing, or outdated tags.

3. Only matching OSM nodes are retrieved; ways and relations
   are excluded.

4. The Flock filter depends on manufacturer tagging and may omit
   legitimate Flock cameras.

5. Historical dates describe OSM mapping activity, not physical
   installation or procurement.

6. Cameras deleted from OSM are absent from the current snapshot
   and therefore from this dataset.

7. Growth over time may reflect mapping campaigns and contributor
   activity rather than actual deployment.

These limitations should be acknowledged when interpreting
camera counts, geographic distributions, and temporal trends.


EXAMPLES
--------
Run commands from the repository root.

Full run using the configured SCOPE:

    uv run python scripts/fetch_osm_flock_history.py

Resume an interrupted run (same command; progress is reused):

    uv run python scripts/fetch_osm_flock_history.py

Set the OSM API contact email for the User-Agent (PowerShell):

    $env:OSM_CONTACT = "you@example.org"
    uv run python scripts/fetch_osm_flock_history.py


DEPENDENCIES
------------
Python 3, requests, and polars.

Install or register them in the uv project environment:

    uv add requests polars

Run the script using the project's environment:

    uv run python scripts/fetch_osm_flock_history.py

VVV Sources VVV
https://www.openstreetmap.org/
https://wiki.openstreetmap.org/wiki/Overpass_API
https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#CSV_output_mode
https://wiki.openstreetmap.org/wiki/API_v0.6 (node history: GET /api/0.6/node/<id>/history)
https://operations.osmfoundation.org/policies/api/ (OSM API usage policy)
https://www.openstreetmap.org/copyright (ODbL 1.0)

Imports Used:
import io  # https://docs.python.org/3/library/io.html
import json  # https://docs.python.org/3/library/json.html
import os  # https://docs.python.org/3/library/os.html
import time  # https://docs.python.org/3/library/time.html
from datetime import datetime, timezone  # https://docs.python.org/3/library/datetime.html
from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
import requests  # https://requests.readthedocs.io/en/latest/
import polars as pl  # https://docs.pola.rs/api/python/stable/reference/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
abs() https://docs.python.org/3/library/functions.html#abs
sum() https://docs.python.org/3/library/functions.html#sum
min() / max() https://docs.python.org/3/library/functions.html#max
int() https://docs.python.org/3/library/functions.html#int
float() https://docs.python.org/3/library/functions.html#float
str() https://docs.python.org/3/library/stdtypes.html#str
bool() https://docs.python.org/3/library/functions.html#bool
list() https://docs.python.org/3/library/stdtypes.html#list
set() https://docs.python.org/3/library/stdtypes.html#set
next() https://docs.python.org/3/library/functions.html#next
sorted() https://docs.python.org/3/library/functions.html#sorted
enumerate() https://docs.python.org/3/library/functions.html#enumerate
range() https://docs.python.org/3/library/stdtypes.html#range
SystemExit https://docs.python.org/3/library/exceptions.html#SystemExit
KeyboardInterrupt https://docs.python.org/3/library/exceptions.html#KeyboardInterrupt
Exception / ValueError / KeyError / TypeError / NameError / RuntimeError https://docs.python.org/3/library/exceptions.html

Object Methods Used:
requests.Session() https://requests.readthedocs.io/en/latest/user/advanced/#session-objects
.headers.update() https://requests.readthedocs.io/en/latest/api/#requests.Session.headers
.post() / .get() (session) https://requests.readthedocs.io/en/latest/api/#requests.Session.request
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
.status_code https://requests.readthedocs.io/en/latest/api/#requests.Response.status_code
.text https://requests.readthedocs.io/en/latest/api/#requests.Response.text
.json() https://requests.readthedocs.io/en/latest/api/#requests.Response.json
requests.RequestException https://requests.readthedocs.io/en/latest/api/#requests.RequestException
io.StringIO() https://docs.python.org/3/library/io.html#io.StringIO
os.environ.get() https://docs.python.org/3/library/os.html#os.environ
os.fsync() https://docs.python.org/3/library/os.html#os.fsync
.fileno() / .flush() https://docs.python.org/3/library/io.html#io.IOBase.fileno
.read() / .truncate() / .write() (file) https://docs.python.org/3/library/io.html#io.IOBase.truncate
json.loads() https://docs.python.org/3/library/json.html#json.loads
json.dumps() https://docs.python.org/3/library/json.html#json.dumps
json.JSONDecodeError https://docs.python.org/3/library/json.html#json.JSONDecodeError
datetime.now() https://docs.python.org/3/library/datetime.html#datetime.datetime.now
.strftime() https://docs.python.org/3/library/datetime.html#datetime.datetime.strftime
time.sleep() https://docs.python.org/3/library/time.html#time.sleep
time.monotonic() https://docs.python.org/3/library/time.html#time.monotonic
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
Path.cwd() https://docs.python.org/3/library/pathlib.html#pathlib.Path.cwd
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parent / .parents https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parents
.exists() https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.open() https://docs.python.org/3/library/pathlib.html#pathlib.Path.open
.unlink() https://docs.python.org/3/library/pathlib.html#pathlib.Path.unlink
.name https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.name
.endswith() / .rfind() (bytes) https://docs.python.org/3/library/stdtypes.html#bytes.rfind
.casefold() https://docs.python.org/3/library/stdtypes.html#str.casefold
.startswith() / .lstrip() https://docs.python.org/3/library/stdtypes.html#str.lstrip
.replace() (str) https://docs.python.org/3/library/stdtypes.html#str.replace
.join() https://docs.python.org/3/library/stdtypes.html#str.join
.get() / .pop() (dict) https://docs.python.org/3/library/stdtypes.html#dict.get
.append() https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
pl.read_csv() https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html
pl.DataFrame() https://docs.pola.rs/api/python/stable/reference/dataframe/index.html
pl.col() https://docs.pola.rs/api/python/stable/reference/expressions/col.html
.cast() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.cast.html
.str.to_datetime() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.str.to_datetime.html
.rename() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.rename.html
.with_columns() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.with_columns.html
.filter() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.filter.html
.sample() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sample.html
.to_dicts() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.to_dicts.html
.write_csv() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.write_csv.html
.is_empty() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.is_empty.html
.head() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.head.html
.height / .shape / .columns https://docs.pola.rs/api/python/stable/reference/dataframe/attributes.html
.n_unique() (Series) https://docs.pola.rs/api/python/stable/reference/series/api/polars.Series.n_unique.html
.null_count() (Series) https://docs.pola.rs/api/python/stable/reference/series/api/polars.Series.null_count.html
.value_counts() (Series) https://docs.pola.rs/api/python/stable/reference/series/api/polars.Series.value_counts.html
.to_list() (Series) https://docs.pola.rs/api/python/stable/reference/series/api/polars.Series.to_list.html

Data Structures / Techniques Used:
dict (AREAS, EXPECTED_COUNTS, results) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
set (RETRY_STATUSES) https://docs.python.org/3/tutorial/datastructures.html#sets
list / dict comprehensions https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
generator expression (next(...), sum(...)) https://docs.python.org/3/reference/expressions.html#generator-expressions
lambda (sort key) https://docs.python.org/3/reference/expressions.html#lambda
dict unpacking ({"id": ..., **result}) https://docs.python.org/3/reference/expressions.html#dictionary-displays
custom exception classes https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions
try / except / finally https://docs.python.org/3/tutorial/errors.html#defining-clean-up-actions
with statement (context managers) https://docs.python.org/3/reference/compound_stmts.html#the-with-statement
JSON Lines checkpoint file https://jsonlines.org/
exponential backoff + Retry-After https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After
conditional expression (X if cond else Y) https://docs.python.org/3/reference/expressions.html#conditional-expressions
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
format spec (:.1f, :.0%) https://docs.python.org/3/library/string.html#format-specification-mini-language
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
User-Agent header https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
"""


###########
# IMPORTS #
###########
import io  # https://docs.python.org/3/library/io.html
# io.StringIO: lets polars read the downloaded CSV text as if it were a file

import json  # https://docs.python.org/3/library/json.html
# reads and writes the JSON Lines checkpoint file

import os  # https://docs.python.org/3/library/os.html
# os.environ: reads OSM_CONTACT; os.fsync: forces checkpoint writes to disk

import time  # https://docs.python.org/3/library/time.html
# time.sleep(): pause between API requests; time.monotonic(): time each lookup

from datetime import datetime, timezone  # https://docs.python.org/3/library/datetime.html
# datetime/timezone: today's UTC date, used to put the date in the file name

from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import requests  # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs

import polars as pl  # https://docs.pola.rs/
# fast DataFrame library used to load, check, and save the camera table


#############
# CONSTANTS #
#############
# Overpass: current camera snapshot. OSM API: per-node edit history.
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_API = "https://api.openstreetmap.org/api/0.6"

# Replace with your real contact email or set OSM_CONTACT.
CONTACT = os.environ.get("OSM_CONTACT", "hackmad003@gmail.com")

# Tell the server who we are (the OSM API asks for contact info)
USER_AGENT = f"FlockOSMResearch/1.0 (contact: {CONTACT})"

# Wait 1 second after every history request; try each node up to 5 times
REQUEST_DELAY = 1.0
MAX_RETRIES = 5

# 509 = OSM API bandwidth limit exceeded.
RATE_LIMIT_STATUSES = {429, 509}
RETRY_STATUSES = {429, 500, 502, 503, 504, 509}

# OSM timestamps look like 2024-03-05T14:22:10Z (UTC).
OSM_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# "us" = nationwide, "chicago" = Chicago only.
# Each scope gets its own cache, checkpoint and output files,
# so switching scopes never mixes data.
SCOPE = "us"

# None = every camera in the scope
# 200 = test on 200 randomly selected edited cameras (prints a
#       runtime projection for the full run)
SAMPLE_SIZE = None
SAMPLE_SEED = 42

# Rough sanity check for a fresh download, NOT an exact truth:
# OSM is edited constantly and different filters return different
# counts. A big gap means "check the query", not "definitely wrong".
EXPECTED_COUNTS = {"us": 111_128, "chicago": None}
COUNT_TOLERANCE = 0.10
SKIP_COUNT_CHECK = False

# Overpass area filter for each SCOPE
AREAS = {
    "us": 'area["ISO3166-1"="US"]->.scope;',
    "chicago": (
        'area["name"="Chicago"]'
        '["boundary"="administrative"]'
        '["admin_level"="8"]->.scope;'
    ),
}

# Stop right away if SCOPE is misspelled
if SCOPE not in AREAS:
    raise SystemExit(f"SCOPE must be one of {list(AREAS)}")


##################
# FIND REPO ROOT #
##################
def find_repo_root() -> Path:
    """Return the repository root: the nearest folder (going upward) that contains .git."""
    try:
        here = Path(__file__).resolve().parent
    except NameError:
        here = Path.cwd().resolve()

    # [here, *here.parents] = this folder followed by every parent folder
    # (the * unpacks the parents into the list).
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p

    return here


#######################
# PROJECT DIRECTORIES #
#######################
REPO_ROOT = find_repo_root()

# Everything lives next to the existing research snapshot
# (data/raw/flock_osm/flock_us_historical_2026-10-30.csv). The final file
# used to go to data/processed/, which is NOT gitignored, so a full
# nationwide dataset could have been committed by accident.
RAW_DIR = REPO_ROOT / "data" / "raw" / "flock_osm"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# Put today's UTC date in the file name so each run is its own snapshot
SNAPSHOT_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Sample runs get their own files so they never mix with a full run
RUN_SUFFIX = "_sample" if SAMPLE_SIZE is not None else ""

# Cached Overpass snapshot, reused on later runs
CURRENT_FILE = RAW_DIR / f"flock_{SCOPE}_current.csv"

# A fresh download that fails the count check is saved here so you
# can inspect it without downloading again. It is never reused.
UNVERIFIED_FILE = RAW_DIR / f"flock_{SCOPE}_current_UNVERIFIED.csv"

# One JSON line per finished history lookup, so a run can resume
CHECKPOINT_FILE = RAW_DIR / (
    f"flock_{SCOPE}_history_checkpoint{RUN_SUFFIX}.jsonl"
)

# Lists every edited node that still has no history result.
FAILURES_FILE = RAW_DIR / (
    f"flock_{SCOPE}_history_unresolved{RUN_SUFFIX}.csv"
)

# Final dataset, written only when every lookup succeeded
OUTPUT_FILE = RAW_DIR / (
    f"flock_{SCOPE}_historical_{SNAPSHOT_DATE}{RUN_SUFFIX}.csv"
)

# Written instead of OUTPUT_FILE whenever some history is missing,
# so an unfinished dataset can't be mistaken for a finished one.
INCOMPLETE_FILE = RAW_DIR / (
    f"flock_{SCOPE}_historical_{SNAPSHOT_DATE}{RUN_SUFFIX}_INCOMPLETE.csv"
)


################
# HTTP SESSION #
################
# One reusable connection with our headers on every request
session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
})


##################
# OVERPASS QUERY #
##################
QUERY_TEMPLATE = """
[out:csv(
    ::id,
    ::lat,
    ::lon,
    ::timestamp,
    ::version,
    ::changeset,
    ::user,
    "man_made",
    "surveillance:type",
    "manufacturer",
    "operator";
    true
)][timeout:600];

__AREA__

node["man_made"="surveillance"]
    ["surveillance:type"="ALPR"]
    ["manufacturer"~"Flock",i]
    (area.scope);

out meta;
"""

query = QUERY_TEMPLATE.replace("__AREA__", AREAS[SCOPE])


#####################
# VALIDATE SNAPSHOT #
#####################
def validate_snapshot(df: pl.DataFrame, check_count: bool) -> None:
    """Raise if the snapshot looks truncated or corrupt."""

    problems = []

    duplicates = df.height - df["id"].n_unique()
    if duplicates:
        problems.append(f"{duplicates} duplicate IDs")

    for col in ("id", "version", "lat", "lon"):
        nulls = df[col].null_count()
        if nulls:
            problems.append(f"{nulls} null values in '{col}'")

    if problems:
        raise ValueError(
            "Snapshot failed validation: " + "; ".join(problems)
        )

    if not check_count or SKIP_COUNT_CHECK:
        return

    expected = EXPECTED_COUNTS.get(SCOPE)

    if not expected:
        return

    gap = abs(df.height - expected) / expected

    if gap > COUNT_TOLERANCE:
        df.write_csv(UNVERIFIED_FILE)
        raise ValueError(
            f"Got {df.height} nodes, but expected roughly {expected} "
            f"({gap:.0%} off). The download may be truncated, or your "
            "tag filters may differ from the earlier count. Saved to "
            f"{UNVERIFIED_FILE.name} for inspection and NOT cached. "
            "If the number is right, set SKIP_COUNT_CHECK = True."
        )

    if gap > 0.02:
        print(
            f"Note: {df.height} nodes vs. ~{expected} expected "
            f"({gap:.1%} off). Probably fine."
        )


############################
# DOWNLOAD CURRENT CAMERAS #
############################
def download_current_cameras() -> pl.DataFrame:
    """Load the cached snapshot or download a fresh one, validate it, and return it."""

    fresh = not CURRENT_FILE.exists()

    if not fresh:
        print(f"Loading cached data: {CURRENT_FILE}")

        df = pl.read_csv(
            CURRENT_FILE,
            infer_schema_length=0
        )

    else:
        print(f"Downloading Flock camera records (scope: {SCOPE})...")
        print("A nationwide query can take a few minutes.")

        response = session.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=900
        )

        response.raise_for_status()  # stop on 4xx/5xx errors

        df = pl.read_csv(
            io.StringIO(response.text),
            separator="\t",
            quote_char=None,
            infer_schema_length=0
        )

        # Remove Overpass metadata prefixes ("@id" -> "id").
        # The {old: new for ...} dict comprehension builds the rename map.
        df = df.rename({
            c: c.lstrip("@")
            for c in df.columns
            if c.startswith("@")
        })

    required = {
        "id", "version", "timestamp",
        "lat", "lon", "changeset"
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}. "
            f"Received columns: {df.columns}. "
            "Overpass may have returned an error page."
        )

    df = df.with_columns(
        pl.col("id").cast(pl.Int64),
        pl.col("version").cast(pl.Int64),
        pl.col("changeset").cast(pl.Int64, strict=False),
        pl.col("lat").cast(pl.Float64, strict=False),
        pl.col("lon").cast(pl.Float64, strict=False),
    )

    # Validate BEFORE caching, so a bad download is never reused.
    validate_snapshot(df, check_count=fresh)

    if fresh:
        df.write_csv(CURRENT_FILE)

    print(f"\nTotal camera nodes ({SCOPE}): {df.height}")

    if not df.is_empty():
        print("\nOSM version distribution:")
        print(
            df["version"]
            .value_counts()
            .sort("version")
            .head(10)
        )

    return df


#################
# IS FLOCK ALPR #
#################
def is_flock_alpr(tags: dict) -> bool:
    """Return True if a set of OSM tags marks a node as a Flock ALPR camera."""

    return (
        tags.get("man_made") == "surveillance"
        and tags.get(
            "surveillance:type", ""
        ).casefold() == "alpr"
        and "flock" in tags.get(
            "manufacturer", ""
        ).casefold()
    )


######################
# HISTORY API ERRORS #
######################
class NonRetryableError(Exception):
    """A request failed in a way retrying will not fix (e.g. HTTP 404)."""
    pass


class RateLimitError(Exception):
    """429/509 persisted through every retry: stop the whole run."""


###############
# RETRY DELAY #
###############
def retry_delay(response: requests.Response, attempt: int) -> float:
    """Return seconds to wait: Retry-After if given, else exponential backoff (1-120 s)."""

    try:
        delay = float(
            response.headers.get("Retry-After")
        )
    except (TypeError, ValueError):
        delay = 2 ** attempt + 2

    return max(1, min(delay, 120))


####################
# GET NODE HISTORY #
####################
def get_node_history(node_id: int) -> list:
    """Download every OSM version of one node, sorted oldest first."""

    url = f"{OSM_API}/node/{node_id}/history.json"

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:
            response = session.get(
                url,
                timeout=45
            )

        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2 ** attempt + 2)
            continue

        status = response.status_code

        if status in RETRY_STATUSES:

            delay = retry_delay(response, attempt)

            print(
                f"Node {node_id}: HTTP {status}, "
                f"retrying in {delay}s"
            )

            last_error = f"HTTP {status}"

            # Stop rather than hammering a rate-limited API.
            if (
                status in RATE_LIMIT_STATUSES
                and attempt == MAX_RETRIES - 1
            ):
                raise RateLimitError(
                    f"Node {node_id}: HTTP {status} on all "
                    f"{MAX_RETRIES} attempts"
                )

            time.sleep(delay)
            continue

        if 400 <= status < 500:
            raise NonRetryableError(
                f"Node {node_id}: HTTP {status}"
            )

        if status != 200:
            last_error = f"HTTP {status}"
            time.sleep(2 ** attempt + 2)
            continue

        try:
            versions = response.json()["elements"]

        except (ValueError, KeyError) as exc:
            last_error = exc
            time.sleep(2 ** attempt + 2)
            continue

        # Oldest version first; the lambda tells sorted() to compare "version".
        return sorted(
            versions,
            key=lambda v: v["version"]
        )

    raise RuntimeError(
        f"Node {node_id}: failed after "
        f"{MAX_RETRIES} attempts: {last_error}"
    )


###################
# EXTRACT HISTORY #
###################
def extract_history(node_id: int) -> dict:
    """Return the creation date and first Flock-tagged date for one node."""

    history = get_node_history(node_id)

    if not history:
        raise ValueError(
            f"Node {node_id}: empty history"
        )

    # Original OSM object creation.
    first_version = history[0]

    # First historical version matching Flock ALPR tags.
    # next(generator, None) returns the first match, or None if none match.
    first_flock = next(
        (
            version
            for version in history
            if version.get("visible", True)
            and is_flock_alpr(
                version.get("tags", {})
            )
        ),
        None
    )

    return {
        "first_insert_date": first_version["timestamp"],
        "first_insert_version": first_version["version"],

        "first_tagged_date": (
            first_flock["timestamp"]
            if first_flock else None
        ),

        "first_tagged_version": (
            first_flock["version"]
            if first_flock else None
        ),

        "first_tagged_changeset": (
            first_flock.get("changeset")
            if first_flock else None
        ),
    }


###################
# LOAD CHECKPOINT #
###################
# Only nodes that needed an API history call are saved here.
# Version-1 nodes are derived from the snapshot for free, so
# skipping them avoids ~100k slow disk flushes.
def load_checkpoint() -> dict:
    """Load finished history lookups from the checkpoint file (node id -> result)."""

    checkpoint = {}

    if not CHECKPOINT_FILE.exists():
        return checkpoint

    # Repair a truncated trailing record after a crash.
    with CHECKPOINT_FILE.open("rb+") as f:
        content = f.read()

        if content and not content.endswith(b"\n"):
            last_newline = content.rfind(b"\n")
            f.truncate(last_newline + 1)

    with CHECKPOINT_FILE.open(
        "r", encoding="utf-8"
    ) as f:

        for line in f:
            if not line.strip():
                continue

            try:
                record = json.loads(line)
                node_id = str(record.pop("id"))
                checkpoint[node_id] = record

            except (json.JSONDecodeError, KeyError):
                continue

    print(
        f"Resuming from {len(checkpoint)} "
        "completed history lookups"
    )

    return checkpoint


#####################
# APPEND CHECKPOINT #
#####################
def append_checkpoint(node_id: int, result: dict) -> None:
    """Append one finished lookup to the checkpoint file and force it to disk."""

    # **result copies every key/value from result into this new dict.
    record = json.dumps({
        "id": node_id,
        **result
    }) + "\n"

    # Append a complete JSONL record.
    with CHECKPOINT_FILE.open("a", encoding="utf-8") as f:
        f.write(record)
        f.flush()
        os.fsync(f.fileno())


###################
# PROCESS CAMERAS #
###################
def process_cameras(df: pl.DataFrame) -> tuple:
    """
    Returns (results, errors, average_seconds, stop_reason).
    results: node id (str) -> historical dates
    errors:  node id (int) -> error message from THIS run
    """

    checkpoint = load_checkpoint()
    results = {}
    errors = {}
    stop_reason = None

    cameras = df.to_dicts()
    total = len(cameras)

    remaining = sum(
        1 for camera in cameras
        if camera["version"] > 1
        and str(int(camera["id"])) not in checkpoint
    )

    print(
        f"\nEdited nodes needing history requests: {remaining} "
        f"(~{remaining * (REQUEST_DELAY + 0.3) / 3600:.1f} hours)"
    )

    api_calls = 0
    api_seconds = 0.0

    try:
        for i, camera in enumerate(cameras, start=1):

            node_id = int(camera["id"])
            key = str(node_id)

            if i % 10000 == 0:
                print(f"Scanned {i}/{total} cameras")

            # Never edited: creation = first tagged = last edit.
            if camera["version"] == 1:
                results[key] = {
                    "first_insert_date": camera["timestamp"],
                    "first_insert_version": 1,
                    "first_tagged_date": camera["timestamp"],
                    "first_tagged_version": 1,
                    "first_tagged_changeset": camera["changeset"],
                }
                continue

            # Edited node already looked up in a previous run.
            if key in checkpoint:
                results[key] = checkpoint[key]
                continue

            started = time.monotonic()

            try:
                result = extract_history(node_id)

                # Save to disk before counting it as done.
                append_checkpoint(node_id, result)
                results[key] = result

            except RateLimitError as exc:

                print(f"Failed node {node_id}: {exc}")
                errors[node_id] = str(exc)
                stop_reason = "API rate limiting (429/509)"
                break

            except Exception as exc:

                print(f"Failed node {node_id}: {exc}")
                errors[node_id] = str(exc)

            finally:
                time.sleep(REQUEST_DELAY)
                api_seconds += time.monotonic() - started
                api_calls += 1

            if api_calls % 25 == 0:
                print(
                    f"History lookups: {api_calls}/{remaining} | "
                    f"Failures: {len(errors)}"
                )

    except KeyboardInterrupt:
        stop_reason = "interrupted by user (Ctrl-C)"

    if stop_reason:
        print(f"\nRun stopped early: {stop_reason}")

    average = (
        api_seconds / api_calls
        if api_calls else None
    )

    return results, errors, average, stop_reason


#######################
# REPORT COMPLETENESS #
#######################
def report_completeness(df: pl.DataFrame, results: dict, errors: dict) -> bool:
    """Print progress, write the unresolved list, return True if done."""

    edited_ids = [
        int(i) for i in
        df.filter(pl.col("version") > 1)["id"].to_list()
    ]

    unresolved = [
        i for i in edited_ids
        if str(i) not in results
    ]

    done = len(edited_ids) - len(unresolved)

    percent = (
        100 * done / len(edited_ids)
        if edited_ids else 100.0
    )

    print("\n--- History completeness ---")
    print(f"Edited nodes needing lookups: {len(edited_ids)}")
    print(f"Successfully completed:       {done}")
    print(f"Unresolved:                   {len(unresolved)}")
    print(f"Completion:                   {percent:.1f}%")

    if unresolved:
        pl.DataFrame({
            "id": unresolved,
            "last_error": [
                errors.get(
                    i, "not completed (run stopped or not reached)"
                )
                for i in unresolved
            ],
        }).write_csv(FAILURES_FILE)

        print(f"Unresolved list saved: {FAILURES_FILE}")
        print("Rerun the script to retry them (progress is saved).")

    elif FAILURES_FILE.exists():
        FAILURES_FILE.unlink()

    return not unresolved


#######################
# BUILD FINAL DATASET #
#######################
def build_final_dataset(df: pl.DataFrame, results: dict, complete: bool) -> pl.DataFrame:
    """Combine the snapshot with the history results and save the final (or INCOMPLETE) CSV."""

    if df.is_empty():
        print("\nNo matching Flock ALPR nodes found.")
        return df

    rows = []

    for camera in df.to_dicts():

        node_id = int(camera["id"])

        historical = results.get(
            str(node_id), {}
        )

        rows.append({
            "osm_id": node_id,
            "lat": camera.get("lat"),
            "lon": camera.get("lon"),
            "manufacturer": camera.get("manufacturer"),
            "operator": camera.get("operator"),

            "version": camera["version"],
            "last_edit": camera["timestamp"],
            "changeset": camera.get("changeset"),
            "user": camera.get("user"),

            "history_ok": bool(historical),

            "first_insert_date": historical.get(
                "first_insert_date"
            ),
            "first_insert_version": historical.get(
                "first_insert_version"
            ),

            "first_tagged_date": historical.get(
                "first_tagged_date"
            ),
            "first_tagged_version": historical.get(
                "first_tagged_version"
            ),
            "first_tagged_changeset": historical.get(
                "first_tagged_changeset"
            ),
        })

    result = pl.DataFrame(
        rows,
        infer_schema_length=None
    )

    # OSM timestamps end in "Z" (UTC). Newer Polars versions require
    # an explicit format and time zone instead of guessing.
    for col in (
        "last_edit",
        "first_insert_date",
        "first_tagged_date"
    ):

        result = result.with_columns(
            pl.col(col)
            .cast(pl.Utf8)
            .str.to_datetime(
                format=OSM_TIMESTAMP_FORMAT,
                time_zone="UTC",
                strict=False,
            )
        )

    out_path = OUTPUT_FILE if complete else INCOMPLETE_FILE

    result.write_csv(out_path)

    # Never leave a stale file of the opposite kind lying around.
    if complete and INCOMPLETE_FILE.exists():
        INCOMPLETE_FILE.unlink()

    if complete:
        print("\nHistorical dataset saved (COMPLETE).")
    else:
        print(
            "\n*** INCOMPLETE dataset saved. Some history is missing. "
            "Do not analyze this as final data. ***"
        )

    print(f"File: {out_path}")
    print(f"Shape: {result.shape}")

    print(
        "Missing creation dates:",
        result["first_insert_date"].null_count()
    )

    print(
        "Missing first-tagged dates:",
        result["first_tagged_date"].null_count()
    )

    retagged = result.filter(
        pl.col("first_tagged_date") > pl.col("first_insert_date")
    ).height

    print(
        "Cameras tagged as Flock after they were first mapped:",
        retagged
    )

    print(
        "\nReminder: these dates are when cameras were MAPPED in "
        "OSM, not when they were installed."
    )

    return result


########
# MAIN #
########
def main() -> None:
    """Download the snapshot, look up each camera's history, and export the dataset."""

    if "example.com" in CONTACT:
        raise SystemExit(
            "Please set a real contact email "
            "using OSM_CONTACT or edit CONTACT."
        )

    df = download_current_cameras()

    if df.is_empty():
        print(
            "No matching cameras were returned. "
            "Verify the area and tags."
        )
        return

    full_edited_count = df.filter(
        pl.col("version") > 1
    ).height

    if SAMPLE_SIZE is not None:

        edited = df.filter(
            pl.col("version") > 1
        )

        if edited.is_empty():
            print("No edited nodes available for sampling.")
            return

        df = edited.sample(
            min(SAMPLE_SIZE, edited.height),
            seed=SAMPLE_SEED
        )

        print(
            f"\nSAMPLE MODE: {df.height} edited nodes"
        )

    results, errors, avg_seconds, stop_reason = process_cameras(df)

    if SAMPLE_SIZE is not None and avg_seconds:

        estimated_hours = (
            full_edited_count * avg_seconds / 3600
        )

        print(
            f"\nAverage: {avg_seconds:.2f}s per node"
        )

        print(
            f"Estimated full runtime: "
            f"{estimated_hours:.2f} hours "
            f"for {full_edited_count} edited nodes "
            "(longer if rate limiting kicks in)"
        )

    complete = report_completeness(df, results, errors)

    result = build_final_dataset(
        df, results, complete
    )

    print("\nPreview:")
    print(result.head(10))


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######
