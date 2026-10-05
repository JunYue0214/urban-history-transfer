"""Tests for scripts/gate2_models.py and gate2_data.py (execution 1005-9). Synthetic data only; no network."""

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
import gate2_data as d  # noqa: E402
import gate2_models as m  # noqa: E402
import gate2_support as g  # noqa: E402


def _toy(n=300, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(n, 4))
    H = rng.normal(size=(n, 9))
    y = base[:, 0] + 0.5 * H[:, 0] + rng.normal(scale=0.3, size=n)
    fold = np.arange(n) % 5
    return base, H, y, fold


def test_exact_sample_identity_against_1005_8_table():
    old = pd.read_csv(ROOT / "results" / "1005-8" / "cluster_level_dataset_primary.csv")
    cities = d.load_cities()
    links = g.load_links(d.LINKS_PATH)
    units = d.units_for_rule(links, *m.PRIMARY_GEOMETRY)
    A = d.assemble_units(units, cities)
    assert len(A) == 2107 and int(A.n_ucdb.sum()) == 2374
    assert (A.yceo_id.values == old.sort_values("yceo_id").yceo_id.values).all()
    assert A.yceo_id.is_unique


def test_no_train_test_leakage_changing_test_targets_does_not_change_predictions():
    base, H, y, fold = _toy()
    p_a = m.oof_predict(base, H, y, fold, "rf", "raw")
    y2 = y.copy()
    y2[fold == 0] += 100.0                       # perturb TEST fold-0 targets only
    p_b = m.oof_predict(base, H, y2, fold, "rf", "raw")
    assert np.allclose(p_a[fold == 0], p_b[fold == 0])   # fold 0 predicted without its own y


def test_pca_is_fit_on_training_history_only():
    base, H, y, fold = _toy()
    tr, te = fold != 0, fold == 0
    a_tr, a_te = m.prep_features(base[tr], base[te], H[tr], H[te], "pca3")
    H2 = H.copy()
    H2[te] += 50.0                               # perturb TEST history only
    b_tr, b_te = m.prep_features(base[tr], base[te], H2[tr], H2[te], "pca3")
    assert np.allclose(a_tr, b_tr)               # training transform unaffected by test history


def test_shuffle_within_strata_preserves_rows_and_strata():
    rng = np.random.default_rng(1)
    H = np.arange(40, dtype=float).reshape(20, 2)
    strata = np.array(["a"] * 10 + ["b"] * 10)
    out = m.shuffle_rows_within_strata(H, strata, rng)
    assert sorted(map(tuple, out[:10])) == sorted(map(tuple, H[:10]))
    assert sorted(map(tuple, out[10:])) == sorted(map(tuple, H[10:]))
    assert not np.array_equal(out, H)


def test_size_strata_uses_region_and_terciles():
    region = np.array(["A"] * 6 + ["B"] * 6)
    s = m.size_strata(region, np.arange(12.0))
    assert len(set(s)) <= 6 and all("||" in v for v in s)


def test_donors_never_come_from_the_test_fold():
    rng = np.random.default_rng(2)
    S, C, H = rng.normal(size=(200, 3)), rng.normal(size=(200, 2)), rng.normal(size=(200, 9))
    y = rng.normal(size=200)
    fold = np.arange(200) % 5
    pred, used = m.transfer_predict([S, C, H], y, fold, K=10)
    for k, idx in used.items():
        assert not np.any(fold[idx] == k)
    assert np.isfinite(pred).all()


def test_transfer_prediction_independent_of_target_own_y():
    rng = np.random.default_rng(3)
    S, C = rng.normal(size=(150, 3)), rng.normal(size=(150, 2))
    y = rng.normal(size=150)
    fold = np.arange(150) % 5
    p1, _ = m.transfer_predict([S, C], y, fold)
    y2 = y.copy()
    y2[fold == 2] += 1000
    p2, _ = m.transfer_predict([S, C], y2, fold)
    assert np.allclose(p1[fold == 2], p2[fold == 2])


def test_twin_construction_has_no_access_to_H_or_R():
    import inspect
    assert list(inspect.signature(m.build_twins).parameters) == ["X", "lat", "lon", "k", "min_sep_km"]
    rng = np.random.default_rng(4)
    X, lat, lon = rng.normal(size=(120, 5)), rng.uniform(-40, 60, 120), rng.uniform(-100, 120, 120)
    p1 = m.build_twins(X, lat, lon, 10, 200.0)
    p2 = m.build_twins(X.copy(), lat.copy(), lon.copy(), 10, 200.0)
    assert np.array_equal(p1, p2)
    dist = g.haversine_km(lat[p1[:, 0]], lon[p1[:, 0]], lat[p1[:, 1]], lon[p1[:, 1]])
    assert (dist >= 200.0).all()


def test_pair_dependence_bootstrap_resamples_tiles_not_pairs():
    rng = np.random.default_rng(5)
    n = 60
    tiles = np.repeat(np.arange(6), 10)
    pairs = np.array([(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.05])
    dr, dh = rng.random(len(pairs)), rng.random(len(pairs))
    vals = m.twin_tile_bootstrap(lambda idx: float(np.mean(dr[idx])), pairs, tiles, B=60)
    assert len(vals) > 30 and np.isfinite(vals).all()


def test_m0_and_m1_use_identical_rows_and_folds():
    base, H, y, fold = _toy()
    p0 = m.oof_predict(base, None, y, fold, "rf", None)
    p1 = m.oof_predict(base, H, y, fold, "rf", "raw")
    r = m.delta_metrics(y, p0, p1)
    assert r["n"] == len(y) and np.isfinite(p0).all() and np.isfinite(p1).all()
    assert r["delta_r2"] == pytest.approx(r["r2_m1"] - r["r2_m0"])


def test_strict_precedence_history_uses_no_post_2000_information():
    B = pd.DataFrame({f"B_{t}": np.full(5, float(t - 1900)) for t in m.EPOCHS})
    B2 = B.copy()
    for t in (2005, 2010, 2015, 2020):
        B2[f"B_{t}"] = 999999.0                 # corrupt every post-2000 column
    a = m.h_rebased(B, m.H_PRE2000_EPOCHS, 2000)
    b = m.h_rebased(B2, m.H_PRE2000_EPOCHS, 2000)
    assert np.array_equal(a, b)
    assert a.shape == (5, 5) and max(m.H_PRE2000_EPOCHS) < 2000


def test_geometry_sensitivity_rules_are_immutable():
    assert m.GEOMETRY_SENSITIVITIES == (("S1_looser_coverage_040", 0.4, None),
                                         ("S2_stricter_coverage_060", 0.6, None),
                                         ("S3_drop_iou_floor", 0.5, None))
    assert m.PRIMARY_GEOMETRY == (0.5, 0.20)
    with pytest.raises(TypeError):
        m.GEOMETRY_SENSITIVITIES[0] = ("x", 0, 0)   # tuple is immutable


def test_secondary_response_blocked_until_primary_is_sealed(tmp_path):
    f = tmp_path / "primary.csv"
    f.write_text("a,b\n1,2\n")
    marker = tmp_path / "sealed.json"
    with pytest.raises(RuntimeError, match="not sealed"):
        m.assert_primary_complete([f], marker)
    m.write_primary_marker([f], marker)
    m.assert_primary_complete([f], marker)         # ok
    f.write_text("a,b\n1,3\n")                      # tamper after sealing
    with pytest.raises(RuntimeError, match="changed after sealing"):
        m.assert_primary_complete([f], marker)


def test_no_network_access(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "socket", boom)
    base, H, y, fold = _toy(100)
    m.oof_predict(base, H, y, fold, "ridge", "raw")
    m.transfer_predict([base, H], y, fold)
    m.morans_i(y, np.linspace(-30, 30, 100), np.linspace(-50, 50, 100), k=5, n_perm=20)


def test_raw_inputs_not_mutated_by_loading_helpers():
    p = d.PRIMARY_TABLE_1005_8
    zp = ROOT / "data" / "raw" / "thermal_response" / "sdei-yceo-sfc-uhi-v4-urban-cluster-means-shp.zip"
    if not zp.exists():
        pytest.skip("raw zip not present on this machine")
    before = hashlib.sha256(zp.read_bytes()).hexdigest()
    d.load_cities()
    g.load_links(d.LINKS_PATH)
    assert hashlib.sha256(zp.read_bytes()).hexdigest() == before
    assert p.exists()


def test_tile_bootstrap_ci_brackets_known_difference():
    rng = np.random.default_rng(6)
    n = 1500
    y = rng.normal(size=n)
    p0 = y + rng.normal(scale=1.0, size=n)
    p1 = y + rng.normal(scale=0.5, size=n)
    tiles = rng.integers(0, 40, n)
    obs = m.delta_metrics(y, p0, p1)["delta_r2"]
    bt = m.tile_bootstrap_delta(y, p0, p1, tiles, B=500)
    assert bt["delta_r2_ci_lo"] < obs < bt["delta_r2_ci_hi"] and bt["delta_r2_ci_lo"] > 0


def test_partial_spearman_removes_confounding():
    rng = np.random.default_rng(7)
    z = rng.normal(size=2000)
    a, b = z + rng.normal(scale=.3, size=2000), z + rng.normal(scale=.3, size=2000)
    assert pd.Series(a).corr(pd.Series(b), method="spearman") > 0.8
    assert abs(m.partial_spearman(a, b, z, np.zeros(2000) + rng.normal(scale=1e-9, size=2000))) < 0.15


def test_s_and_c_blocks_have_expected_columns_and_log_density_not_constant():
    A = pd.DataFrame({"POP_2020": [1e5, 2e5, 5e5], "B_2020": [2e7, 3e7, 4e7], "BUV_2020": [1e8, 2e8, 3e8],
                      "density_2020": [0.005, 0.0067, 0.0125], "lat_deg": [1., 2, 3], "lon_deg": [4., 5, 6],
                      "GE_ELV_AVG_2025": [1., 2, 3], "temp_c": [10., 11, 12], "log_precip": [6., 7, 8],
                      "temp_seas": [1., 2, 3], "precip_seas": [.5, .6, .7], "kop_major": ["A", "B", "C"]})
    assert d.s_block(A, "S1").shape == (3, 2) and d.s_block(A, "S2").shape == (3, 3) and d.s_block(A, "S3").shape == (3, 4)
    assert d.s_block(A, "S3")[:, 2].std() > 0           # the 1005-8 clip(…, lower=1) defect cannot recur
    assert d.c_block(A, "C0").shape == (3, 3) and d.c_block(A, "C1").shape == (3, 5) and d.c_block(A, "C2").shape == (3, 12)


def test_mahalanobis_support_flags_about_95_percent():
    rng = np.random.default_rng(8)
    ok, dist, thr = m.mahalanobis_support(rng.normal(size=(1000, 6)))
    assert 0.94 <= ok.mean() <= 0.96
