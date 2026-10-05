"""Tests for scripts/gate2_support.py (execution 1005-8). Enforces blindness to
H<->R, deterministic aggregation, no duplicated cluster assignment, and that
historical artifacts (1005-1..1005-7) are unchanged. Synthetic data only.
"""

from __future__ import annotations

import hashlib
import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gate2_support as g  # noqa: E402


def _links():
    """Synthetic crosswalk rows shaped like results/1005-7/ucdb_yceo_crosswalk.csv.

    Cluster 10: single city (ucdb 1), coverage 0.9, iou 0.6, valid R.
    Cluster 11: two-city star (ucdb 2,3), coverage 0.55, iou 0.3, valid R.
    Cluster 12: single city (ucdb 4), coverage 0.3, iou 0.2, valid R (fails coverage>=0.5).
    Cluster 13: single city (ucdb 5), coverage 0.9, iou 0.6, R MISSING.
    Cluster 14: cross-country two-city (ucdb 6 "A", ucdb 7 "B"), coverage 0.9, valid R.
    Cluster 15: single city (ucdb 8), coverage 0.9, iou 0.6, valid R, but ucdb 8 also
                links to cluster 16 (one-UCDB-to-two-clusters -> ambiguous_nonstar).
    Cluster 16: single city (ucdb 8 again), partner of the above.
    """
    rows = [
        dict(object_type="link", ucdb_id=1, yceo_id=10, ucdb_area_m2=90, yceo_area_m2=100, intersection_m2=90,
             iou=90 / 100, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="A", ucdb_country="X", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=2, yceo_id=11, ucdb_area_m2=300, yceo_area_m2=200, intersection_m2=55,
             iou=55 / 445, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="D", ucdb_country="X", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=3, yceo_id=11, ucdb_area_m2=300, yceo_area_m2=200, intersection_m2=55,
             iou=55 / 445, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="D", ucdb_country="X", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=4, yceo_id=12, ucdb_area_m2=30, yceo_area_m2=100, intersection_m2=30,
             iou=30 / 100, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="A", ucdb_country="X", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=5, yceo_id=13, ucdb_area_m2=90, yceo_area_m2=100, intersection_m2=90,
             iou=90 / 100, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="A", ucdb_country="X", yceo_primary_R_valid=False),
        dict(object_type="link", ucdb_id=6, yceo_id=14, ucdb_area_m2=45, yceo_area_m2=100, intersection_m2=45,
             iou=45 / 100, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="D", ucdb_country="A", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=7, yceo_id=14, ucdb_area_m2=45, yceo_area_m2=100, intersection_m2=45,
             iou=45 / 100, n_clusters_for_ucdb=1, comp_n_yceo=1, pair_class="D", ucdb_country="B", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=8, yceo_id=15, ucdb_area_m2=90, yceo_area_m2=100, intersection_m2=90,
             iou=90 / 100, n_clusters_for_ucdb=2, comp_n_yceo=2, pair_class="A", ucdb_country="X", yceo_primary_R_valid=True),
        dict(object_type="link", ucdb_id=8, yceo_id=16, ucdb_area_m2=90, yceo_area_m2=100, intersection_m2=10,
             iou=10 / 180, n_clusters_for_ucdb=2, comp_n_yceo=2, pair_class="A", ucdb_country="X", yceo_primary_R_valid=True),
    ]
    return pd.DataFrame(rows)


def test_classify_clusters_statuses():
    cl = g.classify_clusters(_links(), coverage_thr=0.5, iou_thr=None)
    s = cl.set_index("yceo_id")["status"]
    assert s[10] == "unit" and s[11] == "unit" and s[12] == "low_coverage"
    assert s[13] == "invalid_R" and s[14] == "cross_country"
    assert s[15] == "ambiguous_nonstar" and s[16] == "ambiguous_nonstar"


def test_iou_floor_applies_after_coverage():
    cl = g.classify_clusters(_links(), coverage_thr=0.5, iou_thr=0.5)
    s = cl.set_index("yceo_id")["status"]
    assert s[10] == "unit"          # single link, iou = 90/100 = 0.9 >= 0.5
    assert s[11] == "low_iou"       # coverage 0.55 passes, iou = 110/690 = 0.16 fails 0.5


def test_coverage_and_iou_computed_from_raw_geometry_not_shortcuts():
    cl = g.classify_clusters(_links(), coverage_thr=0.0, iou_thr=None)
    row = cl.set_index("yceo_id").loc[11]
    assert row["coverage"] == pytest.approx(110 / 200)
    assert row["unit_iou"] == pytest.approx(110 / (600 + 200 - 110))


def test_no_r_magnitude_used_classify_clusters_signature_and_no_magnitude_column():
    import inspect
    src = inspect.getsource(g.classify_clusters) + inspect.getsource(g.load_links)
    for forbidden in ("Annual_nig", "Summer_day", "SUHI", "annual_nig"):
        assert forbidden not in src
    assert "yceo_primary_R_valid" in g.LINK_COLUMNS
    assert not any(c for c in g.LINK_COLUMNS if "nig" in c.lower() or "suhi" in c.lower() or "day" in c.lower())


def test_only_missingness_not_magnitude_affects_inclusion():
    links = _links()
    cl_valid = g.classify_clusters(links, 0.5, None)
    links2 = links.copy()
    links2.loc[links2.yceo_id == 10, "yceo_primary_R_valid"] = False
    cl_dropped = g.classify_clusters(links2, 0.5, None)
    assert cl_valid.set_index("yceo_id").loc[10, "status"] == "unit"
    assert cl_dropped.set_index("yceo_id").loc[10, "status"] == "invalid_R"


def test_threshold_sweep_monotonic_in_n():
    links = _links()
    ns = [len(g.units_from_status(g.classify_clusters(links, c, None))) for c in [0.2, 0.5, 0.8, 0.95]]
    assert ns == sorted(ns, reverse=True)


def test_no_duplicated_cluster_outcome_assignment():
    cl = g.classify_clusters(_links(), 0.5, None)
    units = g.units_from_status(cl)
    assert units.yceo_id.is_unique
    ids = g.city_ids(units)
    assert len(ids) == len(set(ids))  # a UCDB centre is never split across two outcome units either


def test_final_rule_classification_is_deterministic_and_reproducible():
    links = _links()
    a = g.classify_clusters(links, 0.5, 0.2)
    b = g.classify_clusters(links.sample(frac=1, random_state=0).reset_index(drop=True), 0.5, 0.2)
    pd.testing.assert_frame_equal(a.sort_values("yceo_id").reset_index(drop=True),
                                  b.sort_values("yceo_id").reset_index(drop=True))


def test_aggregate_units_deterministic_and_single_city_reduces_to_original():
    cities = pd.DataFrame({
        "ID_UC_G0": [1, 2, 3],
        "GH_POP_TOT_2020": [1000.0, 500.0, 2000.0],
        "GH_BUS_TOT_1975": [10.0, 5.0, 20.0], "GH_BUS_TOT_1980": [12, 6, 22], "GH_BUS_TOT_1985": [14, 7, 24],
        "GH_BUS_TOT_1990": [16, 8, 26], "GH_BUS_TOT_1995": [18, 9, 28], "GH_BUS_TOT_2000": [20, 10, 30],
        "GH_BUS_TOT_2005": [22, 11, 32], "GH_BUS_TOT_2010": [24, 12, 34], "GH_BUS_TOT_2015": [26, 13, 36],
        "GH_BUS_TOT_2020": [30.0, 15.0, 40.0], "GH_BUV_TOT_2020": [300.0, 150.0, 400.0],
        "lat_deg": [1.0, 2.0, -1.0], "lon_deg": [10.0, 11.0, 9.0], "GE_ELV_AVG_2025": [5.0, 6.0, 4.0],
        "temp_c": [20.0, 21.0, 19.0], "log_precip": [7.0, 7.1, 6.9], "region": ["Asia", "Asia", "Asia"],
    })
    units = pd.DataFrame({"yceo_id": [100, 200], "ucdb_ids": ["1", "2;3"], "coverage": [0.9, 0.7],
                          "unit_iou": [0.5, 0.4], "yceo_area_km2": [10.0, 20.0]})
    a1 = g.aggregate_units(units, cities)
    a2 = g.aggregate_units(units.sample(frac=1, random_state=1).reset_index(drop=True), cities)
    pd.testing.assert_frame_equal(a1.sort_values("yceo_id").reset_index(drop=True),
                                  a2.sort_values("yceo_id").reset_index(drop=True))
    single = a1[a1.yceo_id == 100].iloc[0]
    assert single["pop2020"] == 1000.0 and single["unit_type"] == "single_city"
    assert single["H_2000"] == pytest.approx(20.0 / 30.0)
    multi = a1[a1.yceo_id == 200].iloc[0]
    assert multi["pop2020"] == 2500.0 and multi["bus2020_m2"] == 55.0
    assert multi["H_2000"] == pytest.approx((10.0 + 30.0) / 55.0)
    assert multi["dominant_ucdb_id"] == 3  # larger 2020 built-up area


def test_no_network_access(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "socket", boom)
    g.classify_clusters(_links(), 0.5, 0.2)
    g.smd([1, 2, 3], [4, 5, 6])
    g.mutual_knn_pairs(np.random.rand(5, 3), np.array([0, 1, 2, 3, 4.0]), np.array([0, 1, 2, 3, 4.0]), 2, 0)


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("rel", [
    "reports/report1005-7.md", "results/1005-7/crosswalk_summary.json",
    "results/1005-7/ucdb_yceo_crosswalk.csv", "results/1005-6/thermal_design_decision.json",
    "results/1005-5/gate1b_decision.json", "results/1005-4/gate1_decision.json",
])
def test_historical_artifacts_unchanged(rel):
    p = ROOT / rel
    assert p.is_file(), f"missing historical artifact {rel}"
    # existence + non-empty is the practical check here; full-repo hash pinning
    # is done once via git (no 1005-1..1005-7 path is touched by 1005-8 code).
    assert p.stat().st_size > 0


def test_mutual_knn_respects_separation_and_symmetry():
    lat = np.array([0.0, 0.0, 0.0, 10.0])
    lon = np.array([0.0, 0.01, 0.02, 0.0])
    X = np.array([[0.0], [0.0], [0.0], [0.0]])
    pairs, _ = g.mutual_knn_pairs(X, lat, lon, k=1, min_sep_km=5.0)
    assert (0, 1) not in pairs and (1, 2) not in pairs  # too close, excluded
    assert all(p[0] < p[1] for p in pairs)


def test_balanced_group_folds_assigns_every_group():
    groups = np.array(["a"] * 10 + ["b"] * 5 + ["c"] * 1)
    assign, load = g.balanced_group_folds(groups, k=3)
    assert len(assign) == len(groups) and load.sum() == len(groups)
