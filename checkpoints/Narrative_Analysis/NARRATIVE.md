# Narrative Analysis: Methods, Checks and Limitations

Supporting notes for the **Main Findings** section of the [README](../../README.md). Every number below is printed by
[`narrative.ipynb`](narrative.ipynb) (the final cell lists most of them; the regression tables are printed in the
Finding 2 and 3 cells). That notebook adapts code from `notebooks/personal_notebooks/dev3.ipynb`.

**Scope that applies to everything.** Counts are Flock cameras *mapped* in OpenStreetMap (OSM): 112,823 cameras in the
snapshot and 112,522 with a history date (cohort pulled 2026-10-30). Mapped is not the same as installed. OSM dates are
mapping dates. All results are observational associations, so none of them is causal.

## Research Questions

1. Where are mapped Flock cameras, and how has the mapping grown over time?
2. Is mapped camera density associated with community characteristics?
3. Is mapped camera density associated with county voting patterns?

The story runs in that order. Finding 1 establishes what the data measures: a volunteer map whose geography matches an
independent source but whose dates are not installation dates. Finding 2 asks which places have more mapped cameras.
Finding 3 asks whether politics explains anything beyond the factors in Finding 2.

## What changed after the professor's feedback

The professor recommended a county negative binomial regression:
`flock_count ~ log_pop + log_income + poverty_rate + urban_share + gop_share_2024 + C(state)`, offset `log(land_sq_mi)`.

- It is fitted as NB2 (Var = μ + α·μ²) with **α estimated by maximum likelihood** (statsmodels `NegativeBinomial`,
  starting from the Poisson estimates). A separate profile-likelihood fit gives the same α (1.2552 both ways).
- `urban_share` is **not available**: the repo has no Census urban/rural table, so it is left out rather than replaced
  with a different measure.
- County `poverty_rate` is computed exactly by summing tract counts from ACS S1701. `log_income` uses the
  population-weighted mean of tract median incomes, because the repo has no county median.
- We added `% non-Hispanic white` in some models because it is the variable Finding 2 is about.
- **The offset was tested, and the data reject it** (see Finding 2). We still report the professor's model, but the
  conclusions rest on the version that lets the data estimate the land-area exponent.
- Finding 1 now also compares cumulative cameras with cumulative counties reached. ZIP codes are not used because the
  repo has no ZCTA boundary file.

---

## Finding 1: Geographic distribution and mapping growth

**Finding.** By the end of 2025, mapping had reached 67% of the 2,279 counties that now have a mapped camera, but only
39% of the cameras. 94% of the cameras added in 2026 (61% of all) went into counties that were already mapped, through
many small volunteer uploads. So the growth curve shows mapping spreading and then filling in, not a measurable
installation wave.

**Evidence.**

| Measure | Value |
|---|---|
| First month / cameras | Nov 2024 / 514 |
| Monthly additions through Jun 2025 | 514–2,401 (12,139 cumulative) |
| Cameras first tagged in 2026 | 68,899 (61%) |
| Jul 2026 / Aug 2026 | 11,457 / 11,807 |
| Counties with ≥ 1 dated camera (TIGER 2024) | 2,279 |
| End of 2025: share of final counties reached / share of final cameras | 67% / 39% |
| 2026 cameras in counties already reached before 2026 | 94% |
| 2026 share using object-creation date instead of tag date | 60% (vs 61%) |
| Jul–Aug 2026: changesets / distinct accounts (lower bound) | 22,599 / 9,243 |
| Jul–Aug 2026: share re-tagging an existing object / share in ≥ 50-camera changesets | 1.4% / 0% |
| Whole cohort: re-tagged / in ≥ 50-camera changesets / largest changeset | 3.4% / 1.1% / 430 |
| Top 5 states (CA, TX, GA, FL, OH), share of cameras | 48.6% |
| Spearman ρ, state cameras vs population (95% bootstrap CI, n = 52) | 0.89 (0.80–0.94) |
| Spearman ρ, OSM Flock vs Finding Flock all-vendor (n = 52) | 0.976 (0.935–0.993) |
| OSM Flock total ÷ Finding Flock all-vendor total | 0.78 |
| Georgia vs median state, cameras per 100k | 85.0 vs 26.6 |

**Interpretation.** The history file is a census of the cohort, not a sample, so the monthly counts carry no sampling
error. The uncertainty is about what they measure. The county curve runs well ahead of the camera curve: mapping
first reached most places, and later growth mostly added cameras inside already-mapped counties. An average of about
one camera per changeset during the peak means thousands of people each added a camera or two. That does not look
like a bulk import or a re-tagging sweep.

**Alternative explanations and checks.**

| Alternative | Check | Result |
|---|---|---|
| Bursts are bulk imports or re-tagging by a few editors | Changeset size and re-tag share by month | **Rejected.** 0% of peak-month cameras came in ≥ 50-camera changesets and 1.4% were re-tags. |
| The 2026 surge is a tag-change artifact | Second date measure: object creation date | **Rejected.** 60% of cameras were created in 2026, vs 61% first tagged in 2026. |
| The surge is mapping expanding into new areas | Third measure: cumulative counties reached | **Mostly rejected.** 94% of 2026 cameras were in counties already reached. |
| The curve's start date (Nov 2024) is real | Creation dates vs first-tagged dates | **Rejected.** All 657 nodes created before Nov 2024 reach the current tagging rule only later. |
| Bursts are installation waves | Would need installation or contract dates | **Proposed only.** No such data exists in the repo. |
| Mapped geography only reflects volunteer activity | Compare with Finding Flock | **Mostly rejected.** ρ = 0.976. The OSM count is 78% of the all-vendor total, lowest in the Northeast. |

**Limitations.** Survivorship: cameras mapped and later deleted are not in the cohort. A county counts as "reached"
when its first *surviving* camera was tagged. Flock cameras tagged only by `brand`/`operator` are outside the snapshot
(about 4% by dev2's estimate).

---

## Finding 2: Community characteristics

**Finding.** Whiter places have fewer mapped Flock cameras per resident. The whitest fifth of tracts has 2.33 per
10,000 residents (95% CI 2.25–2.40), 44% fewer than the 4.13 (4.01–4.24) in the 27–55% white fifth. In the county
negative binomial model, each +10 points of non-Hispanic white share is associated with 8% fewer cameras (IRR 0.92,
95% CI 0.89–0.96), holding population, income, poverty, vote share and state fixed. Income and poverty effects are not
robust.

### Tract evidence (dev3 V4/V5)

82,913 tracts (ACS 2024 5-year, TIGER 2024), including 47,912 with zero cameras. Pooled rate = all cameras ÷ all
residents in the group; the 95% intervals come from 1,000 bootstrap resamples of tracts (seed 418).

| Grouping (national quintiles) | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| % NH white (0–27 / 27–55 / 55–73 / 73–86 / 86–100%) | 3.35 | **4.13** | 3.63 | 3.12 | **2.33** |
| % NH white, ranked within state | 3.19 | 3.72 | 3.63 | 3.18 | 2.90 |
| poverty rate (low → high) | 3.20 | 3.25 | 3.27 | 3.41 | 3.63 |
| median income (low → high) | 3.79 | 3.33 | 3.39 | 3.18 | 3.14 |

### County negative binomial regression

n = 3,114 counties with a 2024 vote, residents and all covariates (one county lacks income). 864 of them (28%) have
zero cameras and are kept. The camera count has mean 36.2 and variance 18,216. HC1 robust 95% CIs.

**Units.** IRR = exp(coefficient), the multiplicative change in the expected camera count. Effects are reported per
**doubling** of population or land area, per **+10% income**, and per **+10 percentage points** of poverty, % white or
Republican share. Example: IRR 0.92 per +10 pts % white means a county 10 points whiter is expected to have 8% fewer
mapped cameras than an otherwise similar county in the same state.

| Predictor (unit) | N4 professor's model (land offset) | N5 = N4 + % white (land offset) | **N6 land area estimated (preferred)** |
|---|---|---|---|
| population (doubling) | 1.76 (1.68–1.85) | 1.76 (1.68–1.84) | **1.96 (1.89–2.04)** |
| land area (doubling) | fixed by offset | fixed by offset | **1.01 (0.96–1.07)** |
| income (+10%) | 1.13 (1.07–1.20), p < 0.001 | 1.13 (1.07–1.20) | **1.03 (0.99–1.07), p = 0.14** |
| poverty (+10 pts) | 0.91 (0.71–1.16), p = 0.44 | 0.88 (0.68–1.15), p = 0.34 | **0.76 (0.65–0.90), p = 0.001** |
| % NH white (+10 pts) | — | 0.96 (0.90–1.02), p = 0.20 | **0.92 (0.89–0.96), p < 0.001** |
| Republican share (+10 pts) | 0.78 (0.73–0.83) | 0.80 (0.75–0.85) | **0.95 (0.90–1.00), p = 0.07** |
| α (dispersion, 95% CI) | 1.26 (1.14–1.37) | 1.25 (1.14–1.37) | 0.88 (0.80–0.95) |
| AIC | 20,635 | 20,634 | **19,904** |

Raw coefficients (log scale): N4 log_pop 0.817, log_income 1.318, poverty −0.096, GOP −0.255; N6 log_pop 0.972,
log_land 0.017, log_income 0.303, poverty −0.269, % white −0.080, GOP −0.049. In plain terms, N6 says a county with
twice the population has about twice the mapped cameras (elasticity 0.97), while land area adds essentially nothing.

### Diagnostics

| Check | Result | Meaning |
|---|---|---|
| Overdispersion: Poisson Pearson χ²/df | 39.4 (N4), 14.4 (N6) | Far above 1, so Poisson underestimates the variance |
| NB2 vs Poisson likelihood ratio (α = 0) | 55,167 (N4), 29,263 (N6); p ≈ 0 | NB2 is needed |
| AIC Poisson → NB2 | 75,801 → 20,635 (N4); 49,165 → 19,904 (N6) | NB2 is much better |
| Zero-camera counties: observed / NB2 / Poisson | 864 / 715 (N4), 595 (N6) / 268 (N4), 237 (N6) | NB2 is much closer but still under-predicts zeros (possibly unmapped counties) |
| **Offset test**: N5 (land coefficient fixed at 1) vs N6 (estimated) | coefficient 0.017 (−0.066 to 0.100); LR = 732.8, p ≈ 2e-161; AIC 20,634 → 19,904 | **Cameras do not scale with land area**, so the land-area offset is misspecified |
| VIF (continuous predictors) | log_income 4.19, poverty 3.72, GOP 1.93, log_pop 1.80, % white 1.70, log_land 1.06 | All below 5; income and poverty overlap moderately |
| α by profile likelihood (N4) | 1.2552 = discrete ML 1.2552 | The fit converged to the right place |

### Alternative explanations and checks

| Alternative | Check | Result |
|---|---|---|
| Urban vs rural confounding | Tracts within population-density terciles | **Rejected.** The whitest quintile is lowest in every tercile (e.g. 2.26 vs 5.61 in the least dense third). |
| Regional confounding | Tracts ranked within their own state; county state fixed effects | **Partly supported.** The tract gap shrinks to 2.90 vs 3.72 (46% remains). The county IRR moves from 0.79 without state fixed effects to 0.92 with them. |
| Choice of denominator | County model with land offset (N5), land estimated (N6), population offset (N7) | **% white is robust where the fit is good**: N6 0.923, N7 0.924 (0.886–0.962). Under the rejected land offset it weakens to 0.961 (0.90–1.02). |
| Counties in the same state are not independent | N6 with state-clustered SEs | **Holds.** % white 0.923 (0.878–0.970); poverty 0.764 (0.607–0.961); income 1.029 (0.965–1.098). |
| Tiny tracts with unstable rates | Drop tracts with < 500 residents | **Rejected.** 2.33 vs 4.13, unchanged. |
| Mapping completeness varies by place | Would need a camera census independent of volunteers | **Proposed only.** |

**Interpretation.** The race pattern shows up at both levels and in every well-fitting model, so it is the
best-supported community pattern. It is modest: about 8% per 10 points in counties, and about half of the tract gap is
between states. Income and poverty change with the specification. Income looks important only under the rejected
land-area offset. Poverty is negative in N6–N8 but null under the offset, and it rises slightly in the tract quintiles.
We therefore do not claim an income or poverty effect.

**Limitations.** Mapped, not installed. ACS margins of error are large for small tracts. 204 cameras in Puerto Rico and
USVI have no tract boundary in the repo. `urban_share` is unavailable. County income is an average of tract medians.
The model under-predicts zero-camera counties. A zero-inflated model could test this, but we kept the simpler NB2 as
suggested. County results describe counties, not individuals.

---

## Finding 3: Political characteristics

**Finding.** County 2024 Republican vote share has no consistent association with mapped cameras per resident. The
unadjusted IRR is 1.01 per +10 points (0.98–1.04), the adjusted within-state estimate is 0.95 (0.90–1.00), and other
specifications range from 0.78 to 1.17, so even the sign depends on the model.

**Evidence: unadjusted vs adjusted** (NB2, IRR per +10 points Republican share, HC1 95% CI, n = 3,114).

| Model | IRR (95% CI) | p |
|---|---|---|
| N1 unadjusted, per square mile (land offset) | 0.49 (0.46–0.51) | < 0.001 |
| N2 unadjusted, per resident (population offset) | **1.01 (0.98–1.04)** | 0.59 |
| N3 state fixed effects only, per resident | 0.91 (0.88–0.94) | < 0.001 |
| N4 professor's model (land offset) | 0.78 (0.73–0.83) | < 0.001 |
| N5 N4 + % white (land offset) | 0.80 (0.75–0.85) | < 0.001 |
| N6 + % white, land area estimated (preferred) | **0.95 (0.90–1.00)** | 0.07 |
| N6 with state-clustered SEs | 0.95 (0.88–1.03) | 0.24 |
| N7 population offset + log density | 0.95 (0.90–1.00) | 0.07 |
| N8 N6 without state fixed effects | 1.17 (1.13–1.22) | < 0.001 |

dev3's linear models (OLS of log(1 + cameras per 10k), HC1, per +10 pts) are kept as a second model family: A vote
only −0.028 (−0.048 to −0.007); B + state FE −0.070 (−0.091 to −0.048); C + density, % white, income **+0.007
(−0.029 to +0.042)**; D = C weighted by population −0.014 (−0.054 to +0.027).

**Interpretation.** Unadjusted and per resident, there is no association. The large unadjusted per-square-mile gap
(N1) reflects county size: Republican counties are big and sparsely populated (vote share vs population ρ = −0.53).
Within states, the negative estimate shrinks toward 1 as controls are added (0.91 → 0.95) and its CI reaches 1. Across
states (N8), the sign flips. The professor's model gives the most negative estimate, but its land offset is rejected
by the data. We read this as a supported null: any political association is small and not stable in direction. The
regression did not change dev3's conclusion. It made the comparison more explicit.

**Alternative explanations and checks.**

| Alternative | Check | Result |
|---|---|---|
| County size confounds vote | Per-resident offset; controls; size band × vote band table | **Supported, which is why the raw per-area gap disappears.** Within size bands there is no consistent direction (< 25k: 3.64 → 2.77; 100k–500k: 3.37 → 3.90). |
| Between-state differences drive the result | With vs without state fixed effects (N6 vs N8) | **Supported.** The sign flips, so the vote result depends on which comparison is made. |
| Model family (count vs linear) | NB2 vs dev3 OLS | **Same conclusion.** OLS C +0.007 (CI spans 0); NB2 N6 0.95 (CI reaches 1). |
| Thousands of small counties dominate | Population-weighted OLS (D) | **Rejected.** −0.014, CI spans 0. |

**Limitations.** Over-controlling: income and composition correlate with vote, so adjusted models answer a narrower
question. County vote is a crude proxy for the politics of the agencies and businesses that buy cameras. Alaska and the
territories have no county-level vote.

---

## Did the regression change dev3's conclusions?

| Topic | dev3 (descriptive + OLS) | With NB2 | Change |
|---|---|---|---|
| Race | Whitest tracts lowest; county OLS −0.056 per 10 pts, not robust to weighting | IRR 0.92 (0.89–0.96), robust to clustering and population offset | **Strengthened** at county level |
| Income | Flat in tracts; strong in county OLS (+0.66 per log unit) | Only significant under the rejected land offset; 1.03 (0.99–1.07) in N6 | **Weakened**, not robust |
| Poverty | Slight rise across tract quintiles | 0.76 per +10 pts in N6, null under land offset | **New, not robust**: depends on level and specification |
| Vote | No association after controls | Same; and the sign depends on state fixed effects | **Confirmed** (null) |

## Excluded Analyses

| Analysis (dev3) | Why it is not in the story |
|---|---|
| V1 nationwide hexbin map | Mostly shows population; the state comparison and Finding Flock check make the same point with numbers |
| V3 state per-capita bar chart | Folded into Finding 1 as evidence; one figure per finding |
| V4 income / V5 poverty panels | Near-flat; reported in Finding 2's tables for contrast |
| V6 Chicago income choropleth | A single metro area whose gap is city vs suburb (vendor/jurisdiction); a case study, not a national finding |
| V7 vote-category bar chart | Superseded by the regressions in Finding 3 |
| V9 Atlas of Surveillance "procurement" proxy | No procurement dataset exists; the proxy's vote pattern is a county-size effect |
| ZIP-code growth measure | No ZCTA boundaries in the repo |
| Zero-inflated / hurdle count models | Beyond the scope of the suggested model; flagged as a limitation |
| Live OSM history re-check; strict-tag-rule sensitivity (H4) | Need network access or files not in the repo |
| Chicago crime comparison (dev2) | Crime data is not in the repo |

## Reproducibility

1. Install the environment from the repository root: `uv sync`. The analysis uses geopandas, polars, scipy,
   statsmodels and matplotlib from `pyproject.toml` / `uv.lock` (statsmodels was added for the NB2 models).
2. Make sure the raw inputs exist under `data/raw/` and `data/external/`. Raw data is gitignored; the fetch scripts are
   in `scripts/`. The notebook's first cell asserts that every input exists.
3. Run the notebook top to bottom with the `.venv` kernel, or headless:

   ```bash
   .venv/Scripts/python -m nbconvert --to notebook --execute --inplace checkpoints/Narrative_Analysis/narrative.ipynb
   ```

   (`.venv/bin/python` on macOS/Linux.) It takes about a minute and overwrites `figures/finding-one.png`,
   `figures/finding-two.png` and `figures/finding-three.png`.
4. Bootstrap intervals use a fixed seed (418), and the regressions are deterministic, so reruns give identical results.
   The figure cells contain `assert` statements that stop the notebook if the data no longer support a figure title.
