# Execution Report 1005-6

Execution ID:
1005-6

Source Prompt:
prompts/prompt1005-6.txt

Previous Execution:
1005-5

Report:
reports/report1005-6.md

Results:
results/1005-6/

Task name: Gate 2A — Thermal Response Design Lock

**This execution designs and pre-registers Gate 2; it does not run it. No
thermal-response data and no other research data were downloaded or
requested. Claude made no network transfer of any research-data file. Web
inspection was limited to search-result metadata: WebFetch was blocked for
every domain tried (Figshare, ScienceDirect, OSTI, Google developers, GEE
community catalog, Yale), so no landing page, README or documentation PDF
was read directly. Everything that rests on that gap is marked UNRESOLVED.**

Interruption note: the previous run of 1005-6 was cut off by an upstream API
streaming error (not a scientific or local failure). On resume, the
untracked files it had left were inspected rather than trusted: the prompt
file was confirmed intact; the two acquisition scripts and their test were
re-audited and rewritten (the earlier version hard-coded a Figshare DOI as the
"expected dataset" and a test file ended with a stray statement); the
`results/1005-6/` directory was empty.

---

## 1. Executive Summary

* **THERMAL DESIGN = PROVISIONAL.** A defensible primary response and a
  consistent pre-registration exist, but the primary data file's schema,
  geometry and contents could not be verified, and the response window ends
  before the Gate 1 endpoint.
* **Primary R:** annual-mean nighttime SUHI climatology, 2003-2018 mean, from
  the **YCEO Surface Urban Heat Islands v4** urban-cluster-mean file (NASA
  SEDAC, DOI 10.7927/S5M5-ZK14). **Secondary:** summer daytime SUHI.
  **Contrast:** none locked (optional exploratory trend).
* **The Yang/Xu/Chakraborty 2024 dataset is a different product** from
  YCEO v4 (different method, DEA vs SUE; different archive; different city
  set). It is retained only as an alternate rural-reference check because its
  Figshare record is a README with Baidu/Google Drive links and no verified
  city-level table.
* Primary response is already urban-rural normalized, city(cluster)-level,
  ~5 MB; **no global raster is needed**, and the nested climate controls C0/C1/C2
  can be built entirely from fields already in the UCDB files (verified
  locally, no missing values).
* Response window 2003-2018 overlaps H (epochs 2005-2015) and precedes S(2020):
  **Gate 2 can support predictive association and transferability only, not a
  temporal-legacy claim.** A strict-precedence sensitivity is pre-registered.
* H: **fixed-boundary primary on the full matched sample, dynamic-boundary as
  sensitivity**, not restriction to the 4,739-city sample.
* Acquisition software was rewritten and tested only against synthetic
  loopback servers and synthetic zipped shapefiles (20 tests); design-artifact
  tests add 9; full suite 65/65 pass.
* **PI acquisition recommendation: NOT YET** — do the documentation-only
  Step 0 first.

## 2. Scientific Question for Gate 2

Among cities with similar present-day urban state S and large-scale context C,
do cities with different developmental histories H also show systematically
different thermal responses R? Operationally: does R contain out-of-sample
predictive information associated with H beyond S and C, and does history-aware
analogue selection reduce transfer error? Observational; no causal claim.

## 3. Why Thermal Response Is Being Considered

Gate 1/1B established that S and coarse C do not uniquely determine H (full
sample leave-region-out R²≈0.226, divergent twins 18.3%; dynamic boundary
R²_dyn 0.158 vs R²_fixed 0.320, twins 18.7% vs 16.7%, null effect 23.6% vs
31.3%; Gate 1B = MIXED but not a boundary artifact). Gate 2 asks whether that
unexplained history matters for an environmental response. Thermal response
was chosen because a pre-aggregated global city-level urban-rural contrast
exists (1005-3), so no raster processing is required.

## 4. Candidate R Definitions

Full table with the 14 audit criteria: `results/1005-6/thermal_candidate_audit.csv`.

| ID | Candidate | Role |
|---|---|---|
| A | Annual daytime SUHI | not selected (climate/reference confounding) |
| **B** | **Annual nighttime SUHI** | **PRIMARY** |
| **C** | **Summer daytime SUHI** | **SECONDARY** |
| D | Summer nighttime SUHI | descriptive only (redundant with B) |
| E | Monthly/seasonal climatology | exploratory only (multiplicity, phenology) |
| F | Interannual variability | rejected (noise) |
| G | Long-term trend | exploratory contrast (sensor/processing confound; near-tautological with recent growth) |
| H | Extreme/upper-tail SUHI | rejected (only raster-scale daily product found) |
| I | Raw urban LST | rejected (climate-dominated; raster-scale; would be a good negative control in principle) |
| J | Urban-rural formulations (SUE/DEA/buffer) | sensitivity axis |

Qualitative (ordinal) scoring only; no fake numeric score. Daytime was not
assumed best: daytime SUHI is the more climate- and reference-vegetation-
confounded member and flips sign in arid cities.

## 5. Candidate Dataset Audit

Full table: `results/1005-6/thermal_source_audit.csv` (9 sources, each field
tagged VERIFIED_MULTI / VERIFIED_SINGLE / INFERRED / UNRESOLVED).

| Source | Unit | Coverage | Access | Verdict |
|---|---|---|---|---|
| S1 YCEO SUHI v4 (SEDAC) | urban clusters, fixed Landscan extent | >10,000 clusters, 2003-2018, annual/summer/winter × day/night + monthly & yearly means | official NASA SEDAC; city-level Shapefile ~4.7 MB zip; Earthdata login | **primary candidate** |
| S2 same, via GEE | as S1 | as S1 | GEE assets `YALE/YCEO/UHI/*_v4` | alternate path to S1 |
| S3 Yang et al. 2024 | cities, DEA reference | 10,196 cities; monthly/quarterly/annual; day/night; clear-sky, all-sky, canopy; ~2003-2020 | Figshare = README + Baidu/Google Drive; gridded 1 km on GEE community catalog | alternate-reference check; access unresolved |
| S4 Chakraborty & Lee 2019 | clusters | ~9,500 / 7,374 | superseded | rejected |
| S5 Mentaschi 2022 | 1 km daily rasters, day only | 2003-2020 | repo unresolved | rejected (scale) |
| S6 Si 2022 | clusters | unresolved | no dataset found | unusable |
| S7 Peng 2012 | 419 cities | — | — | rejected (coverage) |
| S8 raw MODIS LST | pixels | — | GB-TB | rejected (scale) |
| S9 Sci. Data 2026 heat-wave exposure | settlements | 2003-2020 | unresolved | noted, not audited in depth |

Direct answers to the audit questions you raised:

1. *Is Yang 2024 the same dataset as any Figshare/GEE/Yale/SEDAC product?*
   Same authors' lineage but **not the same product** as the Yale/SEDAC/GEE
   `YALE/YCEO/UHI` series (that is Chakraborty & Lee, SUE). Yang 2024 is the
   Figshare + `projects/sat-io/open-datasets/UHII/*` GEE community collection.
2. *City tables vs rasters?* S1 has a city(cluster)-level Shapefile (and a
   pixel product we do not need). S3's verified forms are gridded (GEE) and
   Baidu/Google Drive archives; a city table is unverified.
3. *Temporal coverage vs T=2020?* S1 ends 2018; S3 reportedly reaches 2020 but
   end year is single-sourced.
4. *Day/night, monthly/seasonal?* Both products: yes. S1 summer/winter are
   hemisphere-defined (winter months single-sourced; summer inferred).
5. *Rural reference?* S1: non-urban pixels (ESA CCI) inside the same fixed
   Landscan extent, filtered for elevation difference/urban share. S3: DEA,
   background area equal in size to the urban area. Details of thresholds
   unresolved.
6. *Crosswalk keys?* Polygons/coordinates probable but unconfirmed (see §12).
7. *Volume?* S1 city file ~4.7 MB; consistent with coarse global design.

## 6. Primary Dataset Recommendation

**YCEO SUHI v4, urban-cluster-mean Shapefile** (NASA SEDAC; Chakraborty & Lee
2023; DOI 10.7927/S5M5-ZK14). Official archive with a stable DOI and a
published, documented algorithm; small; city-level; ready for a polygon
crosswalk; the fixed-extent definition matches a fixed-boundary H. Not
LOCKED because: schema/geometry/ID not verified; whether the annual/summer
means sit in the 4.7 MB file is not verified; v4 cluster count unknown (2019
version: 7,374 after filtering vs "over 10,000" in v4); tropical summer
definition and exact reference thresholds unknown; window ends 2018.

## 7. Primary R Definition

Annual-mean **nighttime** surface urban-minus-rural LST contrast (°C) per
cluster, averaged over 2003-2018 (expected band `all_nighttime_UHI`; field
name unresolved). Physically: night-time stored-heat release and
morphology-driven contrast, weakly modulated by solar loading and rural
moisture. Preferable to raw urban LST because raw LST is dominated by
latitude, elevation and season, so that most of its variance is C, and
because the rural contrast removes the regional thermal background. It is a
**response** to the present urban state, measured not modelled; it overlaps S
substantially (hence M0 includes S).

## 8. Secondary / Contrast R Definitions

* Secondary: **summer daytime SUHI climatology** (2003-2018) — independent
  physical channel, heat-exposure relevant, but more confounded by the rural
  reference; used for falsification test 8.
* Contrast: none locked. Raw urban LST would be the natural negative control
  (H should add nothing after C) but requires raster processing. Optional
  exploratory outcome: 2003-2018 SUHI trend, with the explicit warning that
  trend is partly definitional with recent growth and sensor/processing
  sensitive.

## 9. Temporal Design

The product forces a 2003-2018 window. Option A (response after T=2020) and C
(before all H) are impossible; the design is D/E: overlapping and straddling
H's last epochs, centred ≈2010.5, with S(2020) after the window. Therefore:
predictive-association / transferability interpretation only; reverse
pathways cannot be excluded. Pre-registered strict-precedence sensitivities:
H≤2000 rebased to B(2000), and the T=2015 endpoint. A result that exists only
with the overlapping H is reported as recent-growth association, not legacy.

## 10. Context C Design

Existing UCDB fields only (verified locally: complete for all 11,422 cities
for CL_B01/B04/B07/B12/B15; Köppen missing for 3):

* C0: latitude, longitude, elevation (Gate 1 C).
* C1: C0 + decadal-mean annual mean temperature (CL_B01, 2000 & 2010 decades)
  + log annual precipitation (CL_B12).
* C2: C1 + temperature seasonality (CL_B04) + precipitation seasonality
  (CL_B15) + Köppen major group.
* CL_B* are C3S reanalysis bioclimatic indicators (Wouters 2021) per the
  official data dictionary. Decade boundaries behind "2000/2010" must be
  confirmed in the dictionary before use. CL_WDS excluded (derivation
  ambiguous); CL_B07 excluded (collinear).

Confounders controlled: latitude/solar geometry, elevation, background
temperature, aridity, seasonality, regime, (size via S). **Possible mediators
not controlled in primary:** urban greenness (GR_AVG_GRN, GR_SQM/SHB), tree
height (GR_CTH), land-use fractions (LU_HEC); socioeconomic classes
(GC_DEV_*) excluded as development proxies. Unmeasured: distance to coast,
humidity, wind. Existing UCDB climate variables **are sufficient** for
C0/C1/C2 with no new raster.

## 11. H Design for Gate 2

Option A (+D): **fixed-boundary H primary on the full matched sample
(≤10,915), dynamic-boundary H as sensitivity on the 4,739 subsample, plus
boundary-robust descriptors.** Justification: no missingness and no 1975
survival filter in fixed H; dynamic complete-history sampling
over-represents pre-1975 cities and has zero YOB>1990 cities (1005-5);
Landscan extents are fixed so fixed H is the geometrically consistent partner;
H_fixed and H_dynamic agree strongly (r≈0.89). Recently urbanized cities stay
in the primary sample and are a pre-registered stratum.

## 12. Crosswalk Strategy

`results/1005-6/crosswalk_design.md`. Geometry first: UCDB polygons (Mollweide)
vs product polygons/points; accepted = mutual one-to-one, area ratio in
[0.25, 4], overlap ≥0.5, country agreement when available; ambiguous =
many-to-one/one-to-many/partial (aggregate sensitivity); rejected = no
geometric support (>10 km). Names are QA only, never primary. Matchability
cannot be estimated without the file; no N is claimed. The 4,739 MTUC
subsample links by `ID_UC_G0` through the existing 1005-5 crosswalk.

## 13. Gate 2 Experiment 1 Pre-registration

M0: R ~ S + C1; M1: R ~ S + C1 + H. Random forest (fixed hyperparameters),
ridge secondary. Leave-region-out + spatially blocked K-fold. Primary:
pooled out-of-fold ΔR² with spatial-block bootstrap CI; ΔRMSE/ΔMAE secondary;
shuffled-H null reference. In-sample improvement is not evidence.
(`gate2_preregistration.md` §6.)

## 14. Gate 2 Experiment 2 Pre-registration

Twins = mutual 10-NN pairs in S3+C1 with ≥200 km separation. Primary:
partial Spearman ρ(D_R, D_H | D_SC, D_geo); secondary tercile contrast;
city-cluster bootstrap and Mantel-style stratified permutation. Hand-picked
examples are not evidence.

## 15. Gate 2 Experiment 3 Pre-registration

Leave-region-out donor pools; A0 (S+C1) vs A1 (S+C1+H, block-balanced
scaling), K=10 inverse-distance donor mean; primary ΔRMSE_transfer; null via
within-strata shuffled H and random matched-variance 9-vector; within-region
donors secondary.

## 16. Falsification Tests

All 14 required tests are listed with an explicit "counts AGAINST" criterion in
`gate2_preregistration.md` §7, together with decision rules (§8).
**Strong FOR:** ΔR²≥+0.02 with CI excluding 0, above the shuffled null, in ≥4/6
regions, ≥20% of Δ beyond pseudo-history, surviving C2 and H≤2000, plus
positive Exp 2/3. **AGAINST:** ΔR²<0.005 with CI including 0, Δ within the
shuffled null, Δ explained by pseudo-history/redundant S features, negative in
≥4 regions, or collapse under C2. Thresholds are judgment-based, fixed before
R is seen, and open to PI revision before data are opened.

## 17. Threats to Validity

`results/1005-6/validity_threats.csv`, ranked: (1) climate/background
confounding; (2) rural-reference definition/contamination; (3) urban-boundary
mismatch; (4) crosswalk selection error; (5) temporal overlap; (6) H–S
redundancy/mediation; (7) spatial autocorrelation; (8) regional imbalance; (9)
MODIS retrieval/cloud sampling; (10) vegetation as mediator; (11) size; (12)
MAUP; (13) latitude; (14) elevation; (15) coastal effects (unmeasured); (16)
recent-urbanization stratum.

## 18. Data Volume / Computational Scale

Primary file ~4.7 MB zipped (single report; to confirm). Monthly/yearly
cluster packages unknown (optional). Pixel GeoTIFFs (hundreds of MB each) and
MODIS rasters are not needed. UCDB climate fields are already local. All Gate 2
computation is city-level (≤10⁴ rows); the twin graph uses kNN pairs, not all
~5×10⁷ pairs. Global raster required: **NO**.

## 19. Acquisition Software

* `scripts/download_thermal_response.py` — explicit `--url` (none hard-coded),
  `--dest`, `--dataset-key` provenance (DOIs flagged "NOT verified" where
  applicable), original filename, no overwrite, `.part` resume, retries,
  HTTP errors fail clearly, UTC log + SHA-256, optional bearer token from an
  env var stripped on cross-host redirects, non-loopback URL refused unless
  `--confirm-human-operator`, no side effects on import.
* `scripts/verify_thermal_response.py` — existence, size, SHA-256, CSV header/
  rows/columns, ZIP integrity, shapefile member check, DBF field names parsed
  with the standard library.
* `scripts/thermal_design_lock.py` — regenerates the audit tables, decision
  and manifest template (no network).
* Tests: `tests/test_thermal_acquisition.py` (20), `tests/test_thermal_design_artifacts.py`
  (9). Only synthetic loopback servers and synthetic files were used.

## 20. Human Download Plan

See `results/1005-6/download_plan.md`. Step 0 (documentation only, mandatory),
Step 1 (download the "UHI (urban cluster means)" shapefile zip; browser
preferred because Earthdata login is interactive; script route with token +
session-scoped proxy variables only), Step 2 (verify), Step 3 (report back).
No `setx`, no global proxy/Git changes. Claude executed none of it.

## 21. Evidence FOR Locking the Thermal Design

* A physically argued single primary R and secondary R, chosen for
  interpretability rather than expected effect.
* Official, DOI-bearing, ~5 MB city-level source with documented method and
  fixed extent matching fixed H.
* Climate controls available locally with complete coverage; mediators
  identified and excluded.
* Complete pre-registration with explicit AGAINST criteria and 14
  falsification tests; crosswalk protocol with fixed tolerances.
* No raster or new-package need.

## 22. Evidence AGAINST Locking the Thermal Design

* Landing pages, README and documentation PDFs could not be read: schema,
  geometry type, ID, field names, package contents, cluster count, tropical
  summer definition, rural-pixel thresholds, night-overpass combination are
  all UNRESOLVED.
* Window 2003-2018 precedes T=2020 and overlaps H: no temporal-legacy claim.
* Fixed Landscan clusters may merge cities; rural reference is generalized and
  sensitive to irrigation/agriculture/phenology; only one product has a
  verified access path, and the alternate-reference product has no verified
  city table.
* Cluster count inconsistent across versions (7,374 vs >10,000).

## 23. Thermal Design Decision

**THERMAL DESIGN = PROVISIONAL** (`results/1005-6/thermal_design_decision.json`).
Not biased toward LOCKED: the unresolved items are factual gaps about the
single recommended file, resolvable in minutes by a human reading the SEDAC
documentation page, which is why the next action is Step 0 rather than a
change of design.

## 24. Exact Files Created/Modified

Created:
* `prompts/prompt1005-6.txt` (from the interrupted run; verified intact)
* `scripts/download_thermal_response.py` (rewritten after audit)
* `scripts/verify_thermal_response.py` (rewritten after audit)
* `scripts/thermal_design_lock.py`
* `tests/test_thermal_acquisition.py` (rewritten; stray statement removed)
* `tests/test_thermal_design_artifacts.py`
* `results/1005-6/thermal_candidate_audit.csv`, `thermal_source_audit.csv`,
  `thermal_design_decision.json`, `gate2_preregistration.md`,
  `crosswalk_design.md`, `validity_threats.csv`, `data_manifest_template.csv`,
  `download_plan.md`, `run_metadata.json`
* `reports/report1005-6.md`

Modified: none. Nothing from 1005-1 through 1005-5 was touched. Read-only
local inspection (not modified): UCDB GeoPackage/PDF and the 1005-4/1005-5
reports/results.

## 25. Reproducibility / Integrity Statement

No research data downloaded; zero research-data network transfers by Claude.
No packages installed. Environment: conda `py311`. The design tables are
regenerated deterministically by `scripts/thermal_design_lock.py`. No
stochastic computation (no seed needed). Metadata statuses distinguish
verified from inferred; WebFetch blockage is disclosed. Full test suite:
65 passed.

## 26. Questions for PI Review

**Q1.** Annual-mean nighttime SUHI climatology.
**Q2.** Night-time surface (LST) urban-minus-rural temperature contrast in °C,
averaged 2003-2018, per urban cluster.
**Q3.** Raw urban LST is mostly latitude/elevation/season; the contrast removes
the regional thermal background and is the quantity of interest for urban
form/history.
**Q4.** Nighttime.
**Q5.** Annual (summer daytime is the secondary).
**Q6.** 2003-2018 (product composite).
**Q7.** Yes: overlaps H epochs 2005-2015 and precedes S(2020); predictive
association/transfer only, no temporal-legacy claim; strict-precedence
sensitivities pre-registered.
**Q8.** YCEO SUHI v4 (urban-cluster means); Yang 2024 only as an alternate
rural-reference check.
**Q9.** Official NASA SEDAC archive of a peer-reviewed-method product (YCEO);
Yang 2024 is peer-reviewed, community-hosted.
**Q10.** "Over 10,000" clusters claimed for v4; usable matched UCDB cities
unknown until the file is inspected.
**Q11.** ≈4.7 MB for the primary city-level file (single report); other
cluster packages unknown.
**Q12.** Yes (SUHI contrast by construction).
**Q13.** Non-urban pixels (ESA CCI land cover) within the same fixed Landscan
urban extent, no fixed buffer, filtered for elevation difference and urban
share (thresholds unresolved).
**Q14.** Generalized reference; irrigation/agriculture/phenology
contamination; peri-urban disturbance; fixed extent; cluster merging.
**Q15.** Polygon/coordinate crosswalk (mutual one-to-one, area ratio and
overlap bounds, country check); names for QA only.
**Q16.** Latitude, longitude, elevation, background temperature, annual
precipitation (C1); seasonality and Köppen group (C2).
**Q17.** Urban greenness/vegetation, tree height, land-use fractions;
socioeconomic class proxies; built volume is handled by the S1/S2/S3 gradient.
**Q18.** Fixed-boundary primary, dynamic-boundary sensitivity (plus
boundary-robust descriptors).
**Q19.** Keep in the primary fixed-boundary sample, report as a stratum
(test 12); do not interpolate dynamic-boundary history.
**Q20.** Pooled out-of-fold ΔR² (M1 − M0), leave-region-out, with spatial
block bootstrap CI and shuffled-H null.
**Q21.** ΔR²≥+0.02, CI excluding 0, above the shuffled null, in ≥4/6 regions,
not explained by pseudo-history, surviving C2 and H≤2000, with positive
Exp 2/3.
**Q22.** ΔR²<0.005 with CI including 0, Δ within the null, explained by
S-derived pseudo-history, negative in ≥4 regions, or collapse under C2.
**Q23.** Partial Spearman ρ(D_R, D_H | D_SC, D_geo) among mutual-kNN twins,
with Mantel-style stratified permutation.
**Q24.** ΔRMSE_transfer of A1 (S+C+H) vs A0 (S+C) with leave-region-out donors,
against shuffled/random-H nulls.
**Q25.** Regional climate/aridity structure jointly driving development
history and SUHI through the rural reference.
**Q26.** The rural-reference/urban-cluster definition (generalized reference;
fixed Landscan extent mismatching UCDB footprints).
**Q27.** Yes.
**Q28.** No.
**Q29.** First the documentation (Step 0); then the "UHI (urban cluster
means)" shapefile zip from the SEDAC page, exact filename to be recorded.
**Q30.** See `results/1005-6/download_plan.md` Step 1 (script route needs the
exact file URL from the SEDAC page, which Claude could not read and did not
guess; browser download is preferred).
**Q31.** PROVISIONAL.
**Q32.** NOT YET.
