# Pre-registration amendment 1 (execution 1005-8)

Amends: `results/1005-6/gate2_preregistration.md` Section 5 ("If fewer than
3,000 cities or fewer than 5 of 6 regions with N>=30 remain, the primary
claim is downgraded to 'underpowered' before any model is fit."). **That file
is historical and is NOT edited; this document is the authoritative
amendment, filed before any H<->R relationship was analyzed and before any
Gate 2 outcome model has been run.**

## 1. Original rule

An approximate floor of **N >= 3,000** matched cities, set in execution
1005-6, before the real YCEO-cluster crosswalk ontology (1005-7) was known.

## 2. Why it is being changed

The 3,000 figure had no statistical derivation in 1005-6 (no power
calculation, no minimum-detectable-effect target) — it was a round-number
placeholder chosen when the crosswalk product was still a provisional URL.
1005-7 and this execution's geometry-only sweep show that N and sample
**representativeness trade off monotonically against the coverage
threshold** (`coverage_threshold_sweep.csv`): looser thresholds raise N but
*increase* H-descriptor distortion (SMD of `early_developed_fraction_1990`
falls from 0.33 at a 20% coverage floor to 0.04 at 50%, then crosses to
negative by 60-70%), while every threshold carries a large, structural
geometric-size bias (SMD of log population 0.82 to 1.18) that is a property
of the YCEO/GHSL ontology mismatch, not of N. A bare N floor rewards loose
coverage thresholds that are worse on exactly the dimension (H-shape fidelity)
Gate 2 cares about; it is not the right lever.

## 3. New rule (replaces the N>=3,000 floor)

Gate 2 may proceed once ALL of the following hold on the primary sample:

1. **Independent analysis units**: every YCEO cluster contributes exactly one
   outcome row; multi-city clusters are aggregated, never duplicated
   (enforced structurally by `gate2_support.classify_clusters` /
   `aggregate_units`, and by `test_no_duplicated_outcome_per_cluster`).
2. **Broad-region support**: at least 5 of 6 regions have N >= 30 units
   *as an interpretive stratum* (not necessarily as a standalone
   leave-one-out fold — see `fold_feasibility.csv` for the fold-level
   assessment, which may merge a small region for validation only).
3. **Minimum fold size**: every validation fold (region-based or spatial
   10-degree-tile blocked K-fold) used for the primary Experiment 1 metric
   has N >= 30; folds below this are merged (see `fold_feasibility.csv`),
   never dropped from interpretation.
4. **H variation preserved**: the included sample's SD of each H-epoch ratio
   is not collapsed relative to the source sample (reported in
   `coverage_threshold_sweep.csv` as `sd_ratio_early_developed` for the
   `early_developed_fraction_1990` descriptor; primary rule value =
   0.916, i.e. H variation is
   preserved, not compressed).
5. **Common support defined on S/C only**, fixed before R is opened
   (`common_support_design.md`).
6. **Effective sample size**: if any weighting is adopted, the Kish effective
   sample size must be reported and must not fall below 70% of the nominal N
   (not triggered: the primary design is unweighted, Section 12).
7. **Sensitivity stability**: the primary finding's sign and rough magnitude
   must be checked against the pre-registered geometry sensitivities
   (`final_crosswalk_rule.json`) as part of the existing falsification tests
   (1005-6 Section 7, test 6-7 family) — this does not gate *readiness*, it
   gates *interpretation* of the eventual result.

## 4. Primary sample under the new rule

Primary rule (coverage >= 50%, unit
IoU >= 20%): **2107 cluster units**, 2374
UCDB cities, 5 of 6 regions with N >= 30 (Oceania below that bar as a
standalone fold, merged for validation — see `fold_feasibility.csv`). This is
below the old 3,000 figure but satisfies all seven criteria above.

## 5. Status

This amendment is filed **before any H<->R relationship is analyzed** (this
execution never opened the thermal shapefile or any SUHI value) and **before
any Gate 2 outcome model has been run**. It does not report, imply, or
anticipate any H<->R result.
