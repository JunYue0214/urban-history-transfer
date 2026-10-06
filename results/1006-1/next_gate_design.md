# Pivot A design — "Gate 2B": urban-side thermal response

**Status: PROVISIONAL.** The scientific design below is fixed; it cannot be executed until the data path in
`acquisition_plan.md` is verified by a human. Nothing here has been run.

## Question
Among global urban centres with comparable present state S and background climate C, does built-up history H carry
incremental out-of-sample information about urban-side land surface temperature R, i.e. without subtracting a rural
reference? (Gate 2 asked this for the SUHI contrast and failed; that result stays frozen.)

## Variables
* **R (primary):** mean of the gap-filled daily-mean LST over the urban-centre footprint, 2018-2023 climatology,
  annual mean (degC). No transform. One value per unit. Day/night bands are not available in the candidate product (unverified).
* **H (primary):** fixed-boundary built-up trajectory, rebased to avoid using any post-2015 information:
  h(t) = B(t)/B(2015), t = 1975…2010 (8 columns), aggregated Σ over linked centres when a unit holds several.
  Because R starts in 2018, H ends three years before R begins (**strict precedence, lag 3-8 years**). The 2020 built-up values enter only S.
* **S:** S3 (log population 2020, log built-up area 2020, log density 2020, log built volume 2020), as in Gate 2.
* **C:** C1 (lat, lon, elevation, decadal-mean temperature, log precipitation); sensitivities C0 and C2 as before.
  Reanalysis temperature is background climate; it is not urban LST.
* **Not controlled (possible mediators):** present greenness, land cover, tree height, socioeconomic proxies.
  A greenness sensitivity (S3 + greenness) is reported only to describe mediation, never as the primary.

## Unit and sample
Primary unit: **GHSL urban centre** (UCDB footprints are the polygons zonal statistics will use), N up to the
10,915-city Gate 1 sample; no YCEO crosswalk needed, which removes the footprint-ontology loss that cut Gate 2 to 22%.
Small centres cover few 1 km pixels (median area 23 km², 5th percentile 7 km², minimum 1 km²), so centres with fewer than
**9 valid 1 km pixels** (≈ 8% of the sample, area < 9 km²) are excluded by a rule fixed here; the exclusion count and
the size/age/region composition of retained vs excluded centres are reported before any model is fit.
Inference target: global urban centres with ≥ 9 km² footprint and valid LST — not all cities.

## Pre-conditions (stop rules, evaluated before any H is looked at)
1. **Noise floor:** the product's stated error (≈ 1.8 K RMSE per pixel/day) averages down over ≥ 9 pixels × many days, but
   spatially correlated error does not. Report the between-centre SD of R after C1; if M0 out-of-fold R² ≥ 0.95 or the
   unexplained SD is below 0.3 K, the design is declared uninformative and not run.
2. **Baseline sanity:** M0 out-of-fold R² must exceed 0.20 (otherwise R is not predictable from S, C and H cannot add to it meaningfully).
3. **Data check:** variable is a daily mean LST in K or degC with documented scale/nodata; no gap-filling flag implies >30% imputed pixels for a retained centre (if a flag exists).

## Primary comparison
M0: R ~ S3 + C1; M1: R ~ S3 + C1 + H. Random forest with the Gate 2 fixed hyperparameters (500 trees, min_samples_leaf 5,
max_features 0.5, seed 42, no tuning); ridge secondary but interpreted only alongside a quadratic baseline (lesson from 1005-9).
Validation: spatial 10° tile 5-fold; leave-major-region-out for Asia, Africa, Europe, North America, South America;
Oceania descriptive only. Metric: pooled out-of-fold ΔR², ΔRMSE, ΔMAE; 2,000-draw tile bootstrap.

## Nulls and falsifications (all mandatory)
Shuffled H within region × size (≥ 300 draws, seed 42); pseudo-H from S+C; redundant S-derived pseudo-H; random matched vectors;
strict precedence is built in, plus a secondary H ≤ 2000 variant; C0/C2; geographic vs random folds (added, missed in Gate 2);
common-support restriction; size/age/region strata; twins (mutual 10-NN in S3+C1, ≥ 200 km, dependence-aware partial Spearman);
transfer (K = 10 IDW donors from training folds, A0 vs A1); Moran's I of residuals; **negative control:** the same pipeline on
an outcome H cannot plausibly affect (e.g. a purely astronomical/geographic quantity such as latitude-derived insolation) should return ΔR² ≈ 0.

## Decision rule
Identical in form to Gate 2: **PASS** needs ΔR² ≥ 0.02 with CI excluding 0, above the shuffled-H null 95th percentile, positive in ≥ 4 of 5
adequate regions, not reproducible by pseudo-H, surviving C2 and H ≤ 2000, and supporting twin or transfer evidence;
**FAIL** if ΔR² < 0.005 with the CI including 0, or inside the shuffled-H null, or ≥ 80% reproducible by pseudo-H; otherwise **MIXED**.
Thresholds are carried over, not tuned; the PI may revise them in a dated amendment before data are opened.

## Interpretation if each outcome occurs
* PASS → response mixing helped explain Gate 2; H carries urban-side thermal information (associational, not causal).
* FAIL → the SUHI result was not an artifact of the rural reference; with area-only H the history hypothesis is closed, and the Gate 1 + Gate 2 + Gate 2B
  sequence becomes a reportable negative result. Pivot B would then require a new data source.
* MIXED → revise before any optimization work.

## Minimum data, N, compute
New data: one human-downloaded zip (2018-2023 slice) of a Zenodo archive; the full archive is 25.2 GB (four zips), per-zip size unverified.
Expected N: ~9,900 centres (10,915 minus ~8% small) before missing-LST exclusions. Compute: windowed zonal means over ≈10⁴ polygons × ≈2,200 daily
files is I/O-bound (hours); modelling is minutes to a few hours (500-tree forests, ≥ 300 shuffles). RAM: windowed reads, < 8 GB.

## What happens next
Not an empirical run. Next step is a **data-verification step** (1006-2): PI approves one download, the human reports the Zenodo file list and
a file header, the aggregation script is validated, and only then are the pre-conditions evaluated.
