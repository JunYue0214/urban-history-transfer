"""Gate 2 pipeline (execution 1005-9). Primary response Annual_nig is analysed and its
outputs SEALED (hash marker) before Summer_day is loaded for the compact replication.
"""

from __future__ import annotations

import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_data as d  # noqa: E402
import gate2_models as m  # noqa: E402
import gate2_support as g  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "results" / "1005-9", ROOT / "figures" / "1005-9"
N_PERM = 300
N_BOOT = 2000
ADEQUATE = ["Asia", "Africa", "Europe", "North America", "South America"]
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


class Ctx:
    """Everything needed to evaluate one specification on one sample."""

    def __init__(self, A, y_col, S="S3", C="C1", year=2020):
        self.A = A.reset_index(drop=True)
        self.y = self.A[y_col].to_numpy(float)
        self.tiles, self.fold = d.folds_for(self.A)
        self.S = d.s_block(self.A, S, year)
        self.C = d.c_block(self.A, C)
        self.base = np.hstack([self.S, self.C])
        self.H = m.h_rebased(self.A, m.H_PRIMARY_EPOCHS, 2020)


def evaluate(ctx, H=None, learner="rf", h_mode="raw", base=None, boot=True, p0=None):
    base = ctx.base if base is None else base
    H = ctx.H if H is None else H
    p0 = m.oof_predict(base, None, ctx.y, ctx.fold, learner, None) if p0 is None else p0
    p1 = m.oof_predict(base, H, ctx.y, ctx.fold, learner, h_mode)
    r = m.delta_metrics(ctx.y, p0, p1)
    if boot:
        r.update(m.tile_bootstrap_delta(ctx.y, p0, p1, ctx.tiles, N_BOOT))
    return r, p0, p1


def row(label, r, **kw):
    out = {"spec": label, **kw}
    out.update({k: v for k, v in r.items()})
    return out


def compact(A, y_col, S="S3", C="C1", year=2020, H=None, learner="rf", h_mode="raw", label=""):
    ctx = Ctx(A, y_col, S, C, year)
    r, p0, p1 = evaluate(ctx, H=H, learner=learner, h_mode=h_mode)
    return row(label, r, S=S, C=C, learner=learner, h_mode=h_mode), ctx, p0, p1


def run_experiments(A, y_col, tag, full=True):
    """Runs the pre-registered experiments for one response. Returns dict of DataFrames/dicts."""
    out = {}
    ctx = Ctx(A, y_col)
    rows = []
    # ---- primary: RF raw-H ; RF PCA3 ; ridge raw ; scalar descriptors
    r, p0, p1 = evaluate(ctx)
    rows.append(row("PRIMARY_rf_S3C1_rawH", r, learner="rf", h_mode="raw"))
    prim = (p0, p1)
    r_pca, _, _ = evaluate(ctx, h_mode="pca3", p0=p0)
    rows.append(row("rf_pcaH_trainfold_only", r_pca, learner="rf", h_mode="pca3"))
    desc = m.history_descriptors(A)
    r_desc, _, _ = evaluate(ctx, H=desc, h_mode="raw", p0=p0)
    rows.append(row("rf_scalar_descriptors", r_desc, learner="rf", h_mode="descriptors"))
    r_rg, rp0, rp1 = evaluate(ctx, learner="ridge")
    rows.append(row("ridge_rawH", r_rg, learner="ridge", h_mode="raw"))
    out["primary_rows"] = rows
    out["oof"] = (ctx, p0, p1, rp0, rp1)
    log(f"[{tag}] primary dR2={r['delta_r2']:.4f} CI=({r['delta_r2_ci_lo']:.4f},{r['delta_r2_ci_hi']:.4f}) ridge dR2={r_rg['delta_r2']:.4f}")

    # ---- nulls (RF)
    strata = m.size_strata(A["region"].to_numpy(), np.log(A["B_2020"].to_numpy()))
    obs = r["delta_r2"]

    def one_perm(i):
        rng = np.random.default_rng(m.SEED + 1000 + i)
        Hs = m.shuffle_rows_within_strata(ctx.H, strata, rng)
        p1s = m.oof_predict(ctx.base, Hs, ctx.y, ctx.fold, "rf", "raw")
        mm = m.delta_metrics(ctx.y, p0, p1s)
        return mm["delta_r2"], mm["delta_rmse"]

    perm = np.array(Parallel(n_jobs=1)(delayed(one_perm)(i) for i in range(N_PERM)))
    log(f"[{tag}] shuffled-H null done mean={perm[:, 0].mean():.4f}")
    nulls = [{"null": "N1_shuffled_H_within_region_x_size", "n_draws": N_PERM, "observed_delta_r2": obs,
              "null_mean": float(perm[:, 0].mean()), "null_sd": float(perm[:, 0].std(ddof=1)),
              "null_q05": float(np.quantile(perm[:, 0], .05)), "null_q50": float(np.quantile(perm[:, 0], .5)),
              "null_q95": float(np.quantile(perm[:, 0], .95)), "null_q99": float(np.quantile(perm[:, 0], .99)),
              "percentile_of_observed": float((perm[:, 0] < obs).mean() * 100),
              "standardized_effect": float((obs - perm[:, 0].mean()) / perm[:, 0].std(ddof=1)),
              "null_delta_rmse_mean": float(perm[:, 1].mean())}]
    # pseudo-H from S (out-of-fold, S+C only), redundant S features, random matched vectors
    Hps = m.pseudo_history_from_S(ctx.base, ctx.H, ctx.fold)
    rps, _, _ = evaluate(ctx, H=Hps, p0=p0, boot=False)
    nulls.append({"null": "N2_pseudoH_predicted_from_S_C_oof", "n_draws": 1, "observed_delta_r2": obs,
                  "null_mean": rps["delta_r2"], "ratio_to_observed": rps["delta_r2"] / obs if obs != 0 else np.nan})
    Hred = m.redundant_pseudo_history(ctx.S)
    rrd, _, _ = evaluate(ctx, H=Hred, p0=p0, boot=False)
    nulls.append({"null": "N3_redundant_pseudoH_from_S", "n_draws": 1, "observed_delta_r2": obs,
                  "null_mean": rrd["delta_r2"], "ratio_to_observed": rrd["delta_r2"] / obs if obs != 0 else np.nan})
    rr = []
    for i in range(50):
        rng = np.random.default_rng(m.SEED + 5000 + i)
        rr.append(evaluate(ctx, H=m.random_matched_history(ctx.H, rng), p0=p0, boot=False)[0]["delta_r2"])
    rr = np.array(rr)
    nulls.append({"null": "N4_random_vector_matched_mean_cov", "n_draws": 50, "observed_delta_r2": obs,
                  "null_mean": float(rr.mean()), "null_sd": float(rr.std(ddof=1)), "null_q95": float(np.quantile(rr, .95)),
                  "percentile_of_observed": float((rr < obs).mean() * 100)})
    # ridge shuffled-H (fewer draws; linear model is cheap)
    rrng = np.random.default_rng(m.SEED + 777)
    rs = np.array([evaluate(ctx, H=m.shuffle_rows_within_strata(ctx.H, strata, rrng), learner="ridge", p0=rp0, boot=False)[0]["delta_r2"]
                   for _ in range(300)])
    nulls.append({"null": "N1_ridge_shuffled_H", "n_draws": 300, "observed_delta_r2": r_rg["delta_r2"], "null_mean": float(rs.mean()),
                  "null_q95": float(np.quantile(rs, .95)), "percentile_of_observed": float((rs < r_rg["delta_r2"]).mean() * 100)})
    out["nulls"] = pd.DataFrame(nulls)
    out["perm"] = perm
    log(f"[{tag}] pseudo-H dR2={rps['delta_r2']:.4f} redundant dR2={rrd['delta_r2']:.4f} random mean={rr.mean():.4f}")

    # ---- region robustness (leave-major-region-out; fresh training each time)
    regs = A["region"].to_numpy()
    rrows = []
    for reg in ADEQUATE + ["Oceania"]:
        te = regs == reg
        fold = np.where(te, 1, 0)
        base_te, base_tr = ctx.base[te], ctx.base[~te]
        m0 = m.make_learner("rf").fit(base_tr, ctx.y[~te])
        Xtr, Xte = m.prep_features(base_tr, base_te, ctx.H[~te], ctx.H[te], "raw")
        m1 = m.make_learner("rf").fit(Xtr, ctx.y[~te])
        a, b = m0.predict(base_te), m1.predict(Xte)
        dm = m.delta_metrics(ctx.y[te], a, b)
        rrows.append({"held_out_region": reg, **dm, "adequate_region": reg in ADEQUATE,
                      "note": "" if reg in ADEQUATE else "DESCRIPTIVE ONLY: N=21, not counted as replication; not merged with Asia"})
    out["region"] = pd.DataFrame(rrows)
    return out


def twin_block(A, ctx, y):
    """Experiment 2 on S3+C1 only; H and R enter after pairs are fixed."""
    X = g.block_scale([ctx.S, ctx.C])
    pairs = m.build_twins(X, A["lat_deg"].to_numpy(), A["lon_deg"].to_numpy(), k=10, min_sep_km=200.0)
    dsc = np.linalg.norm(X[pairs[:, 0]] - X[pairs[:, 1]], axis=1)
    dgeo = g.haversine_km(A["lat_deg"].to_numpy()[pairs[:, 0]], A["lon_deg"].to_numpy()[pairs[:, 0]],
                          A["lat_deg"].to_numpy()[pairs[:, 1]], A["lon_deg"].to_numpy()[pairs[:, 1]])
    dh = m.pair_distances(ctx.H, pairs)
    dr = np.abs(y[pairs[:, 0]] - y[pairs[:, 1]])
    rho = m.partial_spearman(dr, dh, dsc, dgeo)
    strata = m.size_strata(A["region"].to_numpy(), np.log(A["B_2020"].to_numpy()))
    rng = np.random.default_rng(m.SEED)
    null = []
    for _ in range(1000):
        Hs = m.shuffle_rows_within_strata(ctx.H, strata, rng)
        null.append(m.partial_spearman(dr, m.pair_distances(Hs, pairs), dsc, dgeo))
    null = np.array(null)
    boot = m.twin_tile_bootstrap(lambda idx: m.partial_spearman(dr[idx], dh[idx], dsc[idx], dgeo[idx]), pairs, ctx.tiles, B=500)
    cuts = np.quantile(dh, [1 / 3, 2 / 3])
    grp = np.digitize(dh, cuts)
    names = ["low_DH", "mid_DH", "high_DH"]
    strat = []
    for gi, nm in enumerate(names):
        v = dr[grp == gi]
        strat.append({"stratum": nm, "n_pairs": int(len(v)), "median_DR": float(np.median(v)), "q25": float(np.quantile(v, .25)),
                      "q75": float(np.quantile(v, .75)), "mean_DR": float(v.mean())})
    med_diff = lambda idx: float(np.median(dr[idx][np.digitize(dh[idx], cuts) == 2]) - np.median(dr[idx][np.digitize(dh[idx], cuts) == 0]))
    bd = m.twin_tile_bootstrap(med_diff, pairs, ctx.tiles, B=500)
    pairs_df = pd.DataFrame({"i": pairs[:, 0], "j": pairs[:, 1], "yceo_i": A["yceo_id"].to_numpy()[pairs[:, 0]],
                             "yceo_j": A["yceo_id"].to_numpy()[pairs[:, 1]], "D_SC": dsc, "D_geo_km": dgeo, "D_H": dh, "D_R": dr,
                             "DH_stratum": [names[i] for i in grp]})
    summ = {"n_pairs": int(len(pairs)), "n_units_in_pairs": int(len(set(pairs.ravel()))),
            "partial_spearman": rho, "boot_ci": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "perm_null_mean": float(null.mean()), "perm_null_q95": float(np.quantile(null, .95)),
            "perm_null_q99": float(np.quantile(null, .99)),
            "perm_p_one_sided_ge": float((1 + (null >= rho).sum()) / (len(null) + 1)),
            "raw_spearman_DR_DH": float(pd.Series(dr).corr(pd.Series(dh), method="spearman")),
            "DH_tertile_cuts": [float(c) for c in cuts], "strata": strat,
            "high_minus_low_median_DR": float(np.median(dr[grp == 2]) - np.median(dr[grp == 0])),
            "high_minus_low_ci": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
            "pairs_built_without_H_or_R": True}
    return pairs_df, summ


def transfer_block(A, ctx, y, n_null=100):
    S, C, H = ctx.S, ctx.C, ctx.H
    p0, _ = m.transfer_predict([S, C], y, ctx.fold, K=10)
    p1, _ = m.transfer_predict([S, C, H], y, ctx.fold, K=10)
    res = m.delta_metrics(y, p0, p1)
    strata = m.size_strata(A["region"].to_numpy(), np.log(A["B_2020"].to_numpy()))
    nd = {"shuffled_H": [], "random_matched": [], "pseudo_H": []}
    Hps = m.pseudo_history_from_S(ctx.base, H, ctx.fold)
    nd["pseudo_H_value"] = m.delta_metrics(y, p0, m.transfer_predict([S, C, Hps], y, ctx.fold, K=10)[0])["delta_rmse"]
    for i in range(n_null):
        rng = np.random.default_rng(m.SEED + 9000 + i)
        nd["shuffled_H"].append(m.delta_metrics(y, p0, m.transfer_predict([S, C, m.shuffle_rows_within_strata(H, strata, rng)], y, ctx.fold)[0])["delta_rmse"])
        nd["random_matched"].append(m.delta_metrics(y, p0, m.transfer_predict([S, C, m.random_matched_history(H, rng)], y, ctx.fold)[0])["delta_rmse"])
    sh, rm = np.array(nd["shuffled_H"]), np.array(nd["random_matched"])
    boot = m.tile_bootstrap_delta(y, p0, p1, ctx.tiles, N_BOOT)
    # leave-region-out donors (secondary)
    regs = A["region"].to_numpy()
    lro = []
    for reg in ADEQUATE:
        te = regs == reg
        f = np.where(te, 1, 0)
        a, _ = m.transfer_predict([S, C], y, f, K=10)
        b, _ = m.transfer_predict([S, C, H], y, f, K=10)
        mm = m.delta_metrics(y[te], a[te], b[te])
        lro.append({"held_out_region": reg, "n": mm["n"], "rmse_A0": mm["rmse_m0"], "rmse_A1": mm["rmse_m1"],
                    "delta_rmse_transfer": mm["delta_rmse"], "mae_A0": mm["mae_m0"], "mae_A1": mm["mae_m1"], "delta_mae_transfer": mm["delta_mae"]})
    row_main = {"scheme": "spatial_5fold_K10_idw", "rmse_A0": res["rmse_m0"], "rmse_A1": res["rmse_m1"], "delta_rmse_transfer": res["delta_rmse"],
                "mae_A0": res["mae_m0"], "mae_A1": res["mae_m1"], "delta_mae_transfer": res["delta_mae"], "n": res["n"],
                "delta_rmse_ci_lo": boot["delta_rmse_ci_lo"], "delta_rmse_ci_hi": boot["delta_rmse_ci_hi"],
                "null_shuffled_H_mean": float(sh.mean()), "null_shuffled_H_q05": float(np.quantile(sh, .05)),
                "null_shuffled_H_q95": float(np.quantile(sh, .95)), "pct_obs_below_null": float((sh > res["delta_rmse"]).mean() * 100),
                "null_random_matched_mean": float(rm.mean()), "null_random_matched_q05": float(np.quantile(rm, .05)),
                "null_pseudo_H_delta_rmse": nd["pseudo_H_value"], "n_null_draws": n_null}
    return pd.DataFrame([row_main] + [{"scheme": "leave_region_out_donors", **r} for r in lro])


def moran_block(ctx, p0, p1, A):
    rows = []
    for nm, p in [("M0", p0), ("M1", p1)]:
        resid = ctx.y - p
        for k in (8, 20):
            I, pv, ex = m.morans_i(resid, A["lat_deg"].to_numpy(), A["lon_deg"].to_numpy(), k=k)
            rows.append({"model": nm, "k_neighbours": k, "morans_I": I, "perm_p_nominal": pv, "perm_mean": ex,
                         "resid_sd": float(resid.std())})
    return pd.DataFrame(rows)


def main():
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    cities = d.load_cities()
    links = g.load_links(d.LINKS_PATH)
    raw_hash_before = m.sha256_file(d.YCEO_SHP)

    primary_units = d.units_for_rule(links, *m.PRIMARY_GEOMETRY)
    A_all = d.assemble_units(primary_units, cities)
    A = d.attach_response(A_all, fields=("Annual_nig",))
    assert len(A) == 2107 and A["Annual_nig"].notna().all()
    old = pd.read_csv(d.PRIMARY_TABLE_1005_8).sort_values("yceo_id")
    assert (old.yceo_id.values == A.yceo_id.values).all()
    log("sample identity verified vs 1005-8 (2107 units); response joined (Annual_nig only)")

    summary = {"n_units": len(A), "n_ucdb_cities": int(A.n_ucdb.sum()), "n_multi_city": int((A.n_ucdb > 1).sum()),
               "region_counts": A.region.value_counts().to_dict(), "primary_rule": {"coverage": 0.5, "iou": 0.2},
               "response": "Annual_nig", "response_n_missing": int(A.Annual_nig.isna().sum()),
               "response_mean": float(A.Annual_nig.mean()), "response_sd": float(A.Annual_nig.std()),
               "response_min": float(A.Annual_nig.min()), "response_max": float(A.Annual_nig.max()),
               "no_transform_no_winsorize_no_removal": True, "sample_identical_to_1005_8": True,
               "fold_sizes": pd.Series(d.folds_for(A)[1]).value_counts().sort_index().to_dict()}
    (RES / "analysis_sample_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    E = run_experiments(A, "Annual_nig", "primary")
    ctx, p0, p1, rp0, rp1 = E["oof"]
    pd.DataFrame(E["primary_rows"]).to_csv(RES / "primary_model_metrics.csv", index=False)
    pd.DataFrame({"yceo_id": A.yceo_id, "region": A.region, "fold": ctx.fold, "tile": ctx.tiles, "y": ctx.y,
                  "pred_M0_rf": p0, "pred_M1_rf": p1, "pred_M0_ridge": rp0, "pred_M1_ridge": rp1}).to_csv(RES / "primary_oof_predictions.csv", index=False)
    E["nulls"].to_csv(RES / "history_null_results.csv", index=False)
    E["region"].to_csv(RES / "region_holdout_results.csv", index=False)
    pd.DataFrame({"perm_delta_r2": E["perm"][:, 0], "perm_delta_rmse": E["perm"][:, 1]}).to_csv(RES / "history_null_shuffled_draws.csv", index=False)

    # ---- Experiment 2 and 3
    pairs_df, tsum = twin_block(A, ctx, ctx.y)
    pairs_df.to_csv(RES / "twin_results.csv", index=False)
    (RES / "twin_summary.json").write_text(json.dumps(tsum, indent=2), encoding="utf-8")
    log(f"twins: n_pairs={tsum['n_pairs']} partial rho={tsum['partial_spearman']:.4f} CI={tsum['boot_ci']}")
    tr = transfer_block(A, ctx, ctx.y)
    tr.to_csv(RES / "transfer_results.csv", index=False)
    log(f"transfer: dRMSE={tr.iloc[0]['delta_rmse_transfer']:.4f}")

    # ---- strict precedence + T=2015
    rows = []
    prim_delta = E["primary_rows"][0]
    rows.append({"spec": "PRIMARY_H_1975_2015_S2020", **{k: prim_delta[k] for k in ("delta_r2", "delta_r2_ci_lo", "delta_r2_ci_hi", "r2_m0", "r2_m1", "delta_rmse", "n")}})
    Hpre = m.h_rebased(A, m.H_PRE2000_EPOCHS, 2000)
    r, _, _ = evaluate(ctx, H=Hpre)
    rows.append({"spec": "STRICT_Hpre2000_rebased_B2000_with_S2020", **r})
    ctx00 = Ctx(A, "Annual_nig", "S3", "C1", year=2000)
    r, _, _ = evaluate(ctx00, H=Hpre)
    rows.append({"spec": "STRICT_Hpre2000_rebased_B2000_with_S2000", **r})
    Hpost = m.h_rebased(A, [2005, 2010, 2015], 2020)
    r, _, _ = evaluate(ctx, H=Hpost)
    rows.append({"spec": "DIAGNOSTIC_only_overlapping_epochs_2005_2015", **r})
    ctx15 = Ctx(A, "Annual_nig", "S3", "C1", year=2015)
    H15 = m.h_rebased(A, m.H_T2015_EPOCHS, 2015)
    r, _, _ = evaluate(ctx15, H=H15)
    rows.append({"spec": "T2015_S2015_H_1975_2010_rebased_B2015", **r})
    pd.DataFrame(rows).to_csv(RES / "strict_precedence_results.csv", index=False)
    log("strict precedence done: " + ", ".join(f"{x['spec'][:18]}={x['delta_r2']:.4f}" for x in rows))

    # ---- boundary sensitivities (always M0 and M1 on the same subset)
    rows = []
    r, _, _ = evaluate(ctx)
    rows.append({"spec": "A_fixed_aggregate_primary", **r})
    ctxm = Ctx(A, "Annual_nig")
    Hdom = np.column_stack([A[f"DB_{t}"] / A["DB_2020"] for t in m.H_PRIMARY_EPOCHS])
    r, _, _ = evaluate(ctx, H=Hdom)
    rows.append({"spec": "C_dominant_city_H_all_units", **r})
    multi = (A.n_ucdb > 1).to_numpy()
    sub = A[multi]
    if len(sub) > 60:
        cs = Ctx(sub, "Annual_nig")
        r, _, _ = evaluate(cs)
        rows.append({"spec": "C0_multicity_subset_aggregate_H", **r})
        Hd_sub = np.column_stack([sub[f"DB_{t}"] / sub["DB_2020"] for t in m.H_PRIMARY_EPOCHS])
        r, _, _ = evaluate(cs, H=Hd_sub)
        rows.append({"spec": "C1_multicity_subset_dominant_H", **r})
    r, _, _ = evaluate(ctx, H=m.history_descriptors(A))
    rows.append({"spec": "D_boundary_robust_scalar_descriptors", **r})
    # dynamic-boundary H on the MTUC subset: units whose every UCDB city is in the 1005-5 core matched sample
    cw = pd.read_csv(d.MTUC_XWALK)
    cw = cw[cw.included_in_core_matched_sample == True]
    import mtuc_boundary_robustness as mt
    mtuc = mt.load_mtuc_full().set_index("ID_MTUC_G0")
    map_u2m = dict(zip(cw.ID_UC_G0.astype(int), cw.ID_MTUC_G0.astype(int)))
    keep, Hdyn, Hfix = [], [], []
    for i, s in enumerate(A.ucdb_ids):
        ids = [int(x) for x in s.split(";")]
        if all(u in map_u2m for u in ids):
            mt_rows = mtuc.loc[[map_u2m[u] for u in ids]]
            num = np.array([mt_rows[f"MT_BUS_TOT_{t}"].sum() for t in m.H_PRIMARY_EPOCHS])
            den = mt_rows["MT_BUS_TOT_2020"].sum()
            if np.isfinite(num).all() and den > 0:
                keep.append(i)
                Hdyn.append(num / den)
    keep = np.array(keep)
    if len(keep) > 200:
        sub = A.iloc[keep].reset_index(drop=True)
        cs = Ctx(sub, "Annual_nig")
        r, _, _ = evaluate(cs, H=cs.H)
        rows.append({"spec": "B_fixed_H_on_MTUC_subset", **r})
        r, _, _ = evaluate(cs, H=np.array(Hdyn))
        rows.append({"spec": "B_dynamic_MTUC_H_on_MTUC_subset", **r})
    bs = pd.DataFrame(rows)
    bs.to_csv(RES / "boundary_sensitivity_results.csv", index=False)
    log("boundary done")

    # ---- geometry sensitivities (the three locked 1005-8 rules)
    rows = []
    for name, cov, iou in m.GEOMETRY_SENSITIVITIES:
        u = d.units_for_rule(links, cov, iou)
        Ag = d.attach_response(d.assemble_units(u, cities), fields=("Annual_nig",))
        Ag = Ag[Ag.Annual_nig.notna()].reset_index(drop=True)
        r, _, _ = evaluate(Ctx(Ag, "Annual_nig"))
        rows.append({"spec": name, "coverage": cov, "iou": iou if iou is not None else "none", **r})
    pd.DataFrame(rows).to_csv(RES / "geometry_sensitivity_results.csv", index=False)
    log("geometry done")

    # ---- context/state sensitivities
    rows = []
    for S, C in [("S1", "C1"), ("S2", "C1"), ("S3", "C0"), ("S3", "C1"), ("S3", "C2")]:
        r, _, _ = evaluate(Ctx(A, "Annual_nig", S, C))
        rows.append({"spec": f"{S}+{C}", **r})
    pd.DataFrame(rows).to_csv(RES / "context_state_sensitivity.csv", index=False)
    log("context done")

    # ---- common support
    feat = np.column_stack([ctx.S, ctx.C])
    ok, dist, thr = m.mahalanobis_support(feat)
    legacy_feat = np.column_stack([np.log(np.clip(A.POP_2020, 1, None)), np.log(np.clip(A.B_2020, 1, None)),
                                   np.log(np.clip(A.BUV_2020, 1, None)), np.log(np.clip(A.density_2020, 1, None)), ctx.C])
    ok_l, _, thr_l = m.mahalanobis_support(legacy_feat)
    rows = []
    for nm, mask, t in [("full_sample", np.ones(len(A), bool), np.nan), ("support_95pct_correct_logdensity", ok, thr),
                        ("support_95pct_as_implemented_1005_8", ok_l, thr_l)]:
        sub = A[mask].reset_index(drop=True)
        r, _, _ = evaluate(Ctx(sub, "Annual_nig"))
        rows.append({"spec": nm, "threshold": t, **r})
    pd.DataFrame(rows).to_csv(RES / "common_support_results.csv", index=False)
    log("support done")

    # ---- subgroup stratification (pooled OOF predictions from the primary run; predefined strata)
    size_t = pd.qcut(np.log(A.B_2020), 3, labels=["small", "mid", "large"])
    yob_g = np.where(A.yob <= 1975, "established_YOB<=1975", "recent_YOB>1975")
    rows = []
    for dim, labs in [("size_tercile", size_t.astype(str)), ("age", pd.Series(yob_g)), ("region", A.region)]:
        for lv in sorted(set(labs)):
            mk = (np.asarray(labs) == lv)
            dm = m.delta_metrics(ctx.y[mk], p0[mk], p1[mk])
            bt = m.tile_bootstrap_delta(ctx.y[mk], p0[mk], p1[mk], ctx.tiles[mk], 1000)
            rows.append({"dimension": dim, "level": lv, **dm, "delta_r2_ci_lo": bt["delta_r2_ci_lo"], "delta_r2_ci_hi": bt["delta_r2_ci_hi"],
                         "note": "pooled-OOF subset; M0/M1 trained on all folds' training rows; N<30 descriptive" if dm["n"] < 30 else
                                 "pooled-OOF subset; M0/M1 trained on all folds' training rows"})
    pd.DataFrame(rows).to_csv(RES / "subgroup_results.csv", index=False)

    mor = moran_block(ctx, p0, p1, A)
    mor.to_csv(RES / "spatial_residual_diagnostics.csv", index=False)

    # ---- SEAL primary outputs, then secondary response
    primary_files = [RES / f for f in ["analysis_sample_summary.json", "primary_model_metrics.csv", "primary_oof_predictions.csv",
                                       "history_null_results.csv", "history_null_shuffled_draws.csv", "region_holdout_results.csv", "twin_results.csv",
                                       "twin_summary.json", "transfer_results.csv", "strict_precedence_results.csv", "boundary_sensitivity_results.csv",
                                       "geometry_sensitivity_results.csv", "context_state_sensitivity.csv", "common_support_results.csv",
                                       "subgroup_results.csv", "spatial_residual_diagnostics.csv"]]
    m.write_primary_marker(primary_files, RES / "primary_outputs_sealed.json")
    m.assert_primary_complete(primary_files, RES / "primary_outputs_sealed.json")
    log("PRIMARY OUTPUTS SEALED; loading Summer_day")

    A2 = d.attach_response(A_all, fields=("Annual_nig", "Summer_day"))
    assert (A2.yceo_id.values == A.yceo_id.values).all() and A2.Summer_day.notna().all()
    E2 = run_experiments_compact(A2, "Summer_day")
    E2.to_csv(RES / "secondary_response_results.csv", index=False)

    raw_hash_after = m.sha256_file(d.YCEO_SHP)
    meta = {"execution_id": "1005-9", "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
            "seed": m.SEED, "n_shuffle_permutations": N_PERM, "n_block_bootstrap": N_BOOT,
            "rf_params": {k: v for k, v in m.RF_PARAMS.items() if k != "n_jobs"}, "network_access": "none",
            "new_research_data_downloaded": False, "interim_shapefile_sha256_unchanged": raw_hash_before == raw_hash_after,
            "raw_zip_sha256": m.sha256_file(ROOT / "data" / "raw" / "thermal_response" / "sdei-yceo-sfc-uhi-v4-urban-cluster-means-shp.zip"),
            "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
            "runtime_seconds": time.time() - T0}
    import sklearn
    meta["sklearn"] = sklearn.__version__
    (RES / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log("pipeline complete")
    return 0


def run_experiments_compact(A, y_col):
    """Compact replication for the secondary response: Exp 1 (rf+ridge, shuffled null, regions), Exp 2, Exp 3."""
    ctx = Ctx(A, y_col)
    rows = []
    r, p0, p1 = evaluate(ctx)
    rows.append({"experiment": "E1_rf_primary", **r})
    rr, rp0, rp1 = evaluate(ctx, learner="ridge")
    rows.append({"experiment": "E1_ridge", **rr})
    strata = m.size_strata(A["region"].to_numpy(), np.log(A["B_2020"].to_numpy()))
    perm = []
    for i in range(N_PERM):
        rng = np.random.default_rng(m.SEED + 1000 + i)
        perm.append(m.delta_metrics(ctx.y, p0, m.oof_predict(ctx.base, m.shuffle_rows_within_strata(ctx.H, strata, rng), ctx.y, ctx.fold, "rf", "raw"))["delta_r2"])
    perm = np.array(perm)
    rows.append({"experiment": "E1_shuffled_H_null", "observed_delta_r2": r["delta_r2"], "null_mean": float(perm.mean()), "null_q95": float(np.quantile(perm, .95)),
                 "percentile_of_observed": float((perm < r["delta_r2"]).mean() * 100)})
    Hps = m.pseudo_history_from_S(ctx.base, ctx.H, ctx.fold)
    rows.append({"experiment": "E1_pseudoH_from_S", **evaluate(ctx, H=Hps, p0=p0, boot=False)[0]})
    Hpre = m.h_rebased(A, m.H_PRE2000_EPOCHS, 2000)
    rows.append({"experiment": "E1_strict_Hpre2000", **evaluate(ctx, H=Hpre)[0]})
    rows.append({"experiment": "E1_C2", **evaluate(Ctx(A, y_col, "S3", "C2"))[0]})
    regs = A["region"].to_numpy()
    for reg in ADEQUATE + ["Oceania"]:
        te = regs == reg
        m0 = m.make_learner("rf").fit(ctx.base[~te], ctx.y[~te])
        Xtr, Xte = m.prep_features(ctx.base[~te], ctx.base[te], ctx.H[~te], ctx.H[te], "raw")
        m1 = m.make_learner("rf").fit(Xtr, ctx.y[~te])
        rows.append({"experiment": f"E1_region_{reg}" + ("_DESCRIPTIVE_ONLY" if reg == "Oceania" else ""),
                     **m.delta_metrics(ctx.y[te], m0.predict(ctx.base[te]), m1.predict(Xte))})
    pairs_df, tsum = twin_block(A, ctx, ctx.y)
    rows.append({"experiment": "E2_twin_partial_spearman", "partial_spearman": tsum["partial_spearman"], "ci_lo": tsum["boot_ci"][0], "ci_hi": tsum["boot_ci"][1],
                 "perm_null_q95": tsum["perm_null_q95"], "perm_p_one_sided_ge": tsum["perm_p_one_sided_ge"], "n_pairs": tsum["n_pairs"]})
    tr = transfer_block(A, ctx, ctx.y, n_null=50).iloc[0]
    rows.append({"experiment": "E3_transfer", **{k: tr[k] for k in ("rmse_A0", "rmse_A1", "delta_rmse_transfer", "delta_rmse_ci_lo", "delta_rmse_ci_hi",
                                                                    "null_shuffled_H_mean", "null_shuffled_H_q05", "pct_obs_below_null")}})
    mor = moran_block(ctx, p0, p1, A)
    for rr_ in mor.itertuples():
        rows.append({"experiment": f"Moran_{rr_.model}_k{rr_.k_neighbours}", "morans_I": rr_.morans_I})
    out = pd.DataFrame(rows)
    out.insert(0, "response", y_col)
    return out


if __name__ == "__main__":
    sys.exit(main())
