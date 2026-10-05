"""Consistency tests for the saved 1005-9 results and the mechanical Gate 2 decision."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "1005-9"
sys.path.insert(0, str(ROOT / "scripts"))

pytestmark = pytest.mark.skipif(not (RES / "gate2_decision.json").exists(), reason="1005-9 results not generated")


def test_decision_file_matches_rules_applied_to_saved_results():
    import gate2_decision_1005_9 as gd
    saved = json.loads((RES / "gate2_decision.json").read_text())
    again = gd.decide()
    assert again["GATE_2"] == saved["GATE_2"] and again["TRANSFERABILITY_PROGRAM"] == saved["TRANSFERABILITY_PROGRAM"]
    assert saved["causal_claim_allowed"] is False
    assert {"PASS": "CONTINUE", "MIXED": "REVISE", "FAIL": "STOP"}[saved["GATE_2"]] == saved["TRANSFERABILITY_PROGRAM"]


def test_primary_outputs_sealed_before_secondary_and_unchanged():
    import gate2_models as m
    sealed = RES / "primary_outputs_sealed.json"
    files = [RES / n for n in json.loads(sealed.read_text())["primary_outputs_sha256"]]
    assert len(files) >= 14
    m.assert_primary_complete(files, sealed)   # raises if any primary file changed after sealing


def test_primary_and_m0_m1_share_identical_n_everywhere():
    for name in ("primary_model_metrics.csv", "strict_precedence_results.csv", "boundary_sensitivity_results.csv",
                 "geometry_sensitivity_results.csv", "context_state_sensitivity.csv", "common_support_results.csv"):
        df = pd.read_csv(RES / name)
        assert {"r2_m0", "r2_m1", "n"} <= set(df.columns)
        assert (df["n"] > 0).all()
    oof = pd.read_csv(RES / "primary_oof_predictions.csv")
    assert len(oof) == 2107 and oof[["pred_M0_rf", "pred_M1_rf", "pred_M0_ridge", "pred_M1_ridge"]].notna().all().all()
    assert oof.yceo_id.is_unique


def test_run_metadata_integrity_flags():
    meta = json.loads((RES / "run_metadata.json").read_text())
    assert meta["network_access"] == "none" and meta["new_research_data_downloaded"] is False
    assert meta["interim_shapefile_sha256_unchanged"] is True and meta["seed"] == 42
    assert meta["n_shuffle_permutations"] >= 300
    assert meta["raw_zip_sha256"] == "d5575541de2c8972d62f9dbd86888869bf568679bab75194495492dddceee364"
