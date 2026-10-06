"""Reusable raster inspection and polygon zonal-mean utilities.

Origin: execution 1006-1. Extended in 1006-2 for richer header inspection.
No network code. Importing has no side effects. Pixel reads are windowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def inspect_raster(path: Path) -> dict:
    """Inspect raster metadata without reading full pixel arrays."""
    import rasterio

    with rasterio.open(path) as src:
        return {
            "path": str(path),
            "driver": src.driver,
            "count": src.count,
            "dtype": list(src.dtypes),
            "nodata": src.nodata,
            "crs": str(src.crs),
            "bounds": list(src.bounds),
            "shape": [src.height, src.width],
            "transform": list(src.transform)[:6],
            "scales": list(src.scales),
            "offsets": list(src.offsets),
            "units": list(src.units) if src.units else [],
            "block_shapes": [list(x) for x in src.block_shapes],
            "compression": str(src.compression) if src.compression else None,
            "descriptions": list(src.descriptions),
            "tags": src.tags(),
            "band_tags": [src.tags(i) for i in range(1, src.count + 1)],
        }


def zonal_mean(
    raster_path: Path,
    polygons,
    band: int = 1,
    scale: float | None = None,
    offset: float | None = None,
):
    """Mean over valid pixels for each polygon.

    Parameters
    ----------
    raster_path
        Raster readable by rasterio.
    polygons
        Iterable of ``(index, geometry)`` pairs. Geometries MUST already be in
        the raster CRS.
    band
        1-based raster band.
    scale, offset
        Optional overrides. By default raster metadata scales/offsets are used.

    Returns
    -------
    list[tuple]
        ``(index, mean, n_valid_pixels, n_pixels_inside_polygon)``.

    Notes
    -----
    One polygon-sized raster window is read at a time, keeping RAM bounded.
    """
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds

    out = []
    with rasterio.open(raster_path) as src:
        sc = src.scales[band - 1] if scale is None else scale
        off = src.offsets[band - 1] if offset is None else offset

        for idx, geom in polygons:
            if geom is None or geom.is_empty:
                out.append((idx, np.nan, 0, 0))
                continue
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
            inside = geometry_mask(
                [geom],
                out_shape=arr.shape,
                transform=tr,
                invert=True,
                all_touched=False,
            )
            vals = arr[inside]
            valid = vals.compressed() if np.ma.isMaskedArray(vals) else vals
            if valid.size == 0:
                out.append((idx, np.nan, 0, int(inside.sum())))
            else:
                mean = float(valid.astype("float64").mean() * sc + off)
                out.append((idx, mean, int(valid.size), int(inside.sum())))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("raster")
    p.add_argument("--inspect", action="store_true", help="print raster metadata and exit")
    args = p.parse_args(argv)
    if not args.inspect:
        print("Only --inspect is exposed by this utility CLI.", file=sys.stderr)
        return 2
    print(json.dumps(inspect_raster(Path(args.raster)), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
