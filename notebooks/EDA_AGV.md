# EDA: Public Perception of Flock Cameras

**Workstream:** public perception (Muba) · **Notebook:** `notebooks/EDA M4/EDA_AGV.ipynb` · **Figures:** `figures/eda/` (regenerated each time the notebook runs)

## Research questions (revised)

1. **RQ1 (attention):** How has public attention to Flock cameras in Illinois changed over time, and which events line up with the spikes?
2. **RQ2 (attention vs. opposition):** Does Flock attention move with *opposition* activity (DeFlock) or with general surveillance interest?
3. **RQ3 (opinion):** How does opinion of Flock differ across political groups, and is Flock viewed more negatively than public cameras in general?

Original question: *"What is the public perception of Flock cameras in Chicago?"* The reasons for the changes are in [§6](#6-research-questions-revisited).

---

## 1. Dataset profiles (notebook §2)

| Dataset | Role | Shape | Types | Missing | What stands out |
|---|---|---|---|---|---|
| Google Trends time series: `flock camera`, `camera surveillance`, `Facial recognition system` (IL, monthly, Nov 2021 – Nov 2026) | Primary | 61 × 4 | `Time` is a string (parsed to datetime), the rest are int (0–100) | 0 | `flock camera` is 0 in 30 of 61 months, then peaks at 100 in Aug 2026. Median 1 vs mean 5.4. |
| Google Trends time series: `deflock`, `ban flock cameras` | Primary | 61 × 3 | same | 0 | `deflock` first appears Nov 2025. `ban flock cameras` is non-zero in a single month. |
| Navigator Research survey, Sept 10–14 2026, n = 1,000 U.S. registered voters (transcribed from PDF) | Primary | 113 × 5 | `pct` int, other columns str | 0 | Only Flock-specific opinion source. `pct` mixes percentages with net scores. Groups differ by question. |
| YouGov daily poll, Oct 18 2022, U.S. adults ("Do security cameras in public places make you feel…?") | Secondary | 100 × 10 | `published`, `conducted`, `n_adults` all-null | 300 cells | One poll and one question. Mostly neutral answers. |
| Google Trends by region (3 files) | Secondary | 10 × 3–4 | int | 0 | Values are shares between the compared terms (each row sums to 100). Chicago has the lowest `flock camera` share (31) and the highest `red light camera` share (19). |
| Google Trends related queries (5 files) | Secondary | 12–50 × 3 | `increase percent` is a string | 0 | Top "flock camera" queries are "flock camera map" and "what is a flock camera" |

One more Trends file (`facial recognition`, `red light camera`, `Surveillance` time series) is **empty**. See the anomalies below.

## 2. Anomalies (notebook §3, table `anomalies`)

| File | Anomaly | Rows affected | Action |
|---|---|---|---|
| `time_series_…0012` | Empty export (header only) | 0 / 0 | Excluded. Re-export needed. |
| `time_series_…0007` | `deflock` is 0 in most months | 51 / 61 | Kept (the zeros are real). Correlations restricted to Jan 2025+. |
| `time_series_…0007` | `ban flock cameras` is 0 in most months | 60 / 61 | Excluded from correlations (near-constant) |
| Trends time series (any repeated term) | Same term exported in more than one file | per file | Joined once. When a term appears in two exports, the one with the higher peak is kept. |
| `by_region_*` (3 files) | Values are shares, not interest levels | 10 / 10 each | Interpreted as relative shares. Only compared within a region. |
| `by_region_*` (3 files) | Regions outside IL (Terre Haute IN, Evansville IN, St. Louis MO) | 3 / 10 each | Kept and labeled. These media markets overlap IL. |
| `by_region_…0007` | Almost no variance (`deflock` ≈ 100 everywhere) | 10 / 10 | Not used |
| `searched_with_*` (5 files) | `increase percent` mixes `"Breakout"` with text like `"4,700%"` | 12–50 per file | Parsed to numeric `increase_pct` plus an `is_breakout` flag |
| `searched_with_top…2357` | Duplicate of `searched_with_rising…2357` | 49 / 50 | Dropped |
| `yougov_poll_data` | `published`, `conducted`, `n_adults` all null | 100 / 100 | Date taken from the poll URL (2022-10-18). n unknown, so no significance tests. |
| `yougov_poll_data` | `raw_pct` identical to `pct` | 100 / 100 | Dropped |
| `yougov_poll_data` | `All` group repeated in every category | 20 / 100 | Removed (kept once) |
| `navigator_flock_sept2026` | `pct` mixes net scores (−47 to +35) with percentages | 19 / 113 | Split into `navigator_percent` and `navigator_net_scores` |
| `navigator_flock_sept2026` | Values derived (unfavorable = favorable − net) | 8 / 113 | Flagged in `value_type`. Totals checked: support + oppose + not sure = 100, and the net scores match. |
| All Trends files | Each export is normalized separately | all | Levels aren't compared across files. Correlation doesn't depend on scale, so it's still valid. |

Cleaned outputs are written to `data/processed/` (`trends_monthly_IL.csv`, `yougov_clean.csv`, `navigator_percent.csv`, `navigator_net_scores.csv`, `*_parsed.csv`).

## 3. Key distributions (notebook §5)

![Figure D1](figures/eda/D1_trends_distributions.png)

**Figure D1: Trends series.** The Flock series are **extremely right-skewed and zero-inflated**. `flock camera`: median 1, mean 5.4, skew 4.4, 49% zeros. `deflock`: skew 4.1, 84% zeros. Their outliers are the 2026 surge, which is the signal, so they're kept and summarized with median and IQR. `facial recognition system` (median 7, skew 2.1) and `camera surveillance` (median 2, skew 2.3) have a steady non-zero baseline. Flock attention is **event-driven**, while general surveillance interest is steady.

![Figure D2](figures/eda/D2_opinion_query_distributions.png)

**Figure D2: opinion and queries.**
- **Navigator:** `police_use` values spread widely across groups (14–60%), so the split is between groups, not within them. `heard_about` is tight and high (56–68%). `top_concerns` are clustered (11–41%), so no single concern dominates overall.
- **YouGov:** centered on **neutral**. 44% say neither safer nor less safe, 36% safer, 10% less safe.
- **Query intent:** right-skewed toward **location** (14 queries, 252 total interest) and **informational** (14 queries, 213) searches. Opposition queries are a small tail (9 queries, 20). Two "map" queries alone account for 200 of the 581 total interest points.

## 4. Relationships, so what, and what next (notebook §6)

### R1. Attention over time with event and survey dates (RQ1)
*Joins the two Trends time-series exports by month and overlays the dates of both surveys.*

![Figure R1](figures/eda/R1_attention_timeline.png)

- **So what?** Flock attention in Illinois was essentially zero until late 2025. The mean was 0.3 before Aug 2025 and 19.8 after. It rose from Apr 2026, peaked in **Aug 2026**, and by Nov had fallen to 14% of the peak. The Aug 2025 Illinois audit and the Evanston and Oak Park cancellations caused only a small bump. The surge came with national coverage a year later. `deflock` rose together with `flock camera`, while general surveillance terms stayed flat. The **Navigator poll was fielded just after the peak**, at maximum attention. The YouGov poll was taken before Flock was known.
- **What next?** *Did news coverage drive the surge?* Pull GDELT article volume and tone for "Flock Safety" and test whether coverage comes before search interest. Re-export weekly Trends for 2026 to date the peak to specific stories.

### R2. Correlation matrix, scatter plot, and lagged correlation (RQ2)
*Joins series from two separately normalized Trends files. Correlation is scale-invariant, so the comparison is valid.*

![Figure R2](figures/eda/R2_correlations.png)

- **So what?** For Jan 2025 – Nov 2026 (n = 23 months), Flock attention tracks **opposition** almost exactly (`deflock`: Pearson r = 0.95, Spearman ρ = 0.90). It is essentially unrelated to **general surveillance** interest (`facial recognition system`: r = 0.05; `camera surveillance`: r = 0.30). The correlation is highest at lag 0, and lag −1 (0.89) is higher than lag +1 (0.58), so DeFlock interest tends to rise **about a month before** general Flock interest (Jun 2026: deflock 62, flock camera 27). Public attention to Flock is bound up with the opposition movement and isn't part of a broader surveillance trend.
- **What next?** *Does activism drive awareness, or are both reacting to the same news?* 23 monthly points are too few for a Granger test, so repeat with weekly data plus GDELT. Also join camera counts per media market (Finding Flock / DeFlock) with the regional Trends shares to test whether more exposure leads to more attention.

### R3. Opinion by party: Navigator (Flock, 2026) vs YouGov (generic cameras, 2022), plus concerns by group (RQ3)
*Compares the primary survey with the secondary survey across matching party groups.*

![Figure R3](figures/eda/R3_opinion_by_party.png)

- **So what?** In 2022, every party felt **net positive** about generic public cameras (% safer − % less safe): Democrats +35, Republicans +29, Independents +17. On **police use of Flock** in 2026 (% support − % oppose), every group except MAGA Republicans is **net negative**: Democrats −38, Independents −39, non-MAGA Republicans −17, MAGA Republicans +6. The partisan order **flips**. Concerns about collecting data on non-suspects, consent, and tracking are shared across groups (about 30–35%). **Sharing with ICE** splits sharply (Democrats 34% vs MAGA Republicans 11%), and so does transparency (33% vs 21%). Flock is viewed far more negatively than cameras in general, and the gap is driven by concerns about Flock's data sharing, which links to the 2025 Illinois audit in R1.
- **Caveat:** the two surveys differ in wording, population (adults vs registered voters), and year, and YouGov has no sample size. This is a **directional comparison, not a significance test**.
- **What next?** *Is the gap specific to Flock, or did attitudes toward all cameras sour between 2022 and 2026?* Find same-wording polls over time on generic police cameras or license plate readers, and look for Illinois-specific polling.

## 5. Summary of findings
1. Flock attention in Illinois is **new and event-driven**: near zero until late 2025, a peak in Aug 2026, then decline (R1, D1).
2. Attention is **tied to opposition** (r = 0.95 with `deflock`, which leads by about a month) and **not to general surveillance interest** (r ≈ 0.05) (R2).
3. Most searches are about **where the cameras are and what they are**. Awareness is still forming (D2).
4. Opinion of Flock is **net negative in every group except MAGA Republicans**, which reverses the positive 2022 view of generic cameras, especially among Democrats. **ICE data sharing** is the most partisan concern (R3).

## 6. Research questions revisited

**Original:** *"What is the public perception of Flock cameras in Chicago?"*

**Revisions and why**
- **"Perception" was split into attention (RQ1, RQ2) and opinion (RQ3).** Google Trends measures how much people search, not whether they approve. Surveys measure approval but only at single points in time. Separate questions keep each claim matched to a source that can support it.
- **"Chicago" became Illinois plus national surveys.** Trends only resolves to media markets ("Chicago IL" is the whole metro), and both surveys are national. No Chicago-only opinion data was found, so Chicago is now context, not the unit of analysis.
- **RQ2 was added after EDA.** The 0.95 correlation with `deflock` and the dominance of "map" searches showed that opposition activity is central to how people encounter Flock.

**Next steps:** GDELT coverage vs search timing (R1, R2) · weekly 2026 Trends for lead–lag tests (R2) · same-wording polls over time and Illinois polling (R3) · camera density vs attention by region (R2) · re-export the empty Trends file.

**Sources:** Google Trends (trends.google.com, exported Nov 9 2026) · [Navigator Research, Navigator Update 09.28.2026](https://navigatorresearch.org/wp-content/uploads/2026/09/Navigator-Update-09.28.2026.pdf) · [YouGov daily results, Oct 18 2022](https://yougov.com/en-us/daily-results/20221018-4280f-3)
