"""Tests for execution 1005-4's Gate 1 pilot analysis code.

These test pure, synthetic-data functions from scripts/ucdb_gate1_pilot.py
(trajectory normalization, mojibake fix, region mapping, QC logic). They
do not require the downloaded GHS-UCDB raw data files to be present.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "ucdb_gate1_pilot.py"

spec = importlib.util.spec_from_file_location("ucdb_gate1_pilot", SCRIPT_PATH)
pilot = importlib.util.module_from_spec(spec)
sys.modules["ucdb_gate1_pilot"] = pilot
spec.loader.exec_module(pilot)


def _make_synthetic_df(n=20, seed=0):
    rng = np.random.RandomState(seed)
    data = {"ID_UC_G0": np.arange(n)}
    base = rng.uniform(1e6, 1e7, size=n)
    for i, y in enumerate(pilot.EPOCHS_OBSERVED):
        growth = 1.0 + 0.05 * i + rng.uniform(-0.01, 0.01, size=n)
        data[f"GH_BUS_TOT_{y}"] = base * growth
        data[f"GH_POP_TOT_{y}"] = base * growth * 10
        data[f"GH_BUV_TOT_{y}"] = base * growth * 20
    data["GC_UCN_MAI_2025"] = [f"City{i}" for i in range(n)]
    data["GC_CNT_GAD_2025"] = ["France"] * n
    data["GC_UCB_YOB_2025"] = [1975] * n
    data["GC_UCB_YOD_2025"] = [2030] * n
    data["lat_deg"] = rng.uniform(-60, 60, size=n)
    data["lon_deg"] = rng.uniform(-180, 180, size=n)
    data["GE_ELV_AVG_2025"] = rng.uniform(0, 1000, size=n)
    data["region"] = ["Europe"] * n
    return pd.DataFrame(data)


def test_fix_mojibake_roundtrip():
    original = "México"
    corrupted = original.encode("utf-8").decode("latin-1")
    assert pilot.fix_mojibake(corrupted) == original


def test_fix_mojibake_passthrough_on_clean_text():
    assert pilot.fix_mojibake("Tokyo") == "Tokyo"


def test_country_to_region_covers_known_countries():
    for c in ["France", "China", "Brazil", "Nigeria", "Australia", "United States"]:
        assert c in pilot.COUNTRY_TO_REGION


def test_build_H_excludes_endpoint_and_normalizes():
    df = _make_synthetic_df()
    H, descriptors = pilot.build_H(df)
    assert H.shape == (len(df), len(pilot.H_EPOCHS))
    # every trajectory value should be < 1 since built-up grows monotonically to the endpoint
    assert (H < 1.0).all()
    assert (H > 0.0).all()
    assert set(descriptors.columns) >= {
        "ID_UC_G0", "early_developed_fraction_1990", "mid_period_fraction_2000",
        "recent_expansion_fraction_since_2000", "weighted_development_timing",
    }


def test_build_S_nesting_and_density_dependency():
    df = _make_synthetic_df()
    S = pilot.build_S(df)
    assert S["S1"].shape[1] == 2
    assert S["S2"].shape[1] == 3
    assert S["S3"].shape[1] == 4
    # S2's third column (density) must equal pop/built-up-area exactly (documented dependency)
    density = S["S1"][:, 0] / S["S1"][:, 1]
    np.testing.assert_allclose(S["S2"][:, 2], density)


def test_build_C_shape():
    df = _make_synthetic_df()
    C = pilot.build_C(df)
    assert C.shape == (len(df), 3)


def test_run_qc_flags_no_missing_or_negative_in_synthetic_data():
    df = _make_synthetic_df()
    qc = pilot.run_qc(df)
    assert qc["missing_any_bus"].sum() == 0
    assert qc["negative_or_invalid"].sum() == 0
    assert qc["duplicated_id"].sum() == 0


def test_run_qc_detects_engineered_extreme_jump():
    df = _make_synthetic_df()
    # inject an extreme jump: triple the 2020 value relative to 2015
    df.loc[0, "GH_BUS_TOT_2020"] = df.loc[0, "GH_BUS_TOT_2015"] * 5
    qc = pilot.run_qc(df)
    assert bool(qc.loc[0, "extreme_jump"]) is True


def test_build_sample_excludes_post_endpoint_qualifiers():
    df = _make_synthetic_df()
    df.loc[0, "GC_UCB_YOB_2025"] = 2025  # qualifies after T_ENDPOINT
    qc = pilot.run_qc(df)
    sample, summary = pilot.build_sample(df, qc)
    assert summary["final_n"] == len(df) - 1
    assert 0 not in sample["ID_UC_G0"].values


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
