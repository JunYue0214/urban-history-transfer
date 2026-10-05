# Execution Report 1005-9

Execution ID: 1005-9 · Source prompt: prompts/prompt1005-9.txt · Previous: 1005-8
Task: Gate 2 — Does Developmental History Carry Independent Information About Urban Thermal Response?
Results: results/1005-9/ · Figures: figures/1005-9/

**Result: GATE 2 = FAIL. TRANSFERABILITY PROGRAM = STOP (in its current form).** All decision rules were fixed in `results/1005-9/gate2_validation_amendment.md` before any thermal value was joined to the analysis table, and the decision file is produced mechanically from the saved results (`scripts/gate2_decision_1005_9.py`).

---

## 1. Executive Summary

* On 2,107 YCEO cluster units (2,374 UCDB centres), adding the 9-epoch built-up history H to present-day state S3 and context C1 **does not improve spatially-blocked out-of-fold prediction of Annual_nig** with the pre-registered random forest: R² 0.3564 → 0.3518, **ΔR² = −0.0045** (95% spatial-block CI −0.0180 to +0.0054), ΔRMSE +0.0012 °C, ΔMAE +0.0020 °C (history is slightly *worse*).
* The observed ΔR² sits at the **85th percentile of the shuffled-H null** (null mean −0.0081, 95th pct −0.0018): it is inside the null, as are the random-vector (88th pct) results. The mere presence of 9 extra columns costs about −0.008 R².
* Twin test: partial Spearman ρ(D_R, D_H | D_SC, D_geo) = **+0.025** (cluster-bootstrap 95% CI −0.023 to +0.067); the shuffled-H permutation null has mean +0.033, so the observed value is *below* the null centre (one-sided p = 0.73). High-D_H twins have a +0.035 °C larger median D_R than low-D_H twins, CI −0.009 to +0.076 (includes 0).
* Transfer test: history-aware donor selection is **worse** than S+C donors: RMSE 0.3465 → 0.3489 (ΔRMSE_transfer = +0.0024, CI −0.0056 to +0.0107); every shuffled-H, random-vector and pseudo-H alternative is worse still (null mean +0.0078).
* Strict precedence (H ≤ 2000 only): ΔR² = +0.0016 (CI −0.0083 to +0.0120) → **DISAPPEARS**. T=2015 variant −0.0024. Secondary Summer_day: RF ΔR² = −0.0180 (CI −0.0298 to −0.0059, significantly *negative*), **NULL** for a positive effect.
* One stream is positive and deserves explicit explanation: **ridge** shows ΔR² = +0.031 (CI 0.0008 to 0.0646). A post-hoc follow-up (clearly labelled below) shows this is not evidence for history: ridge's M0 baseline is poor (R² 0.171 vs RF 0.356) because the S/C–R relation is non-linear, and a *pseudo-history predicted from S and C alone* gives an even larger ridge gain (+0.080); with a quadratic S/C baseline the real-H gain vanishes (−0.009).
* Pre-registered fail condition (i) and (ii) both hold; the program verdict follows the pre-agreed mapping (FAIL → STOP).

## 2. Exact Scientific Question

Among globally distributed urban agglomerations with comparable present-day state S and context C, does developmental history H contain reproducible information about nighttime SUHI R beyond S and C? Observational; predictive-association language only.

## 3. Analysis Population

Locked in 1005-8 and re-verified here (`test_exact_sample_identity_against_1005_8_table`): 2,107 cluster units, 2,374 UCDB centres, 146 multi-city aggregate units (6.9%); regions Asia 1,028, Africa 323, South America 296, Europe 253, North America 186, Oceania 21. Annual_nig is valid for all 2,107 (no row dropped, no transformation, winsorizing or outlier removal). Inference target: YCEO-detectable global urban agglomerations with defensible GHSL overlap (larger, older-established agglomerations); no generalization to all 10,915 GHSL cities.

## 4. Variables S/H/C/R

* S3: log population 2020, log built-up area 2020, log density 2020 (algebraically Pop/BuiltUp, documented), log built volume 2020. S1 = pop + area; S2 = S1 + density.
* C1: latitude, longitude, elevation, decadal-mean annual temperature, log decadal-mean annual precipitation (all area/built-up-weighted over linked centres). C0 = first three; C2 = C1 + temperature seasonality + precipitation seasonality + Köppen major group (5 dummies). No greenness, land cover or socioeconomic proxies.
* H: 9-vector B(t)/B(2020), t = 1975…2015, summed over linked UCDB centres; also training-fold-only PCA(3) and four scalar descriptors.
* R: Annual_nig (primary), Summer_day (secondary), untransformed.

## 5. Validation Design

Primary: the locked 10° tile blocking, 5 folds (421–422 units each). Secondary: leave-major-region-out for Asia, Africa, Europe, North America, South America; Oceania (N=21) reported descriptively, not merged with Asia, not counted as replication. Learners: Random Forest (500 trees, min_samples_leaf 5, max_features 0.5, seed 42, no tuning) and RidgeCV (training-fold-only). M0 and M1 always use identical rows and folds. Bootstrap: 2,000 resamples of 10° tiles over stored OOF predictions (no refitting; stated limitation). Amendment text: `results/1005-9/gate2_validation_amendment.md` (also records the 1005-8 common-support defect, §13).

## 6. Experiment 1 — Primary Predictive Test

`primary_model_metrics.csv`:

| Spec | R² M0 | R² M1 | ΔR² | 95% CI | ΔRMSE (°C) | ΔMAE (°C) |
|---|---|---|---|---|---|---|
| **RF, raw 9-vector (primary)** | 0.3564 | 0.3518 | **−0.0045** | −0.0180, +0.0054 | +0.0012 | +0.0020 |
| RF, PCA(3) on training-fold H | 0.3564 | 0.3530 | −0.0034 | −0.0120, +0.0033 | +0.0009 | +0.0014 |
| RF, 4 scalar descriptors | 0.3564 | 0.3581 | +0.0017 | −0.0106, +0.0119 | −0.0004 | +0.0006 |
| Ridge, raw 9-vector | 0.1706 | 0.2014 | +0.0308 | +0.0008, +0.0646 | −0.0070 | −0.0058 |

Pre-registered guidance (ΔR² ≥ +0.02 with CI excluding 0) is not met by the primary learner; the primary effect is below the "AGAINST" line (< 0.005, CI includes 0). All 2,107 OOF predictions are stored (`primary_oof_predictions.csv`).

## 7. Null / Pseudo-H Tests

`history_null_results.csv` (seed 42):

| Null | Δ under null | Observed −0.0045 relative to it |
|---|---|---|
| N1 shuffled H within region × size tercile (300 draws) | mean −0.0081, SD 0.0038, q95 −0.0018 | 85th percentile; standardized +0.93; **inside the null (below q95)** |
| N2 pseudo-H predicted from S+C (out-of-fold) | −0.0298 | worse than real H |
| N3 redundant pseudo-history (quadratics/products of S3) | −0.0095 | worse than real H |
| N4 random 9-vectors with H's mean/covariance (50 draws) | mean −0.0084, q95 −0.0026 | 88th percentile |
| N1 for ridge (300 draws) | mean +0.0120, q95 +0.0210 | ridge observed +0.0308 is above this (100th pct) — see §22 caveat |

A pseudo-history built from S alone does not reproduce a positive RF gain only because there is no positive RF gain to reproduce; for ridge the opposite holds (post-hoc follow-up, §22).

## 8. Regional Robustness

`region_holdout_results.csv` (fresh M0/M1 per held-out region):

| Held-out | N | R² M0 | R² M1 | ΔR² |
|---|---|---|---|---|
| Asia | 1,028 | −0.009 | −0.065 | **−0.056** |
| Africa | 323 | 0.148 | 0.148 | −0.0003 |
| Europe | 253 | −0.260 | −0.137 | **+0.122** |
| North America | 186 | 0.024 | 0.063 | **+0.039** |
| South America | 296 | −0.142 | −0.156 | −0.014 |
| Oceania (descriptive only, N=21) | 21 | −0.424 | −0.429 | −0.005 |

ΔR² is positive in 2 of 5 adequate regions (Europe strongest, +0.122; Asia weakest, −0.056). Note that M0 itself has *negative* R² when predicting Europe, South America and Asia from other regions: the S/C–R relation does not transfer across continents even without H, so the regional Δ values are differences between two poor models and are not stable evidence either way. Pre-registered rule: positive in ≥ 4 of 5 for FOR; negative in ≥ 3 of 5 flagged AGAINST — 3 of 5 are negative (Asia, Africa marginally, South America). Oceania: both models far worse than a mean predictor; no inference.

## 9. Experiment 2 — Twin Environmental Divergence

`twin_results.csv`, `twin_summary.json`. Pairs built from S3+C1 and geography only (test `test_twin_construction_has_no_access_to_H_or_R`): mutual k=10 neighbours, ≥ 200 km apart → **6,725 pairs among 2,074 units**. Partial Spearman ρ(D_R, D_H | D_SC, D_geo) = **0.0246**, tile-cluster bootstrap CI (−0.0235, +0.0669); stratified permutation (1,000 shuffles of unit-level H within region × size): null mean 0.033, q95 0.056, one-sided p = 0.733. Raw Spearman(D_R, D_H) = 0.059. The pairs are not treated as independent: the CI replicates pairs by tile-resampling multiplicities, and the null shuffles units, not pairs.

D_H tertile strata (cut points from the D_H distribution only: 0.194, 0.390): median D_R = 0.246 (low), 0.248 (mid), 0.281 (high) °C; high − low median difference 0.035 °C, CI (−0.009, +0.076). The ordering is in the hypothesized direction but statistically indistinguishable from zero and not above the permutation null for the correlation.

## 10. Experiment 3 — History-Aware Transferability

`transfer_results.csv`. K = 10 inverse-distance-weighted donors from the four training folds only; features z-scored on the training rows with equal block variance. Spatial 5-fold: RMSE A0 (S3+C1) = 0.3465, A1 (S3+C1+H) = 0.3489, **ΔRMSE_transfer = +0.0024** (CI −0.0056, +0.0107); MAE 0.2614 → 0.2653. Shuffled-H null: mean +0.0078, q05 +0.0042; random matched vectors +0.0111; pseudo-H from S +0.0082. So real H harms transfer less than random alternatives (it is "better than shuffled H") but is still worse than not using H. Leave-region-out donors (secondary): ΔRMSE_transfer = +0.0056 (Asia), +0.0171 (Africa), +0.0067 (Europe), −0.0169 (North America), −0.0060 (South America).

## 11. Strict Temporal-Precedence Test

`strict_precedence_results.csv`:

| Spec | ΔR² | 95% CI |
|---|---|---|
| Primary (H 1975–2015, S 2020) | −0.0045 | −0.0180, +0.0054 |
| H ≤ 2000 rebased on B(2000), S 2020 | +0.0016 | −0.0083, +0.0120 |
| H ≤ 2000, S 2000 (fully past-state) | −0.0013 | −0.0110, +0.0091 |
| Only overlapping epochs 2005–2015 (diagnostic) | −0.0052 | −0.0162, +0.0054 |
| T = 2015 (S 2015, H 1975–2010 on B(2015)) | −0.0024 | −0.0154, +0.0083 |

Label: **DISAPPEARS** (there is nothing to survive: the primary effect is itself null). Neither the overlapping nor the pre-2000 history carries signal, so the "recent-development association" reading is also unsupported.

## 12. Boundary Sensitivities

`boundary_sensitivity_results.csv`; M0 always recomputed on the same subset.

| Spec | N | ΔR² | 95% CI |
|---|---|---|---|
| A. fixed aggregate H (primary) | 2,107 | −0.0045 | −0.0180, +0.0054 |
| C. dominant-city H, all units | 2,107 | −0.0065 | −0.0195, +0.0033 |
| Multi-city subset, aggregate H | 146 | +0.0056 | −0.0239, +0.0335 |
| Multi-city subset, dominant H | 146 | +0.0123 | −0.0212, +0.0453 |
| D. scalar boundary-robust descriptors | 2,107 | +0.0017 | −0.0106, +0.0119 |
| B. fixed H on MTUC subset | 1,274 | +0.0106 | −0.0067, +0.0251 |
| B. **dynamic** MTUC H on same subset | 1,274 | **+0.0157** | **+0.0017, +0.0293** |

The dynamic-boundary H on the MTUC-matched subset is the only primary-learner spec whose CI excludes 0 (lower bound +0.0017). It is below the 0.02 guidance, on a subset of older, more established agglomerations (the 1005-5 matched sample), with 7 boundary specs tested, and it was not backed by any other stream. It is reported as a lead for scrutiny, not as support (see §19, §22).

## 13. Geometry Sensitivities

`geometry_sensitivity_results.csv` (the three locked 1005-8 rules, no additions): S1 (coverage ≥ 0.40, N = 2,724) ΔR² −0.0014 (−0.0111, +0.0056); S2 (≥ 0.60, N = 1,644) −0.0057 (−0.0194, +0.0068); S3 (≥ 0.50, no IoU floor, N = 2,192) −0.0022 (−0.0111, +0.0071). All null.

## 14. Context / State Sensitivities

`context_state_sensitivity.csv`: S1+C1 −0.0088 (−0.0229, +0.0013); S2+C1 −0.0050; S3+C0 +0.0052 (−0.0186, +0.0238); **S3+C1 −0.0045 (primary)**; S3+C2 −0.0003 (−0.0118, +0.0087). C2 baseline R² rises to 0.371 (from 0.356) and ΔR² stays at zero. The weakly positive C0 value is the only direction in which a weaker context control gives H any credit, consistent with H partly standing in for climate when climate is poorly specified.

## 15. Common-Support Analysis

`common_support_results.csv`. Full sample ΔR² −0.0045; support-restricted (Mahalanobis ≤ own 95th percentile, 4.53; N = 2,001) −0.0052 (−0.0189, +0.0072). I also re-ran the flag exactly as implemented in 1005-8: the 1005-8 code used `log(clip(density, 1))`, a constant 0 because densities are 0.004–0.156 per m², so that column carried no information in the 1005-8 flag and twin-feasibility computations. The corrected flag (true log density) and the as-implemented flag give the same threshold (4.5319 vs 4.5319) and identical N (2,001) and model metrics to every printed digit, so no conclusion changes (I did not diff the unit sets individually). The defect is recorded in the amendment (§G); no 1005-8 file was edited.

## 16. Size / Age / Region Heterogeneity

`subgroup_results.csv` (pooled primary OOF predictions; pre-defined size terciles, YOB ≤ 1975 vs > 1975, region): small +0.0084 (−0.0115, +0.0270), mid −0.0001, large −0.0148 (−0.0419, +0.0096); established −0.0062, recent +0.0009; regions: Asia +0.0070, Africa −0.0190, Europe −0.0367, North America −0.0228, South America −0.0221, Oceania +0.0266 (N=21, descriptive). Every CI includes 0; no subgroup stands out, so the null is not concentrated in large/old cities (the sample's overrepresented stratum) and there is no hidden positive subgroup.

## 17. Secondary Response Replication

Run only after the primary outputs were sealed with file hashes (`primary_outputs_sealed.json`; test `test_secondary_response_blocked_until_primary_is_sealed`). Nothing from Summer_day fed back into any choice. `secondary_response_results.csv`: RF ΔR² = **−0.0180** (CI −0.0298, −0.0059; M0 0.389 → M1 0.371); ridge +0.0125 (−0.0162, +0.0430); shuffled-H null mean −0.0178 (observed at the 47th percentile); strict H ≤ 2000 −0.0014; C2 −0.0075; twins ρ = 0.0057 (CI −0.046, +0.059; p = 0.67); transfer ΔRMSE = +0.0317 (A1 worse; CI +0.0104, +0.0550). Label: **NULL** for a positive effect (and a significantly negative RF contrast for the daytime channel, i.e., H columns add noise). Daytime and nighttime concordantly show no recoverable history signal.

## 18. Spatial Residual Diagnostics

`spatial_residual_diagnostics.csv` (Moran's I of out-of-fold residuals, kNN weights on the sphere, 499 permutations): M0 I = 0.163 (k=8), 0.105 (k=20); M1 I = 0.169 and 0.115. Adding H does **not** reduce unexplained spatial structure (it slightly increases it). Summer_day shows the same pattern (M0 0.210 → M1 0.229). Nominal p-values (0.002) are not interpreted at this N; the residual spatial structure that remains after S+C is real and not accounted for by H.

## 19. Evidence FOR Independent Historical Information

* Ridge ΔR² = +0.031 (CI +0.0008, +0.0646), above its shuffled-H null — but see §22 (artifact of a misspecified linear baseline).
* Dynamic-boundary MTUC H on the 1,274-unit MTUC subset: +0.0157, CI +0.0017 to +0.0293 (single specification, below 0.02, no corroboration).
* Twin and D_H tertile ordering are in the hypothesized direction (ρ = +0.025; high − low median D_R +0.035 °C), and positive in Europe (+0.12) and North America (+0.04) held-out regions.
* Real H hurts transfer and prediction less than shuffled/random alternatives (consistent with H carrying a little structure rather than pure noise), but no more than "less harmful".

## 20. Evidence AGAINST

* Primary ΔR² = −0.0045 (CI includes 0), inside the shuffled-H null (85th percentile) — pre-registered fail condition (i) and (ii).
* RMSE and MAE both worsen with H; transfer RMSE worsens with H; Moran's I does not fall.
* Strict-precedence H, T = 2015, C2, geometry S1–S3 and common-support variants all null.
* Secondary Summer_day significantly negative for RF; twin ρ ≈ 0.
* Regional: positive in only 2 of 5 adequately sized regions; M0 has negative out-of-region R² in three regions.
* Ridge's positive result is reproduced (and exceeded) by a pseudo-history built from S and C alone, and disappears with a quadratic baseline.

## 21. Falsification Summary

| Pre-registered test | Outcome | Counts against? |
|---|---|---|
| Shuffled H within region × size | observed at 85th pct, below q95 | **Yes** |
| Pseudo-H from S | −0.030 (no gain) | n/a (no gain to explain) |
| Redundant S-derived pseudo-H | −0.0095 | n/a |
| Random matched vectors | observed at 88th pct | **Yes** |
| Random vs geographic folds | geographic folds used; no random-fold comparison reported | not run |
| Leave-region-out | positive in 2/5 | **Yes** |
| Alternate context C0/C1/C2 | all ≈ 0 | **Yes** |
| Alternate H boundary | only dynamic MTUC subset > 0 | partly |
| Alternate outcome (Summer_day) | significantly negative RF | **Yes** |
| Temporal window H ≤ 2000, T = 2015 | ≈ 0 | **Yes** |
| City-size / recent-vs-established strata | all CIs include 0 | **Yes** |
| Spatial-autocorrelation-aware CI | CI includes 0 | **Yes** |
| Null analogue transfer | worse than A0; better than shuffled | mixed |

Two items of the 1005-6 list were not run as written: the "random-fold vs geographic-holdout comparison" (test 4) was not part of 1005-9's required experiments, and alternate rural reference (test 9) is unavailable. Neither can overturn a null that is already present under the more demanding geographic validation.

## 22. Scientific Interpretation

Within this sample, present-day state and broad climate predict about 36% of the spatially-held-out variance in nighttime SUHI, and adding the built-up trajectory does not improve that — with the forest, the PCA and scalar representations, either response, every temporal window, every geometry and context choice, the twin design and the donor-transfer design, the estimate is within sampling noise of zero.

The one positive headline stream, ridge, deserves a transparent explanation. I ran a **post-hoc, non-pre-registered** diagnostic (`scripts/posthoc_ridge_followup_1005_9.py`, `posthoc_ridge_followup.csv`; it does not enter the decision): ridge M0 R² = 0.171 versus 0.356 for the forest, so a linear baseline is clearly misspecified; adding *pseudo-history predicted out-of-fold from S and C only* raises ridge ΔR² to +0.080 (CI 0.013, 0.144) — larger than the real-H gain (+0.031) — and with a quadratic S/C baseline the real-H gain falls to −0.009 while the shuffled-H null is −0.004 (q95 +0.0003). Interpretation: history columns act as nonlinear S/C features for a linear model, not as independent information about R. This is exactly the failure mode the pseudo-history null was designed to catch, and it is why the rule mapping uses the forest as the primary learner.

What is supported: "Under the tested specifications, developmental trajectories (9-epoch built-up ratios 1975–2015) do not provide predictive information about 2003–2018 annual nighttime SUHI beyond present-day state and broad climate, in YCEO-detectable agglomerations." This is a statement about this response, this H representation, this resolution and this population, not about history in general.

## 23. Claims Explicitly NOT Supported

* That developmental history causes, determines or "remembers" in SUHI (no causal design; and no associational signal).
* That H carries incremental information for either channel (night or day SUHI), in any region, boundary, or temporal window tested, other than one corroboration-free specification.
* That history-aware analogue selection improves environmental transfer.
* Any claim about small or recently urbanized cities (outside the inference target), or about other environmental responses.
* That the result proves no information exists: ΔR² CIs are roughly ±0.01–0.02, so effects of the 0.02 magnitude pre-registered as "strong" are excluded for the forest, but smaller effects are not.

## 24. Gate 2 Decision

**GATE 2 = FAIL.** Mechanical mapping (`gate2_decision.json`): fail condition (i) ΔR² < 0.005 with CI including 0 — true; (ii) observed Δ not above the shuffled-H 95th percentile — true; (iii) pseudo-H ≥ 80% of a positive observed Δ — not applicable (observed Δ negative); (iv) twin ρ ≤ 0.02 and transfer inside null — false (ρ = 0.025). None of the six STRONG-FOR criteria holds. Regional sign failure (3 of 5), C2 non-survival and strict-precedence failure are recorded as additional AGAINST flags.

## 25. Transferability Program Decision

**TRANSFERABILITY PROGRAM = STOP** the history-aware environmental-transfer hypothesis *in its current form* (aggregate built-up trajectory H as an add-on to S and C for predicting SUHI at YCEO-cluster scale). This is the pre-agreed mapping from FAIL. It does not close the broader program: it says optimization / sensing-network design should not be built on this H, and any reopening needs a materially different hypothesis (not a re-slicing of this one).

## 26. Scientific Limitations

* Single response family (SUHI), one product (YCEO v4) with a generalized rural reference; SUHI is a function of urban form *and* the rural environment (documentation §VI), which can mask urban-side signal.
* R (2003–2018) overlaps most of H; no clean ordering was available even though strict precedence was tested.
* Footprint mismatch between GHSL and YCEO polygons (median IoU ≈ 0.5), 22% of UCDB cities represented, bias toward larger/older agglomerations; null results do not extend to small/recent cities.
* H measures only built-up-surface trajectory, not morphology, materials, green infrastructure or governance; ΔR² CIs bound only effects ≳ 0.02 for the forest.
* The block bootstrap reflects evaluation-sample dependence only and does not refit models; RF used fixed hyperparameters.
* Leave-region-out baselines have negative R² in several regions, so regional ΔR² values compare two poor models.
* The 1005-8 common-support code defect (constant log-density column) was found and documented; it did not change any sample here.
* The random-vs-geographic fold comparison (1005-6 test 4) was not run.

## 27. Exact Files Created/Modified

Created: `prompts/prompt1005-9.txt`; `scripts/gate2_data.py`, `gate2_models.py`, `run_1005_9_pipeline.py`, `gate2_decision_1005_9.py`, `posthoc_ridge_followup_1005_9.py`; `tests/test_gate2_models.py`, `tests/test_gate2_results.py`; `results/1005-9/` (amendment, sample summary, model metrics, OOF predictions, null results and draws, region, twin, transfer, strict-precedence, boundary, geometry, context, common-support, subgroup, secondary, spatial-diagnostic files, `primary_outputs_sealed.json`, `gate2_decision.json`, `posthoc_ridge_followup.csv`, `run_metadata.json`); `figures/1005-9/fig1–fig8`; `reports/report1005-9.md`. Modified: none of 1005-1…1005-8.

## 28. Reproducibility / Integrity

Seed 42; 300 shuffled-H draws; 2,000 tile-bootstrap draws; RF 500 trees fixed. Pipeline: `conda run -n py311 python scripts/run_1005_9_pipeline.py` (≈ 26 min) then `scripts/gate2_decision_1005_9.py`. Primary outputs sealed by SHA-256 before the secondary response was loaded; test verifies they are unchanged. Raw ZIP SHA-256 unchanged (`d5575541…`). No network access, no downloads, no new packages. The decision JSON is recomputed from the CSVs in a test. Order of work: amendment written → data assembled and sample identity verified → pipeline run once → mechanical decision → post-hoc diagnostic (ridge, not part of the decision). No rule, threshold or specification was changed after seeing R.

## 29. Questions for PI Review

**Q1** 2,107 cluster units (2,374 UCDB centres). **Q2** M0 R² 0.3564, M1 0.3518 (RF, spatial 5-fold). **Q3** ΔR² = −0.0045. **Q4** ΔRMSE = +0.0012 °C; ΔMAE = +0.0020 °C (both worse). **Q5** No: CI −0.0180 to +0.0054 includes 0. **Q6** 85th percentile of the shuffled-H null (null mean −0.0081, q95 −0.0018): inside it. **Q7** Not applicable as a "reproduction" — the S-derived pseudo-H gives −0.030 for RF (no gain to reproduce); for ridge it exceeds the real-H gain (+0.080 vs +0.031). **Q8** RF: redundant S-based pseudo-H −0.0095 (no gain). Ridge: +0.019 (smaller than real H). **Q9** No in the sense required: ridge ΔR² is positive (+0.031, CI 0.0008–0.0646) but opposite in sign to RF, driven by linear misspecification (post-hoc follow-up). **Q10** 2 of 5 (Europe, North America). **Q11** Europe (+0.122). **Q12** Asia (−0.056). **Q13** Oceania N=21: both models worse than a mean predictor (R² −0.42/−0.43), ΔR² −0.005; no inference. **Q14** Partial Spearman +0.0246 (CI −0.023, +0.067). **Q15** Marginally higher: median D_R 0.281 vs 0.246 °C (+0.035, CI −0.009, +0.076) — not distinguishable from zero. **Q16** Yes, dependency-aware (tile-cluster bootstrap, unit-level stratified permutation); permutation p = 0.73, observed below the null mean. **Q17** No. **Q18** It worsens RMSE by +0.0024 °C (CI −0.0056, +0.0107). **Q19** It is worse than not using H, though less bad than shuffled/random/pseudo-H (null means +0.008 to +0.011). **Q20** No: DISAPPEARS (ΔR² +0.0016, CI −0.0083, +0.0120). **Q21** Not even that: the overlapping-epochs-only diagnostic is also null (−0.0052). **Q22** Yes, T=2015 gives −0.0024 (CI −0.0154, +0.0083). **Q23** Partly: on the 1,274-unit MTUC subset dynamic H gives +0.0157 (CI +0.0017, +0.0293), but fixed H there is +0.0106 (CI includes 0) and the full-sample estimate is null; treat as an unconfirmed lead. **Q24** Yes (null): −0.0065 (CI −0.0195, +0.0033). **Q25** Yes, all null (−0.0014, −0.0057, −0.0022). **Q26** Yes: C2 −0.0003 vs primary −0.0045; neither shows a signal (the question is moot because there is no history signal to remove). **Q27** No: restricted to common support −0.0052 vs −0.0045. **Q28** No: size terciles +0.008/−0.0001/−0.015, established −0.006, recent +0.001; all CIs include 0. **Q29** No (NULL): RF ΔR² −0.018, CI −0.030 to −0.006. **Q30** No: Moran's I increases slightly with H (0.163 → 0.169 at k=8). **Q31** The shuffled-H null: the primary ΔR² (−0.0045) lies inside it (85th percentile), so the observed result is indistinguishable from adding 9 uninformative columns. **Q32** The ridge result and the dynamic-boundary subset result are the only positive streams, but neither survives its own control (pseudo-history, corroboration); the strongest *negative* evidence stream is the combination of primary CV, shuffled-H null and strict-precedence null. **Q33** The pre-registered primary contrast is null, inside its own shuffled-H null, and not rescued by any of the other designs. **Q34** The ridge ΔR² (+0.031, CI excludes 0) and the dynamic-boundary MTUC subset ΔR² (+0.016, CI excludes 0); both are weak and explained or uncorroborated. **Q35** No. **Q36** FAIL. **Q37** STOP (current form). **Q38** Is there any response or history representation for which the history–response relation survives the pseudo-history and shuffled-H controls? — most concretely, whether *urban-side* thermal signal (e.g., LST or SUHI after conditioning out the cluster's rural reference, or intra-city morphology) rather than the cluster-scale SUHI contrast, relates to history; and, if the dynamic-boundary MTUC lead is to be taken seriously, a pre-registered replication on an independent dynamic-boundary sample.
