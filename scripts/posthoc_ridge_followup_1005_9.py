"""POST-HOC diagnostic (run after the pre-registered pipeline had produced the ridge result).

Question: is the ridge Delta R2 (H gain) real incremental information, or does H merely stand in for
nonlinear S/C structure that the linear baseline cannot represent?  Uses only Annual_nig and the same
folds; nothing here feeds the pre-registered decision.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_data as d  # noqa: E402
import gate2_models as m  # noqa: E402
import gate2_support as g  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "1005-9"


def main():
    cities = d.load_cities()
    links = g.load_links(d.LINKS_PATH)
    A = d.attach_response(d.assemble_units(d.units_for_rule(links, *m.PRIMARY_GEOMETRY), cities), fields=("Annual_nig",))
    tiles, fold = d.folds_for(A)
    S, C, y = d.s_block(A, "S3"), d.c_block(A, "C1"), A["Annual_nig"].to_numpy(float)
    base = np.hstack([S, C])
    H = m.h_rebased(A, m.H_PRIMARY_EPOCHS, 2020)
    strata = m.size_strata(A["region"].to_numpy(), np.log(A["B_2020"].to_numpy()))
    rows = []

    def rec(label, base_, H_, learner="ridge"):
        p0 = m.oof_predict(base_, None, y, fold, learner, None)
        p1 = m.oof_predict(base_, H_, y, fold, learner, "raw")
        r = m.delta_metrics(y, p0, p1)
        r.update(m.tile_bootstrap_delta(y, p0, p1, tiles, 2000))
        rows.append({"spec": label, **r})
        return r["delta_r2"]

    obs = rec("ridge_linear_base_realH", base, H)
    Hps = m.pseudo_history_from_S(base, H, fold)
    rec("ridge_linear_base_pseudoH_from_S_C", base, Hps)
    rec("ridge_linear_base_redundant_pseudoH", base, m.redundant_pseudo_history(S))
    poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform((base - base.mean(0)) / base.std(0))
    rec("ridge_quadratic_base_realH", poly, H)
    rec("ridge_quadratic_base_pseudoH_from_S_C", poly, Hps)
    rng = np.random.default_rng(m.SEED)
    p0q = m.oof_predict(poly, None, y, fold, "ridge", None)
    null = np.array([
        m.delta_metrics(y, p0q, m.oof_predict(poly, m.shuffle_rows_within_strata(H, strata, rng), y, fold, "ridge", "raw"))["delta_r2"]
        for _ in range(300)])
    rows.append({"spec": "ridge_quadratic_base_shuffledH_null", "delta_r2": float(null.mean()), "n": len(y),
                 "r2_m0": np.nan, "r2_m1": np.nan, "null_q95": float(np.quantile(null, .95))})
    pd.DataFrame(rows).to_csv(RES / "posthoc_ridge_followup.csv", index=False)
    print(pd.DataFrame(rows)[["spec", "r2_m0", "r2_m1", "delta_r2", "delta_r2_ci_lo", "delta_r2_ci_hi", "null_q95"]].round(4).to_string())


if __name__ == "__main__":
    main()
