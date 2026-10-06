# Gate 2 Negative Result — Frozen Record

**Execution of record:** 1005-9 (2026-10-05) · **Commit:** `be16037`
**Verdict:** GATE 2 = FAIL (mechanical, from rules fixed before any R was joined) · **Program:** STOP (this formulation)

This file restates the frozen result; it does not reinterpret it. Every number below is copied from
`results/1005-9/*` and is checked against those files by `tests/test_pivot_design_1006_1.py`.

## Original hypothesis

Among YCEO-detectable global urban agglomerations with comparable present-day state S and broad context C,
the fixed-boundary 9-epoch built-up trajectory H (1975–2015, B(t)/B(2020), summed over linked UCDB centres)
carries incremental out-of-sample predictive information about Annual_nig (2003–2018 annual-mean nighttime
SUHI, YCEO v4), beyond S3 (log population, log built-up area, log density, log built volume, 2020) and C1
(latitude, longitude, elevation, decadal-mean temperature, log precipitation).

## Pre-registered decision rules (`results/1005-9/gate2_validation_amendment.md`)

* FAIL if any of: (i) ΔR² < 0.005 with the CI including 0; (ii) observed Δ not above the 95th percentile of the
  shuffled-H null; (iii) S-derived pseudo-history ≥ 80% of a positive observed Δ; (iv) twin ρ ≤ 0.02 AND
  transfer inside its null.
* PASS only if all six STRONG-FOR criteria hold (ΔR² ≥ 0.02 with CI excluding 0; above shuffled null;
  positive in ≥ 4 of 5 adequate regions; not explained by pseudo-history; survives C2 and strict precedence;
  transfer and twin support). FAIL → program STOP.

## Primary numerical result (N = 2,107 units, 2,374 UCDB centres; random forest, 10° tile 5-fold)

| | R² | RMSE (°C) | MAE (°C) |
|---|---|---|---|
| M0 (S3 + C1) | 0.3564 | 0.3272 | 0.2464 |
| M1 (S3 + C1 + H) | 0.3518 | 0.3284 | 0.2484 |

ΔR² = **−0.0045** (95% spatial-block CI −0.0180, +0.0054); ΔRMSE = +0.0012 °C (CI −0.0014, +0.0043);
ΔMAE = +0.0020 °C. History made out-of-fold prediction very slightly worse.

## Key falsifications

1. Shuffled-H null (300 draws): null mean −0.0081, 95th pct −0.0018; observed at the 85th percentile — inside the null.
2. Regions (leave-region-out): ΔR² positive in 2 of 5 adequate regions (Europe +0.122, North America +0.039);
   Asia −0.056, Africa −0.0003, South America −0.014. Oceania (N = 21) descriptive only.
3. Strict precedence (H ≤ 2000, rebased on B(2000)): ΔR² +0.0016 (CI −0.0083, +0.0120) → DISAPPEARS.
4. Secondary Summer_day: RF ΔR² −0.0180 (CI −0.0298, −0.0059); label NULL.
5. Twins (6,725 pairs): partial Spearman +0.0246 (CI −0.0235, +0.0669); permutation null mean +0.033; p = 0.73.
6. Transfer (K = 10 IDW): ΔRMSE +0.0024 (CI −0.0056, +0.0107); shuffled-H null mean +0.0078.
7. C2 context: ΔR² −0.0003. Geometry S1/S2/S3: −0.0014 / −0.0057 / −0.0022. Common support: −0.0052.
8. Moran's I of out-of-fold residuals: M0 0.163, M1 0.169 (k = 8) — H did not reduce residual spatial structure.

Two non-null streams were reported and explained in 1005-9, not used in the decision: ridge ΔR² +0.0308
(CI 0.0008, 0.0646) — reproduced and exceeded by a pseudo-history built from S and C alone (+0.080) and gone
with a quadratic S/C baseline (post-hoc, `posthoc_ridge_followup.csv`); and dynamic-boundary MTUC H on a
1,274-unit subset, ΔR² +0.0157 (CI +0.0017, +0.0293), uncorroborated by any other stream.

## What the failure rules out

In this population and design, the aggregate built-up trajectory does not supply reproducible incremental
out-of-sample information about 2003–2018 YCEO SUHI (night or summer-day) beyond S3 + C1, for effects of the
pre-registered "strong" size (ΔR² ≈ 0.02) in the random-forest contrast. It is not rescued by H representation
(raw, PCA, scalar descriptors), boundary treatment, geometry rule, context set or support restriction.

## What it does not rule out

Effects below ≈ 0.01–0.02 ΔR²; history acting on the urban side only (SUHI subtracts a rural reference);
other H representations (the one tested is area timing only); other responses; small or recently urbanized
cities (outside the inference population); causation (never tested); the unconfirmed dynamic-boundary lead.

## Integrity

Rules fixed before R was joined; decision recomputed from saved CSVs by test; primary outputs sealed by
SHA-256 before the secondary response was loaded; no rule, sample or threshold changed after seeing R.
**This record is frozen. Any further work must test a materially different hypothesis.**
