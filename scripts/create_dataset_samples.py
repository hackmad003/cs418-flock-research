
##########
# SAMPLER #
##########
"""
Create small, commit-friendly samples of every raw dataset.

The full raw files in data/raw/ are gitignored because they are too
large for GitHub. This script writes a small sample of each one to
data/processed/samples/, mirroring the raw folder layout, so the repo
shows what every dataset looks like without storing the full file.

Rules:
    - CSV      random sample of SAMPLE_ROWS rows (fixed seed)
    - GeoJSON  random sample of SAMPLE_ROWS features (fixed seed)
    - MD/TXT   copied whole (dataset documentation / table notes)
    - Files with SAMPLE_ROWS rows or fewer are copied whole.

Census ACS "-Data.csv" files have a second header row of column
labels. That row is always kept as the first row of the sample.

Every value is read as a string so the sample matches the raw
file exactly (no type inference, no lost leading zeros in GEOIDs).

Example:
    uv run python scripts/create_dataset_samples.py

Requires:
    polars
"""

###########
# IMPORTS #
###########
from pathlib import Path
import json
import random
import shutil

import polars as pl


#############
# CONSTANTS #
#############
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samples"

SAMPLE_ROWS = 100
SEED = 42

# Text files larger than this are skipped instead of copied.
MAX_COPY_BYTES = 1024 * 1024  # 1 MB

CSV_SUFFIXES = {".csv"}
GEOJSON_SUFFIXES = {".geojson"}
COPY_SUFFIXES = {".md", ".txt"}


###########
# HELPERS #
###########
def sample_path(raw_path: Path) -> Path:
    """
    Map a raw file to its sample location.

    Example:
        data/raw/flock_osm/flock_us.csv
        -> data/processed/samples/flock_osm/flock_us_sample.csv
    """
    relative = raw_path.relative_to(RAW_DIR)

    name = f"{raw_path.stem}_sample{raw_path.suffix}"

    return OUTPUT_DIR / relative.parent / name


def has_label_row(path: Path) -> bool:
    """
    Census ACS data exports have a second header row of labels.
    """
    return path.name.endswith("-Data.csv")


###########
# SAMPLERS #
###########
def sample_csv(raw_path: Path, out_path: Path) -> str:
    """
    Write a random row sample of one CSV file.
    """
    # infer_schema=False reads every column as a string.
    df = pl.read_csv(
        raw_path,
        infer_schema=False,
        encoding="utf8-lossy",
    )

    total = df.height

    # Keep the ACS label row on top, then sample the real rows.
    header = df.head(1) if has_label_row(raw_path) else df.head(0)
    body = df.slice(header.height)

    if body.height > SAMPLE_ROWS:
        # Sort by original position so the sample keeps file order.
        body = (
            body.with_row_index("_row")
            .sample(n=SAMPLE_ROWS, seed=SEED)
            .sort("_row")
            .drop("_row")
        )

    sample = pl.concat([header, body])

    sample.write_csv(out_path)

    return f"{sample.height:,} of {total:,} rows"


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
        keep = sorted(rng.sample(range(total), SAMPLE_ROWS))
        data["features"] = [features[i] for i in keep]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return f"{len(data['features']):,} of {total:,} features"


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


###########
# CREATOR #
###########
def create_sample(raw_path: Path) -> bool:
    """
    Create the sample for one raw file.
    Returns False if the file failed or was skipped.
    """
    suffix = raw_path.suffix.lower()
    relative = raw_path.relative_to(RAW_DIR)

    if suffix in CSV_SUFFIXES:
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
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = sampler(raw_path, out_path)

        print(f"[OK] {relative}: {result}")
        return True

    except (pl.exceptions.PolarsError, OSError, ValueError) as e:
        print(f"[ERROR] {relative}: {e}")

        # Remove partial output.
        out_path.unlink(missing_ok=True)

        return False


def create_dataset_samples() -> None:
    """
    Create samples for every file under data/raw/.
    """
    raw_files = sorted(
        p for p in RAW_DIR.rglob("*")
        if p.is_file() and not p.name.startswith(".")
    )

    total = len(raw_files)
    completed = 0
    failed = []

    print(f"Creating samples for {total} raw files...\n")

    for raw_path in raw_files:
        success = create_sample(raw_path)

        if success:
            completed += 1
        else:
            failed.append(str(raw_path.relative_to(RAW_DIR)))

    print(f"\nCompleted: {completed}/{total}")
    print(f"Samples saved to: {OUTPUT_DIR}")

    if failed:
        print(f"Skipped or failed: {failed}")
    else:
        print("All dataset samples created successfully!")


########
# MAIN #
########
if __name__ == "__main__":
    create_dataset_samples()


#######
# EOF #
#######
