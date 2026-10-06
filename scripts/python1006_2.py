"""Execution 1006-2: verify the proposed 2018-2023 urban-LST archive.

This runner performs bounded technical verification only:
- no network access
- no download
- no Gate 2B model fitting
- no full 2018-2023 zonal aggregation
- no inspection of H values

Expected input:
    data/raw/urban_lst/2018-2023.zip

Run:
    conda run -n py311 python scripts/python1006_2.py
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import aggregate_lst_zonal as az  # noqa: E402
import ucdb_gate1_pilot as gate1  # noqa: E402

RUN_ID = "1006-2"
RESULT_DIR = ROOT / "results" / "python1006_2"
ARCHIVE = ROOT / "data" / "raw" / "urban_lst" / "2018-2023.zip"
SEED = 42
RASTER_EXTS = {".tif", ".tiff", ".img", ".vrt", ".nc", ".grd"}
QUALITY_WORDS = ("qa", "quality", "mask", "flag", "imput", "gap", "fill", "qc")
DATE_PATTERNS = (
    re.compile(r"(?<!\d)(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)(?!\d)"),
    re.compile(r"(?<!\d)(20\d{2})[-_]?([0-3]\d{2})(?!\d)"),
)


@dataclass
class Decision:
    status: str
    reasons: list[str]


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_date_from_name(name: str) -> date | None:
    base = Path(name).name
    m = DATE_PATTERNS[0].search(base)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = DATE_PATTERNS[1].search(base)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)}-{m.group(2)}", "%Y-%j").date()
        except ValueError:
            pass
    return None


def archive_audit(path: Path) -> tuple[dict, list[zipfile.ZipInfo], list[tuple[zipfile.ZipInfo, date | None]]]:
    if not path.exists():
        raise FileNotFoundError(f"Expected archive not found: {path}")

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        infos = [i for i in zf.infolist() if not i.is_dir()]

    ext_counts: dict[str, int] = {}
    dated = []
    likely = []
    for info in infos:
        ext = Path(info.filename).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        d = parse_date_from_name(info.filename)
        dated.append((info, d))
        if ext in RASTER_EXTS:
            likely.append(info)

    date_values = sorted(d for _, d in dated if d is not None)
    unique_dates = sorted(set(date_values))
    duplicate_dates = sorted({d for d in unique_dates if date_values.count(d) > 1})
    missing_dates = []
    if unique_dates:
        cur = unique_dates[0]
        end = unique_dates[-1]
        present = set(unique_dates)
        while cur <= end:
            if cur not in present:
                missing_dates.append(cur)
            cur = date.fromordinal(cur.toordinal() + 1)

    audit = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "zip_integrity": "PASS" if bad is None else "FAIL",
        "first_bad_member": bad,
        "member_count": len(infos),
        "extensions": ext_counts,
        "compressed_bytes_total": int(sum(i.compress_size for i in infos)),
        "uncompressed_bytes_total": int(sum(i.file_size for i in infos)),
        "likely_raster_member_count": len(likely),
        "dated_member_count": len(date_values),
        "unique_date_count": len(unique_dates),
        "date_min": unique_dates[0].isoformat() if unique_dates else None,
        "date_max": unique_dates[-1].isoformat() if unique_dates else None,
        "duplicate_date_count": len(duplicate_dates),
        "duplicate_dates_head": [d.isoformat() for d in duplicate_dates[:20]],
        "missing_date_count_between_detected_bounds": len(missing_dates),
        "missing_dates_head": [d.isoformat() for d in missing_dates[:30]],
        "quality_like_members": [
            i.filename for i in infos
            if any(w in i.filename.lower() for w in QUALITY_WORDS)
        ][:100],
    }
    return audit, infos, dated


def choose_representative_members(
    dated: list[tuple[zipfile.ZipInfo, date | None]]
) -> list[zipfile.ZipInfo]:
    raster = [(i, d) for i, d in dated if Path(i.filename).suffix.lower() in RASTER_EXTS]
    if not raster:
        return []

    with_dates = sorted([(i, d) for i, d in raster if d is not None], key=lambda x: x[1])
    if with_dates:
        picks = [with_dates[0][0], with_dates[len(with_dates) // 2][0], with_dates[-1][0]]
    else:
        raster = sorted(raster, key=lambda x: x[0].filename)
        picks = [raster[0][0], raster[len(raster) // 2][0], raster[-1][0]]

    out = []
    seen = set()
    for p in picks:
        if p.filename not in seen:
            seen.add(p.filename)
            out.append(p)
    return out


def safe_extract_members(archive: Path, members: Iterable[zipfile.ZipInfo], dest: Path) -> list[Path]:
    extracted = []
    with zipfile.ZipFile(archive, "r") as zf:
        for info in members:
            name = Path(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise RuntimeError(f"Unsafe archive member path: {info.filename}")
            target = dest / name.name
            with zf.open(info, "r") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)
    return extracted


def tiny_value_diagnostic(path: Path) -> dict:
    import rasterio

    with rasterio.open(path) as src:
        out_h = min(128, src.height)
        out_w = min(128, src.width)
        arr = src.read(1, out_shape=(out_h, out_w), masked=True)
        vals = arr.compressed().astype("float64")
        sc = src.scales[0] if src.scales else 1.0
        off = src.offsets[0] if src.offsets else 0.0
        scaled = vals * sc + off
        if scaled.size == 0:
            return {"n": 0}
        q = np.quantile(scaled, [0, .01, .5, .99, 1])
        return {
            "n": int(scaled.size),
            "min": float(q[0]),
            "p01": float(q[1]),
            "median": float(q[2]),
            "p99": float(q[3]),
            "max": float(q[4]),
            "mean": float(scaled.mean()),
        }


def infer_units(meta: dict, diag: dict) -> dict:
    text = json.dumps(
        {
            "units": meta.get("units"),
            "tags": meta.get("tags"),
            "band_tags": meta.get("band_tags"),
            "descriptions": meta.get("descriptions"),
        },
        default=str,
    ).lower()

    if any(x in text for x in ("kelvin", '"k"', " unit=k", "units=k")):
        return {"unit": "K", "evidence": "metadata"}
    if any(x in text for x in ("celsius", "degc", "degree_celsius", "°c")):
        return {"unit": "degC", "evidence": "metadata"}

    med = diag.get("median")
    if med is not None:
        if 180 <= med <= 360:
            return {"unit": "K?", "evidence": "numeric_diagnostic_only"}
        if -100 <= med <= 100:
            return {"unit": "degC?", "evidence": "numeric_diagnostic_only"}
    return {"unit": None, "evidence": "unresolved"}


def grid_signature(meta: dict) -> dict:
    return {
        "crs": meta.get("crs"),
        "shape": meta.get("shape"),
        "transform": meta.get("transform"),
        "bounds": meta.get("bounds"),
        "count": meta.get("count"),
    }


def discover_ucdb_polygon_layer(gpkg: Path) -> tuple[str, dict]:
    import pyogrio

    layers = pyogrio.list_layers(gpkg)
    candidates = []
    for name, geom_type in layers:
        gt = str(geom_type).lower()
        if "polygon" not in gt:
            continue
        try:
            info = pyogrio.read_info(gpkg, layer=name)
            fields = set(map(str, info.get("fields", [])))
        except Exception:
            continue
        if "ID_UC_G0" not in fields:
            continue
        lname = str(name).lower()
        score = (
            10 * ("bound" in lname)
            + 7 * ("uc_" in lname or lname.startswith("uc"))
            + 3 * ("urban" in lname)
        )
        candidates.append((score, str(name), str(geom_type), sorted(fields)))

    if not candidates:
        raise RuntimeError("Could not discover a polygon layer with ID_UC_G0 in the UCDB GeoPackage.")
    candidates.sort(key=lambda x: (-x[0], x[1]))
    best = candidates[0]
    return best[1], {
        "selected_layer": best[1],
        "selected_geometry_type": best[2],
        "candidate_layers": [
            {"name": x[1], "geometry_type": x[2], "score": x[0]}
            for x in candidates
        ],
    }


def load_gate1_sample_ids() -> pd.DataFrame:
    main = gate1.load_main_table()
    qc = gate1.run_qc(main)
    sample, _ = gate1.build_sample(main, qc)
    return sample[["ID_UC_G0", "lat_deg", "lon_deg", "region"]].copy()


def distributed_city_ids(sample: pd.DataFrame, n: int = 12) -> list[int]:
    """Deterministic geographically distributed IDs, without reading H."""
    s = sample.sort_values(["lat_deg", "lon_deg", "ID_UC_G0"]).reset_index(drop=True)
    if len(s) <= n:
        return s["ID_UC_G0"].astype(int).tolist()
    idx = np.linspace(0, len(s) - 1, n, dtype=int)
    return s.iloc[idx]["ID_UC_G0"].astype(int).tolist()


def load_polygon_subset(gpkg: Path, layer: str, ids: list[int]):
    import pyogrio

    gdf = pyogrio.read_dataframe(gpkg, layer=layer, columns=["ID_UC_G0"])
    gdf = gdf[gdf["ID_UC_G0"].astype(int).isin(ids)].copy()
    if gdf.empty:
        raise RuntimeError("No selected Gate-1 city IDs were found in the discovered polygon layer.")
    return gdf


def compatibility_and_benchmark(
    raster_path: Path,
    sample: pd.DataFrame,
    max_polygons: int = 12,
) -> dict:
    import rasterio

    layer, layer_meta = discover_ucdb_polygon_layer(gate1.GPKG_PATH)
    ids = distributed_city_ids(sample, n=max_polygons)
    gdf = load_polygon_subset(gate1.GPKG_PATH, layer, ids)

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        raster_bounds = src.bounds

    source_crs = str(gdf.crs)
    if raster_crs is None:
        raise RuntimeError("Raster CRS is missing.")
    if gdf.crs is None:
        raise RuntimeError("UCDB polygon CRS is missing.")

    if gdf.crs != raster_crs:
        gdf = gdf.to_crs(raster_crs)
    target_crs = str(gdf.crs)

    # Bounding-box overlap only; precise per-polygon validity is checked by zonal_mean.
    gx0, gy0, gx1, gy1 = gdf.total_bounds
    rb = raster_bounds
    bbox_overlap = not (gx1 < rb.left or gx0 > rb.right or gy1 < rb.bottom or gy0 > rb.top)

    pairs = [(int(r.ID_UC_G0), r.geometry) for r in gdf.itertuples()]
    t0 = time.perf_counter()
    rows = az.zonal_mean(raster_path, pairs)
    elapsed = time.perf_counter() - t0

    z = pd.DataFrame(rows, columns=["ID_UC_G0", "mean", "n_valid_pixels", "n_pixels"])
    z["passes_9_valid_pixels"] = z["n_valid_pixels"] >= 9

    return {
        "polygon_layer": layer_meta,
        "ucdb_polygon_crs_source": source_crs,
        "ucdb_polygon_crs_used": target_crs,
        "raster_crs": str(raster_crs),
        "bbox_overlap": bool(bbox_overlap),
        "n_test_polygons": int(len(z)),
        "zonal_test_rows": z.to_dict(orient="records"),
        "n_with_any_valid_pixel": int((z["n_valid_pixels"] > 0).sum()),
        "n_passing_9_valid_pixels": int(z["passes_9_valid_pixels"].sum()),
        "elapsed_seconds": float(elapsed),
        "seconds_per_test_polygon": float(elapsed / max(len(z), 1)),
    }


def git_commit() -> str | None:
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return p.stdout.strip()
    except Exception:
        return None


def environment_info() -> dict:
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "git_commit": git_commit(),
    }


def decide(
    archive_info: dict,
    metas: list[dict],
    unit_info: dict | None,
    compat: dict | None,
) -> Decision:
    reasons = []

    if archive_info.get("zip_integrity") != "PASS":
        return Decision("BLOCKED_DATA_FORMAT", ["ZIP integrity failed."])
    if archive_info.get("likely_raster_member_count", 0) == 0:
        return Decision("BLOCKED_DATA_FORMAT", ["No likely raster members were detected."])
    if not metas:
        return Decision("BLOCKED_DATA_FORMAT", ["Representative rasters could not be inspected."])

    sigs = [grid_signature(m) for m in metas]
    if any(s != sigs[0] for s in sigs[1:]):
        reasons.append("Representative raster grids are not identical.")

    if any(not m.get("crs") or m.get("crs") == "None" for m in metas):
        return Decision("BLOCKED_METADATA", ["Raster CRS is missing."])

    unresolved_units = [u for u in unit_info.get("representatives", []) if u.get("unit") is None]
    numeric_only = [u for u in unit_info.get("representatives", []) if u.get("evidence") == "numeric_diagnostic_only"]
    if unresolved_units:
        return Decision("BLOCKED_METADATA", ["Temperature units are unresolved."])
    if numeric_only:
        reasons.append("Temperature units are inferred from bounded numeric diagnostics, not explicit raster metadata.")

    if compat is None:
        return Decision("BLOCKED_GEOMETRY", ["UCDB compatibility test did not complete."])
    if not compat.get("bbox_overlap"):
        return Decision("BLOCKED_GEOMETRY", ["UCDB test polygons do not overlap raster bounds."])
    if compat.get("n_with_any_valid_pixel", 0) == 0:
        return Decision("BLOCKED_GEOMETRY", ["No valid raster pixels were found for test polygons."])

    # A sampled representative zonal benchmark is not enough to prove total runtime.
    n_rasters = archive_info.get("likely_raster_member_count", 0)
    n_cities = 10915
    seconds_per = compat.get("seconds_per_test_polygon", 0.0)
    naive_seconds = float(n_rasters * n_cities * seconds_per)
    compat["naive_full_polygon_window_estimate_seconds"] = naive_seconds
    compat["naive_full_polygon_window_estimate_hours"] = naive_seconds / 3600
    compat["naive_estimate_note"] = (
        "Linear estimate from one representative raster and a tiny city subset; "
        "for architecture planning only, not a runtime guarantee."
    )

    if naive_seconds > 48 * 3600:
        reasons.append(
            "Naive polygon-window scaling exceeds 48 h; next round should use a more efficient reusable aggregation architecture."
        )

    if sigs and all(s == sigs[0] for s in sigs[1:]):
        reasons.append("Representative rasters share one grid, enabling a reusable grid-based aggregation design.")

    return Decision("READY_FOR_AGGREGATION", reasons)


def markdown_report(summary: dict) -> str:
    a = summary["archive"]
    reps = summary.get("representative_rasters", [])
    compat = summary.get("ucdb_compatibility")
    d = summary["decision"]

    lines = [
        "# Python Results 1006-2",
        "",
        "## Execution",
        f"- Status: **{summary['execution_status']}**",
        f"- Technical decision: **{d['status']}**",
        f"- Runtime: {summary['runtime_seconds']:.2f} s",
        f"- Archive: `{a.get('path')}`",
        f"- SHA256: `{a.get('sha256')}`",
        "",
        "## Archive audit",
        f"- ZIP integrity: {a.get('zip_integrity')}",
        f"- File size: {a.get('bytes')} bytes",
        f"- Members: {a.get('member_count')}",
        f"- Likely raster members: {a.get('likely_raster_member_count')}",
        f"- Detected dates: {a.get('unique_date_count')} ({a.get('date_min')} to {a.get('date_max')})",
        f"- Missing dates between detected bounds: {a.get('missing_date_count_between_detected_bounds')}",
        f"- Duplicate detected dates: {a.get('duplicate_date_count')}",
        f"- Quality/imputation-like members: {len(a.get('quality_like_members', []))}",
        "",
        "## Representative raster inspection",
    ]
    for r in reps:
        meta = r["metadata"]
        lines += [
            f"### {r['member']}",
            f"- Driver: {meta.get('driver')}; shape: {meta.get('shape')}; bands: {meta.get('count')}",
            f"- CRS: {meta.get('crs')}",
            f"- dtype: {meta.get('dtype')}; nodata: {meta.get('nodata')}",
            f"- scale: {meta.get('scales')}; offset: {meta.get('offsets')}",
            f"- unit inference: {r['unit_inference']}",
            f"- tiny bounded value diagnostic: {r['value_diagnostic']}",
            "",
        ]

    if compat:
        lines += [
            "## UCDB compatibility and bounded benchmark",
            f"- Polygon layer: {compat['polygon_layer']['selected_layer']}",
            f"- Polygon source CRS: {compat.get('ucdb_polygon_crs_source')}",
            f"- Polygon CRS used: {compat.get('ucdb_polygon_crs_used')}",
            f"- Raster CRS: {compat.get('raster_crs')}",
            f"- Bounding-box overlap: {compat.get('bbox_overlap')}",
            f"- Test polygons: {compat.get('n_test_polygons')}",
            f"- With any valid pixel: {compat.get('n_with_any_valid_pixel')}",
            f"- Passing >=9 valid pixels: {compat.get('n_passing_9_valid_pixels')}",
            f"- Bounded benchmark: {compat.get('elapsed_seconds'):.3f} s",
            f"- Naive full polygon-window estimate: {compat.get('naive_full_polygon_window_estimate_hours', float('nan')):.2f} h",
            "",
            "### Test rows",
            "",
            "| ID_UC_G0 | mean | valid pixels | pixels | >=9 |",
            "|---:|---:|---:|---:|:---:|",
        ]
        for r in compat.get("zonal_test_rows", []):
            mean = r["mean"]
            mean_s = "nan" if pd.isna(mean) else f"{mean:.4f}"
            lines.append(
                f"| {r['ID_UC_G0']} | {mean_s} | {r['n_valid_pixels']} | {r['n_pixels']} | {r['passes_9_valid_pixels']} |"
            )

    lines += [
        "",
        "## Decision",
        f"**{d['status']}**",
        "",
    ]
    if d.get("reasons"):
        lines += [f"- {x}" for x in d["reasons"]]
    else:
        lines.append("- No blocking reason recorded.")

    lines += [
        "",
        "## Boundary of this result",
        "This run verifies the archive and a bounded UCDB zonal-statistics path only. "
        "It does **not** fit Gate 2B models, inspect H values, or establish any scientific PASS/FAIL.",
        "",
    ]
    return "\n".join(lines)


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    done = RESULT_DIR / "python1006_2_DONE.txt"
    failed = RESULT_DIR / "python1006_2_FAILED.txt"
    for marker in (done, failed):
        if marker.exists():
            marker.unlink()

    summary = {
        "run_id": RUN_ID,
        "execution_status": "RUNNING",
        "archive": {"path": str(ARCHIVE)},
        "representative_rasters": [],
        "ucdb_compatibility": None,
        "decision": {"status": "DATA_MISSING", "reasons": []},
        "environment": environment_info(),
    }

    try:
        if not ARCHIVE.exists():
            summary["execution_status"] = "FAILED"
            summary["decision"] = {
                "status": "DATA_MISSING",
                "reasons": [f"Archive not found: {ARCHIVE}"],
            }
            raise FileNotFoundError(summary["decision"]["reasons"][0])

        archive_info, infos, dated = archive_audit(ARCHIVE)
        summary["archive"] = archive_info

        reps = choose_representative_members(dated)
        if not reps:
            decision = Decision("BLOCKED_DATA_FORMAT", ["No inspectable raster member found."])
            summary["decision"] = asdict(decision)
        else:
            with tempfile.TemporaryDirectory(prefix="urban_lst_verify_") as td:
                extracted = safe_extract_members(ARCHIVE, reps, Path(td))
                rep_rows = []
                unit_rows = []
                for info, path in zip(reps, extracted):
                    meta = az.inspect_raster(path)
                    diag = tiny_value_diagnostic(path)
                    u = infer_units(meta, diag)
                    rep_rows.append(
                        {
                            "member": info.filename,
                            "date": parse_date_from_name(info.filename).isoformat()
                            if parse_date_from_name(info.filename)
                            else None,
                            "metadata": meta,
                            "value_diagnostic": diag,
                            "unit_inference": u,
                        }
                    )
                    unit_rows.append(u)
                summary["representative_rasters"] = rep_rows

                sample = load_gate1_sample_ids()
                summary["gate1_sample_n"] = int(len(sample))
                compat = compatibility_and_benchmark(extracted[0], sample)
                summary["ucdb_compatibility"] = compat

                unit_info = {"representatives": unit_rows}
                decision = decide(archive_info, [x["metadata"] for x in rep_rows], unit_info, compat)
                summary["decision"] = asdict(decision)

        summary["execution_status"] = "SUCCESS"
        summary["runtime_seconds"] = time.time() - started

        write_json(RESULT_DIR / "python1006_2_summary.json", summary)

        manifest = {
            "run_id": RUN_ID,
            "input_archive": str(ARCHIVE),
            "input_sha256": summary.get("archive", {}).get("sha256"),
            "environment": summary["environment"],
            "runtime_seconds": summary["runtime_seconds"],
            "generated_files": [
                "python1006_2_results.md",
                "python1006_2_summary.json",
                "python1006_2_manifest.json",
                "python1006_2_DONE.txt",
            ],
            "seed": SEED,
        }
        write_json(RESULT_DIR / "python1006_2_manifest.json", manifest)
        (RESULT_DIR / "python1006_2_results.md").write_text(markdown_report(summary), encoding="utf-8")
        done.write_text(
            f"RUN_ID={RUN_ID}\nSTATUS=SUCCESS\nDECISION={summary['decision']['status']}\n"
            f"RESULT={RESULT_DIR / 'python1006_2_results.md'}\n",
            encoding="utf-8",
        )

        print("=" * 64)
        print("PYTHON 1006-2 COMPLETE")
        print("STATUS: SUCCESS")
        print(f"DECISION: {summary['decision']['status']}")
        print(f"RESULT: {RESULT_DIR / 'python1006_2_results.md'}")
        print("=" * 64)
        return 0

    except Exception as e:
        summary["runtime_seconds"] = time.time() - started
        if summary.get("execution_status") != "FAILED":
            summary["execution_status"] = "FAILED"
        summary["exception"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
        try:
            write_json(RESULT_DIR / "python1006_2_summary.json", summary)
            (RESULT_DIR / "python1006_2_results.md").write_text(markdown_report(summary), encoding="utf-8")
            failed.write_text(
                f"RUN_ID={RUN_ID}\nSTATUS=FAILED\n"
                f"DECISION={summary.get('decision', {}).get('status')}\n"
                f"ERROR={type(e).__name__}: {e}\n"
                f"RESULT={RESULT_DIR / 'python1006_2_results.md'}\n",
                encoding="utf-8",
            )
        except Exception:
            pass

        print("=" * 64, file=sys.stderr)
        print("PYTHON 1006-2 COMPLETE", file=sys.stderr)
        print("STATUS: FAILED", file=sys.stderr)
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"RESULT: {RESULT_DIR / 'python1006_2_results.md'}", file=sys.stderr)
        print("=" * 64, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
