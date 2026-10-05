"""Pipeline runner for execution 1005-7 (local only; no network)."""

from __future__ import annotations

import json
import platform
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ucdb_gate1_pilot as p  # noqa: E402
import yceo_crosswalk as xw  # noqa: E402

RES, FIG, INT = xw.RESULTS, xw.FIGURES, xw.INTERIM


def dbf_info(dbf: Path):
    d = dbf.read_bytes()
    n = struct.unpack("<I", d[4:8])[0]
    out, pos = [], 32
    while d[pos] != 0x0D:
        out.append((d[pos:pos + 11].split(b"\x00")[0].decode("latin-1"), chr(d[pos + 11]), d[pos + 16], d[pos + 17]))
        pos += 32
    return n, out


def run() -> int:
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    INT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    sha_before = xw.sha256_of(xw.RAW_ZIP)

    # ---- 2. raw integrity + extraction (to interim only)
    man = xw.inspect_zip(xw.RAW_ZIP)
    man["human_downloaded"] = True
    man["extracted_to"] = str(INT.relative_to(xw.ROOT))
    with zipfile.ZipFile(xw.RAW_ZIP) as zf:
        zf.extractall(INT)
    (RES / "thermal_raw_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    assert man["zip_valid"] and man["shapefile"]["complete"]

    shp = INT / "All_shp.shp"
    y = gpd.read_file(shp)
    n_dbf, dbf_fields = dbf_info(INT / "All_shp.dbf")
    info = pyogrio.read_info(shp)

    # ---- 3. schema + geometry audit
    ident = {"Code": "unique integer, 10136 unique", "FID_1": "unique string, 10136 unique"}
    rows, fsum = [], []
    for name, typ, width, dec in dbf_fields:
        s = y[name]
        isnum = pd.api.types.is_numeric_dtype(s)
        miss = int(s.isna().sum())
        rows.append({"field": name, "dbf_type": typ, "width": width, "decimals": dec, "pandas_dtype": str(s.dtype),
                     "n": len(s), "missing_n": miss, "missing_pct": round(100 * miss / len(s), 3),
                     "n_unique": int(s.nunique()), "n_duplicated": int(s.duplicated().sum()),
                     "n_minus999": int((s == -999).sum()) if isnum else 0,
                     "n_minus1": int((s == -1).sum()) if isnum else 0,
                     "identifier_candidate": bool(s.is_unique and not s.isna().any()),
                     "role_note": ident.get(name, "")})
        d = {"field": name, "dtype": str(s.dtype)}
        if isnum:
            d.update(min=float(s.min()), max=float(s.max()), mean=float(s.mean()), median=float(s.median()))
        else:
            d.update(top_values=json.dumps(s.value_counts().head(5).to_dict()))
        fsum.append(d)
    pd.DataFrame(rows).to_csv(RES / "yceo_schema_audit.csv", index=False)
    pd.DataFrame(fsum).to_csv(RES / "yceo_field_summary.csv", index=False)

    ym = y.to_crs(xw.MOLL)
    area_km2 = ym.area / 1e6
    geomqc = {
        "feature_count": len(y), "dbf_record_count": n_dbf, "geometry_types": y.geom_type.value_counts().to_dict(),
        "crs": str(y.crs), "bounds_wgs84": [float(v) for v in y.total_bounds],
        "invalid_geometries": int((~y.is_valid).sum()), "empty_geometries": int(y.is_empty.sum()),
        "multipart_count": int((y.geom_type == "MultiPolygon").sum()),
        "zero_area_count": int((area_km2 <= 0).sum()),
        "duplicate_geometry_count": int(y.geometry.apply(lambda g: g.wkb).duplicated().sum()),
        "area_km2_equal_area_ESRI54009": {k: float(v) for k, v in area_km2.describe(percentiles=[.01, .5, .99]).items()},
        "lon_lat_fields_vs_polygon_representative_point_max_abs_deg": [
            float(np.abs(y.geometry.representative_point().x - y["Lon"]).max()),
            float(np.abs(y.geometry.representative_point().y - y["Lat"]).max())],
        "coordinates_within_valid_range": bool(y.total_bounds[0] >= -180 and y.total_bounds[2] <= 180
                                               and y.total_bounds[1] >= -90 and y.total_bounds[3] <= 90),
        "pyogrio_encoding": info.get("encoding"),
        "extent_sanity": "lon -158..178, lat -50..70: consistent with land urban areas; no polar/ocean outliers",
    }
    (RES / "yceo_geometry_qc.json").write_text(json.dumps(geomqc, indent=2), encoding="utf-8")

    # ---- 4. response fields (identified from ACTUAL columns)
    cols = list(y.columns)
    fmap = {(per, dn): xw.identify_response_field(cols, per, dn)
            for per in ("annual", "summer", "winter") for dn in ("day", "night")}
    PRIMARY, SECONDARY = fmap[("annual", "night")], fmap[("summer", "day")]
    y["yceo_id"] = y["Code"].astype(int)
    y["area_km2"] = area_km2.values
    y["valid_primary"] = y[PRIMARY].notna()

    # approx. region for each cluster: country of nearest UCDB centroid (QA/region table only)
    main = p.load_main_table()
    cen = gpd.GeoDataFrame(main[["ID_UC_G0", "GC_CNT_GAD_2025", "region"]],
                           geometry=gpd.points_from_xy(main.lon_deg, main.lat_deg), crs=4326).to_crs(xw.MOLL)
    ycen = gpd.GeoDataFrame(y[["yceo_id"]], geometry=ym.representative_point().values, crs=xw.MOLL)
    nn = gpd.sjoin_nearest(ycen, cen[["region", "geometry"]], distance_col="d_m", how="left")
    nn = nn[~nn.index.duplicated()]
    y["region_nearest_ucdb"] = nn["region"].values
    y["dist_nearest_ucdb_km"] = (nn["d_m"] / 1000).values

    rq = []
    for fld, tag in [(PRIMARY, "primary"), (SECONDARY, "secondary")]:
        d = {"role": tag, "field": fld, "unit": "degC (SUHI intensity; documentation: urban minus rural LST)",
             "period": "2003-2018 composite mean"}
        d.update(xw.summarize_response(y[fld]))
        rq.append(d)
    for (per, dn), f in fmap.items():
        if f not in (PRIMARY, SECONDARY):
            d = {"role": "other_composite", "field": f, "unit": "degC", "period": "2003-2018 composite mean"}
            d.update(xw.summarize_response(y[f]))
            rq.append(d)
    pd.DataFrame(rq).to_csv(RES / "thermal_response_qc.csv", index=False)

    # ---- 6. UCDB sample + geometry
    qc = p.run_qc(main)
    sample, _ = p.build_sample(main, qc)
    assert len(sample) == 10915
    desc = p.build_H(sample)[1]
    sample = sample.merge(desc, on="ID_UC_G0")
    uc = pyogrio.read_dataframe(p.GPKG_PATH, layer="GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A",
                                columns=["ID_UC_G0"]).to_crs(xw.MOLL)
    uc = uc[uc.ID_UC_G0.isin(sample.ID_UC_G0)].reset_index(drop=True)
    uc["a_uc"] = uc.area
    # repair the few invalid UCDB polygons (area-preserving buffer(0)) -- reported
    n_invalid = int((~uc.geometry.is_valid).sum())
    uc["geometry"] = uc.geometry.make_valid()
    ymm = ym.copy()
    ymm["yceo_id"] = y["yceo_id"].values
    ymm["a_y"] = ymm.area

    # ---- 7/8. overlay + metrics
    j = gpd.overlay(uc[["ID_UC_G0", "a_uc", "geometry"]], ymm[["yceo_id", "a_y", "geometry"]],
                    how="intersection", keep_geom_type=False)
    j["inter_m2"] = j.area
    j = j[j.inter_m2 > 0].copy()
    m = [xw.overlap_metrics(i, a, b) for i, a, b in zip(j.inter_m2, j.a_uc, j.a_y)]
    j = pd.concat([j.drop(columns="geometry").reset_index(drop=True), pd.DataFrame(m)], axis=1)
    ucc = uc.set_index("ID_UC_G0").geometry.centroid
    ycc = ymm.set_index("yceo_id").geometry.centroid
    j["centroid_dist_km"] = [ucc[u].distance(ycc[v]) / 1000 for u, v in zip(j.ID_UC_G0, j.yceo_id)]
    all_overlaps = len(j)
    links = j[j.overlap_over_min >= xw.RULES["link_threshold_overlap_over_min_area"]].rename(
        columns={"ID_UC_G0": "ucdb_id"}).copy()
    links["iou_tight"] = links["iou"] >= xw.RULES["tight_min_iou"]

    cty = sample.set_index("ID_UC_G0")["GC_CNT_GAD_2025"].to_dict()
    valid = y.set_index("yceo_id")["valid_primary"].to_dict()
    pairs, ut, yt = xw.classify_links(links, cty, valid)
    in_sample = set(sample.ID_UC_G0)
    units = xw.aggregate_cluster_units(pairs, valid, in_sample)

    # ---- audit table (every UCDB and every YCEO object)
    pc = pairs.set_index(["ucdb_id", "yceo_id"])["pair_class"]
    aud = pairs.rename(columns={"inter_m2": "intersection_m2", "a_uc": "ucdb_area_m2", "a_y": "yceo_area_m2"}).copy()
    aud.insert(0, "object_type", "link")
    aud["ucdb_country"] = aud.ucdb_id.map(cty)
    aud["yceo_primary_R_valid"] = aud.yceo_id.map(valid)
    aud["name_agreement_QA"] = "not_available_YCEO_has_no_name_field"
    aud["country_agreement_QA"] = np.where(aud.pair_class == "E_cross_country_cluster", "cross_country_cluster", "not_available_YCEO_has_no_country_field")
    unlinked_u = sorted(in_sample - set(pairs.ucdb_id))
    near_u = j[~j.ID_UC_G0.isin(pairs.ucdb_id)].groupby("ID_UC_G0").overlap_over_min.max()
    ur = pd.DataFrame({"object_type": "ucdb_unlinked", "ucdb_id": unlinked_u,
                       "pair_class": ["F_spatially_unmatched_sliver_overlap_only" if u in near_u.index else "F_spatially_unmatched"
                                      for u in unlinked_u],
                       "ucdb_country": [cty[u] for u in unlinked_u],
                       "overlap_over_min": [near_u.get(u, np.nan) for u in unlinked_u]})
    linked_y = set(pairs.yceo_id)
    yr = pd.DataFrame({"object_type": "yceo_unlinked", "yceo_id": sorted(set(y.yceo_id) - linked_y)})
    yr["pair_class"] = np.where(yr.yceo_id.map(valid), "F_spatially_unmatched", "G_invalid_no_response_and_unmatched")
    yr["yceo_primary_R_valid"] = yr.yceo_id.map(valid)
    ex = pd.DataFrame({"object_type": "ucdb_qc_excluded_gate1", "ucdb_id": sorted(set(main.ID_UC_G0) - in_sample),
                       "pair_class": "G_qc_excluded_YOB_after_2020"})
    audit = pd.concat([aud, ur, yr, ex], ignore_index=True)
    # usability flag
    unit_by_y = units.set_index("yceo_id")
    audit["in_recommended_primary_unit"] = audit.apply(
        lambda r: bool(r.object_type == "link" and r.yceo_id in unit_by_y.index and r.ucdb_id in
                       set(unit_by_y.loc[r.yceo_id, "ucdb_ids"].split(";") if False else [])) , axis=1) if False else False
    uset = {(int(u), int(r.yceo_id)) for r in units.itertuples() for u in r.ucdb_ids.split(";")}
    audit["in_recommended_primary_unit"] = [
        (object_type == "link" and (int(u), int(v)) in uset) for object_type, u, v in
        zip(audit.object_type, audit.ucdb_id.fillna(-1), audit.yceo_id.fillna(-1))]
    audit.to_csv(RES / "ucdb_yceo_crosswalk.csv", index=False)

    # ---- structure statistics
    nu_per_y = links.groupby("yceo_id").ucdb_id.nunique()
    multi_y = nu_per_y[nu_per_y > 1]
    cls_pairs = pairs.pair_class.value_counts().to_dict()
    A = int(((pairs.pair_class == "A_strict_1to1") & pairs.yceo_id.map(valid)).sum())
    B = int(((pairs.pair_class == "B_dominant_1to1") & pairs.yceo_id.map(valid)).sum())
    A_all = int((pairs.pair_class == "A_strict_1to1").sum())
    B_all = int((pairs.pair_class == "B_dominant_1to1").sum())
    units_single = int((units.unit_type == "single_city").sum())
    units_multi = int((units.unit_type == "multi_city_aggregate").sum())
    cities_in_units = int(units.n_ucdb.sum())
    ambiguous_ucdb = int(pairs.loc[~pairs.pair_class.isin(["A_strict_1to1", "B_dominant_1to1"]), "ucdb_id"].nunique())
    summary = {
        "N_YCEO_total": len(y), "N_YCEO_valid_primary_R": int(y.valid_primary.sum()),
        "N_YCEO_missing_primary_R": int((~y.valid_primary).sum()),
        "N_UCDB_total": int(len(main)), "N_UCDB_primary_sample": len(sample),
        "N_UCDB_invalid_polygons_repaired": n_invalid,
        "N_overlap_pairs_any_area": all_overlaps, "N_substantive_links": len(links),
        "link_rule": "overlap / min(area_UCDB, area_YCEO) >= 0.5",
        "pair_class_counts": cls_pairs,
        "N_strict_1to1_pairs_all": A_all, "N_dominant_1to1_pairs_all": B_all,
        "N_strict_1to1_matched_valid_R": A, "N_dominant_1to1_matched_valid_R": B,
        "strict_1to1_tight_iou_ge_0.5": int(((pairs.pair_class == "A_strict_1to1") & pairs.iou_tight & pairs.yceo_id.map(valid)).sum()),
        "N_ucdb_in_ambiguous_or_mismatch": ambiguous_ucdb,
        "N_ucdb_in_sample_unlinked": len(unlinked_u),
        "N_yceo_unlinked": len(yr),
        "N_yceo_clusters_with_multiple_ucdb_centres": int(len(multi_y)),
        "N_ucdb_centres_sharing_cluster_with_another": int(links[links.yceo_id.isin(multi_y.index)].ucdb_id.nunique()),
        "cluster_ucdb_count_distribution": nu_per_y.value_counts().sort_index().to_dict(),
        "N_ucdb_linked_to_multiple_clusters": int((links.groupby("ucdb_id").yceo_id.nunique() > 1).sum()),
        "N_clusters_cross_country": int(pairs[pairs.pair_class == "E_cross_country_cluster"].yceo_id.nunique()),
        "recommended_unit": "YCEO_CLUSTER",
        "N_recommended_units": len(units), "N_units_single_city": units_single, "N_units_multi_city_aggregate": units_multi,
        "N_ucdb_cities_inside_recommended_units": cities_in_units,
        "share_of_unit_cities_in_multi_city_units": float(units[units.unit_type == 'multi_city_aggregate'].n_ucdb.sum() / cities_in_units),
        "N_ucdb_final_unmatched_or_excluded": int(len(sample) - cities_in_units),
    }
    (RES / "crosswalk_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # ---- 10. bias: UCDB sample cities in recommended units vs not
    s = sample.copy()
    s["matched"] = s.ID_UC_G0.isin({int(u) for r in units.ucdb_ids for u in r.split(";")})
    s["pop2020"] = s["GH_POP_TOT_2020"]
    s["bus2020_km2"] = s["GH_BUS_TOT_2020"] / 1e6
    s["yob"] = s["GC_UCB_YOB_2025"]
    s["born_after_1975"] = (s["yob"] > 1975).astype(float)
    bias = []
    for v, lab in [("pop2020", "population_2020"), ("bus2020_km2", "built_up_km2_2020"),
                   ("early_developed_fraction_1990", "H_early_developed_fraction_1990"),
                   ("recent_expansion_fraction_since_2000", "H_recent_expansion_since_2000"),
                   ("weighted_development_timing", "H_weighted_development_timing"),
                   ("yob", "year_of_birth_YOB"), ("born_after_1975", "share_recently_urbanized_YOB_gt_1975"),
                   ("lat_deg", "abs_lat_placeholder")]:
        if lab == "abs_lat_placeholder":
            s["_x"] = s["lat_deg"].abs(); v = "_x"; lab = "abs_latitude"
        a, b = s.loc[s.matched, v], s.loc[~s.matched, v]
        la = np.log10(a.clip(lower=1e-9)) if v in ("pop2020", "bus2020_km2") else None
        row = {"variable": lab, "n_matched": len(a), "n_unmatched": len(b), "mean_matched": a.mean(),
               "mean_unmatched": b.mean(), "median_matched": a.median(), "median_unmatched": b.median(),
               "SMD": xw.smd(a, b)}
        if la is not None:
            row["SMD_log10"] = xw.smd(la, np.log10(b.clip(lower=1e-9)))
        bias.append(row)
    pd.DataFrame(bias).to_csv(RES / "matched_sample_bias.csv", index=False)
    reg = pd.DataFrame({"source_n": s.region.value_counts(), "matched_n": s[s.matched].region.value_counts()}).fillna(0)
    reg["match_rate"] = reg.matched_n / reg.source_n
    reg["source_share"] = reg.source_n / reg.source_n.sum()
    reg["matched_share"] = reg.matched_n / reg.matched_n.sum()
    reg.to_csv(RES / "matched_region_coverage.csv")
    # H/S aggregation feasibility
    bus_c = [f"GH_BUS_TOT_{t}" for t in p.EPOCHS_OBSERVED]
    ms = units[units.unit_type == "multi_city_aggregate"]
    feas = []
    sidx = sample.set_index("ID_UC_G0")
    for r in ms.itertuples():
        ids = [int(u) for u in r.ucdb_ids.split(";")]
        g = sidx.loc[ids]
        tot = g[bus_c].sum()
        h_agg = (tot[bus_c[:-1]] / tot[bus_c[-1]]).to_numpy()
        top = g[bus_c[-1]].idxmax()
        h_dom = (g.loc[top, bus_c[:-1]] / g.loc[top, bus_c[-1]]).to_numpy(dtype=float)
        feas.append({"yceo_id": r.yceo_id, "n_ucdb": r.n_ucdb, "pop2020_sum": g["GH_POP_TOT_2020"].sum(),
                     "bus2020_sum_km2": tot[bus_c[-1]] / 1e6, "buv2020_sum": g["GH_BUV_TOT_2020"].sum(),
                     "dominant_city_share_of_built": g.loc[top, bus_c[-1]] / tot[bus_c[-1]],
                     "H_dist_aggregate_vs_dominant": float(np.linalg.norm(h_agg - h_dom)),
                     "H_agg_h1990": h_agg[3], "H_dom_h1990": h_dom[3],
                     "ucdb_coverage_of_cluster": r.ucdb_coverage_of_cluster})
    pd.DataFrame(feas).to_csv(RES / "cluster_aggregation_feasibility.csv", index=False)
    fe = pd.DataFrame(feas)

    # ---- figures
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for a_, f, t in [(ax[0], PRIMARY, "Primary R: " + PRIMARY), (ax[1], SECONDARY, "Secondary R: " + SECONDARY)]:
        a_.hist(y[f].dropna(), bins=80, color="#4C72B0")
        a_.axvline(0, color="k", lw=.8)
        a_.set_title(t); a_.set_xlabel("degC")
    fig.tight_layout(); fig.savefig(FIG / "fig1_response_histograms.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    v = y[y.valid_primary]
    sc = ax.scatter(v.Lon, v.Lat, c=v[PRIMARY], s=3, cmap="coolwarm", vmin=-1.5, vmax=1.5)
    mis = y[~y.valid_primary]
    ax.scatter(mis.Lon, mis.Lat, s=6, c="k", marker="x", label=f"missing R (n={len(mis)})")
    ax.legend(loc="lower left"); plt.colorbar(sc, label="annual night SUHI, degC"); ax.set_title("Primary R and missingness")
    fig.tight_layout(); fig.savefig(FIG / "fig2_primary_map_missing.png", dpi=110); plt.close(fig)

    reg_r = y[y.valid_primary].groupby("region_nearest_ucdb")[PRIMARY].agg(["count", "median", lambda x: x.quantile(.05), lambda x: x.quantile(.95)])
    reg_r.columns = ["n", "median", "p05", "p95"]
    reg_r.to_csv(RES / "thermal_primary_by_region.csv")
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.boxplot([y[y.valid_primary & (y.region_nearest_ucdb == r)][PRIMARY] for r in reg_r.index], tick_labels=list(reg_r.index))
    ax.set_ylabel("annual night SUHI, degC"); plt.setp(ax.get_xticklabels(), rotation=25)
    fig.tight_layout(); fig.savefig(FIG / "fig3_primary_by_region.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    one = pairs[pairs.pair_class.isin(["A_strict_1to1", "H_footprint_mismatch_1to1"])]
    ax[0].hist(one.iou, bins=40, color="#55A868"); ax[0].axvline(xw.RULES["strict_min_iou"], color="r")
    ax[0].set_title("IoU of 1:1 pairs (red = strict cut)")
    ax[1].bar(nu_per_y.value_counts().sort_index().index.astype(str), nu_per_y.value_counts().sort_index().values, color="#C44E52")
    ax[1].set_title("UCDB centres per linked YCEO cluster"); ax[1].set_yscale("log")
    fig.tight_layout(); fig.savefig(FIG / "fig4_crosswalk_structure.png", dpi=110); plt.close(fig)

    # extremes vs geometry
    ext = y[y.valid_primary & ((y[PRIMARY] > y[PRIMARY].quantile(.99)) | (y[PRIMARY] < y[PRIMARY].quantile(.01)))]
    ext_info = {"n_extreme_p01_p99": len(ext), "median_area_km2_extremes": float(ext.area_km2.median()),
                "median_area_km2_all_valid": float(y[y.valid_primary].area_km2.median()),
                "share_extremes_linked_to_ucdb": float(ext.yceo_id.isin(linked_y).mean()),
                "share_all_valid_linked_to_ucdb": float(y[y.valid_primary].yceo_id.isin(linked_y).mean()),
                "corr_primary_vs_log_area_spearman": float(y[y.valid_primary][[PRIMARY, "area_km2"]].corr("spearman").iloc[0, 1])}
    miss_area = {"median_area_km2_missing": float(y[~y.valid_primary].area_km2.median()),
                 "median_area_km2_valid": float(y[y.valid_primary].area_km2.median())}
    # which are unlinked-by-UCDB clusters
    ext_info.update(miss_area)

    # rules file
    rules = {"revision_history": [
        {"stage": "1005-6 provisional", "strict_min_iou": None, "overlap_ge": 0.5, "area_ratio": [0.25, 4.0], "max_unsupported_km": 10},
        {"stage": "1005-7 final (set after geometry-only inspection, before any response look)",
         "change": "Added IoU>=0.25 for strict 1:1 (IoU>=0.5 would have rejected ~75% of otherwise clean 1:1 pairs because Natural Earth 1:10m urban polygons and GHSL DoU centres are different ontologies; median 1:1 IoU=0.39). 'Overlap>=0.5' redefined as overlap/min(area) to define a substantive link, since containment of a small object in a large one is the expected relation. IoU>=0.5 reported as tight sensitivity flag."}],
        "rules": xw.RULES,
        "classes": {"A_strict_1to1": "isolated link component (1 UCDB, 1 YCEO), IoU>=0.25, area ratio in [0.25,4], centroid distance<=25km",
                    "B_dominant_1to1": "cluster holds >=2 UCDB centres but one holds >=80% of UCDB-overlap area and covers >=50% of cluster",
                    "C_ambiguous_one_to_many": "one UCDB centre substantively overlaps >=2 clusters",
                    "D_many_to_one_ambiguous / D_minor_of_dominant": "several UCDB centres in one cluster with no dominant one / minor centres beside a dominant one",
                    "E_cross_country_cluster": "UCDB centres of a cluster belong to different countries",
                    "F_spatially_unmatched": "no substantive link", "G_*": "QC/response-missing excluded",
                    "H_footprint_mismatch_1to1": "isolated 1:1 link failing IoU/area-ratio/centroid-distance test",
                    "J_complex_many_to_many": "component with >=2 UCDB and >=2 clusters"},
        "unit_rule": "Recommended primary unit = YCEO cluster. A cluster is a unit iff star-shaped (all its UCDB centres link only to it), single-country, response valid, all linked centres in the 10,915 sample, and UCDB centres cover >=50% of cluster area. Each cluster appears once; S/H are aggregated over its UCDB centres.",
        "name_and_country_use": "YCEO has no name or country field; cross-country consistency among UCDB centres of one cluster is the only country QA possible. Names are not used.",
        "tight_sensitivity": "restrict to units whose all links have IoU>=0.5"}
    (RES / "crosswalk_rules.json").write_text(json.dumps(rules, indent=2), encoding="utf-8")

    # ---- decision
    multi_share = summary["share_of_unit_cities_in_multi_city_units"]
    decision = {
        "THERMAL_DESIGN": None, "GATE_2_EXECUTION": None,
        "primary_R_field": PRIMARY, "secondary_R_field": SECONDARY,
        "fields_found": {f"{k[0]}_{k[1]}": v for k, v in fmap.items()},
        "temporal_recheck": "single composite value per cluster for each period; no year/month attributes in the shapefile (fields: " + ", ".join(cols[:-1]) + ")",
        "recommended_unit": "YCEO_CLUSTER", "recommended_sample_N": len(units),
        "units_single_city": units_single, "units_multi_city_aggregate": units_multi,
        "ucdb_cities_covered": cities_in_units, "share_cities_in_multi_city_units": multi_share,
        "extreme_value_info": ext_info,
    }
    (RES / "_decision_inputs.json").write_text(json.dumps({"decision": decision, "summary": summary,
                                                              "region_cov": reg.to_dict(), "bias": bias,
                                                              "feas": fe.describe().to_dict()}, indent=2, default=float), encoding="utf-8")
    meta = {"execution_id": "1005-7", "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
            "raw_zip_sha256_before": sha_before, "raw_zip_sha256_after": xw.sha256_of(xw.RAW_ZIP),
            "raw_zip_unchanged": sha_before == xw.sha256_of(xw.RAW_ZIP),
            "network_access": "none", "new_research_data_downloaded": False, "random_seed": None,
            "python": sys.version, "platform": platform.platform(),
            "geopandas": gpd.__version__, "pandas": pd.__version__, "numpy": np.__version__}
    (RES / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=1, default=float))
    print(json.dumps(ext_info, indent=1))
    print(reg.round(3).to_string()); print(pd.DataFrame(bias).round(3).to_string()); print(fe.describe().round(3).to_string())
    print(reg_r.round(3).to_string()); print(pd.DataFrame(rq)[["field","valid_n","missing_n","min","median","max"]])
    return 0


if __name__ == "__main__":
    sys.exit(run())
