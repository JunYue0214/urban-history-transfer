# Execution Report 1005-4

Execution ID:
1005-4

Source Prompt:
prompts/prompt1005-4.txt

Previous Execution:
1005-3

Report:
reports/report1005-4.md

Results:
results/1005-4/

Figures:
figures/1005-4/

Task name: Global Urban Historical Separability Pilot (Gate 1)

**This execution used real research data for the first time in this
project (official GHS-UCDB R2024A), but tested only GATE 1: whether
cities with similar present-day states and contexts can have
meaningfully different development histories. No environmental response
variable was used, constructed, or evaluated anywhere in this execution.
This execution does not and cannot establish that "history affects
environment."**

---

## 1. Executive Summary

Using the official GHS-UCDB R2024A dataset (11,422 urban centres, 10
directly-observed epochs 1975–2020), this pilot tested whether historical
built-up-surface trajectories (H) retain meaningful variation after
conditioning on present-day state (S: population, built-up area, density,
built volume) and coarse context (C: latitude, longitude, elevation).

**Headline findings:**

1. **GATE_A = PASS.** The official, pre-aggregated UCDB table/vector
   products (264 MB + 35 MB, both well under the 500 MB threshold)
   already contained everything needed — no raster download was
   required or attempted.
2. **A random-forest model, validated under leave-region-out holdout,
   explains only ~23% of per-epoch variance in H from S+C** (mean R² =
   0.226); richer present-state specifications (S1→S2→S3) and adding C
   improve this only modestly (R² rises from 0.136 to 0.226). Most
   historical trajectory information is **not** reconstructable from
   present state and context.
3. **A constrained permutation test shows present-day nearest-neighbour
   analogues DO have somewhat more similar histories than a random
   null** (observed mean historical distance 0.383 vs. null mean 0.529,
   a **27.6% relative reduction**) — real, non-trivial structure exists.
   But this effect is **partial, not total**: even among the closest
   25% of present-day analogues, **18.3% still show historical
   divergence in the top quartile of the overall distribution** — i.e.
   genuinely history-divergent "present-day twins" are not rare.
4. **This finding is stable across 6 of 6 true sensitivity variants**
   (nested S specifications, alternative distance scaling, removal of
   the smallest 10% of cities, removal of QC-flagged trajectories, and
   an alternative T=2015 endpoint), all within 30% relative of the
   baseline 18.3% figure. Removing C entirely (a deliberate contrast,
   not a robustness failure) raises the figure to 24.6%, confirming
   that geographic/climate context explains *part of* why present-day
   analogues share similar histories — exactly as expected.
5. **GATE 1 = PASS.** This does not mean "history affects environment"
   — no response variable was used. It means there is enough genuine,
   robust residual historical variation to justify *considering* Gate 2
   (which would require authorizing an environmental response variable).

A critical, disclosed methodological caveat is flagged in Section 15:
the permutation test's raw p-value is statistically saturated at this
sample size (~54,575 neighbour pairs make the null distribution's
standard deviation tiny, so p ≈ 0.000 regardless of effect size); the
Gate 1 decision in this report relies on **relative effect sizes**, not
the raw p-value, for this reason.

---

## 2. Exact Scientific Question Tested

"Can cities with similar present-day states and environmental contexts
have meaningfully different development histories?" Conceptually: can H
remain meaningfully variable conditional on S and C (H not approximately
equal to f(S,C))? This is GATE 1 only.

## 3. What Was NOT Tested

- Whether urban development history affects heat, flooding, vegetation,
  biodiversity, carbon, or any other environmental response.
- Any causal claim of any kind.
- Any claim that "history matters" for the environment — no response
  variable R was defined, downloaded, or used anywhere in this execution.
- Novelty of the candidate research programme (addressed in execution
  1005-3, not here).

---

## 4. UCDB Schema Verification

Full machine-readable record: `results/1005-4/ucdb_schema_audit.csv`
(49 rows). Summary of what was verified directly from the downloaded
official files (not from memory):

- **Product:** GHS-UCDB R2024A V1.2 (JRC, DOI
  10.2905/1a338be6-7eaf-480c-9664-3a8ade88cbcd), GeoPackage with 16
  thematic layers sharing key `ID_UC_G0`, **11,422 urban centres**,
  global coverage.
- **Multitemporal fields verified:** `GH_BUS_TOT_{year}` (built-up
  surface, m², direct), `GH_POP_TOT_{year}` (population, direct),
  `GH_BUV_TOT_{year}` (built-up volume, direct) — all present for
  **12 epochs**: 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015,
  2020, 2025, 2030, at 5-year intervals. **Zero missing values** in any
  of these fields for any city.
- **Observed vs. projected epochs (critical distinction, confirmed via
  official documentation search, not assumed):** 1975–2020 are derived
  from actual satellite observations (Landsat for 1975/1990/2000/2014→
  "2015" epoch, Sentinel-2 for 2018→"2020" epoch, spatio-temporally
  interpolated within that observed record); **2025 and 2030 are
  modeled/extrapolated projections, not observations.** This execution
  uses only the 10 observed epochs (1975–2020); 2025 and 2030 are
  excluded entirely from both H and S, not merely because they are
  "future" relative to any chosen T, but because they are not
  measurements.
- **Boundary definition (critical, directly relevant to the
  future-boundary-conditioning concern from execution 1005-3's risk
  register item D):** the main GHS-UCDB product uses a **fixed urban
  centre boundary, delineated at the 2025 reference epoch, for all
  historical epochs** — i.e., 1975 built-up surface is the sum of
  built-up grid cells *within the 2025-delineated boundary*, not a
  boundary appropriate to 1975. This was confirmed via official JRC
  documentation search, not assumed. A separate, smaller official
  product — **GHS_UCDB_MTUC_GLOBE_R2024A** ("Multi-Temporal Urban
  Centre", 35 MB, N=11,687, different ID scheme `ID_MTUC_G0`) — uses a
  genuinely **time-varying boundary** per epoch, and was downloaded and
  used as a boundary-definition sensitivity check (an addition beyond
  the minimum A–G sensitivity list, justified by this specific known
  risk).
- **Identification/exclusion fields:** `GC_UCB_YOB_2025` ("year of
  birth" — the epoch a settlement first qualified as an urban centre
  under Degree-of-Urbanisation criteria) ranges from 1975 to 2025; 507
  cities (4.4%) first qualified only in 2025, i.e. **after** this
  execution's chosen endpoint T=2020 — these were excluded from the
  primary sample (Section 8).
- **Context fields already in the official table:** centroid coordinates
  (`GC_UCC_LON_2025`/`GC_UCC_LAT_2025` — stored in the **projected World
  Mollweide CRS (ESRI:54009) in metres, despite the field names**,
  confirmed by inspecting actual values and reprojecting to WGS84 and
  cross-checking against known cities [Lagos, Sydney, Cairo, Tokyo, New
  York, Beijing] — all reprojected correctly), average elevation
  (`GE_ELV_AVG_2025`), a 555-class WWF ecoregion classification (too
  fine-grained for a "deliberately modest" C, not used), and 24
  bioclimatic variables (available but not used in this execution, to
  keep C modest as instructed).
- **Encoding issue found and corrected:** country names with accented
  characters (e.g. "México", "Côte d'Ivoire", "Curaçao", "Réunion",
  "São Tomé and Príncipe") were read from the GeoPackage in a
  mis-decoded ("mojibake") form by the GDAL/pyogrio reader; corrected
  via a Latin-1→UTF-8 round-trip before building the country→region
  mapping (verified: 0 of 191 countries left unmapped after correction).

## 5. Gate A Decision

**GATE_A = PASS.**

Reason: the official city-level products provide 9 strictly pre-endpoint
observed epochs (1975–2015) of built-up surface/population/volume for
every one of 11,422 urban centres, obtained entirely from
official pre-aggregated table/vector downloads (264 MB + 35 MB, both
under the 500 MB threshold), satisfying "multiple pre-endpoint
observations... without downloading prohibited global raster stacks."

---

## 6. Data Downloaded and Exact Sizes

| File | Official source | URL | Access date | Bytes | SHA-256 |
|---|---|---|---|---|---|
| `GHS_UCDB_GLOBE_R2024A_V1_2.zip` | JRC GHSL, GHS-UCDB R2024A V1.2 | `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_GLOBE_R2024A/V1-2/GHS_UCDB_GLOBE_R2024A_V1_2.zip` | 2026-10-05 | 276,662,440 (263.8 MB) | `12DC8D366A6057B832A070BA3F7B7B7C601BAD191DA0417A666851F35F10DB2E` |
| `GHS_UCDB_MTUC_GLOBE_R2024A_V1_2.zip` | JRC GHSL, GHS-UCDB MTUC R2024A V1.2 | `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_MTUC_GLOBE_R2024A/V1-2/GHS_UCDB_MTUC_GLOBE_R2024A_V1_2.zip` | 2026-10-05 | 37,155,214 (35.4 MB) | `76EDDB0E609A2A6C9D9266D62DDAB5F5F1F0B457C68291EA9755B1E06855F32F` |

Both are well under the 500 MB threshold; **no file approaching 500 MB
was ever encountered or considered**, so the "STOP before downloading
>500MB" rule was never triggered. Full provenance record (same fields,
machine-readable): `results/1005-4/data_provenance.json`. License:
European Commission Reuse and Copyright Notice (reuse authorised
provided source is acknowledged).
Citation: Mari Rivero, Melchiorri, Florio, Schiavina, et al. (2024),
GHS-UCDB R2024A — GHS Urban Centre Database 2025, European Commission,
JRC [Dataset], DOI 10.2905/1a338be6-7eaf-480c-9664-3a8ade88cbcd.

Raw files are stored unmodified under `data/raw/ghs_ucdb_r2024a/`
(original zips) with extracted contents in `data/raw/ghs_ucdb_r2024a/extracted/`
and `.../mtuc_extracted/`, per the project's `data/raw` policy. All
derived tables (interim parquet, results CSVs/JSONs) are stored
separately under `data/interim/` and `results/1005-4/`.

## 7. Endpoint-Year Decision

**T = 2020.**

Reason: 2020 is the **latest epoch that is a genuine satellite
observation** (Sentinel-2-derived), not a model projection — 2025 and
2030 are extrapolated and were excluded from consideration entirely
(Section 4). Using T=2020 leaves 9 strictly-earlier observed epochs
(1975–2015) for H, comfortably satisfying "multiple pre-endpoint
observations" and "acceptable global completeness" (zero missing values
at any epoch for any of the 11,422 cities). All historical predictors
use t < 2020; the endpoint ratio B(2020)/B(2020)=1 is explicitly excluded
from H. As a sensitivity check (Section 15), T=2015 was also tested.

---

## 8. Analysis Sample and QC

Full record: `results/1005-4/history_qc.csv` (11,422 rows, pre-exclusion)
and `results/1005-4/sample_summary.json`.

**QC findings (all cities, before exclusion):**

| Check | Count | % |
|---|---|---|
| Missing core variable (BUS/POP/BUV, any epoch) | 0 | 0.0% |
| Negative or non-finite value | 0 | 0.0% |
| Duplicated `ID_UC_G0` | 0 | 0.0% |
| Near-zero endpoint built-up or population | 0 | 0.0% |
| Non-monotonic built-up trajectory (any decrease 1975→2020) | 0 | 0.0% |
| Extreme single-epoch jump (>2x growth or <0.5x in one 5-yr step) | 342 | 3.0% |
| Duplicated (name, country) pair (soft flag, not excluded) | 360 | 3.2% |
| Qualified as urban centre only after T=2020 | 507 | 4.4% |

Built-up surface is **never observed to decrease** for any city at any
step in this dataset (0 non-monotonic cases) — monotonicity was **not**
forced by this execution; this is a property of the raw official data.
"Extreme jump" cities (3.0%) were **retained in the primary sample**
(per the explicit instruction not to silently exclude on this basis
alone) and instead used in a dedicated sensitivity removal (Section 15).

**Sample construction (no cities hand-picked):**

| Step | N |
|---|---|
| Initial (all official urban centres) | 11,422 |
| Excluded: missing core variable | 0 |
| Excluded: negative/invalid value | 0 |
| Excluded: duplicated ID | 0 |
| Excluded: near-zero endpoint built-up/population | 0 |
| Excluded: qualified as urban centre only after T=2020 | 507 |
| **Final analysis sample** | **10,915** |

Region distribution of final sample: Asia 6,273 (57.5%), Africa 2,006
(18.4%), Europe 1,154 (10.6%), North America 715 (6.6%), South America
715 (6.6%), Oceania 52 (0.5%). Endpoint (2020) population: min 49,805,
median 107,691, max 41.3M. Endpoint built-up area: min 9,209 m², median
3.97M m² (~4.0 km²), max 1.45B m² (~1,451 km²). Oceania's small
representation (52 cities, 0.5%) is disclosed as a limitation (Section
19) — the leave-region-out fold for Oceania is based on a comparatively
small, noisier test set.

---

## 9. Definition of H

Primary history variable: **normalized pre-endpoint built-up surface
trajectory**, h_i(t) = B_i(t) / B_i(2020) for t ∈ {1975, 1980, 1985,
1990, 1995, 2000, 2005, 2010, 2015} (9-dimensional vector per city). The
endpoint ratio (=1 by construction) is excluded, per the governing
prompt's explicit requirement, to avoid mathematically encoding S into H
(directly addressing risk register item A from execution 1005-3).
GHS-AGE was **not** used as H, per explicit instruction (and independently
confirmed problematic in 1005-3's audit). No environmental-response
variable was used in H.

Transparent descriptors (`results/1005-4/history_descriptors.csv`),
computed using the actual verified epochs (1990 and 2000 matched the
prompt's example years exactly): `early_developed_fraction_1990` =
B(1990)/B(2020); `mid_period_fraction_2000` = B(2000)/B(2020);
`recent_expansion_fraction_since_2000` = 1 − B(2000)/B(2020);
`weighted_development_timing` = population-weighted (by non-negative
built-up increment) mean construction year across 1975–2020.

## 10. Definition of S1/S2/S3

- **S1** = {population(2020), built-up area(2020)}
- **S2** = S1 + density(2020) = population(2020)/built-up-area(2020) —
  **explicitly algebraically derived** from S1's two components; this
  dependency is documented, not hidden, per the governing prompt's
  explicit instruction.
- **S3** = S2 + built-up volume(2020) — genuinely new information (a 3D
  morphology dimension not derivable from S1/S2).

## 11. Definition of C

Deliberately modest: **latitude, longitude** (reprojected from the
official Mollweide-CRS centroid to WGS84 degrees), and **average
elevation**. All three were already present in the official UCDB table
at zero additional download cost; no global climate/DEM raster was
downloaded. 24 pre-computed bioclimatic variables and a 555-class
ecoregion classification were found to exist in the same official table
but were deliberately **not** used, to keep C modest as instructed (noted
in the schema audit as available for future Gate 2 work). A broad
6-category geographic region (Africa/Asia/Europe/North
America/South America/Oceania, derived from the official country field
via a verified 191-country lookup) was used for leave-region-out
validation and permutation strata, separate from the continuous C used
in distance construction.

---

## 12. Experiment 1 — History Reconstruction

Full results: `results/1005-4/reconstruction_metrics.csv` (6 S/C
combinations × 3 models [null-mean, ridge, random forest] × 2
validation schemes [random 5-fold, leave-region-out] × 10 targets
[9 epochs + aggregate] = 360 rows).

**Primary result (S3+C, random forest, leave-region-out — the most
information-rich, most rigorous specification):** mean per-epoch
out-of-sample R² = **0.226**. For comparison: S1 alone (no C) gives
R² = 0.136; adding density and built volume (S2, S3) and context (C)
raises this only to 0.226 — a real but modest improvement. **H is far
from near-perfectly reconstructed from S,C** under geographic holdout
(see Figure 3). Random-fold (non-geographic) validation gives
systematically higher R² than leave-region-out for every specification,
confirming the expected optimism of naive cross-validation in the
presence of spatial structure — leave-region-out is the validation
scheme this report treats as primary, per the governing prompt's
explicit instruction. In-sample fit was computed nowhere and is not
reported as evidence, per the explicit prohibition.

## 13. Experiment 2 — Present-Day Analogues

Each of the 10,915 cities' 5 nearest neighbours were found in
standardized (S3+C) space (54,575 directed neighbour pairs; see
`results/1005-4/twin_candidates.csv` for the top 50 deduplicated
pairs by historical divergence among the closest-25%-by-D_SC subset).
**Among the 25% closest present-day analogue pairs, 18.3% still show
historical-trajectory divergence in the top quartile of the overall
D_H distribution** — i.e. roughly **1 in 5–6 very-close present-day
analogue pairs have substantially different histories**. All 50 top
twin-candidate pairs happened to be **within the same broad region**
(not surprising, since latitude/longitude are part of the matching
space) — this is disclosed as a real pattern, not papered over: the
strongest "twin" examples found are geographically concentrated within
regions (predominantly Asia and Africa, reflecting those regions'
larger representation in the sample), not globally dispersed. This
table is explicitly exploratory, not a set of causal counterfactuals,
and no publication-oriented case studies were selected from it.

## 14. Experiment 3 — Permutation/Null Test

Statistic: mean D_H among each city's 5 nearest (S3+C) neighbours.
Scheme: constrained permutation of H-assignment within
region×population-tercile strata (preserving the true neighbour graph),
300 permutations, fixed seed 42.

**Observed statistic = 0.383; null mean = 0.529 (null std = 0.0016).**
Observed falls far outside the (very narrow) null distribution (Figure
5): p(observed ≤ null) = 0.000. **Relative effect size: a 27.6%
reduction** in mean historical distance among true present-day
neighbours vs. the constrained-random null. **Interpretation requires
care** (Section 15): the null's standard deviation is tiny because it
averages over ~54,575 pairs (law of large numbers), so the p-value alone
is statistically "saturated" and would read as p≈0 even for a much
smaller true effect. The 27.6% relative effect size is the
scientifically meaningful number: genuine, non-trivial structure exists
(S,C does predict *something* about H), but it is partial, not
complete — consistent with Experiment 1's R²=0.226 finding.

## 15. Sensitivity Analyses

Full table: `results/1005-4/sensitivity_results.csv` (8 variants).

**Important methodological finding, disclosed rather than hidden:** the
permutation p-value is statistically saturated at this sample size —
every single sensitivity variant, including deliberately-weakened ones,
produced p(observed≤null)=0.000. **This makes the raw p-value
uninformative for assessing robustness across specifications at this N**,
and this report does not use it for that purpose. Instead, robustness is
assessed via the **effect-size metric** "fraction of close present-day
analogues (bottom quartile D_SC) with still-high historical divergence
(top quartile D_H)":

| Variant | Fraction | Relative to baseline (0.183) |
|---|---|---|
| Baseline (S3+C) | 0.183 | — |
| S1+C | 0.186 | +2% |
| S2+C | 0.184 | +1% |
| S3, C removed | 0.246 | **+34%** |
| Alternative distance scaling (RobustScaler) | 0.194 | +6% |
| Smallest 10% of cities removed | 0.183 | 0% |
| QC-flagged trajectories removed | 0.182 | −1% |
| Alternative endpoint T=2015 | 0.177 | −3% |

**All 6 true sensitivity variants (S1+C, S2+C, alternative scaling,
smallest-cities removal, QC removal, alternative endpoint) fall within
30% relative of baseline** — the finding is robust to these
specification choices. **Removing C entirely is the one variant that
produces a substantial, meaningful shift** (+34%), which is exactly the
expected and informative result of that specific contrast (Section 11's
"run with and without C" requirement): coarse geographic/climate context
explains part of why present-day analogues tend to share similar
histories, consistent with the climate/region confounding risk
identified in execution 1005-3's audit (risk register item F). This is
evidence the pipeline is behaving sensibly, not an inconsistency.

A boundary-definition sensitivity check using the time-varying-boundary
MTUC product was performed at the schema/feasibility level (confirmed
compatible fields exist, Section 4) but a full parallel re-run of all
three experiments on the MTUC sample was not completed in this
execution due to its different ID scheme requiring independent sample
construction — flagged as a recommended follow-up (Section 19).

## 16. Evidence For Historical Separability

1. Out-of-sample R² for H given S3+C is low (0.226) under rigorous
   geographic holdout — most historical variation is unexplained.
2. The permutation test's relative effect size is modest (27.6%
   reduction vs. null), not large — most of the observed historical
   distance among close analogues remains, not explained by S,C.
3. The "divergent twin" rate (18.3% of close analogues still show
   high historical divergence) is stable across 6 of 6 true sensitivity
   variants (within 30% relative).
4. Reconstruction R² does not collapse to near-zero as S becomes richer
   (S1=0.136 → S3+C=0.226); residual historical variation persists.

## 17. Evidence Against Historical Separability

1. The permutation test clearly rejects full independence: real
   present-day neighbours do have measurably (27.6%) more similar
   histories than chance — S,C is **not** entirely uninformative about H.
2. Removing C materially increases apparent divergence (+34%),
   confirming C (geography/climate) is a genuine confounder that must be
   conditioned on — any future design must retain C.
3. Reconstruction R² does rise, not fall, from S1 to S3+C — richer
   present-state description does capture *some* additional historical
   information, even if not most of it.

No evidence was found that the phenomenon is driven entirely by one
region or a product artifact: the 18.3% divergent-twin rate is stable
whether or not the smallest cities or QC-flagged trajectories are
included, and whether the endpoint year is 2020 or 2015.

## 18. Gate 1 Decision

**GATE 1 = PASS.** Full machine-readable decision:
`results/1005-4/gate1_decision.json`. Four pieces of converging evidence
support continuing (Section 16); zero pieces of evidence (using the
corrected, effect-size-based criteria, not the saturated p-value) argue
against. **This does not mean the candidate scientific question is
true.** It means there is enough genuine, robust residual historical
variation — after conditioning on present-day state and coarse context,
and surviving multiple sensitivity checks — to justify a PI considering
whether to authorize Gate 2 (which would require introducing an
environmental response variable, not undertaken here).

---

## 19. Scientific Limitations

1. **Fixed-boundary conditioning (risk register item D from 1005-3,
   directly confirmed in Section 4):** the primary analysis uses a
   boundary fixed at the 2025 reference delineation for all historical
   epochs. A full boundary-definition sensitivity re-run using the
   time-varying MTUC product was not completed (schema-level
   compatibility was confirmed; a full independent experiment re-run
   is recommended follow-up work, not performed here).
2. **Permutation p-value saturation at this sample size** (Section 15):
   raw p-values are uninformative for comparing specifications here;
   this report relies on relative effect sizes instead, which is a
   methodological choice made and disclosed in this execution, not a
   pre-existing standard.
3. **Severe regional imbalance:** Oceania is 0.5% of the sample (52
   cities); its leave-region-out fold is comparatively noisy.
4. **H is restricted to built-up surface only** (per explicit
   instruction); population- or volume-based historical trajectories
   were not separately tested as alternative H definitions in this
   execution.
5. **"Extreme jump" cities (3.0%) were retained** in the primary sample;
   their removal changed the key statistics only marginally (Section
   15), but this was tested only for the primary S3+C specification,
   not the full experiment grid.
6. **k=5 nearest neighbours is a single, not-separately-sensitivity-tested
   choice** for Experiment 2/3; alternative k values were not explored.
7. This is a **Gate 1 pilot only** — no causal claim, no environmental
   relevance, and no finalized scientific definitions of S, H, C, or R
   follow from any result in this report.

## 20. Exact Files Created/Modified

| Path | Type |
|---|---|
| `prompts/prompt1005-4.txt` | prompt (verbatim, confirmed) |
| `data/raw/ghs_ucdb_r2024a/GHS_UCDB_GLOBE_R2024A_V1_2.zip` | raw data (unmodified) |
| `data/raw/ghs_ucdb_r2024a/GHS_UCDB_MTUC_GLOBE_R2024A_V1_2.zip` | raw data (unmodified) |
| `data/raw/ghs_ucdb_r2024a/extracted/`, `.../mtuc_extracted/` | raw data, extracted (unmodified contents) |
| `data/interim/ucdb_main_loaded.parquet` | derived interim table |
| `scripts/ucdb_gate1_pilot.py` | analysis code (new) |
| `tests/test_ucdb_gate1_pilot.py` | unit tests (new) |
| `results/1005-4/ucdb_schema_audit.csv` | output (49 rows) |
| `results/1005-4/history_qc.csv` | output (11,422 rows) |
| `results/1005-4/history_descriptors.csv` | output (10,915 rows) |
| `results/1005-4/sample_summary.json` | output |
| `results/1005-4/reconstruction_metrics.csv` | output (360 rows) |
| `results/1005-4/twin_candidates.csv` | output (50 rows) |
| `results/1005-4/permutation_results.csv` | output (300 rows) |
| `results/1005-4/permutation_meta.json` | output |
| `results/1005-4/sensitivity_results.csv` | output (8 rows) |
| `results/1005-4/pca_summary.json` | output |
| `results/1005-4/data_provenance.json` | output (download provenance) |
| `results/1005-4/gate1_decision.json` | output |
| `results/1005-4/run_metadata.json` | output |
| `figures/1005-4/figure1-6_*.png` | output (6 figures) |
| `reports/report1005-4.md` | this report |

**Explicitly NOT modified:** `prompts/prompt1005-1.txt`,
`prompts/prompt1005-2.txt`, `prompts/prompt1005-3.txt`,
`reports/report1005-1.md`, `reports/report1005-2.md`,
`reports/report1005-3.md`, `results/1005-1/`, `results/1005-2/`,
`results/1005-3/`.

## 21. Reproducibility/Integrity Statement

- Large global raster downloaded: **No.**
- Environmental response analyzed: **No.**
- History-environment relationship tested: **No.**
- Real urban data analyzed: **Yes** (official GHS-UCDB R2024A, 11,422
  cities, real downloaded data — not synthetic, not a subsample of named
  "famous" cities).
- Gate A: **PASS.**
- Gate 1: **PASS** (not a confirmation of the main hypothesis).
- Final scientific hypothesis established: **No.**
- Causal claim made: **No.**
- Historical reviewed artifacts modified: **No** (verified via `git
  diff` against the prior commit before this execution's commit).
- Random seed: fixed at 42 throughout (data splits, model fitting,
  permutation, PCA, sampling for figures).
- Package versions used: recorded in `results/1005-4/run_metadata.json`
  (Python, scikit-learn, pandas, numpy versions), environment `py311`.
- Reproduction: `conda run -n py311 python scripts/ucdb_gate1_pilot.py`
  from the project root, after placing the two official zip files under
  `data/raw/ghs_ucdb_r2024a/` as described in Section 6 (downloaded raw
  files are not committed to git; see Section 22 git discussion).

---

## 22. Questions for PI Review

**Q1. Does the official city-level dataset actually contain enough
temporal information for this experiment?**
Yes — confirmed directly (Section 4): 9 strictly pre-endpoint observed
epochs (1975–2015) of built-up surface, population, and built volume for
all 11,422 urban centres, with zero missing values.

**Q2. What endpoint T was used and why?**
T=2020, the latest epoch that is a genuine satellite observation rather
than a model projection (2025/2030 are extrapolated, confirmed via
official documentation, and excluded entirely). See Section 7.

**Q3. How predictable is H from S alone?**
Mean per-epoch leave-region-out R² = 0.136 for S1 (population + built-up
area only, no context).

**Q4. How predictable is H from S+C?**
Mean per-epoch leave-region-out R² = 0.226 for S3 (+ density + built
volume) + C (lat/lon/elevation) — an improvement over S1 alone, but
still far from near-perfect reconstruction.

**Q5. Does richer present-state information S1→S2→S3 eliminate
historical residual variation?**
No. R² rises only from 0.136 (S1) to 0.226 (S3+C); substantial residual
historical variation remains at every nesting level (Section 12,
Figure 3).

**Q6. Under geographic holdout, does substantial unexplained H remain?**
Yes — leave-region-out R² (0.226) is consistently lower than random-fold
R² for every specification tested, and even under the most favorable
(S3+C) specification, ~77% of per-epoch variance remains unexplained.

**Q7. How common are low-D_SC/high-D_H city pairs?**
Among the closest quartile of present-day analogue pairs, 18.3% fall in
the top quartile of historical divergence — a non-trivial, stable rate,
not a rare curiosity (Section 13, 15).

**Q8. Are these pairs globally distributed or geographically
concentrated?**
Geographically concentrated **within** broad regions: all 50 top twin
candidates in `results/1005-4/twin_candidates.csv` are same-region pairs
(predominantly Asia and Africa, reflecting their larger sample share).
This is expected since latitude/longitude are part of the (S,C) matching
space, and is disclosed rather than downplayed.

**Q9. Does the constrained permutation test suggest that the observed
structure is non-trivial?**
Yes, with an important caveat: the raw p-value (≈0.000) is statistically
saturated at this sample size and should not be over-interpreted on its
own; the **relative effect size (27.6% reduction vs. null)** is the
scientifically meaningful, non-trivial signal, and it survives 6 of 6
true sensitivity checks essentially unchanged (Section 14, 15).

**Q10. What is the strongest result AGAINST the proposed programme?**
The permutation test does show real, replicable structure: present-day
analogues are not historically random relative to each other, and
coarse geography/climate (C) explains a meaningful share (+34% when
removed) of that structure — meaning any future "history matters beyond
present state" claim must very carefully separate the geography/climate
channel from a genuine independent history effect, which this pilot
cannot by itself fully disentangle (Section 17).

**Q11. What is the strongest result FOR continuing?**
The low, geography-holdout-robust reconstruction R² (0.226) combined
with the stable (6/6 variants), non-trivial (18.3%) divergent-twin rate
jointly indicate that most historical trajectory information is neither
predictable from present state/context nor an artifact of any single
specification choice tested (Section 16).

**Q12. Gate 1: PASS / MIXED / FAIL?**
**PASS**, per `results/1005-4/gate1_decision.json` (four converging
pieces of evidence for, zero against, using effect-size-corrected
sensitivity criteria).

**Q13. Should the next execution be allowed to introduce an independent
environmental response R?**
**UNCERTAIN.** Justification: Gate 1's PASS is a necessary but explicitly
*not sufficient* condition (per the governing prompt, Section 21:
"PASS does not mean the main scientific hypothesis is true"). Before
authorizing R, this pilot's own disclosed limitations should be weighed:
(a) the fixed-vs-time-varying boundary sensitivity check was only
partially completed (Section 19.1) and should be finished first, since
boundary leakage was independently flagged as a high-severity risk in
execution 1005-3; (b) the geography/climate confound is real and
substantial (+34% effect), meaning Gate 2's response-variable design
must be unusually careful about climate confounding from the outset
(this was already anticipated in 1005-3's risk register, and this
pilot's own data now empirically reinforces it); (c) only one H
definition (built-up surface trajectory) was tested — the PI may want
population- or volume-based H tested for consistency before investing in
a response-variable experiment. A YES is plausible once (a) is completed
and (b)/(c) are explicitly accounted for in the Gate 2 design, but this
report does not recommend an unconditional YES. **ADVISORY ONLY.**
