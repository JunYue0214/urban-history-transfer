# Gate 2 Pre-registration (execution 1005-6, Gate 2A)

Status: **PROVISIONAL**. Written before any thermal-response data were seen or
downloaded. Parameters marked `[SCHEMA-DEPENDENT]` may be adjusted ONLY to
match the verified file schema (never in response to values of R), and every
such change must be logged in a dated amendment appended to this file before
the first look at R.

Framing: observational global comparative science. No causal claim is made.
Allowed claim: "R carries (or does not carry) out-of-sample predictive
information associated with H beyond S and C." Forbidden: "history causes
heat", "history has a causal effect on SUHI".

## 0. Variables

| Symbol | Definition (locked unless marked) |
|---|---|
| S | Gate 1 S3 at 2020: population, built-up area, built-up volume, plus the algebraically derived density. S1 (pop, built-up) and S2 (+density) are reported as an overcontrol gradient because built volume may mediate H. |
| H (primary) | Gate 1 fixed-boundary history h_i(t)=GH_BUS_TOT_i(t)/GH_BUS_TOT_i(2020), t in {1975..2015} (9-vector); endpoint ratio excluded. |
| C | Nested, see section 3. |
| R (primary) | Annual-mean nighttime SUHI climatology, mean over 2003-2018, degC, from YCEO SUHI v4 city(cluster)-level file. |
| R (secondary) | Summer (warm-season) daytime SUHI climatology, 2003-2018. |
| Contrast | None locked. Optional exploratory trend outcome, never confirmatory. |

R is analysed in native degC. No transformation, no outlier deletion; negative
SUHI values are valid. Missing R rows are dropped and counted; cities are
never dropped on the basis of R values.

## 1. Why this R (and not the others)

Primary = annual nighttime. Daytime SUHI is dominated by evapotranspiration,
rural-reference moisture/vegetation and solar geometry, and its sign flips in
arid cities, so a daytime primary would mostly re-test the climate controls.
Nighttime SUHI reflects heat storage and urban form with less rural-reference
moisture dependence and fewer cloud/solar retrieval artifacts. Annual
aggregation avoids the hemisphere/tropical season-definition ambiguity of
"summer". The choice was made for interpretability, not expected effect size.
Raw urban LST, interannual variability, trend and extreme metrics were
rejected or demoted (thermal_candidate_audit.csv).

## 2. Temporal design

* Response window 2003-2018 is fixed by the product (no post-2018 option exists
  in the verified primary source). Option A (response after T=2020) and
  option C (response before all H) are impossible with this product.
* The window overlaps H epochs 2005, 2010, 2015 and precedes S(2020). This is
  option D/E: a long period overlapping H.
* Consequence: Gate 2 supports **predictive association and transferability**
  only. Reverse pathways (hot cities developing differently) cannot be
  excluded. No "legacy" or temporal-ordering claim is permitted from the
  primary analysis.
* Strict-precedence sensitivity (pre-registered, section 7 test 10): H
  truncated at t<=2000 and rebased as B(t)/B(2000), t in {1975..1995}; and the
  T=2015 variant (S at 2015, H=B(t)/B(2015), t<=2010, already used as the
  Gate 1B alternate endpoint). A positive result that survives only the
  overlapping specification is reported as association, not legacy.
* If the PI later authorizes a post-2018 product (e.g. a Yang 2024 city table
  reaching 2020), the pre-registered primary stays 2003-2018 for comparability.

## 3. Context C (nested; existing UCDB fields only, no new raster)

| Level | Variables | Role |
|---|---|---|
| C0 | latitude, longitude (WGS84), GE_ELV_AVG_2025 | geography (Gate 1 C) |
| C1 | C0 + decadal-mean annual mean temperature (mean of CL_B01_CUR_2000 and CL_B01_CUR_2010) + log of decadal-mean annual precipitation (CL_B12) | thermal background and aridity/moisture |
| C2 | C1 + mean temperature seasonality (CL_B04) + mean precipitation seasonality (CL_B15) + Koppen-Geiger major group (first letter of CL_KOP_CUR_2025, 5 classes) | seasonality and regime |

* Source: UCDB R2024A climate theme; CL_B* are C3S reanalysis bioclimatic
  indicators (Wouters 2021, DOI 10.24381/cds.bce175f0) per the official data
  dictionary; columns exist for all 11,422 cities (verified locally in
  1005-6: no missing values for CL_B01/B04/B07/B12/B15; Koppen missing for 3).
  The exact decade boundaries behind the 2000/2010 values must be confirmed in
  the data dictionary before analysis [SCHEMA-DEPENDENT].
* Primary M0/M1 use **C1**. C0 and C2 are reported (test 6).
* NOT used: all 24 bioclim variables; CL_WDS (warm-day percentage; derivation
  from reanalysis vs CMIP6 is ambiguous in the dictionary text, so excluded
  unless clarified); CL_B07 (collinear with B04).

Confounders (to be controlled): latitude/solar geometry, elevation, background
temperature, aridity/precipitation, seasonality, climate regime, urban size
(in S). Possible mediators (NOT controlled in primary): urban greenness
(GR_AVG_GRN_*, GR_SQM_*, GR_SHB_*), tree height (GR_CTH_*), land-use/land-cover
fractions (LU_HEC_*), built-up volume beyond S2 (handled by the S gradient).
Socioeconomic classes (GC_DEV_*) are proxies for development and are excluded
from C; an exploratory variant may add them but is labelled non-primary.
Unmeasured: distance to coast, humidity, wind, rural-reference vegetation.

## 4. H design

Decision: **A+D** - fixed-boundary H as primary on the full matched sample,
dynamic-boundary H as sensitivity, plus boundary-robust coarse descriptors.

Reasons: (i) fixed H is available for all 10,915 Gate 1 cities with zero
missingness and no 1975 survival filter, while dynamic H complete-history
sampling (N=4,739) over-represents cities already established by 1975 and
contains no YOB>1990 cities; (ii) YCEO's urban extents are fixed (Landscan),
so a fixed-boundary H/S is the geometrically consistent partner of a
fixed-extent R; (iii) 1005-5 showed H_fixed and H_dynamic agree strongly
(mean r=0.89) and that Gate 1 did not depend on boundary choice.
Sensitivities: (a) H_dynamic (MTUC) on the 4,739-city overlap, run with the
same models, compared against H_fixed on the identical subsample; (b) coarse
boundary-robust descriptors (early_developed_fraction_1990, mid_period_fraction_2000,
weighted_development_timing) in place of the 9-vector. Recently urbanized
cities (YOB>1975) stay in the primary sample and are reported as a stratum
(test 12); no interpolation of dynamic-boundary missing history is allowed.

## 5. Analysis sample

Gate 1 sample (N=10,915; YOB<=2020) intersected with accepted crosswalk
matches (crosswalk_design.md) with non-missing R. Sample-flow table and
matched-vs-unmatched balance (region, size, climate, YOB) are reported first.
If fewer than 3,000 cities or fewer than 5 of 6 regions with N>=30 remain, the
primary claim is downgraded to "underpowered" before any model is fit.

## 6. Experiments

Common rules: seed 42; learner = random forest (500 trees, min_samples_leaf=5,
max_features=0.5, no tuning on test folds) with a ridge/elastic-net linear
learner as secondary check; M0 and M1 use identical learners and identical
folds; features standardized inside training folds only; all inputs of the
held-out fold withheld from fitting.

### Experiment 1 - incremental predictive information

* M0: R ~ S + C1. M1: R ~ S + C1 + H (9-vector).
* Primary validation: leave-region-out over the 6 Gate 1 regions; stronger
  check: leave-continent-out is identical here, so additionally spatially
  blocked K-fold (10 degree tiles, 5 folds) is reported.
* Primary metric: pooled out-of-fold R^2 (every city weighted equally) and
  ΔR^2 = R^2(M1) - R^2(M0). Secondary: ΔRMSE, ΔMAE, per-region Δ.
* Uncertainty: spatial block bootstrap (10 degree tiles, 2000 resamples),
  95% percentile CI for Δ.
* Null reference for Δ (does not replace the primary test): Δ_null from M1
  with H shuffled within region x size-tercile x climate (Koppen major group)
  strata, 500 shuffles.
* In-sample improvement is never evidence.

### Experiment 2 - present-day twin environmental divergence

* D_SC: Euclidean distance on standardized S3(log) + C1. Twin graph:
  mutual k-nearest-neighbour pairs, k=10, with an additional minimum
  geographic separation of 200 km to limit shared-rural-context pairs
  (an unrestricted version is the sensitivity). D_H: Euclidean distance
  between 9-vector histories. D_R: |R_i - R_j|.
* Primary statistic: partial Spearman correlation rho(D_R, D_H | D_SC, D_geo)
  over twin pairs. Secondary: median D_R in the top vs bottom tercile of D_H
  among twins.
* Inference: pairs are not independent; use city-level cluster bootstrap and a
  Mantel-style permutation (H permuted within the same strata as Exp 1, 1000
  permutations). Hand-picked twin examples are illustrative only and not
  evidence.

### Experiment 3 - history-aware transferability

* For each target city, donors come from other regions only (leave-region-out
  donor pool). A0: K=10 nearest donors in S3+C1 space; A1: nearest donors in
  S3+C1+H, with each block (S, C, H) scaled to equal total variance so that H
  has no unfair weight. Prediction = inverse-distance-weighted donor mean of R.
* Primary metric: ΔRMSE_transfer = RMSE(A0) - RMSE(A1) pooled over targets
  (positive = history helps). Per-region and per-city paired differences
  reported; block bootstrap CI.
* Null analogue test: A1 recomputed with H shuffled within strata (500
  shuffles) and with a random 9-vector of matched variance; observed ΔRMSE
  must exceed the 95th percentile of these nulls.
* Within-region donor pools are a secondary variant (expected easier; shows
  how much of any gain is regional).

## 7. Falsification tests (all 14; each states what counts AGAINST)

| # | Test | Counts AGAINST the hypothesis if |
|---|---|---|
| 1 | H shuffled within region x size x climate strata | ΔR^2_obs lies within the 95th percentile of the shuffled-Δ null |
| 2 | Pseudo-history from S: H_hat = leave-region-out prediction of H from S3+C1 (Gate 1 reconstruction), used in place of H | Δ with H_hat is >= 80% of Δ with real H (gain is nonlinear S, not history) |
| 3 | Redundant history: add 9 features that are deterministic functions of S (powers/ratios), matched dimension | Δ from redundant features >= Δ from real H |
| 4 | Random-fold vs geographic-holdout | Δ positive under random folds but <= 0.005 under geographic holdout (spatial leakage, not information) |
| 5 | Leave-region-out and leave-continent-out robustness | Δ <= 0 in at least 4 of 6 held-out regions |
| 6 | Alternate climate-control sets C0, C1, C2 | Δ shrinks to <= 0.005 under C2 (history gain was unmodelled climate) |
| 7 | Alternate H boundary definition (MTUC on the 4,739 subsample, same models) | H_dynamic Δ <= 0 while H_fixed Δ on the identical subsample is positive |
| 8 | Alternate outcome (secondary R: summer daytime) | Primary and secondary Δ have opposite sign, or the primary Δ is carried only by one outcome with no physical rationale |
| 9 | Alternate rural reference (Yang 2024 DEA, only if a city table is confirmed) | Sign/size of Δ not reproduced with DEA-based nighttime SUHI (rank-correlation of the two R <0.5 downgrades to INCONCLUSIVE) |
| 10 | Temporal-window sensitivity: H<=2000 rebased; T=2015 endpoint | Δ present only with the overlapping H (epochs 2005-2015) and absent with H<=2000 -> "recent-growth association", not legacy |
| 11 | City-size sensitivity (terciles, and S-matched trimming) | Δ confined to the largest-size tercile or vanishes after size trimming |
| 12 | Recently urbanized vs long-established strata | Δ exists only in recently urbanized cities (partly definitional) |
| 13 | Spatial-autocorrelation-aware uncertainty (block bootstrap) | 95% block-bootstrap CI for Δ includes 0 |
| 14 | Null analogue-transfer test (Exp 3) | ΔRMSE_transfer within the shuffled/random-H null range |

Every test is run for the primary R and reported even if favourable results
make it unnecessary.

## 8. Decision rules (fixed in advance)

Thresholds below are judgment-based minimum-effect choices fixed BEFORE R is
seen; the PI may revise them in a dated amendment before data are opened.

**Strong evidence FOR incremental historical information** requires ALL of:
1. ΔR^2 >= +0.02 (pooled, leave-region-out, C1) with 95% spatial-block
   bootstrap CI excluding 0;
2. Δ_obs above the 95th percentile of the shuffled-H null (test 1);
3. Δ>0 in at least 4 of 6 held-out regions (test 5);
4. Δ with real H exceeds Δ with H_hat and with redundant features by a margin
   (tests 2-3), i.e. at least 20% of Δ_real remains beyond the pseudo-history;
5. same sign and >= half the size under C2 (test 6) and under H<=2000 (test 10);
6. Exp 3 ΔRMSE_transfer>0 and above its null 95th percentile; Exp 2 partial
   rho >= 0.05 with permutation p<0.01.

**Evidence AGAINST** if ANY of: ΔR^2 < 0.005 with CI including 0; Δ within the
shuffled null; Δ explained by pseudo-history/redundant features (tests 2-3);
Δ negative in >= 4 regions; collapse under C2; Exp 2 partial rho <= 0.02 and
Exp 3 ΔRMSE_transfer within null.

**MIXED/INCONCLUSIVE**: anything else, reported as such. Results are
interpreted as predictive association (temporal overlap), never as causation.

## 9. Multiplicity

One primary outcome, one primary model contrast (Exp 1 ΔR^2), one primary twin
statistic, one primary transfer statistic. Everything else is a pre-registered
robustness check reported in full; no outcome-switching. The three experiments
are jointly interpreted under the rules in section 8, not selected post hoc.

## 10. Amendment log

(empty at lock; schema-dependent adjustments to be appended here with date and
reason before R is opened)
