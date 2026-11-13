#!/usr/bin/env python3
"""
###########
# SAMPLER #
###########
###################################
# Commit-Friendly Dataset Samples #
###################################


Create small, commit-friendly samples of every raw dataset and save them to
data/processed/samples/<same folder as in data/raw/>/<name>_sample.<ext>

One sample = up to SAMPLE_ROWS (100) randomly chosen rows / features of one
raw file. Documentation files (.md / .txt) are copied whole with their
original name.

Source:  data/raw/ (the full, gitignored outputs of the scripts/fetch_*.py scripts)
License: each sample keeps the license of its raw dataset (see that
         dataset's fetch script or documentation).

Example User Usage (from the repository root):
    uv run python scripts/create_dataset_samples.py

The full raw files in data/raw/ are gitignored because they are too
large for GitHub. This script writes a small sample of each one to
data/processed/samples/, mirroring the raw folder layout, so the repo
shows what every dataset looks like without storing the full file.

Rules:
    - CSV      random sample of SAMPLE_ROWS rows (fixed seed)
    - CSV.GZ   same as CSV; the sample is written as a plain .csv
               (al_wac_S000_JT00_2023.csv.gz -> al_wac_S000_JT00_2023_sample.csv)
    - XLSX     one CSV sample per sheet (<file>_<sheet>_sample.csv, or
               <file>_sample.csv when the sheet has the file's name)
    - GeoJSON  random sample of SAMPLE_ROWS features (fixed seed)
    - MD/TXT   copied whole (dataset documentation / table notes)
    - Files (or sheets) with SAMPLE_ROWS rows or fewer are copied whole.
    - A sample that already exists is never overwritten: it is skipped
      with "[SKIP] ... (exists)". To refresh one, delete it by hand first.
    - Folders in EXCLUDED_DIRS (Chicago case study, unused PL blocks) are
      skipped with "[SKIP] ... (excluded)".

Census ACS "-Data.csv" files have a second header row of column
labels. That row is always kept as the first row of the sample.

Every CSV value is read as a string so the sample matches the raw
file exactly (no type inference, no lost leading zeros in GEOIDs).

Excel samples are converted from typed values, because the workbook
stores numbers, not text, so there is no text to copy. Each sheet is
read with its column types, then every column is cast to text. The
values are exact, but whole numbers in decimal columns appear as 0.0
and 1.0, and very small values are written in plain decimal
(0.0000604722885737611, not 6.04722885737611E-5). Reading the sheet
as text instead would round numbers to 9 decimal places. Polars also
leaves out fully blank rows.

Requires:
    polars (and fastexcel, which polars uses to read .xlsx files)

VVV Sources VVV
https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html
https://datatracker.ietf.org/doc/html/rfc7946 (GeoJSON)
https://www.census.gov/programs-surveys/acs/data/data-via-ftp.html (ACS data files)

Imports Used:
from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
import json  # https://docs.python.org/3/library/json.html
import random  # https://docs.python.org/3/library/random.html
import shutil  # https://docs.python.org/3/library/shutil.html
import polars as pl  # https://docs.pola.rs/api/python/stable/reference/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
open() https://docs.python.org/3/library/functions.html#open
sorted() https://docs.python.org/3/library/functions.html#sorted
range() https://docs.python.org/3/library/stdtypes.html#range
str() https://docs.python.org/3/library/stdtypes.html#str
ValueError https://docs.python.org/3/library/exceptions.html#ValueError
OSError https://docs.python.org/3/library/exceptions.html#OSError

Object Methods Used:
pl.read_csv() https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html
pl.read_excel() https://docs.pola.rs/api/python/stable/reference/api/polars.read_excel.html
pl.all() / .cast() https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.cast.html
pl.concat() https://docs.pola.rs/api/python/stable/reference/api/polars.concat.html
.head() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.head.html
.slice() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.slice.html
.with_row_index() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.with_row_index.html
.sample() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sample.html
.sort() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sort.html
.drop() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.drop.html
.write_csv() https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.write_csv.html
.height https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.height.html
pl.exceptions.PolarsError https://docs.pola.rs/api/python/stable/reference/exceptions.html
json.load() https://docs.python.org/3/library/json.html#json.load
json.dump() https://docs.python.org/3/library/json.html#json.dump
random.Random() https://docs.python.org/3/library/random.html#random.Random
.sample() (random) https://docs.python.org/3/library/random.html#random.sample
shutil.copy2() https://docs.python.org/3/library/shutil.html#shutil.copy2
Path() https://docs.python.org/3/library/pathlib.html#pathlib.Path
.resolve() https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
.parent / .parents https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parents
.relative_to() https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.relative_to
.is_relative_to() https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to
.exists() https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists
.stem / .suffix / .name https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.stem
.rglob() https://docs.python.org/3/library/pathlib.html#pathlib.Path.rglob
.is_file() https://docs.python.org/3/library/pathlib.html#pathlib.Path.is_file
.stat() https://docs.python.org/3/library/pathlib.html#pathlib.Path.stat
.mkdir() https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
.unlink(missing_ok=True) https://docs.python.org/3/library/pathlib.html#pathlib.Path.unlink
.endswith() / .startswith() https://docs.python.org/3/library/stdtypes.html#str.endswith
.lower() https://docs.python.org/3/library/stdtypes.html#str.lower
.get() (dict) https://docs.python.org/3/library/stdtypes.html#dict.get
.append() https://docs.python.org/3/tutorial/datastructures.html#more-on-lists

Data Structures / Techniques Used:
set (CSV_SUFFIXES, ...) https://docs.python.org/3/tutorial/datastructures.html#sets
dict (status counts, sheets by name) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
any() https://docs.python.org/3/library/functions.html#any
list comprehension https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
generator expression (sorted(p for p in ...)) https://docs.python.org/3/reference/expressions.html#generator-expressions
functions as values (sampler = sample_csv) https://docs.python.org/3/tutorial/controlflow.html#defining-functions
fixed random seed (reproducible samples) https://docs.python.org/3/library/random.html#notes-on-reproducibility
try / except https://docs.python.org/3/tutorial/errors.html#handling-exceptions
with statement (context managers) https://docs.python.org/3/reference/compound_stmts.html#the-with-statement
conditional expression (X if cond else Y) https://docs.python.org/3/reference/expressions.html#conditional-expressions
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
format spec (:,) https://docs.python.org/3/library/string.html#format-specification-mini-language
type hints (-> bool) https://docs.python.org/3/library/typing.html
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
"""

###########
# IMPORTS #
###########
from pathlib import Path  # https://docs.python.org/3/library/pathlib.html
# Path: a nicer way to work with file and folder paths than plain strings.

import json  # https://docs.python.org/3/library/json.html
# reads and writes GeoJSON files

import random  # https://docs.python.org/3/library/random.html
# picks a random (but repeatable, fixed-seed) set of GeoJSON features

import shutil  # https://docs.python.org/3/library/shutil.html
# shutil.copy2(): copies .md / .txt files whole

import polars as pl  # https://docs.pola.rs/
# fast DataFrame library used to read, sample, and write CSV files


#############
# CONSTANTS #
#############
# <repo>/  (this file lives in <repo>/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Where the full raw datasets live (gitignored)
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Where the small samples are written (committed to the repo)
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samples"

# Rows / features per sample; fixed seed so every run picks the same rows
SAMPLE_ROWS = 100
SEED = 42

# Text files larger than this are skipped instead of copied.
MAX_COPY_BYTES = 1024 * 1024  # 1 MB

# Which file types get sampled and which get copied whole
CSV_SUFFIXES = {".csv"}
GEOJSON_SUFFIXES = {".geojson"}
COPY_SUFFIXES = {".md", ".txt"}
XLSX_SUFFIXES = {".xlsx"}

# Gzipped CSVs (LODES) are sampled like CSVs. Path.suffix only sees the
# last part (".gz"), so this full ending is checked on the file name.
GZIP_CSV_SUFFIX = ".csv.gz"

# Folders under data/raw/ that never get samples. They are compared as
# path prefixes, so a nested folder like census/population/2020_pl_blocks
# works, while census/population/2024/ is still sampled.
EXCLUDED_DIRS = [
    Path("chicago_crime"),  # Chicago case study, not documented in the README
    Path("census") / "population" / "2020_pl_blocks",  # not used by any code
]


###############
# SAMPLE PATH #
###############
def sample_path(raw_path: Path) -> Path:
    """
    Map a raw file to its sample location.

    Example:
        data/raw/flock_osm/flock_us.csv
        -> data/processed/samples/flock_osm/flock_us_sample.csv
    """
    relative = raw_path.relative_to(RAW_DIR)

    if raw_path.name.lower().endswith(GZIP_CSV_SUFFIX):
        # Drop the whole ".csv.gz" ending; the sample is a plain CSV.
        # e.g. al_wac_S000_JT00_2023.csv.gz -> al_wac_S000_JT00_2023_sample.csv
        base = raw_path.name[: -len(GZIP_CSV_SUFFIX)]
        name = f"{base}_sample.csv"
    else:
        name = f"{raw_path.stem}_sample{raw_path.suffix}"

    return OUTPUT_DIR / relative.parent / name


#####################
# SHEET SAMPLE PATH #
#####################
def sheet_sample_path(raw_path: Path, sheet_name: str) -> Path:
    """
    Map one sheet of a raw Excel file to its CSV sample location.

    Example:
        data/raw/census/urban_rural/2020/2020_UA_COUNTY.xlsx, sheet CT_2022
        -> data/processed/samples/census/urban_rural/2020/2020_UA_COUNTY_CT_2022_sample.csv
    """
    relative = raw_path.relative_to(RAW_DIR)

    # A sheet with the same name as the file does not repeat it.
    if sheet_name == raw_path.stem:
        name = f"{raw_path.stem}_sample.csv"
    else:
        name = f"{raw_path.stem}_{sheet_name}_sample.csv"

    return OUTPUT_DIR / relative.parent / name


###############
# IS EXCLUDED #
###############
def is_excluded(relative: Path) -> bool:
    """
    True if a raw file (path relative to data/raw/) is inside one of EXCLUDED_DIRS.
    """
    # is_relative_to() checks for a path prefix, e.g.
    # census/population/2020_pl_blocks/il2020.pl.zip is inside
    # census/population/2020_pl_blocks, but census/population/2024/x.csv is not.
    return any(relative.is_relative_to(folder) for folder in EXCLUDED_DIRS)


#################
# HAS LABEL ROW #
#################
def has_label_row(path: Path) -> bool:
    """
    Census ACS data exports have a second header row of labels.
    """
    return path.name.endswith("-Data.csv")


###############
# SAMPLE ROWS #
###############
def sample_rows(body: pl.DataFrame) -> pl.DataFrame:
    """
    Pick SAMPLE_ROWS random rows (fixed seed), kept in file order.
    Tables with SAMPLE_ROWS rows or fewer are returned whole.
    """
    if body.height <= SAMPLE_ROWS:
        return body

    # Sort by original position so the sample keeps file order.
    return (
        body.with_row_index("_row")
        .sample(n=SAMPLE_ROWS, seed=SEED)
        .sort("_row")
        .drop("_row")
    )


##############
# SAMPLE CSV #
##############
def sample_csv(raw_path: Path, out_path: Path) -> str:
    """
    Write a random row sample of one CSV file (plain or gzipped).
    """
    # infer_schema=False reads every column as a string.
    # read_csv also opens .csv.gz files, decompressing them on the fly.
    df = pl.read_csv(
        raw_path,
        infer_schema=False,
        encoding="utf8-lossy",
    )

    total = df.height

    # Keep the ACS label row on top, then sample the real rows.
    header = df.head(1) if has_label_row(raw_path) else df.head(0)
    body = sample_rows(df.slice(header.height))

    sample = pl.concat([header, body])

    sample.write_csv(out_path)  # save the sample next to its raw-folder twin

    return f"{sample.height:,} of {total:,} rows"


##################
# SAMPLE GEOJSON #
##################
def sample_geojson(raw_path: Path, out_path: Path) -> str:
    """
    Write a random feature sample of one GeoJSON file.
    """
    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total = len(features)

    if total > SAMPLE_ROWS:
        rng = random.Random(SEED)

        # Keep original order of the chosen features.
        # rng.sample() picks SAMPLE_ROWS distinct positions; the list
        # comprehension then keeps the features at those positions.
        keep = sorted(rng.sample(range(total), SAMPLE_ROWS))
        data["features"] = [features[i] for i in keep]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return f"{len(data['features']):,} of {total:,} features"


###############
# SAMPLE XLSX #
###############
def sample_xlsx(raw_path: Path) -> str:
    """
    Write one CSV sample per sheet of an Excel file, skipping sheets
    whose sample already exists. Returns "made" or "exists".
    """
    relative = raw_path.relative_to(RAW_DIR)

    try:
        # sheet_id=0 reads every sheet into a dict {sheet name: DataFrame}.
        # infer_schema_length=None looks at every row to pick column types.
        sheets = pl.read_excel(raw_path, sheet_id=0, infer_schema_length=None)
    except ImportError as e:
        raise ValueError("reading .xlsx needs fastexcel; run uv sync") from e
    except OSError:
        raise  # a missing or unreadable file is reported as it is
    except Exception as e:
        # fastexcel (the Excel reader polars uses) raises its own error
        # types, such as CalamineError for a damaged file, so any read
        # error is turned into one clear ValueError here.
        first_line = str(e).splitlines()[0]
        raise ValueError(f"could not read Excel file: {first_line}") from e

    made = 0
    written = []  # sample files created by this call, removed if a later sheet fails

    try:
        for sheet_name, df in sheets.items():
            out_path = sheet_sample_path(raw_path, sheet_name)

            if out_path.exists():
                print(f"[SKIP] {relative} [{sheet_name}] (exists)")
                continue

            if df.height == 0:
                raise ValueError(f"sheet '{sheet_name}' has no rows")

            # The workbook stores numbers, not text, so each column is
            # cast from its read type to text (see the docstring at the top).
            text = df.with_columns(pl.all().cast(pl.String))
            sample = sample_rows(text)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            written.append(out_path)
            sample.write_csv(out_path)

            print(f"[OK] {relative} [{sheet_name}]: {sample.height:,} of {df.height:,} rows")
            made += 1

    except (pl.exceptions.PolarsError, OSError, ValueError):
        # Remove only the files this call wrote, never an existing sample.
        for path in written:
            path.unlink(missing_ok=True)
        raise

    return "made" if made > 0 else "exists"


#############
# COPY TEXT #
#############
def copy_text(raw_path: Path, out_path: Path) -> str:
    """
    Copy a small documentation file as-is.
    """
    size = raw_path.stat().st_size

    if size > MAX_COPY_BYTES:
        raise ValueError(f"too large to copy ({size:,} bytes)")

    # Text files keep their original name (no _sample suffix).
    shutil.copy2(raw_path, out_path)

    return "copied whole"


#################
# CREATE SAMPLE #
#################
def create_sample(raw_path: Path) -> str:
    """
    Create the sample for one raw file.
    Returns a status word: "made", "exists", "unsupported" or "failed".
    """
    suffix = raw_path.suffix.lower()
    relative = raw_path.relative_to(RAW_DIR)

    # An Excel file gives one sample per sheet, so sample_xlsx() picks
    # its own output paths and checks each one for an existing sample.
    if suffix in XLSX_SUFFIXES:
        try:
            return sample_xlsx(raw_path)

        except (pl.exceptions.PolarsError, OSError, ValueError) as e:
            print(f"[ERROR] {relative}: {e}")
            return "failed"

    # Checked before CSV_SUFFIXES, because the suffix of x.csv.gz is ".gz".
    if raw_path.name.lower().endswith(GZIP_CSV_SUFFIX):
        sampler = sample_csv
        out_path = sample_path(raw_path)
    elif suffix in CSV_SUFFIXES:
        # Store the function itself (no parentheses) and call it later.
        sampler = sample_csv
        out_path = sample_path(raw_path)
    elif suffix in GEOJSON_SUFFIXES:
        sampler = sample_geojson
        out_path = sample_path(raw_path)
    elif suffix in COPY_SUFFIXES:
        sampler = copy_text
        out_path = OUTPUT_DIR / relative
    else:
        print(f"[SKIP] {relative} (unsupported type)")
        return "unsupported"

    # Never overwrite: an existing sample is left exactly as it is.
    if out_path.exists():
        print(f"[SKIP] {relative} (exists)")
        return "exists"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = sampler(raw_path, out_path)

        print(f"[OK] {relative}: {result}")
        return "made"

    except (pl.exceptions.PolarsError, OSError, ValueError) as e:
        print(f"[ERROR] {relative}: {e}")

        # Remove partial output. This is always a file this run started,
        # because existing samples were skipped above.
        out_path.unlink(missing_ok=True)

        return "failed"


##########################
# CREATE DATASET SAMPLES #
##########################
def create_dataset_samples() -> None:
    """
    Create samples for every file under data/raw/.
    """
    # rglob("*") lists everything under data/raw/ (all subfolders);
    # keep real files and skip hidden ones such as .gitkeep.
    raw_files = sorted(
        p for p in RAW_DIR.rglob("*")
        if p.is_file() and not p.name.startswith(".")
    )

    total = len(raw_files)

    # How many raw files ended in each status (an Excel file counts once,
    # however many sheets it has).
    counts = {"made": 0, "exists": 0, "excluded": 0, "unsupported": 0, "failed": 0}
    failed = []

    print(f"Creating samples for {total} raw files...\n")

    for raw_path in raw_files:
        relative = raw_path.relative_to(RAW_DIR)

        if is_excluded(relative):
            print(f"[SKIP] {relative} (excluded)")
            status = "excluded"
        else:
            status = create_sample(raw_path)

        counts[status] += 1

        if status == "failed":
            failed.append(str(relative))

    print(
        f"\nRaw files: {total} | Made: {counts['made']} | "
        f"Already existed: {counts['exists']} | Excluded: {counts['excluded']} | "
        f"Unsupported: {counts['unsupported']} | Failed: {counts['failed']}"
    )
    print(f"Samples saved to: {OUTPUT_DIR}")

    if failed:
        print(f"Failed: {failed}")
    else:
        print("No samples failed.")


########
# MAIN #
########
def main() -> None:
    """Create a sample of every raw dataset."""
    create_dataset_samples()


###############
# ENTRY POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######
