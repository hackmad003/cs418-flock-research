"""
Flock ALPR cameras in OpenStreetMap: current state + historical dates.

WHAT THE DATE COLUMNS MEAN (and do NOT mean)
  first_insert_date  When the OSM node was originally created.
  first_tagged_date  When an OSM version first identified the node as a
                     Flock ALPR camera (can be later than first_insert_date).
  last_edit          When the node was most recently edited in OSM.

None of these is the date a physical camera was installed. A camera
installed in 2022 may only have been mapped in 2025. A camera that was
deleted and re-added as a new node also gets a new date. Analyses built
on these columns describe growth in MAPPED cameras, not deployment.
"""

import io
import json
import os
import time
from pathlib import Path

import requests
import polars as pl


# ============================================================
# 1. CONFIGURATION
# ============================================================

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_API = "https://api.openstreetmap.org/api/0.6"

# Replace with your real contact email or set OSM_CONTACT.
CONTACT = os.environ.get("OSM_CONTACT", "hackmad003@gmail.com")

USER_AGENT = f"FlockOSMResearch/1.0 (contact: {CONTACT})"

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

AREAS = {
    "us": 'area["ISO3166-1"="US"]->.scope;',
    "chicago": (
        'area["name"="Chicago"]'
        '["boundary"="administrative"]'
        '["admin_level"="8"]->.scope;'
    ),
}

if SCOPE not in AREAS:
    raise SystemExit(f"SCOPE must be one of {list(AREAS)}")


# ============================================================
# 2. PROJECT DIRECTORIES
# ============================================================

def find_repo_root():
    try:
        here = Path(__file__).resolve().parent
    except NameError:
        here = Path.cwd().resolve()

    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p

    return here


REPO_ROOT = find_repo_root()

RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RUN_SUFFIX = "_sample" if SAMPLE_SIZE is not None else ""

CURRENT_FILE = RAW_DIR / f"flock_{SCOPE}_current.csv"

# A fresh download that fails the count check is saved here so you
# can inspect it without downloading again. It is never reused.
UNVERIFIED_FILE = RAW_DIR / f"flock_{SCOPE}_current_UNVERIFIED.csv"

CHECKPOINT_FILE = RAW_DIR / (
    f"flock_{SCOPE}_history_checkpoint{RUN_SUFFIX}.jsonl"
)

# Lists every edited node that still has no history result.
FAILURES_FILE = RAW_DIR / (
    f"flock_{SCOPE}_history_unresolved{RUN_SUFFIX}.csv"
)

OUTPUT_FILE = PROCESSED_DIR / (
    f"flock_{SCOPE}_historical{RUN_SUFFIX}.csv"
)

# Written instead of OUTPUT_FILE whenever some history is missing,
# so an unfinished dataset can't be mistaken for a finished one.
INCOMPLETE_FILE = PROCESSED_DIR / (
    f"flock_{SCOPE}_historical{RUN_SUFFIX}_INCOMPLETE.csv"
)

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
})


# ============================================================
# 3. OVERPASS QUERY
# ============================================================

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


# ============================================================
# 4. DOWNLOAD + VALIDATE CURRENT CAMERAS
# ============================================================

def validate_snapshot(df, check_count):
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


def download_current_cameras():

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

        response.raise_for_status()

        df = pl.read_csv(
            io.StringIO(response.text),
            separator="\t",
            quote_char=None,
            infer_schema_length=0
        )

        # Remove Overpass metadata prefixes.
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


# ============================================================
# 5. IDENTIFY FLOCK ALPR TAGS
# ============================================================

def is_flock_alpr(tags):

    return (
        tags.get("man_made") == "surveillance"
        and tags.get(
            "surveillance:type", ""
        ).casefold() == "alpr"
        and "flock" in tags.get(
            "manufacturer", ""
        ).casefold()
    )


# ============================================================
# 6. OSM HISTORY API
# ============================================================

class NonRetryableError(Exception):
    pass


class RateLimitError(Exception):
    """429/509 persisted through every retry: stop the whole run."""


def retry_delay(response, attempt):

    try:
        delay = float(
            response.headers.get("Retry-After")
        )
    except (TypeError, ValueError):
        delay = 2 ** attempt + 2

    return max(1, min(delay, 120))


def get_node_history(node_id):

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

        return sorted(
            versions,
            key=lambda v: v["version"]
        )

    raise RuntimeError(
        f"Node {node_id}: failed after "
        f"{MAX_RETRIES} attempts: {last_error}"
    )


# ============================================================
# 7. EXTRACT HISTORICAL DATES
# ============================================================

def extract_history(node_id):

    history = get_node_history(node_id)

    if not history:
        raise ValueError(
            f"Node {node_id}: empty history"
        )

    # Original OSM object creation.
    first_version = history[0]

    # First historical version matching Flock ALPR tags.
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


# ============================================================
# 8. CHECKPOINT RECOVERY
# Only nodes that needed an API history call are saved here.
# Version-1 nodes are derived from the snapshot for free, so
# skipping them avoids ~100k slow disk flushes.
# ============================================================

def load_checkpoint():

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


def append_checkpoint(node_id, result):

    record = json.dumps({
        "id": node_id,
        **result
    }) + "\n"

    # Append a complete JSONL record.
    with CHECKPOINT_FILE.open("a", encoding="utf-8") as f:
        f.write(record)
        f.flush()
        os.fsync(f.fileno())


# ============================================================
# 9. PROCESS CAMERA HISTORIES
# ============================================================

def process_cameras(df):
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


# ============================================================
# 10. COMPLETENESS REPORT
# ============================================================

def report_completeness(df, results, errors):
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


# ============================================================
# 11. EXPORT HISTORICAL DATASET
# ============================================================

def build_final_dataset(df, results, complete):

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


# ============================================================
# 12. MAIN
# ============================================================

def main():

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


if __name__ == "__main__":
    main()