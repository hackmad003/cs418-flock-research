# dev3: Findings Summary

Plain-language summary of the results in [`dev3.ipynb`](dev3.ipynb). The notebook runs only on datasets that live in
this repo (`data/raw/`, `data/external/`).

## Ground rules (apply to every finding)

- **Mapped is not the same as installed.** Counts are Flock cameras that volunteers have tagged in OpenStreetMap (OSM). A
  dense area can mean many cameras *or* many active mappers. An empty area doesn't prove there are no cameras.
- **Dates are mapping dates.** An OSM date is when someone *mapped* a camera, not when it was installed.
- **Flock only**, using the strict tag rule. Cameras tagged only through `brand`/`operator` are not counted (dev2
  estimated about 4%).
- **Observational and cross-sectional.** Nothing here shows causation or explains *why* cameras are where they are.

## Data used

| Source | What it gives |
|---|---|
| OSM Flock snapshot (2026-10-30) | 112,830 camera nodes; 112,823 in the analysis after cleaning |
| OSM Flock history (2026-10-30) | First date each camera was Flock-tagged (112,522 dated) |
| ACS 2024 5-year (tract) | Population (B01003), median income (B19013), poverty (S1701), race/ethnicity (B03002) |
| TIGER 2024 boundaries | Tracts (50 states + DC) and counties |
| 2024 presidential election (county) | Republican share of the two-party vote |
| Finding Flock, Atlas of Surveillance | Independent cross-checks |

---

## Q1. Where are mapped Flock cameras, and how has the mapping grown?

### V1: Nationwide map
**Plot:** US map split into roughly 25 km hexagons. Darker blue means more cameras (log scale). Alaska, Hawaii and
PR/USVI are insets.

**Finding:** cameras follow population. The densest areas are the big metros (Atlanta, Houston, Dallas–Fort Worth, LA,
Bay Area, Chicago, Detroit, Denver, Phoenix, Seattle). The eastern half of the country, from Texas to Michigan to
Georgia, is almost continuously covered. The Mountain West and Great Plains have scattered clusters along highways.
Northern New England is nearly empty. The densest hexagon holds 984 cameras.

### V2: Growth over time
**Plot:** the top panel shows new cameras per month (bars); the bottom panel shows the running total (line).

**Finding:** through mid-2025 the map gains about 500–2,400 cameras a month (12,139 by June 2025). Then it jumps twice:
**Nov 2025 – Jan 2026** (about 9.3k, 8.7k and 7.5k per month) and **Jul–Aug 2026** (about 11.5k and 11.8k, the two
biggest months). 42,322 cameras were first tagged in 2025 and 68,899 in Jan–Oct 2026.

These bursts look like **mapping campaigns or bulk re-tagging, not installation waves**. Nearly 12k cameras in one month
is far beyond a plausible installation rate.

### V3: Cameras by state
**Plot:** horizontal bars of cameras per 100,000 residents, with the raw count in brackets.

**Finding:**
- In raw numbers, five states (CA, TX, GA, FL, OH) hold 48.6% of cameras. State totals track population closely
  (Spearman ρ = 0.89).
- Per capita, the median state has about 27 per 100k. **Georgia is the outlier at 85 per 100k** (Flock's home state),
  followed by Texas (52), Ohio (52), Alabama (51) and Indiana (49). California falls to the middle (42).
- The lowest rates are in New England (NH 1.1, VT 2.8, ME 3.2), plus Alaska (3.4), Hawaii (4.4) and PR (4.5). NY and PA
  are about 11 despite their large populations.
- **Cross-check:** state rankings agree almost perfectly with Finding Flock's all-vendor totals (ρ = 0.98). OSM Flock is
  78% of their total. The Northeast has the lowest share, so either other vendors are more common there or Flock is
  less completely mapped (or both).

---

## Q2. Is mapped camera density associated with community characteristics?

V4 and V5 use the same design. Census tracts are split into five equal-size groups (quintiles). The **left panel** is
the pooled rate (all cameras ÷ all residents × 10,000) with 95% bootstrap intervals. The **right panel** is the % of
tracts with at least one camera. Tracts with zero cameras are included.

### V4: Neighbourhood income
**Finding: essentially no income gradient.** The lowest-income quintile is slightly higher (3.79 per 10k, CI
3.68–3.90). The other four quintiles are 3.14–3.39. Every quintile has 41–43% of tracts with a camera. The tract-level
correlation is ρ = −0.03. Ranking tracts within their own state flattens it further (3.24–3.49), so the small bump is
partly a between-state effect.

### V5: Poverty rate and race/ethnicity
*(This replaces dev2's Chicago crime figure, because crime data isn't in the repo.)*

- **Poverty:** a very slight rise, from 3.20 per 10k (lowest poverty) to 3.63 (highest). The share of tracts with a
  camera is flat at 42%, and ρ = +0.02.
- **Race:** **the one clear gradient in Q2.** The whitest tracts (86–100% non-Hispanic white) have the lowest density,
  2.33 per 10k, against 4.13 in the 27–55% white quintile (and 34% vs 49% of tracts with a camera). The shape is an
  inverted U: the least-white quintile sits in between (3.35). Tract-level correlations are weak (ρ = −0.07 for % white,
  +0.11 for % Black).
  - **Not just urban vs rural:** the whitest quintile is still lowest within every population-density tercile.
  - **Partly regional:** ranking within states shrinks the gap from 4.13 vs 2.33 to 3.72 vs 2.90. High-rate states
    (GA, AL, TX) have large Black and Hispanic populations, and low-rate states (NH, VT, ME) are among the whitest.
    About half of the gap is between states and half is within them.

### V6: Chicago-area income map
**Plot:** the 9 Illinois counties of the Chicago area. Tracts are shaded by median household income, each camera is an
orange dot, and the City of Chicago is outlined.

**Finding:** 3,387 mapped Flock cameras are in the area, but **only 100 are in the City of Chicago**.
- At first glance, low-income tracts (under $50k) look under-covered: 1.29 per 10k vs 3.70–5.15 for the other income
  classes.
- That gap is really **city vs suburbs**. City tracts average 0.36 per 10k and the suburbs 5.52, and 80% of the
  under-$50k tracts are in the city.
- **Within the suburbs, the income gradient disappears** (4.89–6.16 per 10k in every class). Inside the city, ward
  income isn't meaningfully linked to cameras either (ρ = 0.14).
- The pattern comes from the jurisdiction and its choice of ALPR vendor, not from neighbourhood income. Chicago's own
  non-Flock ALPR network isn't shown.

---

## Q3. Is mapped camera density associated with county voting patterns?

The analysis set is 3,115 counties with a 2024 presidential vote (Alaska excluded).

### V7: Density by vote category
**Plot:** the same two-panel design as V4, with counties grouped by Republican share of the 2024 two-party vote.

**Finding: density doesn't differ by vote.** Every group is 3.1–3.6 per 10k, with heavily overlapping intervals. The
one difference is that only **64% of the most Republican counties (≥ 70%) have any camera**, compared with 79–83%
elsewhere. That's a **county-size effect**: the ≥ 70% group is mostly very small rural counties (1,643 counties holding
14% of residents). Within size bands there's no consistent direction.

### V8: County scatter + regression
**Plot:** each dot is a county (dot area ∝ population). The x-axis is Republican vote share and the y-axis is cameras per
10k (log scale). Zero-camera counties sit in a grey strip at the bottom, and the orange line is the pooled rate in
5-point bins.

**Finding: no trend.** The orange line stays between about 2.8 and 3.7 per 10k across the range.
- The raw correlation is weak and slightly negative (ρ = −0.10; −0.18 within states). That comes from the small
  Republican counties with zero cameras. Among counties with at least one camera it is slightly positive (+0.13).
- Republican share is strongly tied to county size (ρ = −0.53 with population).
- Regression of log(1 + cameras per 10k) with state fixed effects: the vote coefficient is −0.07 per 10 points.
  **After adding density, % white and income it vanishes: +0.007 (95% CI −0.03 to +0.04).**
- What does matter: **county income** (richer counties have more cameras per resident, +0.66 per log-unit) and **%
  non-Hispanic white** (−0.06 per 10 points, consistent with V5).

### V9: Adoption evidence by vote *(proxy)*
**Plot:** grouped bars for each vote category. One bar is the % of counties where the Atlas of Surveillance records an
agency using Flock, and the other is the % of counties with OSM-mapped cameras.

There is no procurement dataset (council votes or contracts), so this is a **labelled proxy**.

**Finding:**
- **The two independent sources agree.** Only 7 of the 1,040 Atlas-Flock counties have no mapped cameras. The Atlas is
  less complete: 1,217 counties have mapped cameras but no Atlas record. This agreement supports OSM as a signal of real
  deployment.
- **The vote pattern is again a size effect.** The Atlas share drops to 25% in ≥ 70% Republican counties, but within
  size bands it doesn't fall with Republican share, and it mostly *rises* (27% → 46% for counties of 25k–100k people;
  63% → 71% for 100k–500k).

---

## Summary table

| Question | Finding | Strength |
|---|---|---|
| Q1 Where | Cameras follow population (state ρ = 0.89); per capita, Georgia 85 per 100k vs New England ≈ 1–3 | **Strong** |
| Q1 Growth | Mapping grew in bursts (Nov 2025 – Jan 2026, Jul–Aug 2026): campaigns/re-tagging, not installations | Strong (descriptive) |
| Q1 Check | State totals agree with Finding Flock (ρ = 0.98); counties agree with the Atlas of Surveillance | Strong |
| Q2 Income | Flat nationally (tract ρ = −0.03); the Chicago-area gap is city vs suburbs | **None** |
| Q2 Poverty | Very slight rise with poverty (3.2 → 3.6 per 10k) | Negligible |
| Q2 Race | Whitest tracts have fewer cameras (2.3 vs 4.1 per 10k); about half is between states; also negative at county level | **Modest** |
| Q3 Vote | Flat by vote category; small raw differences disappear after size, income, race and state | **None** |
| Q3 Procurement | No procurement data; the Atlas proxy's vote pattern is a county-size effect | Not answerable |

**In one line:** mapped Flock cameras follow population. Georgia leads per capita. Income and voting show no real link
once size and location are accounted for. Lower density in very white areas is the only notable community-level pattern.

## QA and limitations

- **Every visual reconciles to its source:** V1/V3 to the 112,823-camera snapshot, V2 to the 112,522 dated cameras, V4–V5
  to the tract table (with counted exclusions plus 204 PR/USVI cameras that have no tract), V6 to the Chicago-area
  tract counts, and V7–V8 to the 3,115-county set (the V8 model uses 3,114).
- **Missing from the repo:** crime data (V5 replaced), procurement data (V9 proxy), PR tract boundaries, and the OSM
  history cache (M3 checks reduced). The strict-tag-rule sensitivity check (H4) couldn't be re-run.
- Group averages hide local variation; income, race, region and urbanicity are correlated with each other. Uneven
  mapping effort is a possible confounder throughout.
