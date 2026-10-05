# Common-support design (execution 1005-8)

**Pre-registered BEFORE any H<->R analysis; uses S and C only, computed on the
primary cluster-level sample.**

## Population

Primary inference population: YCEO clusters passing the final primary
crosswalk rule (`final_crosswalk_rule.json`) with observed primary R
(validity only, never magnitude).

## Method: Mahalanobis distance support (chosen over kNN density or a
propensity score)

Chosen because it is (a) simple and auditable — a single scalar per unit —
(b) coordinate-free (invariant to the 7 S3+C1 feature choices' arbitrary
scaling), and (c) directly reusable for Experiments 1-3 (twin selection in
section 15 already uses the same standardized S3+C1 block; donor pools in
Experiment 3 can reuse the same distance). kNN density support was not chosen
because its outcome depends on an arbitrary bandwidth/k and is harder to
report as one audit number per unit; a propensity-to-be-matched score was not
chosen because it would need to be fit on S/C against inclusion, adding a
model-selection step this execution is meant to avoid.

Feature block (computed on the primary cluster-level dataset, 7 dims):
log(population 2020), log(built-up area), log(built volume), log(density)
[S3]; latitude, longitude, elevation, decadal-mean temperature, log decadal
precipitation [C1]. Each sub-block is standardized and scaled to equal total
variance before concatenation (`gate2_support.block_scale`), identical to the
scaling the twin and transfer experiments will use.

## Support rule (to be applied unchanged in Gate 2, before any R is examined)

For any downstream spatial-holdout, twin, or donor-transfer analysis, a unit
is **in common support** iff its Mahalanobis distance to the primary sample's
S3+C1 centroid is **<= the sample's own 95th percentile** (computed once, on
this sample, here: **4.53**, 2107 units). This is self-referential
(no external population), auditable, and fixed before R is opened. Units
outside support are flagged, not silently dropped, and are reported as the
sample's own tail, not as a second exclusion stage with new researcher
discretion.

## What is explicitly NOT done

No observation is removed based on model residuals, predicted R, or any
post-hoc model fit. No support redefinition after Experiment 1-3 results are
seen. No outcome variable enters this file.
