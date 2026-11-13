# BUG.md: Data Science Pitfalls Audit (General)

> **For Claude:** Audit this project against the checklist below. Do not fix
> anything yet. Skip items that don't apply (for example, train/test splits in a
> purely descriptive analysis) and say they were skipped. For each applicable
> item, inspect the code and data, then report OK / PROBLEM / CAN'T TELL with
> the file, line, or numbers that support your answer. Do not guess. Finish with
> a ranked list of problems, most damaging to the conclusions first. Log
> confirmed problems in "Known Issues" at the bottom.

## 1. Loading and types
- [ ] Column types are correct (IDs and codes stored as strings, dates parsed as dates, numbers not read as text).
- [ ] Leading zeros are preserved in codes (ZIP, FIPS, IDs).
- [ ] Encoding, delimiter, and header issues checked on every raw file.
- [ ] Units are consistent and labeled (dollars vs. thousands, meters vs. feet, percent vs. fraction).
- [ ] Time zones and date formats are consistent.

## 2. Missing, sentinel, and duplicate data
- [ ] Missing values counted per column, and the handling is deliberate (drop, impute, flag).
- [ ] Placeholder values (`-999`, `0`, `""`, `"N/A"`, `9999`) are not treated as real data.
- [ ] Duplicate rows and duplicate IDs checked.
- [ ] Missingness checked for patterns (is it random, or tied to a group or time?).

## 3. Joins and merges
- [ ] Join keys have matching types and formatting (case, whitespace, padding).
- [ ] Row counts checked before and after every join.
- [ ] The join relationship is as intended (one-to-one or many-to-one, never accidental many-to-many).
- [ ] Unmatched keys are listed and explained.
- [ ] Inner joins are not silently dropping meaningful rows, including legitimate zeros.

## 4. Data quality and measurement
- [ ] You know what the data actually measures (a proxy, a sample, a self-report, a snapshot).
- [ ] Sampling bias and coverage gaps are identified and stated.
- [ ] Outliers inspected, not silently dropped or kept.
- [ ] The time period of each dataset is known, and sources being combined actually overlap in time.
- [ ] Numbers that should agree across files are reconciled.

## 5. Exploratory analysis
- [ ] Distributions plotted before choosing a method (skew, heavy tails, zeros, ceilings).
- [ ] Sanity checks against known facts (totals, ranges, a few rows checked by hand).
- [ ] Correlation checked between predictors.
- [ ] Simpson's paradox considered: does a pattern reverse within subgroups?

## 6. Splits and leakage (if predicting)
- [ ] Data is split before any fitting, scaling, imputing, or feature selection.
- [ ] No information from the target or from the future leaks into features.
- [ ] Time-ordered data uses time-based splits, not random ones.
- [ ] Related rows (same person, place, or group) are not split across train and test.
- [ ] Test data is touched once, not used for repeated tuning.

## 7. Modeling and statistics
- [ ] The model type fits the outcome (counts, binary, continuous, ordered).
- [ ] Model assumptions checked (overdispersion, residual patterns, independence).
- [ ] A simple baseline is included for comparison.
- [ ] Collinearity checked and reported.
- [ ] Results tested against alternative specifications, and the spread is reported.
- [ ] Uncertainty reported (confidence intervals), not just point estimates.
- [ ] Multiple comparisons and cherry-picked specifications acknowledged.
- [ ] Metrics fit the problem (accuracy misleads on imbalanced classes).

## 8. Interpretation
- [ ] Association is not described as cause, and wording does not imply intent.
- [ ] Ecological fallacy avoided: group-level results are not stated as facts about individuals.
- [ ] Practical significance, not just statistical significance, is discussed.
- [ ] Claims stay within what the data covers (population, time, place).
- [ ] Limitations are stated plainly, near the findings, not buried.

## 9. Visualization
- [ ] Axes labeled with units, and scales are honest (no misleading truncated axes).
- [ ] Color choices work for color-blind readers and print.
- [ ] Each figure supports one clear point and has a caption.
- [ ] Sample size or uncertainty is visible where it matters.

## 10. Reproducibility
- [ ] The notebook runs top to bottom on a clean environment from the documented install step.
- [ ] Paths are relative to the project root, with no personal absolute paths.
- [ ] Random seeds are set wherever randomness is used.
- [ ] Every reported number and figure is produced by code, not typed or exported by hand.
- [ ] Data sources have a URL and download date recorded.
- [ ] Raw data is never edited in place.
- [ ] Dependencies are pinned.

## 11. Repo hygiene
- [ ] No large data files or secrets committed (check `.gitignore` and `git status`).
- [ ] Old notebooks are fixed or clearly marked archived.
- [ ] README and data documentation match the current files.
- [ ] No dead code, unused imports, or duplicated helpers.

## 12. Ethics and privacy
- [ ] No personal or identifying information is exposed in data, figures, or commits.
- [ ] Data licenses and terms of use are respected and cited.
- [ ] Potential harm from misreading the results is considered, and wording is careful.

## Known Issues
Format: `BUG-###: title`, then Status, Where, Symptom, Reproduce, Expected vs. Actual, Suspected cause, Next step.

Scope of this first batch: the scripts in `scripts/` only (logged 2026-11-12,
from a read-through against `docs/CODING_STYLE.md`). The full checklist above
has not been audited yet.

### BUG-001: Personal email address hardcoded and pushed
- **Status:** Open (high, privacy / checklist 11 and 12)
- **Where:** `scripts/fetch_osm_flock_history.py`, `CONTACT = os.environ.get("OSM_CONTACT", ...)` (about line 472)
- **Symptom:** The fallback value for `OSM_CONTACT` is a real personal email address. It is in commit `10a4532`, which is on `origin/team-M6`.
- **Reproduce:** `git show 10a4532:scripts/fetch_osm_flock_history.py` and search for `OSM_CONTACT`.
- **Expected vs. Actual:** Expected: the contact comes only from the `OSM_CONTACT` environment variable, or a placeholder. Actual: a personal address ships with the code.
- **Suspected cause:** Default filled in for convenience during testing.
- **Next step:** Replace the default with a placeholder such as `you@example.org` (`main()` already refuses to run when the contact contains `example.com`). Decide whether the pushed history needs rewriting.

### BUG-002: Atlas download overwrites a same-day snapshot
- **Status:** Open (medium, CODING_STYLE §7)
- **Where:** `scripts/fetch_atlas_of_surveillance.py`, `out_path.write_bytes(resp.content)` (about line 128)
- **Symptom:** Running the script twice on the same day silently replaces that day's CSV. `--out` pointing at an existing file is overwritten too.
- **Reproduce:** Run `uv run python scripts/fetch_atlas_of_surveillance.py` twice on one day.
- **Expected vs. Actual:** Expected: refuse with a clear message, as `fetch_osm_alpr_cameras.py` does. Actual: the file is replaced.
- **Suspected cause:** No `out_path.exists()` check before writing.
- **Next step:** Add the same `FileExistsError` check used in `fetch_osm_alpr_cameras.py`.

### BUG-003: History script overwrites its output files
- **Status:** Open (medium, CODING_STYLE §7)
- **Where:** `scripts/fetch_osm_flock_history.py`: `result.write_csv(out_path)` (about line 1234), `df.write_csv(UNVERIFIED_FILE)` (about line 664), `.write_csv(FAILURES_FILE)` (about line 1146)
- **Symptom:** A second run on the same UTC day replaces `flock_<scope>_historical_<date>.csv` (or `_INCOMPLETE.csv`). The `_UNVERIFIED` and `_unresolved` files are also rewritten every time.
- **Reproduce:** Finish one run, then run again the same day.
- **Expected vs. Actual:** Expected: earlier finished outputs are kept. Actual: they are replaced without warning.
- **Suspected cause:** Intentional for resuming (the INCOMPLETE file must be refreshed), but the final COMPLETE file is not protected.
- **Next step:** Refuse to overwrite an existing COMPLETE output. Keep refreshing INCOMPLETE/unresolved, and document that.

### BUG-004: `manufacturer` differs between CSV and GeoJSON output
- **Status:** Open (medium, checklist 4: numbers that should agree across files)
- **Where:** `scripts/fetch_osm_alpr_cameras.py`, `to_geojson()` (`tags.get("manufacturer") or tags.get("brand")`, about line 899) vs. `to_csv()` (`tags.get("manufacturer")`, about line 990)
- **Symptom:** For a node with `brand` but no `manufacturer`, the GeoJSON `manufacturer` holds the brand while the CSV `manufacturer` is empty. The CSV also has a separate `brand` column that GeoJSON lacks.
- **Reproduce:** Export the same scope with `--format csv` and `--format geojson` and compare `manufacturer` for nodes tagged with `brand` only.
- **Expected vs. Actual:** Expected: the same field means the same thing in both formats. Actual: it depends on the format.
- **Suspected cause:** The two converters were written separately.
- **Next step:** Use the same rule in both, and add `brand` to the GeoJSON properties. Note: `--flock-only` requires `manufacturer~Flock`, so Flock-only exports are less affected.

### BUG-005: Script falls back to the terminal's current directory
- **Status:** Open (low, CODING_STYLE §7)
- **Where:** `scripts/fetch_osm_flock_history.py`, `find_repo_root()` (`except NameError: here = Path.cwd()`, about line 528). `RAW_DIR.mkdir(...)` also runs at import time (about line 551).
- **Symptom:** When `__file__` is undefined (pasted into a notebook or REPL) the data folder is resolved from wherever the terminal is. Importing the module also creates folders.
- **Reproduce:** Paste the file into a notebook started outside the repo.
- **Expected vs. Actual:** Expected: paths are anchored to the project root, like the other scripts (`Path(__file__).resolve().parents[1]`). Actual: they can depend on the working directory.
- **Suspected cause:** Written to also work inside notebooks.
- **Next step:** Use `Path(__file__).resolve().parents[1]` like the other scripts, and move `mkdir` into `main()`.

### BUG-006: Dead code in the scripts
- **Status:** Open (low, checklist 11)
- **Where:**
  - `scripts/fetch_osm_alpr_cameras.py`, `run_query()`: `if response.status_code in RETRY_STATUSES: response.raise_for_status()` is immediately followed by an unconditional `response.raise_for_status()` (about lines 785-787), so the `if` does nothing extra.
  - `scripts/fetch_osm_flock_history.py`, `main()`: `stop_reason` from `process_cameras()` is never used (Pylance warning, about line 1322).
- **Symptom:** No wrong output. Misleading to readers.
- **Next step:** Remove the redundant `if`, and either print `stop_reason` in `main()` or stop returning it.

### BUG-007: Snapshot dates use local time in one script, UTC in the others
- **Status:** Open (low, checklist 1: time zones consistent)
- **Where:** `scripts/fetch_atlas_of_surveillance.py` uses `date.today()` (local, about line 116). `fetch_osm_alpr_cameras.py` and `fetch_osm_flock_history.py` use `datetime.now(timezone.utc)`.
- **Symptom:** Run near midnight (Chicago is UTC-6/-5), files downloaded in the same session can carry different dates.
- **Next step:** Use the UTC date in all fetch scripts, and update the atlas docstring ("local download date").

### BUG-008: Census script filename says "track" instead of "tract"
- **Status:** Open (low, naming)
- **Where:** `scripts/fetch_census_track_boundaries.py`
- **Symptom:** The file downloads census *tract* boundaries. The misspelling makes it harder to find and is repeated in its usage line.
- **Next step:** Rename to `fetch_census_tract_boundaries.py` and update references (README, docs, its own docstring).

Not logged (need checking before they count as confirmed):
- `--state` in `fetch_osm_alpr_cameras.py` matches any `admin_level=4` area with that name, not only U.S. states. Whether a non-U.S. area with a U.S. state's name exists has not been checked.
- `fetch_osm_flock_history.py` downloads from a single Overpass endpoint with no retry, unlike `fetch_osm_alpr_cameras.py`. This is a reliability limitation, not a wrong result.