"""Tests for 1006-1: frozen negative result, pivot design integrity, and the mock-only aggregation helper."""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
R6, R9 = ROOT / "results" / "1006-1", ROOT / "results" / "1005-9"
sys.path.insert(0, str(ROOT / "scripts"))

needs_results = pytest.mark.skipif(not R6.exists(), reason="1006-1 results not generated")


@needs_results
def test_freeze_numbers_match_the_1005_9_files():
    txt = (R6 / "gate2_negative_result_freeze.md").read_text(encoding="utf-8")
    prim = pd.read_csv(R9 / "primary_model_metrics.csv").set_index("spec").loc["PRIMARY_rf_S3C1_rawH"]
    dec = json.loads((R9 / "gate2_decision.json").read_text())
    for val in (f"{prim.r2_m0:.4f}", f"{prim.r2_m1:.4f}", f"{prim.rmse_m0:.4f}", f"{prim.rmse_m1:.4f}",
                f"{prim.mae_m0:.4f}", f"{prim.mae_m1:.4f}", f"{prim.delta_r2:.4f}".replace("-", "−")):
        assert val in txt, val
    assert dec["GATE_2"] == "FAIL" and dec["TRANSFERABILITY_PROGRAM"] == "STOP"
    assert "GATE 2 = FAIL" in txt and "frozen" in txt.lower()
    assert "What the failure rules out" in txt and "What it does not rule out" in txt


@needs_results
def test_1005_9_outputs_still_sealed_and_unchanged():
    import gate2_models as m
    sealed = R9 / "primary_outputs_sealed.json"
    files = [R9 / n for n in json.loads(sealed.read_text())["primary_outputs_sha256"]]
    m.assert_primary_complete(files, sealed)


@needs_results
def test_exactly_one_primary_pivot_and_consistent_scores():
    sel = json.loads((R6 / "selected_pivot.json").read_text())
    assert sel["primary_pivot"] in {"A", "B", "C", "D"} and sel["exactly_one_primary"] is True
    assert sel["backup_pivot"] in {"A", "B", "C", "D", "NONE"} and sel["backup_pivot"] != sel["primary_pivot"]
    sc = pd.read_csv(R6 / "pivot_scoring.csv")
    assert set(sc["pivot"]) == {"A", "B", "C", "D"}
    dims = [c for c in sc.columns if c.startswith("dim_")]
    assert len(dims) == 11 and ((sc[dims] >= 1) & (sc[dims] <= 5)).all().all()
    assert (sc[dims].sum(axis=1) == sc["total"]).all()                    # totals are the sum of the dimensions
    assert sel["scores_total_of_55"] == dict(zip(sc["pivot"], sc["total"]))


@needs_results
def test_decision_labels_and_dataset_state_are_provisional():
    sel = json.loads((R6 / "selected_pivot.json").read_text())
    assert sel["pivot_design"] in {"LOCKED", "PROVISIONAL", "REJECTED"} and sel["next_empirical_gate"] in {"READY", "NOT YET", "STOP"}
    plan = (R6 / "acquisition_plan.md").read_text(encoding="utf-8")
    assert "PROPOSED" in plan and "Step 0" in plan and "nothing downloaded" in plan.lower()
    audit = pd.read_csv(R6 / "data_source_audit.csv")
    assert set(audit.status) <= {"LOCAL", "PROPOSED", "NOT FOUND", "NOT VERIFIED"}
    local = set(audit[audit.status == "LOCAL"].dataset)
    assert not any("Xiang" in d for d in local)                          # the new LST archive must not be marked local


@needs_results
def test_no_new_research_data_present():
    for d in (ROOT / "data" / "raw" / "urban_lst", ROOT / "data" / "interim" / "urban_lst"):
        assert not d.exists() or not [f for f in d.rglob("*") if f.is_file() and f.suffix.lower() in {".tif", ".zip", ".nc", ".hdf", ".csv"}]
    meta = json.loads((R6 / "run_metadata.json").read_text())
    assert meta["research_data_downloaded"] is False and meta["gate_2_artifacts_modified"] is False


@needs_results
def test_required_outputs_exist():
    for n in ("gate2_negative_result_freeze.md", "failure_diagnosis.md", "candidate_pivots.csv", "data_source_audit.csv",
              "data_volume_audit.csv", "temporal_ordering_audit.csv", "prior_art_audit.md", "pivot_scoring.csv",
              "selected_pivot.json", "next_gate_design.md", "acquisition_plan.md", "run_metadata.json"):
        assert (R6 / n).is_file() and (R6 / n).stat().st_size > 0, n


def test_downloader_cannot_transfer_by_default(tmp_path, capsys):
    import download_thermal_response as dl
    rc = dl.main(["--url", "https://zenodo.org/records/0/files/x.zip", "--dest", str(tmp_path)])
    assert rc == 2 and not list(tmp_path.iterdir())
    assert "REFUSED" in capsys.readouterr().err


def _make_raster(path, arr, nodata=-9999.0, scale=0.02, offset=0.0):
    import rasterio
    from rasterio.transform import from_origin
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
                       crs="EPSG:4326", transform=from_origin(10.0, 50.0, 0.01, 0.01), nodata=nodata) as dst:
        dst.write(arr.astype("float32"), 1)
        dst.scales, dst.offsets = (scale,), (offset,)


def test_zonal_mean_on_synthetic_raster_and_header_only_inspect(tmp_path, monkeypatch):
    import aggregate_lst_zonal as az
    from shapely.geometry import box
    arr = np.full((100, 100), 15000.0)                   # 15000 * 0.02 = 300 K
    arr[:, 50:] = 16000.0                                  # right half 320 K
    arr[10:20, 10:20] = -9999.0                            # nodata block
    f = tmp_path / "t.tif"
    _make_raster(f, arr)
    def boom(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "socket", boom)
    info = az.inspect_raster(f)
    assert info["count"] == 1 and info["nodata"] == -9999.0 and info["shape"] == [100, 100]
    polys = [("left", box(10.1, 49.1, 10.4, 49.9)), ("right", box(10.6, 49.1, 10.9, 49.9)),
             ("allnodata", box(10.11, 49.81, 10.19, 49.89)), ("outside", box(30, 30, 31, 31))]
    res = {i: (m, nv, n) for i, m, nv, n in az.zonal_mean(f, polys)}
    assert res["left"][0] == pytest.approx(300.0, abs=0.01) and res["right"][0] == pytest.approx(320.0, abs=0.01)
    assert np.isnan(res["allnodata"][0]) and res["allnodata"][1] == 0
    assert np.isnan(res["outside"][0]) and res["outside"][1] == 0


def test_aggregation_script_only_exposes_inspect():
    import aggregate_lst_zonal as az
    assert az.main(["nonexistent.tif"]) == 2
