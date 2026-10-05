"""Execution 1005-8 support library: geometry-rule units, aggregation, bias, support.

BLIND BY CONSTRUCTION. Nothing here reads the thermal response. The only
thermal-derived input is the boolean `yceo_primary_R_valid` already stored in
results/1005-7/ucdb_yceo_crosswalk.csv; the shapefile and its SUHI columns are
never opened. All functions are pure and unit-tested. No network access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

# The ONLY columns that may be read from the 1005-7 crosswalk audit table.
LINK_COLUMNS = [
    "object_type", "ucdb_id", "yceo_id", "ucdb_area_m2", "yceo_area_m2", "intersection_m2",
    "iou", "overlap_over_min", "n_clusters_for_ucdb", "comp_n_yceo", "pair_class",
    "ucdb_country", "yceo_primary_R_valid",
]
H_EPOCHS = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015]
T_END = 2020

# One primary rule + the pre-registered sensitivities are defined in the runner;
# defaults mirror the 1005-7 rule (coverage >= 0.5, no IoU floor).
EXCLUSION_ORDER = ["invalid_R", "cross_country", "ambiguous_nonstar", "low_coverage", "low_iou"]


def load_links(path) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=LINK_COLUMNS, low_memory=False)
    df = df[df["object_type"] == "link"].copy()
    df["ucdb_id"] = df["ucdb_id"].astype(int)
    df["yceo_id"] = df["yceo_id"].astype(int)
    df["yceo_primary_R_valid"] = df["yceo_primary_R_valid"].map(lambda v: str(v).strip().lower() == "true")
    return df.reset_index(drop=True)


def classify_clusters(links: pd.DataFrame, coverage_thr: float, iou_thr: float | None = None,
                      require_valid_R: bool = True) -> pd.DataFrame:
    """One row per linked YCEO cluster with unit metrics and a single status.

    coverage = sum(intersection of linked UCDB centres) / cluster area (the exact
    1005-7 `cluster_ucdb_coverage` metric). unit IoU = I / (sum A_uc + A_y - I).
    Status precedence follows EXCLUSION_ORDER; 'unit' means usable. Each cluster
    appears exactly once, so one cluster-level outcome can never be assigned twice.
    """
    rows = []
    for y, g in links.groupby("yceo_id", sort=True):
        a_y = float(g["yceo_area_m2"].iloc[0])
        inter = float(g["intersection_m2"].sum())
        a_uc = float(g["ucdb_area_m2"].sum())
        cov = inter / a_y
        iou = inter / (a_uc + a_y - inter)
        valid = bool(g["yceo_primary_R_valid"].iloc[0])
        countries = set(g["ucdb_country"].dropna())
        star = bool((g["comp_n_yceo"] == 1).all() and (g["n_clusters_for_ucdb"] == 1).all())
        if require_valid_R and not valid:
            status = "invalid_R"
        elif len(countries) > 1:
            status = "cross_country"
        elif not star:
            status = "ambiguous_nonstar"
        elif cov < coverage_thr - 1e-12:
            status = "low_coverage"
        elif iou_thr is not None and iou < iou_thr - 1e-12:
            status = "low_iou"
        else:
            status = "unit"
        rows.append({"yceo_id": int(y), "n_ucdb": int(g["ucdb_id"].nunique()),
                     "ucdb_ids": ";".join(map(str, sorted(g["ucdb_id"].astype(int)))),
                     "coverage": cov, "unit_iou": iou, "yceo_area_km2": a_y / 1e6,
                     "R_valid": valid, "status": status})
    return pd.DataFrame(rows)


def units_from_status(cl: pd.DataFrame) -> pd.DataFrame:
    u = cl[cl["status"] == "unit"].copy()
    u["unit_type"] = np.where(u["n_ucdb"] == 1, "single_city", "multi_city_aggregate")
    return u.reset_index(drop=True)


def city_ids(units: pd.DataFrame) -> list[int]:
    return [int(i) for s in units["ucdb_ids"] for i in s.split(";")]


def h_vector(df: pd.DataFrame) -> np.ndarray:
    """Cluster H_j(t) = sum_i B_i(t) / sum_i B_i(T) over the rows of `df` (one cluster)."""
    num = np.array([df[f"GH_BUS_TOT_{t}"].sum() for t in H_EPOCHS], dtype=float)
    return num / float(df[f"GH_BUS_TOT_{T_END}"].sum())


def aggregate_units(units: pd.DataFrame, cities: pd.DataFrame, extra_cols: list[str] | None = None) -> pd.DataFrame:
    """Deterministic cluster-level S, C, H table.

    S: population, built-up area, built volume are SUMS over linked centres;
    density = sum pop / sum built-up. C: built-up-area-weighted means (lat, lon,
    elevation, temperature, log precipitation). H: sum B(t)/sum B(T) (fixed boundary).
    Dominant centre = largest 2020 built-up area (ties -> smaller ID).
    """
    ci = cities.set_index("ID_UC_G0")
    extra_cols = extra_cols or []
    out = []
    for r in units.sort_values("yceo_id").itertuples():
        ids = sorted(int(i) for i in r.ucdb_ids.split(";"))
        g = ci.loc[ids]
        bus = g[f"GH_BUS_TOT_{T_END}"].to_numpy(float)
        w = bus / bus.sum()
        dom_pos = int(np.lexsort((np.array(ids), -bus))[0])
        dom_id = ids[dom_pos]
        h_agg = h_vector(g)
        h_dom = h_vector(g.iloc[[dom_pos]])
        row = {"yceo_id": r.yceo_id, "n_ucdb": len(ids), "ucdb_ids": ";".join(map(str, ids)),
               "unit_type": "single_city" if len(ids) == 1 else "multi_city_aggregate",
               "region": g["region"].iloc[dom_pos], "dominant_ucdb_id": dom_id,
               "pop2020": g[f"GH_POP_TOT_{T_END}"].sum(), "bus2020_m2": bus.sum(),
               "buv2020": g[f"GH_BUV_TOT_{T_END}"].sum(),
               "dominant_share_of_built": float(bus[dom_pos] / bus.sum()),
               "coverage": r.coverage, "unit_iou": r.unit_iou, "yceo_area_km2": r.yceo_area_km2,
               "H_dist_aggregate_vs_dominant": float(np.linalg.norm(h_agg - h_dom))}
        row["density"] = row["pop2020"] / row["bus2020_m2"]
        for c in ["lat_deg", "lon_deg", "GE_ELV_AVG_2025", "temp_c", "log_precip"] + extra_cols:
            row[c] = float((g[c].to_numpy(float) * w).sum())
        for t, v in zip(H_EPOCHS, h_agg):
            row[f"H_{t}"] = float(v)
        out.append(row)
    return pd.DataFrame(out)


def smd(a, b) -> float:
    """Standardised mean difference (included minus excluded), pooled SD."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def kish_ess(w) -> float:
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum())


def zscore(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, float)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    return (X - X.mean(axis=0)) / sd


def block_scale(blocks: list[np.ndarray]) -> np.ndarray:
    """z-score columns then rescale every block to the same total variance (one per block)."""
    parts = []
    for b in blocks:
        z = zscore(b)
        parts.append(z / np.sqrt(z.shape[1]))
    return np.hstack(parts)


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def mutual_knn_pairs(X: np.ndarray, lat: np.ndarray, lon: np.ndarray, k: int, min_sep_km: float):
    """Mutual k-NN pairs in X, neighbours restricted to units >= min_sep_km apart. S/C only."""
    n = len(X)
    d = cdist(X, X)
    geo = haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    d = np.where(geo < min_sep_km, np.inf, d)
    np.fill_diagonal(d, np.inf)
    nn = np.argsort(d, axis=1)[:, :k]
    ok = np.take_along_axis(d, nn, axis=1) < np.inf
    nbr = [set(nn[i][ok[i]].tolist()) for i in range(n)]
    pairs = sorted({(min(i, j), max(i, j)) for i in range(n) for j in nbr[i] if i in nbr[j]})
    return pairs, d


def tile_ids(lat, lon, size_deg: float = 10.0) -> np.ndarray:
    return (np.floor((np.asarray(lat) + 90) / size_deg).astype(int) * 1000
            + np.floor((np.asarray(lon) + 180) / size_deg).astype(int))


def balanced_group_folds(groups: np.ndarray, k: int):
    """Greedy largest-first assignment of groups to k folds (deterministic)."""
    s = pd.Series(groups).value_counts()
    s = s.sort_values(ascending=False, kind="mergesort")
    load = np.zeros(k)
    assign = {}
    for g, c in s.items():
        f = int(np.argmin(load))
        assign[g] = f
        load[f] += c
    return np.array([assign[g] for g in groups]), load
