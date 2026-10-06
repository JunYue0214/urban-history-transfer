"""Zonal-mean aggregation of a gridded LST product to polygon footprints (execution 1006-1: code + mock test only).

NOT run on real research data in 1006-1. Importing has no side effects; there is no network code here.
`--inspect` reads only the raster header. Windowed reads keep memory bounded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def inspect_raster(path: Path) -> dict:
    """Header-only inspection: no pixel arrays are read."""
    import rasterio
    with rasterio.open(path) as src:
        return {"path": str(path), "count": src.count, "dtype": list(src.dtypes), "nodata": src.nodata,
                "crs": str(src.crs), "bounds": list(src.bounds), "shape": [src.height, src.width],
                "scales": list(src.scales), "offsets": list(src.offsets)}


def zonal_mean(raster_path: Path, polygons, band: int = 1, scale: float | None = None, offset: float | None = None):
    """Mean over valid pixels for each polygon (geometries in the raster CRS). Returns rows of
    (index, mean, n_valid_pixels, n_pixels). Reads one polygon-sized window at a time."""
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds
    out = []
    with rasterio.open(raster_path) as src:
        sc = src.scales[band - 1] if scale is None else scale
        off = src.offsets[band - 1] if offset is None else offset
        for idx, geom in polygons:
            try:
                win = from_bounds(*geom.bounds, transform=src.transform).round_offsets().round_lengths()
                win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            except Exception:
                out.append((idx, np.nan, 0, 0))
                continue
            if win.width < 1 or win.height < 1:
                out.append((idx, np.nan, 0, 0))
                continue
            arr = src.read(band, window=win, masked=True)
            tr = src.window_transform(win)
            inside = geometry_mask([geom], out_shape=arr.shape, transform=tr, invert=True, all_touched=False)
            vals = arr[inside]
            valid = vals.compressed() if np.ma.isMaskedArray(vals) else vals
            if valid.size == 0:
                out.append((idx, np.nan, 0, int(inside.sum())))
            else:
                out.append((idx, float(valid.mean() * sc + off), int(valid.size), int(inside.sum())))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("raster")
    p.add_argument("--inspect", action="store_true", help="print header only and exit")
    args = p.parse_args(argv)
    if not args.inspect:
        print("Only --inspect is enabled in 1006-1; the full aggregation is deferred to 1006-2.", file=sys.stderr)
        return 2
    print(json.dumps(inspect_raster(Path(args.raster)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
