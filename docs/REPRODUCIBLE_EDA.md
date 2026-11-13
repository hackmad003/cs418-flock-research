# Reproducible EDA

How Claude builds an EDA notebook that meets **Checkpoint Three: Exploratory
Analysis**. Two goals: **easy to read** and **one observation per cell**. The
six steps below match the six rubric items one to one.

## How to invoke
Personal notebook for one dataset:
> Follow `docs/REPRODUCIBLE_EDA.md`. Build an EDA notebook for
> `<dataset path or name>`.

Unified checkpoint notebook:
> Follow `docs/REPRODUCIBLE_EDA.md` in **unified mode**. Cover every primary
> dataset, plus the join with the secondary dataset.

## Before writing anything
1. Read this file and `docs/CODING_STYLE.md`. Skim `docs/BUGS.md` for the
   usual traps (joins, types, missing values, placeholder values).
2. Read the project's research questions in `README.md`, or use the ones I give you.
3. Open the dataset: columns, types, row count. Use a loader from
   `src/cs418_flock_research/loaders/` if one exists.
4. If the dataset or a step is unclear, ask me. Don't guess.
5. Use `checkpoints/Exploratory_Analysis/EDA_AA.ipynb` as a model for
   **structure and tone only**. Its paths and imports are out of date, and its
   long notes should be split up (see Cell rules).

## Output
- **Personal notebook:** `notebooks/eda_<dataset_name>.ipynb`.
- **Unified mode:** `checkpoints/Exploratory_Analysis/eda.ipynb`, covering every
  primary dataset. Also write `checkpoints/Exploratory_Analysis/EDA.md` (below).
- Never overwrite an existing file. If the name exists, add a suffix.
- Each notebook must run top to bottom in the project environment and produce
  every table and plot, with code, outputs, and notes together.

### `EDA.md` (unified mode only)
Summarize all six steps: a profile of each primary dataset, the anomalies and
what was done, the key distribution shapes, the relationships plotted, and the
"so what?" and "what next?" for each. Name the notebook plot each point comes
from. Every number must match a notebook output.

### README section (unified mode only)
Don't edit `README.md`. Put a draft "Exploratory analysis" section in your final
message: basics about the datasets, the revised research questions, the anomaly
table, and the most significant findings.

## Milestones
Make each step a `##` heading cell, in this order.

### Step 1: Dataset profile
Give each **primary** dataset its own section. Profile secondary datasets only
if a plot uses them. For each one, run these and write what stands out:
1. `df.shape`: rows and columns.
2. Duplicates: compare the shape with the unique-rows shape.
3. `df.glimpse()` or `df.schema`: do the types make sense? Codes and IDs should
   be text, dates should be dates.
4. `df.head()`: a quick look at real values.
5. `df.null_count()`: count nulls per column. Also count placeholders that hide
   missing data (`""`, `-999`, `0`, `9999`).
6. `df.describe()`: look for caps and ceilings, odd zeros, and extreme values.
7. Categories: counts for the 2-3 most important text columns.
8. Time: if there's a date column, count rows per year. Say whether the date is
   when a record was created or last edited.
9. Geography: if there's a map column, check the coordinate system, invalid
   shapes, and whether the points land where they should.
10. Raw vs. loaded: if both exist, compare them and say what the loader changes.

### Step 2: Anomalies
Look for **missing values, duplicates, inconsistent formatting, wrong data
types, invalid values, and mixed units**. Put every one in a single table:

| Dataset | Anomaly | Rows affected | What I did |
|---|---|---|---|

"What I did" is one of: **Fixed**, **Dropped the rows**, or **Left and flagged**.
Every number in the table must appear in an earlier output.

### Step 3: Distributions
Make **at least one plot for every feature that matters to the research
questions**. Use a bar chart for categories and a histogram or box plot for
numbers. Describe the shape in short cells: one for **center and spread**, one
for **skew and outliers**.

### Step 4: Relationships
Make **at least three plots** that relate two or more features, chosen with the
research questions in mind: a scatter plot, a comparison across subgroups, a
time series, or a correlation matrix. If there is a secondary dataset, **at least
one plot must use the join or comparison** described in the data acquisition
checkpoint. Compare groups on a fair basis, such as rates per area or per
person, not raw counts.

Useful prompts: How is X distributed? How do X and Y relate? Is X the same across
subgroups of Z? Is anything unusual in X, in (X, Y), or in X within a subgroup?

### Step 5: So what?
Every relationship plot gets a **So what?** cell with:
- one observation: what the plot shows,
- one sentence on why it matters for the research questions,
- a tag: **Expected**, **Unexpected**, or **In between**, with a short reason.

### Step 6: What next? and revised research questions
Every relationship plot also gets a **What next?** cell with one idea: an extra
comparison, a subgroup to split out, another dataset to join, or a domain expert
to ask. Then restate the research questions. Mark each **(unchanged)**,
**(revised)**, **(new)**, or **(dropped)**, with one line on *what changed and why*.

## Cell rules
- **One observation per cell.** Start it with `**Observation:**`. State one
  finding with the number that supports it. A second finding gets a new cell.
- **One result per code cell:** one table or one plot, with a markdown cell
  right next to each plot.
- Every number in the text must come from code. Never type a result by hand.
- Skip the observation when a result is routine. Don't write one for every cell.
- Label every plot axis with units, at a readable size, and give every plot a title.
- Watch for overplotting on large data (sample, use transparency, or bin).
- A chart showing two things move together does not show that one causes the other.

Too long (several findings in one cell):
> - The shape is (8047, 11). There are 7,064 missing operators. The direction
>   column has lists. The timestamp is the last edit...

Better (one finding per cell):
> **Observation:** `operator` is missing for 7,064 of 8,047 cameras (88%).

> **Observation:** `timestamp` is the last edit date, not the install date.

## Easy to read
- Short sentences and plain words. Explain a technical term the first time you use it.
- Put column names in backticks, like `median_income`.
- Say what stands out and why it matters for the research questions.
- Say what the data shows and what it can't. Don't claim cause: write "goes with"
  or "is linked to", not "causes".
- Keep the voice neutral. Skip filler like "honestly".

## Code and style
- Follow `docs/CODING_STYLE.md` where it fits a notebook: descriptive names,
  comments that explain **why**, `pathlib` paths built from the project root
  (not `../`), Polars for tables, GeoPandas for maps, and never overwriting files.
- Skip the script-only parts: shebang, section banners, `main()`, the entry
  point, and the EOF banner. Use headings instead.
- Put all imports in the first code cell. Don't repeat them.
- Never change raw data. Set random seeds if anything is random.
- For area or distance, convert to a projected coordinate system first.
- Use samples in `data/processed/samples/` only for quick tests.
- Build any joined table the plots need once, in a short setup cell with a
  one-line explanation.

## Before you finish
- Run the notebook top to bottom. If a needed tool isn't installed, ask me.
- Check for the usual traps: rows lost in joins, codes that lost leading zeros,
  placeholder values read as real numbers.
- Don't commit anything. Every group member needs at least one commit for this
  checkpoint, so I'll commit myself.

## Final message to me
Keep it short:
- File paths.
- A checklist of the six rubric items: covered or not, with the reason if not.
- The draft README section (unified mode).
- Anything you couldn't verify.