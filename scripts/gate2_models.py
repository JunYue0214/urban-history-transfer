"""Execution 1005-9 model library (Gate 2: H -> R incremental information).

Pure, unit-tested functions. Nothing here touches the network or raw data.
Response values enter only as the `y` arguments passed in by the pipeline.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
RF_PARAMS = dict(n_estimators=500, min_samples_leaf=5, max_features=0.5, random_state=SEED, n_jobs=-1)
RIDGE_ALPHAS = np.logspace(-3, 3, 13)
EPOCHS = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
H_PRIMARY_EPOCHS = EPOCHS[:-1]                      # 1975..2015
H_PRE2000_EPOCHS = [1975, 1980, 1985, 1990, 1995]   # strict precedence: rebased on B(2000)
H_T2015_EPOCHS = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]
GEOMETRY_SENSITIVITIES = (  # immutable copy of the three 1005-8 sensitivities
    ("S1_looser_coverage_040", 0.4, None),
    ("S2_stricter_coverage_060", 0.6, None),
    ("S3_drop_iou_floor", 0.5, None),
)
PRIMARY_GEOMETRY = (0.5, 0.20)


# --------------------------------------------------------------------- learners
def make_learner(name: str):
    if name == "rf":
        return RandomForestRegressor(**RF_PARAMS)
    if name == "ridge":
        return make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS))
    raise ValueError(name)


def prep_features(base_tr, base_te, H_tr, H_te, h_mode):
    """Features for one fold. h_mode: None (M0), 'raw', 'pca3'. PCA is fit on TRAINING H only."""
    if h_mode is None:
        return base_tr, base_te
    if h_mode == "raw":
        return np.hstack([base_tr, H_tr]), np.hstack([base_te, H_te])
    if h_mode == "pca3":
        sc = StandardScaler().fit(H_tr)
        pca = PCA(n_components=3, random_state=SEED).fit(sc.transform(H_tr))
        return (np.hstack([base_tr, pca.transform(sc.transform(H_tr))]),
                np.hstack([base_te, pca.transform(sc.transform(H_te))]))
    raise ValueError(h_mode)


def oof_predict(base, H, y, fold_ids, learner="rf", h_mode=None) -> np.ndarray:
    """Out-of-fold predictions; each row is predicted by a model that never saw it."""
    base = np.asarray(base, float)
    y = np.asarray(y, float)
    H = None if H is None else np.asarray(H, float)
    pred = np.full(len(y), np.nan)
    for k in np.unique(fold_ids):
        te = fold_ids == k
        tr = ~te
        Xtr, Xte = prep_features(base[tr], base[te], None if H is None else H[tr], None if H is None else H[te], h_mode)
        m = make_learner(learner).fit(Xtr, y[tr])
        pred[te] = m.predict(Xte)
    return pred


def metrics(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    sse = float(((y - p) ** 2).sum())
    sst = float(((y - y.mean()) ** 2).sum())
    return {"r2": 1 - sse / sst, "rmse": float(np.sqrt(sse / len(y))), "mae": float(np.abs(y - p).mean()), "n": int(len(y))}


def delta_metrics(y, p0, p1) -> dict:
    a, b = metrics(y, p0), metrics(y, p1)
    return {"r2_m0": a["r2"], "r2_m1": b["r2"], "delta_r2": b["r2"] - a["r2"],
            "rmse_m0": a["rmse"], "rmse_m1": b["rmse"], "delta_rmse": b["rmse"] - a["rmse"],
            "mae_m0": a["mae"], "mae_m1": b["mae"], "delta_mae": b["mae"] - a["mae"], "n": a["n"]}


def tile_bootstrap_delta(y, p0, p1, tiles, B=2000, seed=SEED) -> dict:
    """Spatial block bootstrap over 10-degree tiles of stored OOF predictions."""
    y, p0, p1, tiles = (np.asarray(v) for v in (y, p0, p1, tiles))
    ut, inv = np.unique(tiles, return_inverse=True)
    T = len(ut)

    def tsum(v):
        return np.bincount(inv, weights=v, minlength=T)

    n = tsum(np.ones(len(y)))
    sy, syy = tsum(y), tsum(y ** 2)
    sse0, sse1 = tsum((y - p0) ** 2), tsum((y - p1) ** 2)
    sae0, sae1 = tsum(np.abs(y - p0)), tsum(np.abs(y - p1))
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(T, np.full(T, 1.0 / T), size=B).astype(float)
    N = counts @ n
    sst = counts @ syy - (counts @ sy) ** 2 / N
    r0, r1 = 1 - (counts @ sse0) / sst, 1 - (counts @ sse1) / sst
    rm0, rm1 = np.sqrt((counts @ sse0) / N), np.sqrt((counts @ sse1) / N)
    ma0, ma1 = (counts @ sae0) / N, (counts @ sae1) / N
    out = {}
    for name, d in [("delta_r2", r1 - r0), ("delta_rmse", rm1 - rm0), ("delta_mae", ma1 - ma0)]:
        out[name + "_ci_lo"], out[name + "_ci_hi"] = (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)))
        out[name + "_boot_sd"] = float(d.std(ddof=1))
    return out


# ------------------------------------------------------------------------ nulls
def size_strata(region, size_values) -> np.ndarray:
    q = np.quantile(size_values, [1 / 3, 2 / 3])
    terc = np.digitize(size_values, q)
    return np.array([f"{r}||{t}" for r, t in zip(region, terc)])


def shuffle_rows_within_strata(M, strata, rng) -> np.ndarray:
    """Permute whole rows of M among units sharing a stratum (rows stay intact)."""
    M = np.asarray(M)
    out = M.copy()
    strata = np.asarray(strata)
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        out[idx] = M[rng.permutation(idx)]
    return out


def redundant_pseudo_history(S3) -> np.ndarray:
    """9 deterministic functions of present state S3 (4 columns: lpop, lbus, lbuv, ldens)."""
    S3 = np.asarray(S3, float)
    z = (S3 - S3.mean(0)) / S3.std(0)
    a, b, c, d = z.T
    cols = [a ** 2, b ** 2, c ** 2, d ** 2, a * b, a * c, b * c, a * d, b * d]
    return np.column_stack(cols)


def pseudo_history_from_S(base, H, fold_ids) -> np.ndarray:
    """Out-of-fold prediction of H from S+C only (R never enters)."""
    base, H = np.asarray(base, float), np.asarray(H, float)
    out = np.zeros_like(H)
    for k in np.unique(fold_ids):
        te = fold_ids == k
        m = RandomForestRegressor(**RF_PARAMS).fit(base[~te], H[~te])
        out[te] = m.predict(base[te])
    return out


def random_matched_history(H, rng) -> np.ndarray:
    H = np.asarray(H, float)
    return rng.multivariate_normal(H.mean(0), np.cov(H.T), size=len(H))


# ------------------------------------------------------------------------ twins
def build_twins(X, lat, lon, k=10, min_sep_km=200.0):
    """Mutual-kNN pairs from S/C features and geography ONLY (no H, no R argument)."""
    import gate2_support as g
    pairs, _ = g.mutual_knn_pairs(np.asarray(X, float), np.asarray(lat, float), np.asarray(lon, float), k, min_sep_km)
    return np.array(pairs, dtype=int)


def _resid(y, Z):
    Z1 = np.column_stack([np.ones(len(y)), Z])
    beta, *_ = np.linalg.lstsq(Z1, y, rcond=None)
    return y - Z1 @ beta


def partial_spearman(dr, dh, dsc, dgeo) -> float:
    r = [rankdata(np.asarray(v, float)) for v in (dr, dh, dsc, dgeo)]
    Z = np.column_stack([r[2], r[3]])
    a, b = _resid(r[0], Z), _resid(r[1], Z)
    return float(np.corrcoef(a, b)[0, 1])


def pair_distances(H, pairs):
    return np.linalg.norm(H[pairs[:, 0]] - H[pairs[:, 1]], axis=1)


def twin_tile_bootstrap(stat_fn, pairs, tiles, B=500, seed=SEED):
    """Cluster bootstrap over tiles; a pair is replicated m_a*m_b times (dependence-aware)."""
    rng = np.random.default_rng(seed)
    ut, inv = np.unique(tiles, return_inverse=True)
    ta, tb = inv[pairs[:, 0]], inv[pairs[:, 1]]
    out = []
    for _ in range(B):
        m = rng.multinomial(len(ut), np.full(len(ut), 1.0 / len(ut)))
        w = m[ta] * m[tb]
        idx = np.repeat(np.arange(len(pairs)), w)
        if len(idx) > 10:
            out.append(stat_fn(idx))
    return np.array(out)


# --------------------------------------------------------------------- transfer
def block_scaled_features(blocks_tr, blocks_te):
    """z-score each block on TRAINING rows; scale each block to the same total variance."""
    tr, te = [], []
    for btr, bte in zip(blocks_tr, blocks_te):
        mu, sd = btr.mean(0), btr.std(0)
        sd[sd == 0] = 1.0
        f = np.sqrt(btr.shape[1])
        tr.append((btr - mu) / sd / f)
        te.append((bte - mu) / sd / f)
    return np.hstack(tr), np.hstack(te)


def idw_knn_predict(Ftr, ytr, Fte, K=10):
    tree = cKDTree(Ftr)
    d, idx = tree.query(Fte, k=K)
    w = 1.0 / (d + 1e-9)
    return (w * ytr[idx]).sum(1) / w.sum(1), idx


def transfer_predict(blocks, y, fold_ids, K=10, donor_mask_fn=None):
    """Held-out targets use donors from other folds only. donor_mask_fn(test_mask) may restrict donors further."""
    y = np.asarray(y, float)
    pred = np.full(len(y), np.nan)
    used = {}
    for k in np.unique(fold_ids):
        te = fold_ids == k
        donors = ~te
        if donor_mask_fn is not None:
            donors = donors & donor_mask_fn(te)
        Ftr, Fte = block_scaled_features([b[donors] for b in blocks], [b[te] for b in blocks])
        p, idx = idw_knn_predict(Ftr, y[donors], Fte, K)
        pred[te] = p
        used[k] = np.where(donors)[0][np.unique(idx)]
    return pred, used


# --------------------------------------------------------------- history builders
def h_rebased(B: pd.DataFrame, epochs, base_year) -> np.ndarray:
    """H_j(t) = B(t)/B(base_year) using only columns B_<t> for t in epochs and base_year."""
    return np.column_stack([B[f"B_{t}"].to_numpy(float) / B[f"B_{base_year}"].to_numpy(float) for t in epochs])


def history_descriptors(B: pd.DataFrame) -> np.ndarray:
    base = B["B_2020"].to_numpy(float)
    h1990, h2000 = B["B_1990"] / base, B["B_2000"] / base
    inc = np.clip(np.diff(np.column_stack([B[f"B_{t}"] for t in EPOCHS]).astype(float), axis=1), 0, None)
    mid = np.array([(EPOCHS[i] + EPOCHS[i + 1]) / 2 for i in range(len(EPOCHS) - 1)])
    den = inc.sum(1)
    timing = np.where(den > 0, (inc * mid).sum(1) / den, np.nan)
    return np.column_stack([h1990, h2000, 1 - h2000, timing])


# ------------------------------------------------------------------- diagnostics
def morans_i(resid, lat, lon, k=8, n_perm=499, seed=SEED):
    lat_r, lon_r = np.radians(lat), np.radians(lon)
    xyz = np.column_stack([np.cos(lat_r) * np.cos(lon_r), np.cos(lat_r) * np.sin(lon_r), np.sin(lat_r)])
    _, nb = cKDTree(xyz).query(xyz, k=k + 1)
    nb = nb[:, 1:]
    z = np.asarray(resid, float) - np.mean(resid)

    def stat(v):
        return float((v * v[nb].mean(1)).sum() / (v ** 2).sum())

    obs = stat(z)
    rng = np.random.default_rng(seed)
    perm = np.array([stat(rng.permutation(z)) for _ in range(n_perm)])
    return obs, float((1 + (perm >= obs).sum()) / (n_perm + 1)), float(perm.mean())


def mahalanobis_support(X, q=0.95):
    X = np.asarray(X, float)
    sd = X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - X.mean(0)) / sd
    cov = np.cov(Z.T) + np.eye(Z.shape[1]) * 1e-6
    d = np.sqrt(np.einsum("ij,jk,ik->i", Z - Z.mean(0), np.linalg.inv(cov), Z - Z.mean(0)))
    thr = float(np.quantile(d, q))
    return d <= thr, d, thr


# --------------------------------------------------------- primary/secondary guard
def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_primary_marker(files, marker_path) -> dict:
    rec = {Path(f).name: sha256_file(f) for f in sorted(files)}
    Path(marker_path).write_text(json.dumps({"primary_outputs_sha256": rec}, indent=2), encoding="utf-8")
    return rec


def assert_primary_complete(files, marker_path) -> None:
    mp = Path(marker_path)
    if not mp.is_file():
        raise RuntimeError("primary outputs not sealed: secondary response analysis is not allowed yet")
    rec = json.loads(mp.read_text(encoding="utf-8"))["primary_outputs_sha256"]
    for f in files:
        f = Path(f)
        if rec.get(f.name) != sha256_file(f):
            raise RuntimeError(f"primary output changed after sealing: {f.name}")
