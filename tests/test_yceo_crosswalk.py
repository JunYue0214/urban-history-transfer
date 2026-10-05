"""Tests for scripts/yceo_crosswalk.py (1005-7). Synthetic data only; no network."""

from __future__ import annotations

import socket
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import box
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import yceo_crosswalk as xw  # noqa: E402


def _zip(path: Path, names: list[str], corrupt: bool = False) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        for n in names:
            zf.writestr(n, b"x" * 50)
    if corrupt:
        b = bytearray(path.read_bytes())
        b[40] ^= 0xFF  # flip a byte inside the first member's data
        path.write_bytes(bytes(b))
    return path


def test_zip_valid_and_members_detected(tmp_path):
    z = _zip(tmp_path / "a.zip", ["A.shp", "A.shx", "A.dbf", "A.prj", "A.cpg", "doc.pdf"])
    m = xw.inspect_zip(z)
    assert m["zip_valid"] and m["shapefile"]["complete"]
    assert m["shapefile"]["optional_present"][".cpg"] and not m["shapefile"]["optional_present"][".sbn"]
    assert m["sha256"] == xw.sha256_of(z) and m["bytes"] == z.stat().st_size


def test_zip_missing_component_and_corrupt_and_nonzip(tmp_path):
    m = xw.inspect_zip(_zip(tmp_path / "b.zip", ["A.shp", "A.dbf", "A.shx"]))
    assert not m["shapefile"]["complete"] and not m["shapefile"]["required_present"][".prj"]
    assert not xw.inspect_zip(_zip(tmp_path / "c.zip", ["A.shp"], corrupt=True))["zip_valid"]
    bad = tmp_path / "d.zip"
    bad.write_bytes(b"not a zip")
    assert not xw.inspect_zip(bad)["zip_valid"]
    assert not xw.inspect_zip(tmp_path / "missing.zip")["zip_valid"]


def test_raw_zip_immutable_and_no_network(tmp_path, monkeypatch):
    z = _zip(tmp_path / "raw.zip", ["A.shp", "A.shx", "A.dbf", "A.prj"])
    before = (xw.sha256_of(z), z.stat().st_mtime_ns, z.stat().st_size)

    def boom(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", boom)
    xw.inspect_zip(z)
    assert (xw.sha256_of(z), z.stat().st_mtime_ns, z.stat().st_size) == before


def test_crs_transformation_equal_area():
    to_moll = Transformer.from_crs("EPSG:4326", xw.MOLL, always_xy=True).transform
    eq = transform(to_moll, box(10, 0, 11, 1)).area / 1e6
    hi = transform(to_moll, box(10, 60, 11, 61)).area / 1e6
    assert 12300 < eq < 12420          # ~12,364 km2 for 1x1 deg at the equator
    assert 5900 < hi < 6200            # equal-area: ~cos(60.5deg)*12,364 ~ 6,100 km2


def test_overlap_metrics():
    m = xw.overlap_metrics(inter=50, a_uc=100, a_y=200)
    assert m["frac_of_ucdb"] == 0.5 and m["frac_of_yceo"] == 0.25
    assert m["overlap_over_min"] == 0.5 and m["iou"] == pytest.approx(50 / 250)
    assert m["area_ratio_ucdb_over_yceo"] == 0.5
    assert xw.is_link(0.5) and not xw.is_link(0.49)
    assert np.isnan(xw.overlap_metrics(1, 0, 5)["frac_of_ucdb"])


def _links(rows):
    cols = ["ucdb_id", "yceo_id", "inter_m2", "a_uc", "a_y"]
    df = pd.DataFrame(rows, columns=cols)
    m = [xw.overlap_metrics(r.inter_m2, r.a_uc, r.a_y) for r in df.itertuples()]
    df = pd.concat([df, pd.DataFrame(m)], axis=1)
    df["centroid_dist_km"] = 1.0
    return df


def test_one_to_one_strict_and_mismatch():
    l = _links([(1, 10, 80, 100, 100), (2, 11, 30, 30, 1000)])
    pairs, ut, yt = xw.classify_links(l, {1: "X", 2: "X"}, {10: True, 11: True})
    cls = dict(zip(pairs.ucdb_id, pairs.pair_class))
    assert cls[1] == "A_strict_1to1"
    assert cls[2] == "H_footprint_mismatch_1to1"      # area ratio 0.03 outside [0.25, 4]


def test_one_to_many_ucdb_in_two_clusters():
    l = _links([(1, 10, 60, 100, 80), (1, 11, 60, 100, 80)])
    pairs, *_ = xw.classify_links(l, {1: "X"}, {10: True, 11: True})
    assert set(pairs.pair_class) == {"C_ambiguous_one_to_many"}


def test_many_to_one_dominant_vs_ambiguous_and_cross_country():
    dom = _links([(1, 10, 85, 90, 100), (2, 10, 5, 5, 100)])
    pairs, *_ = xw.classify_links(dom, {1: "X", 2: "X"}, {10: True})
    cl = dict(zip(pairs.ucdb_id, pairs.pair_class))
    assert cl[1] == "B_dominant_1to1" and cl[2] == "D_minor_of_dominant"
    amb = _links([(1, 10, 40, 40, 100), (2, 10, 40, 40, 100)])
    pairs, *_ = xw.classify_links(amb, {1: "X", 2: "X"}, {10: True})
    assert set(pairs.pair_class) == {"D_many_to_one_ambiguous"}
    pairs, *_ = xw.classify_links(amb, {1: "X", 2: "Y"}, {10: True})
    assert set(pairs.pair_class) == {"E_cross_country_cluster"}


def test_no_duplicate_outcome_assignment_and_missing_response_excluded():
    l = _links([(1, 10, 40, 40, 100), (2, 10, 40, 40, 100),      # star cluster, valid R -> aggregate unit
                (3, 11, 90, 100, 100),                            # strict, but R missing
                (4, 12, 90, 100, 100), (4, 13, 90, 100, 100)])    # ucdb 4 in two clusters -> never a unit
    cty = {i: "X" for i in range(1, 5)}
    valid = {10: True, 11: False, 12: True, 13: True}
    pairs, *_ = xw.classify_links(l, cty, valid)
    units = xw.aggregate_cluster_units(pairs, valid, {1, 2, 3, 4})
    assert list(units.yceo_id) == [10] and units.iloc[0].n_ucdb == 2
    assert units.yceo_id.is_unique
    assert units.iloc[0].unit_type == "multi_city_aggregate"
    # a UCDB centre outside the primary sample blocks aggregation of its cluster
    assert xw.aggregate_cluster_units(pairs, valid, {1}).empty


def test_primary_r_field_identification():
    cols = ["Annual_nig", "Annual_day", "Winter_nig", "Winter_day", "Summer_nig", "Summer_day", "Lon", "Lat", "Code"]
    assert xw.identify_response_field(cols, "annual", "night") == "Annual_nig"
    assert xw.identify_response_field(cols, "summer", "day") == "Summer_day"
    assert xw.classify_field("Lon") is None
    with pytest.raises(ValueError):
        xw.identify_response_field(cols[:1] + cols[2:], "annual", "day")
    with pytest.raises(ValueError):
        xw.identify_response_field(cols + ["annual_night"], "annual", "night")


def test_summarize_response_and_smd():
    s = pd.Series([-1.0, 0.0, 1.0, 2.0, np.nan])
    d = xw.summarize_response(s)
    assert d["valid_n"] == 4 and d["missing_n"] == 1 and d["n_lt0"] == 1 and d["n_eq0"] == 1 and d["n_gt0"] == 2
    assert xw.smd(np.array([2.0, 3, 4]), np.array([1.0, 2, 3])) == pytest.approx(1.0)
