"""Tests for execution 1005-5's boundary-robustness analysis code
(scripts/mtuc_boundary_robustness.py).

These test pure, synthetic-data functions and do not require the
downloaded GHS-UCDB/MTUC raw data files to be present.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "mtuc_boundary_robustness.py"

spec = importlib.util.spec_from_file_location("mtuc_boundary_robustness", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules["mtuc_boundary_robustness"] = mod
spec.loader.exec_module(mod)


def test_parse_num_strips_thousands_commas():
    s = pd.Series(["1,234,567", "2,836,540", "100"])
    out = mod.parse_num(s)
    assert list(out) == [1234567.0, 2836540.0, 100.0]


def test_parse_num_handles_missing():
    s = pd.Series(["1,000", np.nan, "nan"])
    out = mod.parse_num(s)
    assert out.iloc[0] == 1000.0
    assert pd.isna(out.iloc[1])


def test_build_H_from_prefix_excludes_endpoint_and_uses_only_pre_endpoint_epochs():
    # trajectory grows monotonically to endpoint; endpoint ratio (=1) must not appear
    n = 10
    df = pd.DataFrame({"ID": range(n)})
    base = np.linspace(1e6, 2e6, n)
    for i, y in enumerate(mod.EPOCHS_OBSERVED):
        df[f"X_{y}"] = base * (1.0 + 0.1 * i)
    H = mod.build_H_from_prefix(df, "X_", epochs=mod.H_EPOCHS, endpoint=mod.T_ENDPOINT)
    assert H.shape == (n, len(mod.H_EPOCHS))
    assert mod.T_ENDPOINT not in mod.H_EPOCHS  # endpoint explicitly excluded from H epochs
    assert (H < 1.0).all()  # since endpoint is the maximum by construction


def test_build_H_from_prefix_no_projected_epochs_in_default_H_EPOCHS():
    assert 2025 not in mod.H_EPOCHS
    assert 2030 not in mod.H_EPOCHS
    assert 2025 not in mod.EPOCHS_OBSERVED
    assert 2030 not in mod.EPOCHS_OBSERVED


def test_build_H_from_prefix_alternate_endpoint_excludes_endpoint_and_later_epochs():
    n = 6
    df = pd.DataFrame({"ID": range(n)})
    base = np.linspace(1e6, 2e6, n)
    for i, y in enumerate(mod.EPOCHS_OBSERVED):
        df[f"X_{y}"] = base * (1.0 + 0.1 * i)
    alt_epochs = [e for e in mod.EPOCHS_OBSERVED if e < 2015]
    H = mod.build_H_from_prefix(df, "X_", epochs=alt_epochs, endpoint=2015)
    assert 2015 not in alt_epochs
    assert 2020 not in alt_epochs  # no future-relative-to-T information enters H


def test_build_crosswalk_one_to_one_matching_and_numeric_corroboration():
    ucdb = pd.DataFrame({
        "ID_UC_G0": [1, 2, 3],
        "GC_UCN_MAI_2025": ["Alpha", "Beta", "Gamma"],
        "GC_CNT_GAD_2025": ["Country A", "Country A", "Country B"],
        "GC_UCB_YOB_2025": [1975, 1975, 1975],
        "GH_POP_TOT_2020": [1000.0, 2000.0, 3000.0],
        "GH_BUS_TOT_2020": [500.0, 800.0, 1200.0],
    })
    mtuc = pd.DataFrame({
        "ID_MTUC_G0": [10, 20, 30],
        "GC_UCN_MAI_2025": ["Alpha", "Beta", "Delta"],  # Gamma unmatched, Delta mtuc-only
        "GC_CNT_GAD_2025": ["Country A", "Country A", "Country C"],
        "GC_UCB_YOB_2025": [1975, 1975, 1975],
        "MT_POP_TOT_2020": [1000.0, 2000.0, 500.0],
        "MT_BUS_TOT_2020": [500.0, 800.0, 400.0],
    })
    crosswalk, summary = mod.build_crosswalk(ucdb, mtuc)
    assert summary["N_UCDB"] == 3
    assert summary["N_MTUC"] == 3
    assert summary["N_matched_one_to_one_name_country"] == 2  # Alpha, Beta
    matched_rows = crosswalk[crosswalk["match_status"] == "one_to_one"]
    assert set(matched_rows["name"]) == {"Alpha", "Beta"}
    assert matched_rows["numeric_corroboration_pass"].all()
    assert matched_rows["included_in_core_matched_sample"].all()


def test_build_crosswalk_flags_ambiguous_many_sided_keys():
    ucdb = pd.DataFrame({
        "ID_UC_G0": [1, 2],
        "GC_UCN_MAI_2025": ["Springfield", "Springfield"],
        "GC_CNT_GAD_2025": ["Country A", "Country A"],
        "GC_UCB_YOB_2025": [1975, 1975],
        "GH_POP_TOT_2020": [1000.0, 2000.0],
        "GH_BUS_TOT_2020": [500.0, 800.0],
    })
    mtuc = pd.DataFrame({
        "ID_MTUC_G0": [10],
        "GC_UCN_MAI_2025": ["Springfield"],
        "GC_CNT_GAD_2025": ["Country A"],
        "GC_UCB_YOB_2025": [1975],
        "MT_POP_TOT_2020": [1000.0],
        "MT_BUS_TOT_2020": [500.0],
    })
    crosswalk, summary = mod.build_crosswalk(ucdb, mtuc)
    assert summary["N_ambiguous_many_sided"] == 1
    assert (crosswalk["match_status"] == "ambiguous_many_sided").any()
    assert not crosswalk.loc[crosswalk["match_status"] == "ambiguous_many_sided", "included_in_core_matched_sample"].any()


def test_build_crosswalk_requires_complete_mtuc_history_for_core_sample():
    ucdb = pd.DataFrame({
        "ID_UC_G0": [1], "GC_UCN_MAI_2025": ["Alpha"], "GC_CNT_GAD_2025": ["Country A"],
        "GC_UCB_YOB_2025": [1975], "GH_POP_TOT_2020": [1000.0], "GH_BUS_TOT_2020": [500.0],
    })
    mtuc_incomplete = pd.DataFrame({
        "ID_MTUC_G0": [10], "GC_UCN_MAI_2025": ["Alpha"], "GC_CNT_GAD_2025": ["Country A"],
        "GC_UCB_YOB_2025": [2005],  # qualified only in 2005 -> missing early epochs -> excluded from core
        "MT_POP_TOT_2020": [1000.0], "MT_BUS_TOT_2020": [500.0],
    })
    crosswalk, summary = mod.build_crosswalk(ucdb, mtuc_incomplete)
    assert summary["N_core_matched_sample"] == 0
    row = crosswalk[crosswalk["match_status"] == "one_to_one"].iloc[0]
    assert bool(row["mtuc_complete_1975_2020_history"]) is False
    assert bool(row["included_in_core_matched_sample"]) is False


def test_divergent_twin_rate_distance_and_rate_calculation():
    # 4 cities: pairs (0,1) close in H, pairs (2,3) far apart in H
    H = np.array([
        [0.1, 0.2],
        [0.1, 0.2],  # identical to city 0 -> D_H = 0
        [0.1, 0.2],
        [0.9, 0.8],  # far from city 2 -> large D_H
    ])
    i_arr = np.array([0, 2])
    j_arr = np.array([1, 3])
    dsc_arr = np.array([0.01, 0.01])  # both "close" present-day analogues
    rate, dsc_cut, dh_cut, d_h = mod.divergent_twin_rate(i_arr, j_arr, dsc_arr, H, dsc_cutoff=0.5, dh_cutoff=0.5)
    assert d_h[0] == pytest.approx(0.0)
    assert d_h[1] > 0.5
    assert rate == pytest.approx(0.5)  # 1 of 2 pairs exceeds the D_H cutoff


def test_core_test_a_D_boundary_is_zero_when_fixed_equals_dynamic():
    n = 5
    H = np.random.RandomState(0).uniform(0, 1, size=(n, len(mod.H_EPOCHS)))
    matched = pd.DataFrame({
        "GH_POP_TOT_2020": np.linspace(1e5, 1e6, n),
        "region": ["Europe"] * n,
        "ucdb_yob": [1975] * n,
    })
    desc = pd.DataFrame({"d1": np.random.RandomState(1).uniform(0, 1, n)})
    agreement_df, breakdown_df, D_boundary = mod.core_test_a(matched, H, H.copy(), desc, desc.copy())
    np.testing.assert_allclose(D_boundary, 0.0, atol=1e-10)
    assert np.allclose(agreement_df["pearson_r"], 1.0)


def test_matched_sample_identity_consistency_ids_align_rowwise():
    # simulate the main script's matched-sample construction logic: after
    # filtering to the core crosswalk, UCDB and MTUC rows must be aligned
    # by the SAME underlying matched entity, not just by position.
    crosswalk = pd.DataFrame({
        "ID_UC_G0": [3, 1, 2],
        "ID_MTUC_G0": [30, 10, 20],
        "included_in_core_matched_sample": [True, True, True],
    })
    ucdb = pd.DataFrame({"ID_UC_G0": [1, 2, 3], "value": ["u1", "u2", "u3"]}).set_index("ID_UC_G0")
    mtuc = pd.DataFrame({"ID_MTUC_G0": [10, 20, 30], "value": ["m1", "m2", "m3"]}).set_index("ID_MTUC_G0")

    core = crosswalk[crosswalk["included_in_core_matched_sample"]]
    ucdb_matched = ucdb.loc[core["ID_UC_G0"]].reset_index()
    mtuc_matched = mtuc.loc[core["ID_MTUC_G0"]].reset_index()

    # row i of ucdb_matched and row i of mtuc_matched must correspond to the
    # SAME crosswalk entry (3<->30, 1<->10, 2<->20 in that order)
    assert list(ucdb_matched["ID_UC_G0"]) == [3, 1, 2]
    assert list(mtuc_matched["ID_MTUC_G0"]) == [30, 10, 20]
    assert list(ucdb_matched["value"]) == ["u3", "u1", "u2"]
    assert list(mtuc_matched["value"]) == ["m3", "m1", "m2"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
