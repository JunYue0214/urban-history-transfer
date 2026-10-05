"""Execution 1005-7: YCEO SUHI v4 validation + UCDB<->YCEO crosswalk gate.

Local-only. NO network access, NO writes to data/raw. Does not read or model
the SUHI response in any crosswalk decision: the crosswalk is built from
geometry only; response values are used only for QC after the rules are fixed.

Pure helper functions are importable and unit-tested; `main()` runs the pipeline.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_ZIP = ROOT / "data" / "raw" / "thermal_response" / "sdei-yceo-sfc-uhi-v4-urban-cluster-means-shp.zip"
INTERIM = ROOT / "data" / "interim" / "1005-7" / "yceo_suhi_v4"
RESULTS = ROOT / "results" / "1005-7"
FIGURES = ROOT / "figures" / "1005-7"
MOLL = "ESRI:54009"
REQUIRED_SHP = (".shp", ".shx", ".dbf", ".prj")
OPTIONAL_SHP = (".cpg", ".sbn", ".sbx", ".fix", ".qix", ".xml")

# ---------------------------------------------------------------- rules (fixed
# before any classification; see crosswalk_rules.json for the justification)
RULES = {
    "link_threshold_overlap_over_min_area": 0.5,
    "strict_min_iou": 0.25,  # revised from 0.5 after geometry-only inspection (median 1:1 IoU = 0.39)
    "tight_min_iou": 0.5,    # sensitivity flag only
    "strict_area_ratio_range": [0.25, 4.0],
    "dominant_min_share_of_cluster_ucdb_overlap": 0.8,
    "dominant_min_cluster_coverage": 0.5,
    "aggregate_min_cluster_coverage": 0.5,
    "max_centroid_distance_km_for_strict": 25.0,
}


# ------------------------------------------------------------------ raw file
def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def shapefile_members(names: list[str]) -> dict:
    """Detect shapefile component presence by stem (case-insensitive)."""
    low = {n.lower(): n for n in names}
    stems = sorted({n[:-4] for n in low if n.endswith(".shp")})
    out = {"stems": stems, "required_present": {}, "optional_present": {}, "complete": False}
    if not stems:
        return out
    stem = stems[0]
    out["required_present"] = {e: (stem + e) in low for e in REQUIRED_SHP}
    out["optional_present"] = {e: (stem + e) in low for e in OPTIONAL_SHP}
    out["complete"] = all(out["required_present"].values())
    return out


def inspect_zip(path: Path) -> dict:
    """Read-only integrity inspection of the raw ZIP (never modifies it)."""
    path = Path(path)
    m: dict = {"path": str(path), "exists": path.is_file()}
    if not m["exists"]:
        m["zip_valid"] = False
        return m
    st = path.stat()
    m.update(bytes=st.st_size, sha256=sha256_of(path),
             mtime_utc=datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat())
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            m["zip_valid"] = bad is None
            m["first_bad_member"] = bad
            m["members"] = [{"name": i.filename, "bytes": i.file_size,
                             "modified": "%04d-%02d-%02dT%02d:%02d:%02d" % i.date_time} for i in zf.infolist()]
            m["shapefile"] = shapefile_members(zf.namelist())
    except zipfile.BadZipFile as exc:
        m["zip_valid"] = False
        m["error"] = str(exc)
    return m


# ------------------------------------------------------- response identification
_PERIOD = {"annual": "annual", "summer": "summer", "winter": "winter"}


def classify_field(name: str) -> tuple[str, str] | None:
    """('annual'|'summer'|'winter', 'day'|'night') from an ACTUAL field name, else None."""
    m = re.fullmatch(r"(annual|summer|winter)_(day|nig|night)", name.strip().lower())
    if not m:
        return None
    return _PERIOD[m.group(1)], ("day" if m.group(2) == "day" else "night")


def identify_response_field(columns: list[str], period: str, diurnal: str) -> str:
    """Exactly one actual column for (period, diurnal) or raise."""
    hits = [c for c in columns if classify_field(c) == (period, diurnal)]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one {period}/{diurnal} field, found {hits}")
    return hits[0]


# ------------------------------------------------------------- overlap metrics
def overlap_metrics(inter: float, a_uc: float, a_y: float) -> dict:
    union = a_uc + a_y - inter
    return {
        "frac_of_ucdb": inter / a_uc if a_uc > 0 else np.nan,
        "frac_of_yceo": inter / a_y if a_y > 0 else np.nan,
        "overlap_over_min": inter / min(a_uc, a_y) if min(a_uc, a_y) > 0 else np.nan,
        "iou": inter / union if union > 0 else np.nan,
        "area_ratio_ucdb_over_yceo": a_uc / a_y if a_y > 0 else np.nan,
    }


def is_link(overlap_over_min: float, rules: dict = RULES) -> bool:
    return bool(overlap_over_min >= rules["link_threshold_overlap_over_min_area"])


def strict_pair_ok(iou: float, ratio: float, dist_km: float, rules: dict = RULES) -> bool:
    lo, hi = rules["strict_area_ratio_range"]
    return bool(iou >= rules["strict_min_iou"] and lo <= ratio <= hi
                and dist_km <= rules["max_centroid_distance_km_for_strict"])


# ----------------------------------------------------------- graph classification
def classify_links(links: pd.DataFrame, uc_country: dict, yceo_valid: dict,
                   rules: dict = RULES) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Classify the bipartite link graph (only substantive links are passed in).

    links columns: ucdb_id, yceo_id, inter_m2, a_uc, a_y, iou, area_ratio_ucdb_over_yceo,
                   centroid_dist_km, frac_of_yceo
    Returns (pair_table, ucdb_table, yceo_table); each node ends up with exactly one
    structural class. A YCEO cluster is NEVER assigned to more than one 'usable' UCDB
    city unless explicitly flagged as an aggregate unit.
    """
    links = links.copy()
    nu = links.groupby("yceo_id")["ucdb_id"].nunique()
    ny = links.groupby("ucdb_id")["yceo_id"].nunique()
    links["n_ucdb_in_cluster"] = links["yceo_id"].map(nu)
    links["n_clusters_for_ucdb"] = links["ucdb_id"].map(ny)
    tot = links.groupby("yceo_id")["inter_m2"].transform("sum")
    links["share_of_cluster_ucdb_overlap"] = links["inter_m2"] / tot
    links["cluster_ucdb_coverage"] = tot / links["a_y"]

    # connected components of the bipartite graph
    parent: dict = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, y in zip(links["ucdb_id"], links["yceo_id"]):
        parent[find(("u", u))] = find(("y", y))
    links["component"] = [find(("u", u)) for u in links["ucdb_id"]]
    comp_nu = links.groupby("component")["ucdb_id"].nunique()
    comp_ny = links.groupby("component")["yceo_id"].nunique()
    links["comp_n_ucdb"] = links["component"].map(comp_nu)
    links["comp_n_yceo"] = links["component"].map(comp_ny)

    pair_cls, u_cls, y_cls = [], {}, {}
    countries = links.groupby("yceo_id")["ucdb_id"].apply(lambda s: {uc_country.get(u) for u in s})
    for r in links.itertuples():
        cn, cy = r.comp_n_ucdb, r.comp_n_yceo
        if cn == 1 and cy == 1:
            ok = strict_pair_ok(r.iou, r.area_ratio_ucdb_over_yceo, r.centroid_dist_km, rules)
            cls = "A_strict_1to1" if ok else "H_footprint_mismatch_1to1"
        elif cy == 1 and cn >= 2:
            if len(countries[r.yceo_id] - {None}) > 1:
                cls = "E_cross_country_cluster"
            else:
                is_top = r.share_of_cluster_ucdb_overlap >= rules["dominant_min_share_of_cluster_ucdb_overlap"]
                if is_top and r.frac_of_yceo >= rules["dominant_min_cluster_coverage"]:
                    cls = "B_dominant_1to1"
                elif is_top:
                    cls = "D_many_to_one_ambiguous"
                else:
                    top_exists = (links[links.yceo_id == r.yceo_id]["share_of_cluster_ucdb_overlap"]
                                  >= rules["dominant_min_share_of_cluster_ucdb_overlap"]).any()
                    cls = "D_minor_of_dominant" if top_exists else "D_many_to_one_ambiguous"
        elif cn == 1 and cy >= 2:
            cls = "C_ambiguous_one_to_many"
        else:
            cls = "J_complex_many_to_many"
        pair_cls.append(cls)
    links["pair_class"] = pair_cls

    # node-level: UCDB node takes its (unique per component logic) class; if a UCDB node
    # has several pairs they share one component and one class family (C or J).
    for u, g in links.groupby("ucdb_id"):
        u_cls[u] = g["pair_class"].iloc[0] if g["pair_class"].nunique() == 1 else \
            sorted(g["pair_class"].unique())[0]
    for y, g in links.groupby("yceo_id"):
        classes = set(g["pair_class"])
        if "B_dominant_1to1" in classes:
            y_cls[y] = "B_dominant_1to1"
        elif classes == {"D_minor_of_dominant"}:
            y_cls[y] = "D_many_to_one_ambiguous"
        else:
            y_cls[y] = sorted(classes)[0]
    for y in list(y_cls):
        if not yceo_valid.get(y, False):
            y_cls[y] = "G_response_missing(" + y_cls[y] + ")"
    ut = pd.DataFrame({"ucdb_id": list(u_cls), "structural_class": list(u_cls.values())})
    yt = pd.DataFrame({"yceo_id": list(y_cls), "structural_class": list(y_cls.values())})
    return links, ut, yt


def aggregate_cluster_units(links: pd.DataFrame, yceo_valid: dict, in_sample: set,
                            rules: dict = RULES) -> pd.DataFrame:
    """One row per usable YCEO cluster. A cluster is a usable unit iff it is a star
    (all its UCDB centres link only to it), single-country, has valid response, all its
    linked UCDB centres are in the primary sample and the UCDB centres cover >=
    `aggregate_min_cluster_coverage` of the cluster. Each cluster appears exactly once
    (no duplication of one response across several units)."""
    rows = []
    for y, g in links.groupby("yceo_id"):
        if not yceo_valid.get(y, False):
            continue
        if (g["comp_n_yceo"] != 1).any() or (g["n_clusters_for_ucdb"] != 1).any():
            continue
        if (g["pair_class"] == "E_cross_country_cluster").any():
            continue
        if not set(g["ucdb_id"]).issubset(in_sample):
            continue
        cov = g["inter_m2"].sum() / g["a_y"].iloc[0]
        if cov < rules["aggregate_min_cluster_coverage"]:
            continue
        rows.append({"yceo_id": y, "n_ucdb": int(g["ucdb_id"].nunique()),
                     "ucdb_ids": ";".join(map(str, sorted(g["ucdb_id"]))),
                     "ucdb_coverage_of_cluster": float(cov),
                     "unit_type": "single_city" if g["ucdb_id"].nunique() == 1 else "multi_city_aggregate"})
    return pd.DataFrame(rows)


def smd(a: np.ndarray, b: np.ndarray) -> float:
    """Standardised mean difference (matched minus unmatched), pooled SD."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def summarize_response(x: pd.Series) -> dict:
    v = x.dropna()
    q = v.quantile([.01, .05, .5, .95, .99])
    return {"valid_n": int(v.size), "missing_n": int(x.isna().sum()), "min": float(v.min()),
            "p01": float(q[.01]), "p05": float(q[.05]), "median": float(q[.5]), "mean": float(v.mean()),
            "p95": float(q[.95]), "p99": float(q[.99]), "max": float(v.max()),
            "n_lt0": int((v < 0).sum()), "n_eq0": int((v == 0).sum()), "n_gt0": int((v > 0).sum())}


def main() -> int:  # pragma: no cover - exercised by running the script
    from run_1005_7_pipeline import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
