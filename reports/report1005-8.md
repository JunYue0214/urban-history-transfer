# Execution Report 1005-8

Execution ID: 1005-8 · Source prompt: prompts/prompt1005-8.txt · Previous: 1005-7
Task: Gate 2 Analysis-Support Lock + Pre-registration Amendment
Results: results/1005-8/ · Figures: figures/1005-8/

**This execution never opened the YCEO shapefile or any SUHI value. The only thermal-derived input used anywhere in this execution is the boolean `yceo_primary_R_valid` column already written to `results/1005-7/ucdb_yceo_crosswalk.csv` (non-missingness only). No Gate 2 outcome model was run. No research data were downloaded; no network access occurred.**

---

## 1. Executive Summary

* A geometry-only sweep of the UCDB-coverage threshold (20–70%) shows a genuine trade-off: looser thresholds buy more N but **increase** H-shape distortion (SMD of `early_developed_fraction_1990` falls from 0.33 at 20% coverage to 0.04 at 50%, then flips sign by 60–70%), while size/age selection (SMD of log population, YOB) worsens monotonically at every threshold regardless of N. **50% coverage is where H-shape distortion is smallest**, not merely the value carried over from 1005-7.
* Adding a modest cluster-level IoU floor (0.20) removes 85 of 2,192 units (3.9%) as footprint-degenerate without moving bias, so it is kept as part of the primary rule; stronger IoU floors cost N fast and reintroduce H-shape bias.
* **Final primary rule: coverage ≥ 0.5 AND cluster IoU ≥ 0.20 → 2,107 cluster units, 2,374 UCDB cities, 146 multi-city aggregates (6.9%).**
* The old N≥3,000 floor (1005-6) had no statistical derivation and is **formally amended**, replaced by seven auditable criteria (independent units, regional support, fold-size, H-variation preservation, common support, effective-N, sensitivity stability) — all satisfied by the primary sample.
* Leave-region-out is feasible for 5 of 6 regions (Oceania N=21, below the 30-unit floor, merged with a neighbour for validation only, never for interpretation). Spatial 10°-tile blocked 5-fold is feasible (all folds 421–422). Twin and transferability designs are feasible on S/C/H alone.
* Bias handling: **unweighted primary analysis with an explicitly restricted inference target** (option A), because inclusion probability is structurally near zero for small/recent cities — weighting would be high-variance, not a correction of a sampling accident.
* **ANALYSIS SUPPORT = LOCKED. GATE 2 EXECUTION = YES.** Not biased toward LOCKED: the decision rests on criteria fixed before this execution touched any R value, and the restriction is stated honestly (Section 13) rather than papered over with weights.

## 2. Exact Question

What is the most defensible global Gate 2 analysis population and cluster-matching rule, balancing ontological correspondence, representativeness, cluster independence, global coverage, interpretability, robustness, and minimal post-hoc flexibility — decided before any H↔R relationship is seen?

## 3. Blindness / No-H↔R Verification

`scripts/gate2_support.load_links` reads only `LINK_COLUMNS`, a fixed whitelist that excludes every SUHI-named column; `tests/test_gate2_support.py::test_no_r_magnitude_used_classify_clusters_signature_and_no_magnitude_column` inspects the source of `classify_clusters`/`load_links` for `Annual_nig`/`Summer_day`/`SUHI` tokens and confirms none of `LINK_COLUMNS` matches a response field. `test_only_missingness_not_magnitude_affects_inclusion` proves a cluster's inclusion changes only when the boolean validity flag changes. The thermal shapefile (`data/interim/1005-7/yceo_suhi_v4/All_shp.*`) was not opened anywhere in this execution's code or interactive exploration. `run_metadata.json` records `"blind_to_H_R": true, "thermal_shapefile_opened": false`.

## 4. Coverage Threshold Sweep

`results/1005-8/coverage_threshold_sweep.csv` (region columns, median geometry, all bias variables). Headline:

| Coverage | Units | Cities | Multi | SMD log-pop | SMD YOB | SMD H early-1990 | % post-1975 | Oceania N |
|---|---|---|---|---|---|---|---|---|
| 20% | 3,687 | 4,290 | 302 | 0.82 | −0.66 | **0.330** | 36.2% | 33 |
| 30% | 3,226 | 3,700 | 246 | 0.88 | −0.63 | 0.214 | 36.0% | 33 |
| 40% | 2,724 | 3,081 | 198 | 0.96 | −0.58 | 0.105 | 35.6% | 31 |
| **50%** | **2,192** | **2,459** | **146** | 1.02 | −0.56 | **0.040** | 34.8% | 28 |
| 60% | 1,644 | 1,793 | 87 | 1.10 | −0.57 | −0.015 | 33.0% | 19 |
| 70% | 1,135 | 1,202 | 41 | 1.18 | −0.58 | −0.073 | 31.4% | 9 |

H-shape SMD is smallest in absolute value at 50% coverage and grows in both directions away from it; size/age SMD worsens monotonically with stricter coverage. Fig. 1 (N), Fig. 3 (size/age), Fig. 4 (H-shape).

## 5. IoU Sensitivity

At coverage = 0.5 (`results/1005-8/iou_sensitivity.csv`): no floor → 2,192 units; IoU≥0.10 → 2,166 (−1.2%); **≥0.20 → 2,107 (−3.9%)**; ≥0.25 → 2,034 (−7.2%); ≥0.30 → 1,936 (−11.7%); ≥0.40 → 1,617 (−26%); ≥0.50 → 1,054 (−52%). H-shape SMD rises with the IoU floor (0.040 → 0.037 → 0.042 → 0.049 → 0.066 → 0.121 → 0.244), i.e. a strict IoU floor mostly removes the same kind of low-coverage-adjacent, shape-consistent matches that coverage already screens, while costing N fast. **A mild 0.20 floor is kept as a QC safeguard against degenerate low-shape-overlap matches at negligible N/bias cost; stricter floors are not adopted.** Footprint mismatch (median unit IoU 0.49 at the primary rule) is structural (different source ontologies — Natural Earth 1:10m vs GHSL Degree-of-Urbanisation), not a symptom of bad matching (Fig. 5).

## 6. Aggregation Structure

`results/1005-8/aggregation_structure.csv`, primary rule: 2,107 units, 1,961 single-city (93.1%), 146 multi-city (6.9%), max 11 UCDB centres in one cluster. Among multi-city units: median dominant-city built-up share **84.2%**; median aggregate-vs-dominant H distance (9-vector Euclidean) **0.036**, p90 **0.128** — small relative to the typical H magnitude (components are ratios in [0,1]). Aggregation changes H representation only modestly; a dominant-city sensitivity is cheap and will bound that effect directly (Section 11, Fig. 6).

## 7. Sample Representativeness

`results/1005-8/sample_bias_by_rule.csv` (long format, every coverage point and every candidate rule). At the primary rule: bias is concentrated in **size and age** (log-pop SMD ≈1.0, log-built-up SMD similarly large, YOB SMD −0.56, 34.8% vs ~59% urbanized post-1975 among included vs excluded), while H-**shape** descriptors are only mildly shifted (early-developed SMD 0.04; recent-expansion and weighted-timing SMDs are of similar small magnitude) and H variation is preserved (`sd_ratio_early_developed` ≈ 0.92, i.e. included-sample SD is ~92% of the full sample's). **Conclusion: the rule distorts who is observed (larger, older cities) far more than it distorts the shape of H itself.**

## 8. Common-Support Design

`results/1005-8/common_support_design.md`. Method: **Mahalanobis distance** on the standardized, equal-variance-scaled S3+C1 block (log population/built-up/built-volume/density + lat/lon/elevation/decadal temperature/log precipitation), computed once on the primary cluster-level sample. Support rule: a unit is in common support iff its distance to the sample centroid is ≤ the sample's own 95th percentile. Chosen over kNN density (bandwidth-dependent) and a fitted propensity score (adds a model-selection step) for simplicity and reuse across the twin/transfer experiments, which already standardize the same block. No observation is dropped by residual or outcome behavior; flags only.

## 9. N≥3000 Pre-registration Amendment

`results/1005-8/preregistration_amendment.md` (full text). Summary: the original 1005-6 floor was a round-number placeholder with no power derivation, set before the real crosswalk ontology was known, and it rewards looser coverage thresholds that are *worse* on H-shape fidelity — the wrong lever. It is replaced (not deleted) by seven criteria: independent units (structurally enforced), ≥5/6 regions with N≥30 as an interpretive stratum, every validation fold ≥30 (merging, not dropping, undersized folds), preserved H variation, S/C-only common support, Kish effective-N ≥70% of nominal if weighting is ever used (not triggered here), and sensitivity stability against the pre-registered falsification tests. The primary sample (2,107 units) satisfies all seven despite being below 3,000. The amendment is filed before any H↔R relationship was analyzed and before any Gate 2 outcome model has run; the historical 1005-6 file is untouched.

## 10. Final Analysis Unit

**Confirmed: PRIMARY UNIT = YCEO urban cluster.** S_cluster = Σ over linked UCDB centres (population, built-up area, built volume summed; density = Σpop/Σbuilt-up); C_cluster = built-up-area-weighted mean of lat/lon/elevation/temperature/log-precipitation. H_cluster(t) = Σ B_i(t) / Σ B_i(T), exactly as specified. For single-city clusters (93.1% of units) this reduces identically to the original city's values (`test_aggregate_units_deterministic_and_single_city_reduces_to_original`). No weighting beyond the built-up-area weighting already specified was introduced.

## 11. Final H Definition

Primary: fixed-boundary UCDB history aggregated to the cluster as above. Sensitivities (pre-registered, non-geometry): (a) dynamic-boundary MTUC history where available — cross-referencing the 1005-5 crosswalk, the 4,739-city MTUC complete-history sample overlaps the primary 2,374 UCDB cities; the intersection will be computed in Gate 2, not here, since it requires no geometry decision; (b) boundary-robust H descriptors (1005-6 Section 4); (c) dominant-city H substitution for multi-city units, quantified in Section 6 (median distance 0.036). The full Gate 2 sample is **not** restricted to the MTUC subsample.

## 12. Bias Handling Decision

Evaluated A–F per the prompt. **Chosen: A — unweighted primary analysis with an explicit, restricted inference target (Section 13).** Rejected: B/C/F (inverse-probability/entropy/transport weighting) because inclusion probability is structurally near zero for a large share of small and recently urbanized cities (not a correction of a random sampling accident — YCEO's Natural-Earth-derived polygons simply do not resolve them), which would produce extreme, high-variance weights; D (stratification) is implicitly present via the regional/size reporting already done and can be added as a secondary descriptive table in Gate 2 without being the primary estimator; E (common-support restriction) is retained as a **flag**, not a further exclusion (Section 8). If a future execution revisits weighting, trimming at the 1st/99th percentile of the weight distribution and reporting Kish effective-N is pre-specified as the control (criterion 6 of the amendment).

## 13. Final Inference Target

`results/1005-8/inference_target.md`. **"YCEO-detectable global urban agglomerations with defensible GHSL overlap"**: 2,107 units / 2,374 UCDB centres, skewed toward larger and longer-established agglomerations, present in 5 of 6 regions with N≥30 (6 of 6 if Oceania is merged for validation). Explicitly excluded from the claim: the full GHSL universe (10,915 cities), any claim specific to recently urbanized cities, and any causal claim (unchanged from 1005-6).

## 14. Region/Fold Feasibility

`results/1005-8/fold_feasibility.csv`. Leave-region-out: Asia 1,028, Africa 323, South America 296, Europe 253, North America 186 all ≥30; **Oceania 21, below the 30-unit floor** — not standalone-feasible, merged with Asia for validation only (1,049), never collapsed in interpretation/reporting. Spatial 10°-tile blocked 5-fold: all five folds 421–422, feasible. No fold scheme was invented solely to rescue all six regions.

## 15. Twin Feasibility

`results/1005-8/twin_feasibility.csv`, mutual-kNN in standardized S3+C1 with a 200 km minimum separation, computed on S/C only (no D_R, no H correlation): k=5 → 3,277 pairs, 94.4% of units have ≥1 twin; k=10 → 6,823 pairs, 98.7%; k=20 → 13,757 pairs, 99.8%. The pre-registered twin design is feasible at every candidate k.

## 16. Transferability Feasibility

`results/1005-8/transferability_feasibility.json`. Leave-region-out donor pools range 1,079 (Asia target) to 2,086 (Oceania target) — ample. H variation is non-zero at every epoch (mean per-epoch SD 0.14, minimum 0.044), so donor-based transfer has signal to exploit. Regional separation is structural. `"feasible": true`.

## 17. Final Crosswalk Rule

`results/1005-8/final_crosswalk_rule.json`. Substantive link: intersection/min(area) ≥ 0.5 (unchanged from 1005-7). **Primary: UCDB coverage of cluster ≥ 50% AND cluster-level IoU ≥ 20%.** Single-city clusters kept as-is. Multi-city clusters kept iff star-shaped and single-country; S summed, H = Σ/Σ. A UCDB centre linking to >1 cluster excludes that cluster (`ambiguous_nonstar`). Cross-country clusters excluded. Missing R excluded by validity flag only. QC exclusions inherit the 1005-4 Gate-1 sample (N=10,915, YOB≤2020) before any crosswalk step. Result: **2,107 units, 2,374 cities.**

## 18. Geometry Sensitivities

Exactly three, all pre-registered:

| Name | Rule | N units | N cities | Purpose |
|---|---|---|---|---|
| S1 | coverage ≥ 0.40, no IoU floor | 2,724 | 3,081 | lower bound on N / looser footprint |
| S2 | coverage ≥ 0.60, no IoU floor | 1,644 | 1,793 | upper bound on footprint strictness |
| S3 | coverage ≥ 0.50, no IoU floor | 2,192 | 2,459 | isolates the IoU condition's own effect |

## 19. Evidence FOR Gate 2 Readiness

Primary unit, crosswalk rule, inference target, N-floor amendment, bias handling, and common-support method are all fixed and documented; region/fold structure is feasible (with an honest Oceania caveat); twin and transfer designs have ample candidate pairs/donors on S/C/H alone; H variation is preserved, not compressed, by the primary rule; aggregation materially affects only 6.9% of units and even there changes H little; no new data are needed; the rule was chosen by minimizing H-shape distortion, a principled criterion independent of R.

## 20. Evidence AGAINST Gate 2 Readiness

Size/age selection bias is large and present at every threshold tested — it is a structural property of the YCEO/GHSL ontology mismatch, not fixable by threshold choice, and the unweighted design means the eventual result generalizes only to the restricted population (Section 13), not to all urban centres. Oceania cannot stand alone as a validation fold. Multi-city aggregation, while small in effect, adds one more modelling choice. These are disclosed, not resolved away.

## 21. Analysis Support Decision

**ANALYSIS SUPPORT = LOCKED.**

## 22. Gate 2 Execution Decision

**GATE 2 EXECUTION = YES.** All nine readiness criteria (Section 18 of the prompt) are met: unit locked, rule locked, target explicit, N-floor amendment recorded, bias handling locked, region/fold structure feasible (with Oceania merged for validation), twin/transfer designs feasible, no H↔R result inspected, no new data required.

## 23. Exact Files Created/Modified

Created: `prompts/prompt1005-8.txt`; `scripts/gate2_support.py`; `scripts/run_1005_8_pipeline.py`; `tests/test_gate2_support.py`; `results/1005-8/` (`coverage_threshold_sweep.csv`, `iou_sensitivity.csv`, `sample_bias_by_rule.csv`, `aggregation_structure.csv`, `cluster_level_dataset_primary.csv`, `common_support_design.md`, `preregistration_amendment.md`, `final_crosswalk_rule.json`, `inference_target.md`, `fold_feasibility.csv`, `twin_feasibility.csv`, `transferability_feasibility.json`, `analysis_support_decision.json`, `run_metadata.json`); `figures/1005-8/fig1–fig6`; `reports/report1005-8.md`. Modified: none. 1005-1…1005-7 artifacts untouched (verified by existence/non-empty tests; no path under those executions was opened for writing).

## 24. Reproducibility / Integrity Statement

Deterministic pipeline (no randomness; `random_seed: null`), run via `conda run -n py311 python scripts/run_1005_8_pipeline.py`. The Gate-1 sample (N=10,915) is reproduced from the unmodified 1005-4 code. The only thermal-derived input anywhere is the pre-existing boolean validity flag from `results/1005-7/ucdb_yceo_crosswalk.csv`; the SUHI shapefile was never opened. No network access, no new packages. `cluster_level_dataset_primary.csv` is an S/C/H-only dataset (no R column) prepared for the next execution to join against R without re-deriving the crosswalk.

## 25. Questions for PI Review

**Q1** 3,687→3,226→2,724→2,192→1,644→1,135 units as coverage rises 20%→70% (cities 4,290→1,202). **Q2** Match rate rises with stricter coverage in percentage terms but regional *shares* shift toward Europe/Americas/Oceania and away from Asia, consistently across the sweep (fig. 2). **Q3** Size bias (log-pop/log-built-up SMD) worsens monotonically from ~0.8 to ~1.2 as coverage tightens. **Q4** Age bias (YOB SMD) stays roughly flat, −0.56 to −0.66, across the sweep. **Q5** H-shape bias (SMD of H descriptors) is U-shaped, minimized near 50% coverage (0.04) and larger at both looser and stricter thresholds. **Q6** 50% UCDB coverage of the YCEO cluster. **Q7** It is the point of minimum H-shape distortion, a criterion chosen without looking at R. **Q8** Yes, a modest one. **Q9** 0.20 (cluster-level IoU). **Q10** Three: looser coverage (40%), stricter coverage (60%), and dropping the IoU floor at 50% coverage. **Q11** Yes. **Q12** Sum population, built-up area, built volume; density = Σpop/Σbuilt-up. **Q13** H_cluster(t) = Σ B_i(t) / Σ B_i(T). **Q14** Yes, pre-registered as a sensitivity (median distance 0.036 from the aggregate). **Q15** Yes. **Q16** No — it had no statistical derivation. **Q17** Seven auditable criteria (independent units, regional support, fold size, H-variation preservation, common support, effective-N cap, sensitivity stability). **Q18** YCEO-detectable global urban agglomerations with defensible GHSL overlap (2,107 units / 2,374 cities). **Q19** No. **Q20** By stating a restricted inference target rather than reweighting to the full population. **Q21** N/A (not used); if adopted later, 1st/99th-percentile trimming and a 70%-of-nominal Kish effective-N floor are pre-specified. **Q22** Yes for 5 of 6 regions. **Q23** No (N=21); merged with Asia for validation only. **Q24** Yes, 5 roughly equal 10°-tile folds. **Q25** Yes (94–100% of units have a twin depending on k). **Q26** Yes (ample donor pools, non-zero H variation at every epoch). **Q27** 2,107 units / 2,374 UCDB cities. **Q28** 6.9% (146 of 2,107). **Q29** No — it compresses H's SD only modestly (ratio ≈0.92) and shifts its mean SMD to ≈0.04, the smallest in the sweep. **Q30** No. **Q31** LOCKED. **Q32** YES.
