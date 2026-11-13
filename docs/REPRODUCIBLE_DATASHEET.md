# Reproducible Datasheet

How Claude builds a `DATASHEET.md` that meets **Checkpoint Four: Data Documentation**.
Two goals: **every rubric item is answered** and **it is easy to read**. The steps below
match the six rubric items one to one, plus a summary card at the top.

The reader is a CS 418 student in 3026 who found this repo and wants to know whether
they can trust and reuse the data. Write for them: plain words, no assumed context.

## How to invoke
Datasheet for one dataset:
> Follow `docs/REPRODUCIBLE_DATASHEET.md`. Build a datasheet for
> `<dataset path or name>`.

Unified checkpoint datasheet:
> Follow `docs/REPRODUCIBLE_DATASHEET.md` in **unified mode**. Cover every primary
> dataset, plus the secondary datasets used in joins.

## Before writing anything
1. Read this file and `docs/CODING_STYLE.md`. Skim `docs/BUGS.md` for known traps.
2. Read the research questions in `README.md`, or use the ones I give you.
3. If the assignment spec is reachable (see Assignment specs in `CLAUDE.md`), read the
   Checkpoint Four spec and check this file against it. Don't copy it into the repo.
4. Open the dataset and the code that produces it: the fetch script in `scripts/`,
   the loader in `src/cs418_flock_research/loaders/`, and any join code.
5. Find the **publisher's own documentation** (WebSearch / WebFetch). Cite it and
   quote short phrases. Never write a publisher claim from memory.
6. If the dataset, a link, or a date is unclear, ask me. Don't guess.
7. If a teammate's `DATASHEET.md` exists in the repo, use it for tone and layout only.
   Do not copy its gaps (see "Gaps to avoid").

## Output
- **One dataset:** `docs/datasheets/DATASHEET_<dataset_name>.md`.
- **Unified mode:** `checkpoints/Data_Documentation/DATASHEET.md`, covering every primary
  dataset. Also draft the README section (below).
- If `docs/CODING_STYLE.md` puts these files somewhere else, follow it and tell me.
- Never overwrite an existing file. If the name exists, add a suffix.
- Do not edit `README.md`. Put the draft "Data documentation" section in your final message.

### Statistics script
Every number in the datasheet must come from code. Put the code in
`scripts/datasheet_stats_<dataset_name>.py`. It reads the raw file, prints every count,
range, and join result the datasheet uses, and writes nothing into `data/raw/`.
- It follows `docs/CODING_STYLE.md` in full: file order, a banner per function, Polars
  and GeoPandas, `pathlib` paths built from the project root, comments that explain why.
- The datasheet links to it and says how to run it (`uv run python scripts/<name>.py`).
- Run it before you write the numbers into the datasheet.

### Tags on every answer
End each answer with one tag, so the reader sees where it came from:
- `[publisher]` from the publisher's documentation, with a link.
- `[code]` computed by the statistics script or another script in the repo.
- `[our note]` something our group did or decided.
- `[not documented by the publisher]` the publisher doesn't say. Write exactly this.
A line with no tag is a mistake.

## Milestones
Make the summary card and each step a `##` heading, in this order.

### Summary card (top of the file)
A short "nutrition label" so a skimming reader gets the picture in 30 seconds. One table
per primary dataset with these rows:

| Item | Value |
|---|---|
| What one row is | |
| Rows × columns | |
| Time span | |
| Source and maintainer | |
| License | |
| Snapshot date (from the file, not only its name) | |
| Safe for | |
| Not safe for | |
| Biggest limitation | one or two sentences |

Under the table, link to the statistics script and to the six sections below.

### Step 1: Datasheet (seven sections)
For each **primary** dataset, answer these seven sections. Skip a question only if it
truly doesn't apply, and say so in one line.
1. **Motivation:** why it was created, by whom, funded by whom.
2. **Composition:** what one row is, how many rows, every possible instance or a sample,
   what is missing and why. Count placeholders that hide missing data, not only nulls.
3. **Collection process:** how it was gathered, over what time frame, whether people
   knew or consented.
4. **Preprocessing:** cleaning or labeling the publisher did, and whether raw data exists.
5. **Uses:** what it has been used for, and what it should **not** be used for.
6. **Distribution:** how it is published and under what license or terms.
7. **Maintenance:** who maintains it, whether it is updated, how we would know.

Check what the file actually says against its name. For example, compare the date in the
file name with the newest timestamp inside the file, and state any difference.

### Step 2: Scope
For **each research question**, give a short block:
- **Target population:** who or what the question is about.
- **Access frame:** what could in principle be reached (the source and its coverage).
- **Sample:** the rows we actually analyze, with counts `[code]`.
- **Who or what is missing:** and what that stops us from claiming.

Use these definitions in one line each at the top of the step: target population (everyone
the question is about), access frame (the list or source we can draw from), sample (what
we got). Keep the claims modest: say "mapped", not "installed", where that applies.

### Step 3: Codebook
One table row for **every column used in the analysis, including columns we created**:

| Column | Type | Units | Meaning | Range or allowed values | Missing coding | Origin |
|---|---|---|---|---|---|---|

- **Profile real values.** Run code for the min and max, number of unique values, the
  category list, and the count of nulls **and** placeholders (`""`, `-999`, `0`, `9999`).
  Don't write "not profiled" for anything the script can compute.
- **Derived columns:** the formula and a pointer to the code (file and function name).
- Group columns by dataset. Keep each table readable: short meanings, long lists in a
  note under the table.

### Step 4: Recipe
A numbered list of **every step from raw files to the analysis dataframe**, in order:
downloads, filters, type fixes, dropped rows, joins. For each step:
- what it does, in one sentence,
- the code that does it (file path and function name, with a command to run it),
- row counts before and after `[code]`.

For **every join**, add a row to this table, with all numbers printed by code:

| Join | Key | Left rows | Right rows | Matched | Unmatched (left) | Unmatched (right) | Why unmatched |
|---|---|---|---|---|---|---|---|

Rules:
- Say which steps are slow (for example, the history fetch takes hours) and where the
  frozen snapshot lives, so a stranger can skip the download.
- Say what is **not** reproducible (a live query that changes over time) and what we kept
  instead (the dated raw file).
- Finish with the exact commands, in order, that rebuild the analysis dataframe from
  `data/raw/` on a clean checkout. Run them if you can.

### Step 4b: Access and reuse (FAIR)
One table row per dataset, including secondary datasets:

| Dataset | Persistent link | Version or access date | Format | License or terms | May others reuse our processed data? |
|---|---|---|---|---|---|

- Look up each license on the publisher's page. **Never guess a license.** If there is no
  stated license, write `[not documented by the publisher]` and link the terms page.
- For share-alike or attribution licenses, say what our processed data must carry.
- Under the table, one line each for **Findable, Accessible, Interoperable, Reusable**:
  what we did and what is still missing.

### Step 5: People in the data
Answer even when the data is mostly about things, not people:
- **Who is in the data, directly or indirectly?** Name any personal fields (for example
  mapper usernames, or people whose vehicles pass a camera).
- **Representation:** which groups could be over- or under-represented, and why
  (for example, volunteer mapping effort, or how Census categories are defined).
- **Who could be mis-represented or harmed** by conclusions drawn from the data?
- **CARE lens:** one or two sentences each on collective benefit, authority to control,
  responsibility, and ethics, kept honest and specific to this data.
- State facts, not accusations. Don't call a place or a group "inherently" anything.

## Writing rules
- Short sentences and plain words. Explain a term the first time you use it.
- One fact per bullet. Use tables for repeated structure (codebook, joins, access).
- Column names and file names in backticks. Numbers have the same format everywhere.
- Every number comes from code. Never type a number by hand, and never copy one from an
  LLM answer or an earlier chat.
- Quote a publisher in a few words only, always with a link. Otherwise paraphrase.
- If you don't know, say so with a tag. A visible gap is better than a guess.

## Gaps to avoid
- Writing "not profiled" or "calculate with the code below" instead of running the code.
- Leaving access dates, export queries, or download URLs blank when the file or script
  records them. Record what the script fetched, the date, and the cut-off time.
- Paths written as `../data/raw/...`. Use project-root paths.
- Calling a file complete when it's a partial year or a snapshot.
- A join described without matched and unmatched counts on both sides.
- Reporting a snapshot date from the file name alone.

## Code in the datasheet
- Keep snippets short and runnable from the project root, following
  `docs/CODING_STYLE.md` (Polars, `pathlib`, descriptive names, no `../`).
- Link to the full script instead of pasting it.

## Before you finish
- Run the statistics script top to bottom and check each number in the datasheet against
  its output.
- Check each link opens, and each code pointer names a file and function that exist.
- Check the six rubric items below are all answered.
- Don't commit anything. Every group member needs at least one commit for this
  checkpoint, so I'll commit myself.

## Final message to me
Keep it short:
- File paths (datasheet and statistics script).
- A checklist of the six rubric items (datasheets, scope, codebook, recipe, access and
  reuse, people): covered or not, with the reason if not.
- The draft README "Data documentation" section: a link to `DATASHEET.md`, each dataset
  with its source and license, and the biggest limitation in one or two sentences.
- Anything you couldn't verify, and any publisher page you couldn't open.

## Rubric (what each step must satisfy)
1. **Datasheets:** each primary dataset has all seven sections, answers cited to the
   publisher, gaps marked `[not documented by the publisher]`.
2. **Scope:** each research question has target population, access frame, and sample,
   plus who or what is missing and what that limits.
3. **Codebook:** every column used, including derived ones, has type, units, meaning,
   range or allowed values, missing coding, and origin.
4. **Recipe:** steps in order, each linked to code, with the key and the matched and
   unmatched counts for every join.
5. **Access and reuse:** each dataset has a persistent link, access date or version,
   format, license, and a statement on reusing our processed data.
6. **People in the data:** how people are represented, which groups could be
   (mis)represented, or, if no people, who may be affected by decisions made with the data.