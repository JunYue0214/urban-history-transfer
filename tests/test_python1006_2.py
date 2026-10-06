"""Synthetic tests for execution 1006-2.

No network and no research data are used.
"""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import aggregate_lst_zonal as az  # noqa: E402
import python1006_2 as r  # noqa: E402


def test_parse_dates():
    assert r.parse_date_from_name("LST_20180101.tif") == date(2018, 1, 1)
    assert r.parse_date_from_name("x_2018-12-31.tif") == date(2018, 12, 31)
    assert r.parse_date_from_name("x_2018365.tif") == date(2018, 12, 31)
    assert r.parse_date_from_name("no_date.tif") is None


def test_synthetic_zip_and_raster(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    tif = tmp_path / "LST_20180101.tif"
    arr = np.arange(100, dtype="float32").reshape(10, 10) + 273.15
    with rasterio.open(
        tif,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-5, 5, 1, 1),
        nodata=-9999.0,
    ) as dst:
        dst.write(arr, 1)
        dst.set_band_description(1, "daily mean LST")
        dst.update_tags(1, units="kelvin")

    zpath = tmp_path / "2018-2023.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif, arcname=tif.name)

    audit, infos, dated = r.archive_audit(zpath)
    assert audit["zip_integrity"] == "PASS"
    assert audit["likely_raster_member_count"] == 1
    assert audit["date_min"] == "2018-01-01"

    reps = r.choose_representative_members(dated)
    assert len(reps) == 1

    meta = az.inspect_raster(tif)
    diag = r.tiny_value_diagnostic(tif)
    units = r.infer_units(meta, diag)
    assert meta["crs"] == "EPSG:4326"
    assert units["unit"] == "K"
    assert units["evidence"] == "metadata"


def test_zonal_mean_synthetic(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    shapely = pytest.importorskip("shapely")
    from rasterio.transform import from_origin
    from shapely.geometry import box

    tif = tmp_path / "a.tif"
    arr = np.ones((10, 10), dtype="float32") * 300.0
    with rasterio.open(
        tif,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(0, 10, 1, 1),
        nodata=-9999,
    ) as dst:
        dst.write(arr, 1)

    rows = az.zonal_mean(tif, [(1, box(0, 0, 10, 10))])
    assert len(rows) == 1
    assert rows[0][1] == pytest.approx(300.0)
    assert rows[0][2] == 100
    assert rows[0][3] == 100
