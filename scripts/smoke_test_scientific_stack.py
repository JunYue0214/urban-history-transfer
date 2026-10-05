"""Smoke test for the project's scientific/GIS Python stack.

Intended to be invoked explicitly through the project's official
environment, e.g.:

    conda run -n py311 python scripts/smoke_test_scientific_stack.py --out results/1005-2/scientific_stack_smoke_test.json

Uses only synthetic/in-memory/local-temporary data. Does not download
any external research data. Does not produce any scientific result
figure; any temporary files created for the test are removed afterward.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _try(component: str, version_getter, test_fn) -> dict:
    entry = {
        "component": component,
        "status": "FAIL",
        "version": None,
        "test_performed": None,
        "error": None,
    }
    try:
        entry["version"] = version_getter()
    except Exception as exc:  # noqa: BLE001
        entry["error"] = f"version lookup failed: {type(exc).__name__}: {exc}"
    try:
        entry["test_performed"] = test_fn()
        entry["status"] = "PASS"
    except Exception as exc:  # noqa: BLE001
        entry["status"] = "FAIL"
        entry["error"] = (entry["error"] or "") + f" test failed: {type(exc).__name__}: {exc}"
    return entry


def test_numpy() -> dict:
    import numpy as np

    def run():
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        total = float(arr.sum())
        assert total == 10.0
        return f"np.array([1,2,3,4]).sum() == {total}"

    return _try("numpy", lambda: __import__("numpy").__version__, run)


def test_pandas() -> dict:
    def run():
        import pandas as pd

        df = pd.DataFrame({"group": ["a", "a", "b"], "value": [1, 2, 3]})
        agg = df.groupby("group")["value"].sum().to_dict()
        assert agg == {"a": 3, "b": 3}
        return f"groupby('group').sum() == {agg}"

    return _try("pandas", lambda: __import__("pandas").__version__, run)


def test_scipy() -> dict:
    def run():
        from scipy import stats

        result = stats.zscore([1.0, 2.0, 3.0])
        assert len(result) == 3
        return f"scipy.stats.zscore([1,2,3]) == {list(result)}"

    return _try("scipy", lambda: __import__("scipy").__version__, run)


def test_matplotlib() -> dict:
    def run():
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke_test_plot.png"
            fig.savefig(out)
            existed = out.exists()
        plt.close(fig)
        assert existed
        return "created and saved a minimal non-interactive plot to a temporary file, then closed it"

    return _try("matplotlib", lambda: __import__("matplotlib").__version__, run)


def test_shapely() -> dict:
    def run():
        from shapely.geometry import Point, Polygon

        p = Point(0, 0)
        poly = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1)])
        assert poly.contains(p)
        return "Polygon.contains(Point(0,0)) == True"

    return _try("shapely", lambda: __import__("shapely").__version__, run)


def test_pyproj() -> dict:
    def run():
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x, y = transformer.transform(0.0, 0.0)
        assert abs(x) < 1e-6 and abs(y) < 1e-6
        return f"EPSG:4326->EPSG:3857 transform of (0,0) == ({x}, {y})"

    return _try("pyproj", lambda: __import__("pyproj").__version__, run)


def test_geopandas() -> dict:
    def run():
        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )
        gdf_3857 = gdf.to_crs("EPSG:3857")
        assert gdf_3857.crs.to_epsg() == 3857
        return "GeoDataFrame created with EPSG:4326 and reprojected to EPSG:3857"

    return _try("geopandas", lambda: __import__("geopandas").__version__, run)


def test_rasterio() -> dict:
    def run():
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke_test_raster.tif"
            data = np.ones((2, 4, 4), dtype="uint8")
            transform = from_origin(0, 4, 1, 1)
            with rasterio.open(
                out,
                "w",
                driver="GTiff",
                height=4,
                width=4,
                count=2,
                dtype="uint8",
                crs="EPSG:4326",
                transform=transform,
            ) as dst:
                dst.write(data)
            with rasterio.open(out) as src:
                read_back = src.read()
                crs_ok = src.crs.to_epsg() == 4326
        assert read_back.shape == (2, 4, 4)
        assert crs_ok
        return "wrote/read a synthetic 2-band 4x4 uint8 GeoTIFF with CRS EPSG:4326 and an affine transform"

    return _try("rasterio", lambda: __import__("rasterio").__version__, run)


def test_xarray() -> dict:
    def run():
        import numpy as np
        import xarray as xr

        da = xr.DataArray(
            np.arange(6).reshape(2, 3),
            dims=("y", "x"),
            coords={"y": [0, 1], "x": [0, 1, 2]},
        )
        total = float(da.sum().values)
        assert total == 15.0
        return f"xr.DataArray(2x3).sum() == {total}"

    return _try("xarray", lambda: __import__("xarray").__version__, run)


def test_rioxarray() -> dict:
    def run():
        import numpy as np
        import rioxarray  # noqa: F401 - registers the .rio accessor
        import xarray as xr
        from affine import Affine

        da = xr.DataArray(
            np.ones((1, 4, 4), dtype="uint8"),
            dims=("band", "y", "x"),
        )
        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.write_transform(Affine(1.0, 0.0, 0.0, 0.0, -1.0, 4.0))
        crs_ok = da.rio.crs.to_epsg() == 4326
        assert crs_ok
        return "assigned CRS EPSG:4326 and an affine transform to a synthetic xarray DataArray via rioxarray"

    return _try("rioxarray", lambda: __import__("rioxarray").__version__, run)


def test_pyarrow() -> dict:
    def run():
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke_test_table.parquet"
            pq.write_table(table, out)
            read_back = pq.read_table(out)
        assert read_back.num_rows == 3
        return "round-tripped a 3-row pyarrow Table through a temporary local Parquet file"

    return _try("pyarrow", lambda: __import__("pyarrow").__version__, run)


COMPONENT_TESTS = [
    test_numpy,
    test_pandas,
    test_scipy,
    test_matplotlib,
    test_shapely,
    test_pyproj,
    test_geopandas,
    test_rasterio,
    test_xarray,
    test_rioxarray,
    test_pyarrow,
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    results = [fn() for fn in COMPONENT_TESTS]
    overall_status = "PASS" if all(r["status"] == "PASS" for r in results) else "PARTIAL"
    if all(r["status"] == "FAIL" for r in results):
        overall_status = "FAIL"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "overall_status": overall_status,
        "components": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Smoke test results written to: {out_path}")
    print(f"Overall status: {overall_status}")
    for r in results:
        print(f"  {r['component']}: {r['status']}" + (f" ({r['error']})" if r["error"] else ""))

    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
