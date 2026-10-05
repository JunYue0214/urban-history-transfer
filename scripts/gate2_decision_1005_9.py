"""Mechanical Gate 2 decision + diagnostic figures for 1005-9.

Applies ONLY the rules written in results/1005-9/gate2_validation_amendment.md (sections C, D, H) to the
saved result files. No new modelling happens here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "results" / "1005-9", ROOT / "figures" / "1005-9"
ADEQUATE = ["Asia", "Africa", "Europe", "North America", "South America"]


def decide() -> dict:
    prim = pd.read_csv(RES / "primary_model_metrics.csv").set_index("spec")
    rf, rg = prim.loc["PRIMARY_rf_S3C1_rawH"], prim.loc["ridge_rawH"]
    nulls = pd.read_csv(RES / "history_null_results.csv").set_index("null")
    n1, n2, n3 = (nulls.loc["N1_shuffled_H_within_region_x_size"], nulls.loc["N2_pseudoH_predicted_from_S_C_oof"],
                  nulls.loc["N3_redundant_pseudoH_from_S"])
    reg = pd.read_csv(RES / "region_holdout_results.csv")
    reg = reg[reg.held_out_region.isin(ADEQUATE)]
    twin = json.loads((RES / "twin_summary.json").read_text())
    tr = pd.read_csv(RES / "transfer_results.csv").iloc[0]
    ctxs = pd.read_csv(RES / "context_state_sensitivity.csv").set_index("spec")
    strict = pd.read_csv(RES / "strict_precedence_results.csv").set_index("spec")
    sec = pd.read_csv(RES / "secondary_response_results.csv").set_index("experiment")

    d1 = float(rf.delta_r2)
    ci_lo, ci_hi = float(rf.delta_r2_ci_lo), float(rf.delta_r2_ci_hi)
    n_pos = int((reg.delta_r2 > 0).sum())
    n_neg = int((reg.delta_r2 < 0).sum())
    above_null = d1 > float(n1.null_q95)
    pseudo_explains = bool(d1 > 0 and float(n2.null_mean) >= 0.8 * d1)
    c2 = float(ctxs.loc["S3+C2"].delta_r2)
    c2_ok = bool(d1 > 0 and np.sign(c2) == np.sign(d1) and abs(c2) >= 0.5 * abs(d1))
    sp = strict.loc["STRICT_Hpre2000_rebased_B2000_with_S2020"]
    d2, d2_lo = float(sp.delta_r2), float(sp.delta_r2_ci_lo)
    if d1 < 0.005 or d2 < 0.005 or d2_lo <= 0:
        strict_label = "DISAPPEARS"
    elif d2 >= max(0.005, 0.5 * d1):
        strict_label = "SURVIVES"
    else:
        strict_label = "WEAKENS"
    sec_rf = sec.loc["E1_rf_primary"]
    sec_present = bool(sec_rf.delta_r2 >= 0.005 and sec_rf.delta_r2_ci_lo > 0)
    prim_present = bool(d1 >= 0.005 and ci_lo > 0)
    sec_label = "CONCORDANT" if (prim_present and sec_present) else "NULL" if (not prim_present and not sec_present) else "DISCORDANT"
    ridge_same = bool(np.sign(float(rg.delta_r2)) == np.sign(d1) and (float(rg.delta_r2_ci_lo) > 0) == (ci_lo > 0))

    cond_i = bool(d1 < 0.005 and ci_lo <= 0 <= ci_hi)
    cond_ii = not above_null
    cond_iii = pseudo_explains
    cond_iv = bool(twin["partial_spearman"] <= 0.02 and float(tr.delta_rmse_transfer) >= float(tr.null_shuffled_H_q05))
    fail = cond_i or cond_ii or cond_iii or cond_iv
    strong = {
        "1_dR2>=0.02_and_CI_excludes_0": bool(d1 >= 0.02 and ci_lo > 0),
        "2_above_shuffled_null_q95": bool(above_null),
        "3_positive_in_>=4_of_5_regions": bool(n_pos >= 4),
        "4_not_explained_by_pseudo_history": bool(d1 > 0 and float(n2.null_mean) < 0.8 * d1 and float(n3.null_mean) < d1),
        "5_survives_C2_and_strict_precedence": bool(c2_ok and strict_label == "SURVIVES"),
        "6_transfer_negative_below_null_and_twin_rho>=0.05_p<0.01": bool(
            float(tr.delta_rmse_transfer) < 0 and float(tr.delta_rmse_transfer) < float(tr.null_shuffled_H_q05)
            and twin["partial_spearman"] >= 0.05 and twin["perm_p_one_sided_ge"] < 0.01),
    }
    gate = "FAIL" if fail else ("PASS" if all(strong.values()) else "MIXED")
    program = {"PASS": "CONTINUE", "MIXED": "REVISE", "FAIL": "STOP"}[gate]
    out = {
        "GATE_2": gate, "TRANSFERABILITY_PROGRAM": program,
        "fail_conditions": {"i_dR2<0.005_and_CI_includes_0": cond_i, "ii_not_above_shuffled_null_q95": cond_ii,
                            "iii_pseudoH_>=80pct_of_positive_observed": cond_iii, "iv_twin<=0.02_and_transfer_within_null": cond_iv},
        "strong_for_criteria": strong,
        "against_flags_not_by_themselves_FAIL": {"negative_in_>=3_of_5_regions": bool(n_neg >= 3), "C2_collapse": bool(not c2_ok),
                                                 "strict_precedence_fails": strict_label != "SURVIVES"},
        "primary": {"r2_m0": float(rf.r2_m0), "r2_m1": float(rf.r2_m1), "delta_r2": d1, "delta_r2_ci": [ci_lo, ci_hi],
                    "delta_rmse": float(rf.delta_rmse), "delta_rmse_ci": [float(rf.delta_rmse_ci_lo), float(rf.delta_rmse_ci_hi)],
                    "delta_mae": float(rf.delta_mae), "n": int(rf.n)},
        "shuffled_H_null": {"mean": float(n1.null_mean), "q95": float(n1.null_q95), "percentile_of_observed": float(n1.percentile_of_observed)},
        "pseudoH_from_S_delta_r2": float(n2.null_mean), "redundant_pseudoH_delta_r2": float(n3.null_mean),
        "ridge": {"delta_r2": float(rg.delta_r2), "ci": [float(rg.delta_r2_ci_lo), float(rg.delta_r2_ci_hi)], "same_qualitative_conclusion_as_rf": ridge_same},
        "regions_positive": n_pos, "regions_negative": n_neg, "regions_adequate": len(reg),
        "twin_partial_spearman": twin["partial_spearman"], "twin_ci": twin["boot_ci"], "twin_perm_p": twin["perm_p_one_sided_ge"],
        "transfer_delta_rmse": float(tr.delta_rmse_transfer), "transfer_null_shuffled_mean": float(tr.null_shuffled_H_mean),
        "transfer_null_shuffled_q05": float(tr.null_shuffled_H_q05),
        "strict_precedence": strict_label, "strict_delta_r2": d2, "strict_ci": [d2_lo, float(sp.delta_r2_ci_hi)],
        "secondary_Summer_day": sec_label, "secondary_rf_delta_r2": float(sec_rf.delta_r2),
        "secondary_rf_ci": [float(sec_rf.delta_r2_ci_lo), float(sec_rf.delta_r2_ci_hi)],
        "causal_claim_allowed": False,
        "h_r_inspected_before_rules_fixed": False,
        "rules_source": "results/1005-9/gate2_validation_amendment.md (sections C, D, H), written before any R was joined",
    }
    (RES / "gate2_decision.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def figures(dec: dict) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    oof = pd.read_csv(RES / "primary_oof_predictions.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.3), sharex=True, sharey=True)
    for a, c, t in [(ax[0], "pred_M0_rf", "M0 (S3+C1)"), (ax[1], "pred_M1_rf", "M1 (S3+C1+H)")]:
        a.scatter(oof[c], oof["y"], s=4, alpha=.35)
        lim = [oof.y.min(), oof.y.max()]
        a.plot(lim, lim, "k--", lw=.8)
        a.set_xlabel("out-of-fold prediction (degC)"); a.set_title(t)
    ax[0].set_ylabel("observed Annual_nig (degC)")
    fig.tight_layout(); fig.savefig(FIG / "fig1_oof_obs_vs_pred.png", dpi=110); plt.close(fig)

    draws = pd.read_csv(RES / "history_null_shuffled_draws.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.hist(draws.perm_delta_r2, bins=30, color="#999999")
    ax.axvline(dec["primary"]["delta_r2"], color="r", label=f"observed {dec['primary']['delta_r2']:.4f}")
    ax.axvline(dec["shuffled_H_null"]["q95"], color="k", ls=":", label="null 95th pct")
    ax.axvline(0.02, color="g", ls="--", label="pre-registered strong-for 0.02")
    ax.set_xlabel("delta R2 (M1 - M0), shuffled H"); ax.legend(fontsize=8); ax.set_title("Observed gain vs shuffled-H null (300 draws)")
    fig.tight_layout(); fig.savefig(FIG / "fig2_delta_vs_shuffled_null.png", dpi=110); plt.close(fig)

    reg = pd.read_csv(RES / "region_holdout_results.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    cols = ["#4C72B0" if r in ADEQUATE else "#BBBBBB" for r in reg.held_out_region]
    ax.bar(reg.held_out_region, reg.delta_r2, color=cols)
    ax.axhline(0, color="k", lw=.7)
    for i, (r, n) in enumerate(zip(reg.held_out_region, reg.n)):
        ax.text(i, 0, f"N={n}", ha="center", va="bottom", fontsize=7)
    ax.set_ylabel("delta R2 (leave-region-out)"); ax.set_title("Regional delta R2 (grey = Oceania, descriptive only)")
    plt.setp(ax.get_xticklabels(), rotation=20)
    fig.tight_layout(); fig.savefig(FIG / "fig3_regional_delta_r2.png", dpi=110); plt.close(fig)

    tw = pd.read_csv(RES / "twin_results.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].hexbin(tw.D_H, tw.D_R, gridsize=40, mincnt=1, cmap="Greys")
    ax[0].set_xlabel("D_H"); ax[0].set_ylabel("D_R (degC)"); ax[0].set_title("Twin pairs (n=%d)" % len(tw))
    order = ["low_DH", "mid_DH", "high_DH"]
    ax[1].boxplot([tw[tw.DH_stratum == s].D_R for s in order], tick_labels=order, showfliers=False)
    ax[1].set_ylabel("D_R (degC)"); ax[1].set_title("D_R by D_H tertile")
    fig.tight_layout(); fig.savefig(FIG / "fig4_twin_DH_vs_DR.png", dpi=110); plt.close(fig)

    tr = pd.read_csv(RES / "transfer_results.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    lab = ["pooled"] + list(tr.held_out_region.dropna())
    vals = [tr.iloc[0].delta_rmse_transfer] + list(tr.delta_rmse_transfer.iloc[1:])
    ax.bar(lab, vals, color=["#C44E52"] + ["#4C72B0"] * (len(lab) - 1))
    ax.axhline(0, color="k", lw=.7)
    ax.axhline(tr.iloc[0].null_shuffled_H_mean, color="gray", ls=":", label="shuffled-H null mean (pooled)")
    ax.set_ylabel("delta RMSE_transfer (A1 - A0); negative = history helps"); ax.legend(fontsize=8)
    plt.setp(ax.get_xticklabels(), rotation=20)
    fig.tight_layout(); fig.savefig(FIG / "fig5_transfer_delta_rmse.png", dpi=110); plt.close(fig)

    sp = pd.read_csv(RES / "strict_precedence_results.csv")
    bd = pd.read_csv(RES / "boundary_sensitivity_results.csv")
    gm = pd.read_csv(RES / "geometry_sensitivity_results.csv")
    cx = pd.read_csv(RES / "context_state_sensitivity.csv")
    cs = pd.read_csv(RES / "common_support_results.csv")
    allr = pd.concat([sp.assign(g="temporal"), bd.assign(g="boundary"), gm.assign(g="geometry"), cx.assign(g="context"), cs.assign(g="support"),
                      pd.read_csv(RES / "primary_model_metrics.csv").assign(g="learner/H-rep")], ignore_index=True)
    allr = allr.dropna(subset=["delta_r2", "delta_r2_ci_lo"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 0.28 * len(allr) + 1.5))
    y = np.arange(len(allr))[::-1]
    ax.errorbar(allr.delta_r2, y, xerr=[allr.delta_r2 - allr.delta_r2_ci_lo, allr.delta_r2_ci_hi - allr.delta_r2], fmt="o", ms=3, lw=.8)
    ax.axvline(0, color="k", lw=.7); ax.axvline(0.02, color="g", ls="--", lw=.8); ax.axvline(0.005, color="orange", ls=":", lw=.8)
    ax.set_yticks(y); ax.set_yticklabels([f"{g}: {s}"[:58] for g, s in zip(allr.g, allr.spec)], fontsize=6)
    ax.set_xlabel("delta R2 (95% spatial-block CI); green = 0.02, orange = 0.005 guidance")
    fig.tight_layout(); fig.savefig(FIG / "fig6_sensitivity_forest.png", dpi=110); plt.close(fig)

    sec = pd.read_csv(RES / "secondary_response_results.csv").set_index("experiment")
    pr = pd.read_csv(RES / "primary_model_metrics.csv").set_index("spec")
    fig, ax = plt.subplots(figsize=(6, 4))
    items = [("Annual_nig RF", pr.loc["PRIMARY_rf_S3C1_rawH"]), ("Summer_day RF", sec.loc["E1_rf_primary"]),
             ("Annual_nig ridge", pr.loc["ridge_rawH"]), ("Summer_day ridge", sec.loc["E1_ridge"])]
    for i, (n, r) in enumerate(items):
        ax.errorbar(r.delta_r2, i, xerr=[[r.delta_r2 - r.delta_r2_ci_lo], [r.delta_r2_ci_hi - r.delta_r2]], fmt="o", color="#4C72B0")
    ax.set_yticks(range(len(items))); ax.set_yticklabels([n for n, _ in items]); ax.axvline(0, color="k", lw=.7)
    ax.set_xlabel("delta R2 with 95% CI"); ax.set_title("Primary vs secondary response")
    fig.tight_layout(); fig.savefig(FIG / "fig7_primary_vs_secondary.png", dpi=110); plt.close(fig)

    mo = pd.read_csv(RES / "spatial_residual_diagnostics.csv")
    fig, ax = plt.subplots(figsize=(5, 3.8))
    for k, sh in [(8, "o"), (20, "s")]:
        s = mo[mo.k_neighbours == k]
        ax.plot(s.model, s.morans_I, sh + "-", label=f"k={k}")
    ax.set_ylabel("Moran's I of OOF residuals"); ax.legend(); ax.set_title("Residual spatial structure (Annual_nig)")
    fig.tight_layout(); fig.savefig(FIG / "fig8_residual_morans_i.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    dec = decide()
    figures(dec)
    print(json.dumps({k: dec[k] for k in ("GATE_2", "TRANSFERABILITY_PROGRAM", "fail_conditions", "strong_for_criteria",
                                          "against_flags_not_by_themselves_FAIL", "strict_precedence", "secondary_Summer_day")}, indent=1))
    sys.exit(0)
