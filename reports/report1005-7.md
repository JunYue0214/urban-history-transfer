# Execution Report 1005-7

Execution ID: 1005-7 · Source prompt: prompts/prompt1005-7.txt · Previous: 1005-6
Task: Thermal Data Validation + UCDB Crosswalk Gate
Results: results/1005-7/ · Figures: figures/1005-7/

**No research data were downloaded and no network access occurred (tests enforce this for the library code). The human-downloaded ZIP was only read; its SHA-256 was identical before and after the run. No Gate 2 outcome model was run: the crosswalk is built from geometry alone, and response values were used only for QC.**

---

## 1. Executive Summary

* The ZIP is valid and the file is what 1005-6 hoped for: 10,136 urban-cluster polygons with directly verified `Annual_nig` (primary) and `Summer_day` (secondary), each valid for 9,995 clusters (141 missing, 1.4%), no sentinel codes, no invalid/empty/duplicate geometry.
* The ZIP also contains the official documentation PDF, which resolved most 1005-6 unknowns (and corrected one: urban extents are **Natural Earth 1:10m polygons, not Landscan**).
* The cluster ontology is genuinely different from GHSL urban centres. 422 clusters contain ≥2 UCDB centres (1,281 centres); only 3,856 linked clusters are 1:1 at the link level, and **5,848 of the 10,915 UCDB sample cities have no substantive YCEO cluster at all**. Scientific decision: **option C, a cluster-level response** — the Gate 2 unit should be the YCEO cluster with S/H aggregated over its UCDB centres, never one R copied to several cities.
* Defensible sample: **2,192 cluster units** (2,046 single-city, 146 multi-city aggregates) covering **2,459 UCDB cities (22.5%)**. They are globally distributed but biased toward larger and older cities.
* **THERMAL DESIGN = PROVISIONAL. GATE 2 EXECUTION = NOT YET.** The data and R are sound; what remains is a sample-size and selection-bias decision that is the PI's, because 2,192 units is below the 3,000-city floor I pre-registered in 1005-6. Not biased toward LOCKED.

## 2. Raw File Integrity

`data/raw/thermal_response/sdei-yceo-sfc-uhi-v4-urban-cluster-means-shp.zip` — **5,074,854 bytes**, SHA-256 `d5575541de2c8972d62f9dbd86888869bf568679bab75194495492dddceee364`, ZIP test passed (no bad member), mtime 2026-10-05T10:50:51Z. Hash unchanged after the run. Path is git-ignored (`data/raw/*`). Extracted only to `data/interim/1005-7/yceo_suhi_v4/` (also ignored). Record: `thermal_raw_manifest.json`.

## 3. Exact ZIP Contents

`sdei-yceo-sfc-uhi-v4-documentation.pdf` (540,972 B); `All_shp.shp` (4,910,116), `.shx`, `.dbf` (1,997,209), `.prj` (335), `.cpg`, `.sbn`, `.sbx`, `.fix`. Required components .shp/.shx/.dbf/.prj all present. Member dates 2022-02-16 (shapefile) and 2023-09-05 (PDF).

## 4. Shapefile Schema

Fields (`yceo_schema_audit.csv`, `yceo_field_summary.csv`): `Annual_nig`, `Annual_day`, `Winter_nig`, `Winter_day`, `Summer_nig`, `Summer_day` (float, 141 missing each, same 141 rows), `hasPlace` (int; values −1,0,1,2,5,6,15,20 — **undocumented, not used**), `FeatureCla` (constant "Urban area"), `Lon`, `Lat` (cluster coordinates), `Code` (unique int 0–11996, no duplicates), `FID_1` (unique string). There is **no name, country, region, area or population field**. No −999/−1 sentinels in the SUHI fields (−1 appears only in `hasPlace`).

## 5. Geometry / CRS

10,136 features (dbf count equal): 10,135 Polygon + 1 MultiPolygon; EPSG:4326 (WGS 84); bounds lon −157.98…178.03, lat −49.98…69.70; 0 invalid, 0 empty, 0 zero-area, 0 duplicate geometries. Equal-area (ESRI:54009) area: median 33.8 km², p99 1,188 km², max 18,789 km². `Lon`/`Lat` match polygon interior points to within 0.71°/0.20° (they are cluster-level coordinates, not exact centroids). (`yceo_geometry_qc.json`.)

## 6. Primary R Verification

Exactly one field matches annual-night: **`Annual_nig`**, unit °C (documentation). It is a 2003–2018 composite per the bundled documentation (`UHI_all_averaged`: "averaged across 2003 to 2018 for annual, summer and winter periods"); the field name itself carries no period, so this rests on the documentation, not on the shapefile. Valid 9,995, missing 141. min −1.897, p01 −0.478, p05 −0.123, **median 0.388**, mean 0.437, p95 1.208, p99 1.701, max 3.031. <0: 1,022 (10.2%); =0: 2; >0: 8,971.

## 7. Secondary R Verification

**`Summer_day`** (summer by hemisphere: JJA north, DJF south): valid 9,995, missing 141; min −6.262, p01 −2.633, p05 −1.006, median 1.017, mean 0.960, p95 2.731, p99 3.566, max 5.517; <0: 1,672 (16.7%); =0: 2; >0: 8,321. Daytime SUHI is about 2.6× the night median and far more often negative, consistent with the 1005-6 reasoning for choosing night as primary. All six composites are in `thermal_response_qc.csv`; annual-night correlates ≈0.03 with annual-day, so they are nearly independent channels.

## 8. Response QC

Figures: `fig1_response_histograms`, `fig2_primary_map_missing`, `fig3_primary_by_region`, `fig4_crosswalk_structure`. Distribution is unimodal, slightly right-skewed, no spikes; no trimming or winsorizing applied. Negative values are kept (physically plausible). The 200 extremes (outside p01–p99) are not geometry artifacts: median area 50 vs 33 km², 48% vs 42% linked to UCDB. Primary R rises with cluster size (Spearman 0.375 with area), confirming size must stay in S. The 141 missing clusters are larger than average (median 116 km² vs 33 km²), so missingness is not random (large clusters lacking usable rural pixels); only 12 strict and 3 dominant pairs are lost to it. Region medians (nearest-UCDB-country region, approximate): Asia 0.53, South America 0.43, Africa 0.40, North America 0.33, Europe 0.32, Oceania 0.26 (`thermal_primary_by_region.csv`).

## 9. YCEO Urban-Cluster Ontology

From the documentation: clusters are Natural Earth 1:10m "Urban areas" polygons (fixed, "may be outdated or erroneous, especially for less urbanized areas"); SUHI = mean LST of urban pixels minus mean of non-urban, non-water pixels *within the cluster*, rural pixels limited to ±50 m of the urban median elevation; MODIS LST error ≤3 °C; Terra+Aqua combined; 10,136 clusters in v4 (7,374 in v1). Clusters are "larger urban agglomerations" and not cities. So a cluster **can and often does** contain several GHSL centres (see §12), and the rural reference is inside the same polygon, so R depends on the polygon boundary itself.

## 10. UCDB Crosswalk Method

Geometry-only; names unusable (YCEO has none) and country unusable except as cross-country QA among a cluster's UCDB centres. UCDB (10,915-city Gate 1 sample, 22 invalid polygons repaired with `make_valid`) and YCEO both in ESRI:54009. Substantive link = intersection / min(area) ≥ 0.5. Classes per `crosswalk_rules.json`. **Threshold revision, made after inspecting geometry only and before looking at R:** the 1005-6 "overlap ≥ 0.5" was reinterpreted as overlap/min-area, and a strict IoU floor of **0.25** was added (not 0.5): the median IoU of clean 1:1 pairs is 0.39 because the two products are different ontologies, so IoU ≥ 0.5 would keep only 944 of 3,739 clean pairs. IoU ≥ 0.5 is reported as a tight sensitivity flag.

## 11. Crosswalk Results

Pair classes (`crosswalk_summary.json`, full audit in `ucdb_yceo_crosswalk.csv`, 17,351 rows incl. unmatched/excluded objects): A strict 1:1 **2,988**; B dominant **70**; D many-to-one ambiguous 844 (+240 minor centres beside a dominant one); C one-to-many 100; J complex 75; E cross-country clusters 70 pairs (24 clusters); H 1:1 footprint mismatch 751; F unmatched UCDB 5,848 (528 with sliver-only overlaps); unlinked clusters 5,858; G QC-excluded 507 UCDB (YOB > 2020) and 73 unlinked clusters without response. After requiring valid R: strict 1:1 **2,976**, dominant **67**.

## 12. One-to-Many / Many-to-One Structure

* 422 YCEO clusters contain ≥2 UCDB centres (273 with 2, 77 with 3, up to 23); **1,281 UCDB centres share a cluster with another**.
* 61 UCDB centres substantially overlap ≥2 clusters; 24 clusters span countries.
* Assigning one cluster R to several UCDB cities would be **pseudo-replication** (the 1,281 centres would count as independent observations carrying ≥422 shared outcomes). Prohibited and tested (`test_no_duplicate_outcome_assignment…`).
* Aggregation feasibility (`cluster_aggregation_feasibility.csv`): for the 146 aggregate units, summing population, built-up area and volume and building H as ΣB(t)/ΣB(2020) is straightforward and cheap (pure table sums, no raster). The dominant city holds a median 84% of the built-up area, and aggregate vs dominant-city H differ little (median Euclidean distance 0.036 on a 9-vector; max 0.29), so a dominant-city sensitivity is cheap and informative.

## 13. Recommended Gate 2 Analysis Unit

**Option C: YCEO cluster (cluster-level response, S/H aggregated over contained UCDB centres).** Rule: star-shaped cluster (its centres link to nothing else), single country, valid R, all centres in the Gate 1 sample, UCDB coverage ≥ 50% of the cluster area; each cluster once. Option A (city) is wrong for 422 clusters; option B (dominant city) is kept as sensitivity; option D (unsuitable) is not warranted because 93% of units are single-city clusters.

## 14. Matched Sample

N units **2,192** (2,046 single, 146 multi-city) = **2,459 UCDB cities**, vs 10,915 in the source sample. 5,848 sample cities are unlinked, 2,009 sit in ambiguous or mismatched relationships. Prior pair counts of 3,043 strict+dominant clusters shrink to 2,192 because the unit rule additionally demands ≥50% UCDB coverage of the cluster, which removes 1,088 clusters (a loosened coverage rule would be a PI choice, not mine to make post hoc).

## 15. Matched-vs-Unmatched Bias

`matched_sample_bias.csv` (SMD = matched − unmatched, pooled SD):

| Variable | Matched | Unmatched | SMD |
|---|---|---|---|
| population 2020, median | 231,250 | 94,031 | 0.39 (log10: **1.02**) |
| built-up km² 2020, median | 10.5 | 3.0 | 0.47 (log10: **1.28**) |
| year of birth (YOB), median | 1975 | 1985 | **−0.56** |
| share urbanized after 1975 | 34.8% | 59.1% | **−0.50** |
| early developed fraction 1990 | 0.545 | 0.537 | 0.04 |
| recent expansion since 2000 | 0.272 | 0.294 | −0.13 |
| weighted development timing | 1998.8 | 1998.2 | 0.16 |
| |latitude| | 29.0 | 25.6 | 0.25 |

**Recently urbanized cities are disproportionately lost**, and so are small cities (YCEO uses coarse 1:10m polygons). The history *shape* descriptors are only mildly biased (|SMD| ≤ 0.16), which is reassuring for H variation, but the size/age shift means conclusions apply to the larger, older-established part of the urban system.

## 16. Regional Coverage

| Region | Source | Matched | Rate | Source share → matched share |
|---|---|---|---|---|
| Asia | 6,273 | 1,156 | 18% | 57.5% → 47.0% |
| Africa | 2,006 | 372 | 19% | 18.4% → 15.1% |
| Europe | 1,154 | 311 | 27% | 10.6% → 12.6% |
| North America | 715 | 257 | 36% | 6.6% → 10.5% |
| South America | 715 | 335 | 47% | 6.6% → 13.6% |
| Oceania | 52 | 28 | 54% | 0.5% → 1.1% |

All six regions are present and five have N ≥ 30 cities (Oceania 28 cities), so the sample is still global but under-represents Asia and Africa.

## 17. Temporal Recheck

The shapefile holds **one composite value per cluster per period**: no year or month attributes (verified from the field list). Per the bundled documentation it is the 2003–2018 mean. Gate 2 scope is not expanded; the 1005-6 interpretation (predictive association, no legacy claim) stands.

## 18. Evidence FOR Thermal Design Lock

Valid, complete, small file (4.9 MB); primary and secondary R exist uniquely, 98.6% valid, plausible distribution; documented methodology (and the rural reference is the one assumed in 1005-6); crosswalk is geometry-first and auditable; cluster-level aggregation is feasible without rasters; H shape is not strongly selected; no further data needed.

## 19. Evidence AGAINST Thermal Design Lock

N = 2,192 units is below the pre-registered 3,000 floor; strong size/age selection; ontology mismatch (median IoU 0.39) means S/H and R cover different footprints; undocumented `hasPlace` and no identifier semantics (`Code`/`FID_1` are YCEO-internal, with no link to Natural Earth documented here); response is polygon-dependent; missingness correlates with size; time window overlaps H.

## 20. Thermal Design Decision

**THERMAL DESIGN = PROVISIONAL.** Raw integrity, primary-R identity and ontology are resolved; what is not resolved is whether a ~2,200-unit, size- and age-biased sample can still answer the Gate 2 question and with what bias handling.

## 21. Gate 2 Execution Decision

**GATE 2 EXECUTION = NOT YET.** Needed: a narrowly scoped PI decision (amend the N floor; choose the bias handling: reweighting, size-/region-stratified analysis, or common-support restriction; confirm the cluster unit and the ≥50% coverage rule), recorded as an amendment to the 1005-6 pre-registration (which I did not edit; it belongs to a prior execution). Optionally one small step to compute those sensitivities (looser coverage, IoU, mismatch inclusion) on geometry alone. No new data are needed.

## 22. Exact Files Created/Modified

Created: `prompts/prompt1005-7.txt`; `scripts/yceo_crosswalk.py`; `scripts/run_1005_7_pipeline.py`; `tests/test_yceo_crosswalk.py`; `results/1005-7/` (`thermal_raw_manifest.json`, `yceo_schema_audit.csv`, `yceo_field_summary.csv`, `yceo_geometry_qc.json`, `thermal_response_qc.csv`, `crosswalk_rules.json`, `ucdb_yceo_crosswalk.csv`, `crosswalk_summary.json`, `matched_sample_bias.csv`, `matched_region_coverage.csv`, `thermal_primary_by_region.csv`, `cluster_aggregation_feasibility.csv`, `thermal_design_lock.json`, `run_metadata.json`); `figures/1005-7/fig1–fig4`; `reports/report1005-7.md`. Untracked/ignored: `data/interim/1005-7/*`. Modified: none. 1005-1…1005-6 artifacts untouched.

## 23. Reproducibility / Integrity Statement

Run with `conda run -n py311 python scripts/run_1005_7_pipeline.py` (deterministic, no randomness; geopandas 1.2.0, shapely 2.1.2, pyproj 3.7.2). Raw ZIP hash before = after. No downloads or URL access, no packages installed. Gate 1 sample reproduced from the 1005-4 code (N = 10,915). The raw ZIP is not committed. Region labels for YCEO clusters are approximate (nearest UCDB centroid's country). The period of `Annual_nig` is taken from the bundled documentation, not the file.

## 24. Questions for PI Review

**Q1** Yes. **Q2** 5,074,854 bytes; SHA-256 `d5575541de2c8972d62f9dbd86888869bf568679bab75194495492dddceee364`. **Q3** documentation PDF + All_shp (.shp .shx .dbf .prj .cpg .sbn .sbx .fix). **Q4** 10,136. **Q5** Polygon (10,135) + 1 MultiPolygon. **Q6** EPSG:4326. **Q7** `Code` (unique int) and `FID_1` (unique string); no documented link to external ID systems; no name/country. **Q8** `Annual_nig`. **Q9** It is the 2003–2018 composite per the bundled documentation; the file has one value per cluster and no year/month fields. **Q10** valid 9,995, missing 141. **Q11** median 0.39 °C, mean 0.44, p05 −0.12, p95 1.21, range −1.90…3.03; 10.2% negative. **Q12** `Summer_day`. **Q13** 2,988 strict pairs (2,976 with valid R); 944 of them have IoU ≥ 0.5. **Q14** 70 dominant (67 valid R). **Q15** 422. **Q16** 1,281. **Q17** Yes, if one R were assigned to several cities. **Q18** Switch to the YCEO cluster. **Q19** Yes (sums plus ΣB(t)/ΣB(2020); table sums only). **Q20** 2,192 units (2,459 cities). **Q21** Yes, all six regions, but Asia/Africa are under-represented and Oceania has 28 cities. **Q22** Larger and older cities favoured (log-pop SMD 1.0, YOB SMD −0.56). **Q23** Yes (35% vs 59% urbanized after 1975). **Q24** No: 1.4% missing (but skewed to large clusters), no sentinels, no geometry-driven extremes. **Q25** No. **Q26** No. **Q27** PROVISIONAL. **Q28** NOT YET.
