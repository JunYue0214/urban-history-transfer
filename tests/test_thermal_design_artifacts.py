"""Consistency tests for the 1005-6 design-lock artifacts (no network, no research data)."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("thermal_design_lock", ROOT / "scripts" / "thermal_design_lock.py")
tdl = importlib.util.module_from_spec(spec)
sys.modules["thermal_design_lock"] = tdl
spec.loader.exec_module(tdl)

REQUIRED = [
    "thermal_candidate_audit.csv", "thermal_source_audit.csv", "thermal_design_decision.json",
    "gate2_preregistration.md", "crosswalk_design.md", "validity_threats.csv",
    "data_manifest_template.csv", "download_plan.md", "run_metadata.json",
]


def _rows(p: Path):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_build_writes_all_generated_artifacts(tmp_path):
    tdl.build(tmp_path)
    for name in ["thermal_candidate_audit.csv", "thermal_source_audit.csv", "thermal_design_decision.json",
                 "validity_threats.csv", "data_manifest_template.csv", "run_metadata.json"]:
        assert (tmp_path / name).is_file()


def test_committed_results_directory_is_complete():
    for name in REQUIRED:
        assert (ROOT / "results" / "1005-6" / name).is_file(), name


def test_exactly_one_primary_and_one_secondary_outcome(tmp_path):
    tdl.build(tmp_path)
    roles = [r["role"] for r in _rows(tmp_path / "thermal_candidate_audit.csv")]
    assert roles.count("PRIMARY") == 1 and roles.count("SECONDARY") == 1


def test_all_prompt_candidates_audited(tmp_path):
    tdl.build(tmp_path)
    assert [r["id"] for r in _rows(tmp_path / "thermal_candidate_audit.csv")] == list("ABCDEFGHIJ")


def test_decision_is_provisional_and_no_download_authorized(tmp_path):
    tdl.build(tmp_path)
    d = json.loads((tmp_path / "thermal_design_decision.json").read_text(encoding="utf-8"))
    assert d["THERMAL_DESIGN"] in {"LOCKED", "PROVISIONAL", "REJECTED"}
    assert d["THERMAL_DESIGN"] == "PROVISIONAL" and d["why_not_LOCKED"]
    assert d["claude_authorized_download"] is False and d["global_raster_required"] is False
    assert d["alternate_reference_dataset"]["is_same_dataset_as_primary"] is False


def test_run_metadata_records_no_research_download(tmp_path):
    meta = tdl.build(tmp_path)
    assert meta["new_research_data_downloaded"] is False
    assert meta["real_research_data_network_transfers_by_claude"] == 0


def test_threats_ranked_contiguously_and_sources_flag_unresolved(tmp_path):
    tdl.build(tmp_path)
    ranks = [int(r["rank"]) for r in _rows(tmp_path / "validity_threats.csv")]
    assert ranks == list(range(1, len(ranks) + 1))
    src = {r["source_id"]: r for r in _rows(tmp_path / "thermal_source_audit.csv")}
    assert src["S1"]["unresolved"] and src["S3"]["unresolved"]
    assert "DIFFERENT" in src["S3"]["same_dataset_as"]


def test_manifest_template_has_no_invented_hashes(tmp_path):
    tdl.build(tmp_path)
    for r in _rows(tmp_path / "data_manifest_template.csv"):
        assert r["expected_sha256"].startswith("<") and not r["observed_sha256"]


def test_downloader_dataset_keys_match_decision(tmp_path):
    spec2 = importlib.util.spec_from_file_location("dl_for_check", ROOT / "scripts" / "download_thermal_response.py")
    dl = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(dl)
    d = tdl.DECISION
    assert dl.CANDIDATE_DATASETS["yceo_suhi_v4"]["doi"] == d["primary_dataset"]["doi"]
    assert dl.CANDIDATE_DATASETS["yang2024_uhii"]["doi"] == d["alternate_reference_dataset"]["doi"]
