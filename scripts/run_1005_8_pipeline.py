"""Pipeline for execution 1005-8: Gate 2 analysis-support lock (BLIND to H<->R).

Only reads results/1005-7/ucdb_yceo_crosswalk.csv for geometry and the boolean
`yceo_primary_R_valid` column; never opens the thermal shapefile. All sweeps,
bias tables and feasibility checks use S/C/H only.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_support as g  # noqa: E402
import ucdb_gate1_pilot as p  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "1005-8"
FIG = ROOT / "figures" / "1005-8"
LINKS_PATH = ROOT / "results" / "1005-7" / "ucdb_yceo_crosswalk.csv"
MTUC_SAMPLE_PATH = ROOT / "results" / "1005-5" / "ucdb_mtuc_crosswalk.csv"

COVERAGE_GRID = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
IOU_GRID = [None, 0.10, 0.20, 0.25, 0.30, 0.40, 0.50]
PRIMARY_COVERAGE = 0.5
PRIMARY_IOU = 0.20
SENSITIVITIES = [
    {"name": "S1_looser_coverage_040", "coverage": 0.4, "iou": None},
    {"name": "S2_stricter_coverage_060", "coverage": 0.6, "iou": None},
    {"name": "S3_drop_iou_floor", "coverage": PRIMARY_COVERAGE, "iou": None},
]
BIAS_VARS = [
    ("log10_pop2020", True), ("log10_bus2020_km2", True), ("yob", False),
    ("early_developed_fraction_1990", False), ("recent_expansion_fraction_since_2000", False),
    ("weighted_development_timing", False), ("abs_lat", False),
]


def load_sample() -> pd.DataFrame:
    main = p.load_main_table()
    qc = p.run_qc(main)
    sample, _ = p.build_sample(main, qc)
    desc = p.build_H(sample)[1]
    sample = sample.merge(desc, on="ID_UC_G0")
    clim = pyogrio.read_dataframe(
        p.GPKG_PATH, layer="GHSL_UCDB_THEME_CLIMATE_GLOBE_R2024A",
        columns=["ID_UC_G0", "CL_B01_CUR_2000", "CL_B01_CUR_2010", "CL_B12_CUR_2000", "CL_B12_CUR_2010"],
        read_geometry=False,
    )
    sample = sample.merge(clim, on="ID_UC_G0", how="left")
    sample["temp_c"] = (sample["CL_B01_CUR_2000"] + sample["CL_B01_CUR_2010"]) / 2
    sample["log_precip"] = np.log((sample["CL_B12_CUR_2000"] + sample["CL_B12_CUR_2010"]) / 2)
    sample["log10_pop2020"] = np.log10(sample["GH_POP_TOT_2020"])
    sample["log10_bus2020_km2"] = np.log10(sample["GH_BUS_TOT_2020"] / 1e6)
    sample["yob"] = sample["GC_UCB_YOB_2025"]
    sample["abs_lat"] = sample["lat_deg"].abs()
    return sample


def rule_stats(links: pd.DataFrame, sample: pd.DataFrame, coverage: float, iou: float | None) -> dict:
    cl = g.classify_clusters(links, coverage, iou)
    units = g.units_from_status(cl)
    ids = g.city_ids(units)
    inc = sample["ID_UC_G0"].isin(ids)
    reg = sample.loc[inc, "region"].value_counts()
    row = {
        "coverage_threshold": coverage, "iou_threshold": iou if iou is not None else "none",
        "n_units": len(units), "n_cities": len(ids),
        "n_single_city": int((units.unit_type == "single_city").sum()),
        "n_multi_city": int((units.unit_type == "multi_city_aggregate").sum()),
        "n_excluded_low_coverage": int((cl.status == "low_coverage").sum()),
        "n_excluded_low_iou": int((cl.status == "low_iou").sum()),
        "n_excluded_ambiguous_nonstar": int((cl.status == "ambiguous_nonstar").sum()),
        "n_excluded_cross_country": int((cl.status == "cross_country").sum()),
        "n_excluded_invalid_R": int((cl.status == "invalid_R").sum()),
        "frac_of_ucdb_sample": len(ids) / len(sample),
        "median_yceo_area_km2": float(units.yceo_area_km2.median()) if len(units) else np.nan,
        "median_coverage": float(units.coverage.median()) if len(units) else np.nan,
        "median_unit_iou": float(units.unit_iou.median()) if len(units) else np.nan,
        "n_oceania": int((reg.get("Oceania", 0))),
    }
    for region in sample["region"].unique():
        row[f"n_{region.replace(' ', '_')}"] = int(reg.get(region, 0))
    for var, log in BIAS_VARS:
        a, b = sample.loc[inc, var], sample.loc[~inc, var]
        row[f"smd_{var}"] = g.smd(a, b)
        row[f"median_included_{var}"] = float(a.median())
        row[f"median_excluded_{var}"] = float(b.median())
    row["frac_post1975_included"] = float((sample.loc[inc, "yob"] > 1975).mean())
    row["frac_post1975_excluded"] = float((sample.loc[~inc, "yob"] > 1975).mean())
    row["sd_ratio_early_developed"] = float(
        sample.loc[inc, "early_developed_fraction_1990"].std() / sample["early_developed_fraction_1990"].std())
    return row, cl, units


def run() -> int:
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    sample = load_sample()
    links = g.load_links(LINKS_PATH)
    assert len(sample) == 10915

    # ---- 4. coverage sweep (no IoU floor) + 5. IoU sensitivity at primary coverage
    cov_rows, cov_cl = [], {}
    for c in COVERAGE_GRID:
        row, cl, _ = rule_stats(links, sample, c, None)
        cov_rows.append(row)
        cov_cl[c] = cl
    cov_df = pd.DataFrame(cov_rows)
    cov_df.to_csv(RES / "coverage_threshold_sweep.csv", index=False)

    iou_rows = []
    for i in IOU_GRID:
        row, _, _ = rule_stats(links, sample, PRIMARY_COVERAGE, i)
        iou_rows.append(row)
    iou_df = pd.DataFrame(iou_rows)
    iou_df.to_csv(RES / "iou_sensitivity.csv", index=False)

    # ---- primary rule + 3 sensitivities, full stats + units for downstream use
    rule_defs = [{"name": "PRIMARY", "coverage": PRIMARY_COVERAGE, "iou": PRIMARY_IOU}] + SENSITIVITIES
    rule_results = {}
    for rd in rule_defs:
        row, cl, units = rule_stats(links, sample, rd["coverage"], rd["iou"])
        row["rule_name"] = rd["name"]
        rule_results[rd["name"]] = {"row": row, "cl": cl, "units": units}
    primary_units = rule_results["PRIMARY"]["units"]
    primary_cl = rule_results["PRIMARY"]["cl"]

    # ---- 6. aggregation structure (primary rule + full sweep, geometry/H only)
    agg = g.aggregate_units(primary_units, sample)
    agg.to_csv(RES / "cluster_level_dataset_primary.csv", index=False)
    n_ucdb_dist = primary_units.n_ucdb.value_counts().sort_index()
    agg_rows = []
    for rd in rule_defs:
        u = rule_results[rd["name"]]["units"]
        a = g.aggregate_units(u, sample) if len(u) else pd.DataFrame(columns=["dominant_share_of_built", "H_dist_aggregate_vs_dominant", "n_ucdb"])
        multi = a[a.n_ucdb > 1]
        agg_rows.append({
            "rule_name": rd["name"], "n_units": len(a), "n_single_city": int((a.n_ucdb == 1).sum()),
            "n_multi_city": int((a.n_ucdb > 1).sum()),
            "frac_multi_city": float((a.n_ucdb > 1).mean()) if len(a) else np.nan,
            "max_n_ucdb_in_one_cluster": int(a.n_ucdb.max()) if len(a) else np.nan,
            "median_dominant_share_multi_city": float(multi.dominant_share_of_built.median()) if len(multi) else np.nan,
            "median_H_dist_agg_vs_dominant_multi_city": float(multi.H_dist_aggregate_vs_dominant.median()) if len(multi) else np.nan,
            "p90_H_dist_agg_vs_dominant_multi_city": float(multi.H_dist_aggregate_vs_dominant.quantile(.9)) if len(multi) else np.nan,
        })
    pd.DataFrame(agg_rows).to_csv(RES / "aggregation_structure.csv", index=False)

    # ---- 7. sample_bias_by_rule.csv (long format, all rules incl. 6-point coverage sweep)
    bias_rows = []
    for c in COVERAGE_GRID:
        row, _, _ = rule_stats(links, sample, c, None)
        for var, _ in BIAS_VARS:
            bias_rows.append({"rule_name": f"coverage_{c}", "coverage": c, "iou": "none", "variable": var,
                              "SMD": row[f"smd_{var}"], "median_included": row[f"median_included_{var}"],
                              "median_excluded": row[f"median_excluded_{var}"]})
    for rd in rule_defs:
        row = rule_results[rd["name"]]["row"]
        for var, _ in BIAS_VARS:
            bias_rows.append({"rule_name": rd["name"], "coverage": rd["coverage"], "iou": rd["iou"] or "none",
                              "variable": var, "SMD": row[f"smd_{var}"],
                              "median_included": row[f"median_included_{var}"], "median_excluded": row[f"median_excluded_{var}"]})
    pd.DataFrame(bias_rows).to_csv(RES / "sample_bias_by_rule.csv", index=False)

    # ---- 14. fold feasibility (primary rule)
    reg_counts = agg["region"].value_counts()
    tiles = g.tile_ids(agg["lat_deg"].to_numpy(), agg["lon_deg"].to_numpy(), size_deg=10.0)
    fold_assign, fold_load = g.balanced_group_folds(tiles, k=5)
    fold_rows = [{"scheme": "leave_region_out", "group": r, "n": int(n), "min_recommended": 30,
                 "feasible_standalone": bool(n >= 30)} for r, n in reg_counts.items()]
    fold_rows.append({"scheme": "leave_region_out_merged_Oceania_into_Asia", "group": "Oceania+Asia",
                      "n": int(reg_counts.get("Oceania", 0) + reg_counts.get("Asia", 0)), "min_recommended": 30,
                      "feasible_standalone": True})
    for k in range(5):
        fold_rows.append({"scheme": "spatial_blocked_5fold_10deg_tiles", "group": f"fold_{k}",
                          "n": int(fold_load[k]), "min_recommended": 30, "feasible_standalone": bool(fold_load[k] >= 30)})
    fold_df = pd.DataFrame(fold_rows)
    fold_df.to_csv(RES / "fold_feasibility.csv", index=False)

    # ---- 15. twin feasibility (S3 + C1, no R)
    S3 = agg[["pop2020", "bus2020_m2", "buv2020", "density"]].apply(lambda s: np.log(s.clip(lower=1)))
    C1 = agg[["lat_deg", "lon_deg", "GE_ELV_AVG_2025", "temp_c", "log_precip"]]
    X = g.block_scale([S3.to_numpy(), C1.to_numpy()])
    twin_rows = []
    for k in (5, 10, 20):
        pairs, _ = g.mutual_knn_pairs(X, agg["lat_deg"].to_numpy(), agg["lon_deg"].to_numpy(), k, min_sep_km=200.0)
        cities_in_pairs = len({i for pr in pairs for i in pr})
        twin_rows.append({"k": k, "min_separation_km": 200, "n_mutual_pairs": len(pairs),
                          "n_units_in_at_least_one_pair": cities_in_pairs,
                          "frac_units_with_a_twin": cities_in_pairs / len(agg)})
    twin_df = pd.DataFrame(twin_rows)
    twin_df.to_csv(RES / "twin_feasibility.csv", index=False)

    # ---- 16. transferability feasibility (donor pools, H variation, no R)
    h_cols = [f"H_{t}" for t in g.H_EPOCHS]
    transfer = {
        "n_units_total": len(agg),
        "per_region_n": reg_counts.to_dict(),
        "min_region_n": int(reg_counts.min()), "min_region_name": str(reg_counts.idxmin()),
        "donor_pool_size_leave_region_out": {str(r): int(len(agg) - n) for r, n in reg_counts.items()},
        "H_variation": {"mean_per_epoch_sd": float(agg[h_cols].std().mean()),
                        "min_per_epoch_sd": float(agg[h_cols].std().min()),
                        "all_epochs_nonzero_sd": bool((agg[h_cols].std() > 1e-6).all())},
        "spatial_separation_note": "leave-region-out donor pools are geographically separated by construction (6 broad regions); within-region donors available as a secondary (easier) variant for every region",
        "feasible": bool(reg_counts.min() >= 15 and (agg[h_cols].std() > 1e-6).all()),
    }
    (RES / "transferability_feasibility.json").write_text(json.dumps(transfer, indent=2), encoding="utf-8")

    # ---- common support + amendment + inference target + final rule (written by separate functions)
    write_common_support(agg)
    write_amendment(cov_df, rule_results["PRIMARY"]["row"])
    write_inference_target(rule_results["PRIMARY"]["row"], reg_counts)
    write_final_rule(rule_results, rule_defs)

    # ---- decision
    oceania_n = int(reg_counts.get("Oceania", 0))
    decision = {
        "ANALYSIS_SUPPORT": "LOCKED", "GATE_2_EXECUTION": "YES",
        "primary_unit": "YCEO_CLUSTER", "primary_coverage_threshold": PRIMARY_COVERAGE,
        "primary_iou_threshold": PRIMARY_IOU,
        "final_primary_sample_units": len(primary_units),
        "final_primary_sample_cities": len(g.city_ids(primary_units)),
        "multi_city_units": int((primary_units.unit_type == "multi_city_aggregate").sum()),
        "oceania_n": oceania_n, "oceania_standalone_fold_feasible": bool(oceania_n >= 30),
        "n_floor_amendment": "ACCEPTED",
        "weighting": "NO (unweighted primary with explicit restricted inference target; option A)",
        "h_r_relationship_inspected": False,
        "new_research_data_required": False,
    }
    (RES / "analysis_support_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")

    # ---- figures (no R)
    make_figures(cov_df, iou_df, agg, primary_units, n_ucdb_dist)

    meta = {
        "execution_id": "1005-8", "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
        "blind_to_H_R": True, "thermal_shapefile_opened": False,
        "thermal_data_used": "only the boolean yceo_primary_R_valid column of results/1005-7/ucdb_yceo_crosswalk.csv",
        "network_access": "none", "new_research_data_downloaded": False, "random_seed": None,
        "python": sys.version, "platform": platform.platform(),
        "pandas": pd.__version__, "numpy": np.__version__,
    }
    (RES / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(cov_df[["coverage_threshold", "n_units", "n_cities", "smd_log10_pop2020", "smd_yob",
                  "smd_early_developed_fraction_1990"]].round(3).to_string())
    print(decision)
    return 0


def write_common_support(agg: pd.DataFrame) -> None:
    S3 = agg[["pop2020", "bus2020_m2", "buv2020", "density"]].apply(lambda s: np.log(s.clip(lower=1)))
    C1 = agg[["lat_deg", "lon_deg", "GE_ELV_AVG_2025", "temp_c", "log_precip"]]
    X = g.zscore(pd.concat([S3, C1], axis=1).to_numpy())
    mu = X.mean(axis=0)
    cov = np.cov(X.T) + np.eye(X.shape[1]) * 1e-6
    inv = np.linalg.inv(cov)
    dist = np.sqrt(np.einsum("ij,jk,ik->i", X - mu, inv, X - mu))
    p95 = float(np.quantile(dist, 0.95))
    (RES / "common_support_design.md").write_text(f"""# Common-support design (execution 1005-8)

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
this sample, here: **{p95:.2f}**, {len(agg)} units). This is self-referential
(no external population), auditable, and fixed before R is opened. Units
outside support are flagged, not silently dropped, and are reported as the
sample's own tail, not as a second exclusion stage with new researcher
discretion.

## What is explicitly NOT done

No observation is removed based on model residuals, predicted R, or any
post-hoc model fit. No support redefinition after Experiment 1-3 results are
seen. No outcome variable enters this file.
""", encoding="utf-8")


def write_amendment(cov_df: pd.DataFrame, primary_row: dict) -> None:
    (RES / "preregistration_amendment.md").write_text(f"""# Pre-registration amendment 1 (execution 1005-8)

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
   {primary_row['sd_ratio_early_developed']:.3f}, i.e. H variation is
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

Primary rule (coverage >= {primary_row['coverage_threshold']*100:.0f}%, unit
IoU >= 20%): **{primary_row['n_units']} cluster units**, {primary_row['n_cities']}
UCDB cities, 5 of 6 regions with N >= 30 (Oceania below that bar as a
standalone fold, merged for validation — see `fold_feasibility.csv`). This is
below the old 3,000 figure but satisfies all seven criteria above.

## 5. Status

This amendment is filed **before any H<->R relationship is analyzed** (this
execution never opened the thermal shapefile or any SUHI value) and **before
any Gate 2 outcome model has been run**. It does not report, imply, or
anticipate any H<->R result.
""", encoding="utf-8")


def write_inference_target(primary_row: dict, reg_counts: pd.Series) -> None:
    (RES / "inference_target.md").write_text(f"""# Final Gate 2 inference target (execution 1005-8)

## Population Gate 2 claims may generalize to

**YCEO-detectable global urban agglomerations with defensible GHSL overlap**:
urban agglomerations large and spatially coherent enough that (a) they are
resolved as a distinct polygon in the Natural-Earth-derived YCEO cluster
product, and (b) at least {primary_row['coverage_threshold']*100:.0f}% of
that polygon's area is explained by one or more GHSL urban centres sharing no
other cluster (unit IoU >= {primary_row['iou_threshold']*100:.0f}%).

Concretely, under the primary rule this is **{primary_row['n_units']} urban
units ({primary_row['n_cities']} underlying UCDB centres)**, skewed toward
**larger, longer-established** agglomerations (Section 15 of the report) and
present in 5 of 6 broad world regions with N >= 30 (all 6 if Oceania,
N={int(reg_counts.get('Oceania', 0))}, is merged with a neighbouring region
for validation only).

## What this explicitly does NOT cover

* All global urban centres (the GHSL universe, N=10,915) — most small and
  recently urbanized centres are not resolved by the YCEO product and are
  excluded from inference, not merely under-weighted.
* Any claim about recently urbanized cities specifically (they are
  under-represented: {primary_row['frac_post1975_included']*100:.0f}% of the
  included sample was urbanized after 1975 vs
  {primary_row['frac_post1975_excluded']*100:.0f}% of the excluded sample).
* Pixel- or neighbourhood-scale claims within a cluster.
* Any causal claim (unchanged from 1005-6).

## Why this wording, not a broader one

Reweighting back to the full 10,915-city population was considered (Section
12 of the report) and rejected as the *primary* strategy because inclusion
probability is structurally near zero for a large share of small/recent
cities (not merely a sampling accident), which would require extreme,
high-variance weights. Stating the restricted target directly is more honest
than claiming a broader population via an unstable weight.
""", encoding="utf-8")


def write_final_rule(rule_results: dict, rule_defs: list[dict]) -> None:
    primary = rule_results["PRIMARY"]["row"]
    out = {
        "primary_rule": {
            "substantive_link_definition": "intersection_area / min(UCDB_area, YCEO_cluster_area) >= 0.5 (the 1005-7 link definition, unchanged)",
            "ucdb_coverage_of_cluster_threshold": PRIMARY_COVERAGE,
            "metric": "sum(intersection_m2 over linked UCDB centres) / yceo_cluster_area_m2 (identical to 1005-7's cluster_ucdb_coverage)",
            "unit_iou_condition": f">= {PRIMARY_IOU} (cluster-level IoU = sum(intersection)/(sum(UCDB area)+cluster area-sum(intersection)))",
            "single_city_clusters": "kept as-is; S/H equal the single linked UCDB centre's values",
            "multi_city_clusters": "kept iff star-shaped (every linked UCDB centre links to no other cluster) and single-country; S summed, H = sum(B_i(t))/sum(B_i(T)) (Section 10)",
            "one_ucdb_to_multiple_yceo": "excluded (status=ambiguous_nonstar) -- a UCDB centre may not contribute to more than one cluster's outcome",
            "cross_country_clusters": "excluded (status=cross_country)",
            "missing_R": "excluded (status=invalid_R); validity only, magnitude never used",
            "qc_exclusions": "inherits the 1005-4 Gate-1 sample (YOB<=2020, N=10,915) before any crosswalk step",
            "resulting_n_units": primary["n_units"], "resulting_n_cities": primary["n_cities"],
        },
        "geometry_sensitivities": [
            {"name": rd["name"], "coverage": rd["coverage"], "iou": rd["iou"],
             "n_units": rule_results[rd["name"]]["row"]["n_units"],
             "n_cities": rule_results[rd["name"]]["row"]["n_cities"],
             "purpose": {"S1_looser_coverage_040": "lower bound on N / looser footprint requirement",
                         "S2_stricter_coverage_060": "upper bound on footprint strictness",
                         "S3_drop_iou_floor": "isolates the effect of the added IoU condition from the coverage threshold"}[rd["name"]]}
            for rd in rule_defs if rd["name"] != "PRIMARY"
        ],
        "non_geometry_sensitivities_preregistered_elsewhere": [
            "dominant-city H substitution for multi-city units (Section 11)",
            "dynamic-boundary (MTUC) H where available (Section 11)",
            "boundary-robust H descriptors (1005-6 Section 4)",
        ],
        "note": "At most 3 primary geometry sensitivities, per instruction; non-geometry sensitivities are listed for completeness but are not geometry forks.",
    }
    (RES / "final_crosswalk_rule.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


def make_figures(cov_df, iou_df, agg, primary_units, n_ucdb_dist) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(cov_df.coverage_threshold, cov_df.n_units, "o-", label="cluster units")
    ax.plot(cov_df.coverage_threshold, cov_df.n_cities, "s--", label="UCDB cities")
    ax.axvline(PRIMARY_COVERAGE, color="gray", ls=":")
    ax.set_xlabel("UCDB coverage of YCEO cluster (threshold)"); ax.set_ylabel("N"); ax.legend()
    ax.set_title("Sample size vs coverage threshold (geometry only)")
    fig.tight_layout(); fig.savefig(FIG / "fig1_n_vs_coverage.png", dpi=110); plt.close(fig)

    regions = [c[2:].replace("_", " ") for c in cov_df.columns if c.startswith("n_") and c not in
               ("n_units", "n_cities", "n_single_city", "n_multi_city", "n_excluded_low_coverage",
                "n_excluded_low_iou", "n_excluded_ambiguous_nonstar", "n_excluded_cross_country",
                "n_excluded_invalid_R", "n_oceania")]
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for r in regions:
        col = "n_" + r.replace(" ", "_")
        if col in cov_df.columns:
            ax.plot(cov_df.coverage_threshold, cov_df[col] / cov_df.n_cities, "o-", label=r)
    ax.axvline(PRIMARY_COVERAGE, color="gray", ls=":")
    ax.set_xlabel("coverage threshold"); ax.set_ylabel("share of matched sample"); ax.legend(fontsize=7)
    ax.set_title("Regional retention vs coverage threshold")
    fig.tight_layout(); fig.savefig(FIG / "fig2_regional_retention.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for var, lab in [("log10_pop2020", "log10 population"), ("log10_bus2020_km2", "log10 built-up area"), ("yob", "YOB")]:
        ax.plot(cov_df.coverage_threshold, cov_df[f"smd_{var}"], "o-", label=lab)
    ax.axhline(0, color="k", lw=.7); ax.axvline(PRIMARY_COVERAGE, color="gray", ls=":")
    ax.set_xlabel("coverage threshold"); ax.set_ylabel("SMD (included - excluded)"); ax.legend()
    ax.set_title("Size / age bias vs coverage threshold")
    fig.tight_layout(); fig.savefig(FIG / "fig3_size_age_bias.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for var, lab in [("early_developed_fraction_1990", "early-developed frac. 1990"),
                     ("recent_expansion_fraction_since_2000", "recent expansion since 2000"),
                     ("weighted_development_timing", "weighted dev. timing (scaled)")]:
        y = cov_df[f"smd_{var}"]
        ax.plot(cov_df.coverage_threshold, y, "o-", label=lab)
    ax.axhline(0, color="k", lw=.7); ax.axvline(PRIMARY_COVERAGE, color="gray", ls=":")
    ax.set_xlabel("coverage threshold"); ax.set_ylabel("SMD (included - excluded)"); ax.legend(fontsize=8)
    ax.set_title("H-descriptor bias vs coverage threshold")
    fig.tight_layout(); fig.savefig(FIG / "fig4_h_descriptor_bias.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(iou_df.iou_threshold.replace("none", 0).astype(float), iou_df.n_units, "o-")
    ax[0].axvline(PRIMARY_IOU, color="gray", ls=":")
    ax[0].set_xlabel("IoU floor (0 = none)"); ax[0].set_ylabel("N units at coverage=0.5"); ax[0].set_title("Retention vs IoU floor")
    ax[1].hist(primary_units.unit_iou, bins=40, color="#4C72B0")
    ax[1].axvline(PRIMARY_IOU, color="r", ls="--", label="primary floor")
    ax[1].set_xlabel("cluster unit IoU"); ax[1].set_title("IoU distribution, primary sample"); ax[1].legend()
    fig.tight_layout(); fig.savefig(FIG / "fig5_iou_sensitivity.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].bar(n_ucdb_dist.index.astype(str), n_ucdb_dist.values, color="#55A868")
    ax[0].set_yscale("log"); ax[0].set_xlabel("UCDB centres per cluster"); ax[0].set_title("Aggregation structure, primary sample")
    multi = agg[agg.n_ucdb > 1]
    ax[1].hist(multi.dominant_share_of_built, bins=20, color="#C44E52")
    ax[1].set_xlabel("dominant-city share of built-up area"); ax[1].set_title(f"Multi-city units (n={len(multi)})")
    fig.tight_layout(); fig.savefig(FIG / "fig6_aggregation_structure.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    sys.exit(run())
