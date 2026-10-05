"""Verifier for a downloaded thermal-response file (execution 1005-6).

Checks file existence, size, optional SHA-256, and basic format integrity for
CSV files and for ZIP archives (ZIP integrity; for zipped shapefiles, the
presence of .shp/.shx/.dbf members and the DBF field names, parsed with the
standard library only). Does no network access. Importing has no side effects.

Usage (human-operated, after download):
    conda run -n py311 python scripts/verify_thermal_response.py FILE \
        [--sha256 HEX] [--min-bytes N] [--require-columns a,b,c]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

CHUNK = 1024 * 1024
SHAPEFILE_CORE = (".shp", ".shx", ".dbf")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def dbf_fields(data: bytes) -> tuple[list[str], int]:
    """Return (field names, record count) from a dBASE III/IV header."""
    if len(data) < 33:
        raise ValueError("DBF header too short")
    n_records = struct.unpack("<I", data[4:8])[0]
    names: list[str] = []
    pos = 32
    while pos + 32 <= len(data) and data[pos] != 0x0D:
        names.append(data[pos:pos + 11].split(b"\x00")[0].decode("latin-1"))
        pos += 32
    if not names:
        raise ValueError("DBF has no field descriptors")
    return names, n_records


def _check_columns(report: dict, columns: list[str], required: list[str] | None, fail) -> None:
    report["columns"] = columns
    if required:
        missing = [c for c in required if c not in columns]
        if missing:
            fail(f"Missing required columns: {missing}", "required_columns")
        else:
            report["checks"]["required_columns"] = True


def verify(path: Path, expected_sha256: str | None = None, min_bytes: int = 1,
           required_columns: list[str] | None = None) -> dict:
    report: dict = {"path": str(path), "checks": {}, "ok": True, "errors": []}

    def fail(msg: str, key: str) -> None:
        report["checks"][key] = False
        report["errors"].append(msg)
        report["ok"] = False

    if not path.is_file():
        fail(f"File does not exist: {path}", "exists")
        return report
    report["checks"]["exists"] = True

    size = path.stat().st_size
    report["bytes"] = size
    if size < min_bytes:
        fail(f"File size {size} < minimum {min_bytes}", "size")
    else:
        report["checks"]["size"] = True

    digest = sha256_of(path)
    report["sha256"] = digest
    if expected_sha256 is not None:
        if digest.lower() == expected_sha256.lower():
            report["checks"]["sha256"] = True
        else:
            fail(f"SHA-256 mismatch: expected {expected_sha256}, got {digest}", "sha256")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    fail("CSV has no header row", "csv_header")
                else:
                    report["checks"]["csv_header"] = True
                    first = next(reader, None)
                    if first is None:
                        fail("CSV has a header but no data rows", "csv_rows")
                    elif len(first) != len(header):
                        fail(f"First data row has {len(first)} fields, header has {len(header)}", "csv_rows")
                    else:
                        report["checks"]["csv_rows"] = True
                    _check_columns(report, header, required_columns, fail)
        except UnicodeDecodeError as exc:
            fail(f"CSV is not valid UTF-8: {exc}", "csv_encoding")
    elif suffix == ".zip":
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    fail(f"Corrupt member in ZIP: {bad}", "zip_integrity")
                else:
                    report["checks"]["zip_integrity"] = True
                    members = zf.namelist()
                    report["zip_members"] = members
                    shp = [m for m in members if m.lower().endswith(".shp")]
                    if shp:
                        stem = shp[0][:-4]
                        have = {m.lower() for m in members}
                        absent = [e for e in SHAPEFILE_CORE if (stem + e).lower() not in have]
                        if absent:
                            fail(f"Shapefile {shp[0]} missing sidecar members: {absent}", "shapefile_members")
                        else:
                            report["checks"]["shapefile_members"] = True
                            dbf_name = next(m for m in members if m.lower() == (stem + ".dbf").lower())
                            names, n = dbf_fields(zf.read(dbf_name))
                            report["dbf_records"] = n
                            _check_columns(report, names, required_columns, fail)
                    elif required_columns:
                        fail("Required columns were given but the ZIP holds no shapefile to inspect",
                             "required_columns")
        except zipfile.BadZipFile as exc:
            fail(f"Not a valid ZIP archive: {exc}", "zip_integrity")
        except ValueError as exc:
            fail(f"Shapefile DBF unreadable: {exc}", "dbf_header")
    elif required_columns:
        fail(f"Cannot check columns for file type {suffix!r}", "required_columns")
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("file")
    p.add_argument("--sha256", default=None)
    p.add_argument("--min-bytes", type=int, default=1)
    p.add_argument("--require-columns", default=None, help="Comma-separated column names.")
    args = p.parse_args(argv)
    cols = args.require_columns.split(",") if args.require_columns else None
    rep = verify(Path(args.file), args.sha256, args.min_bytes, cols)
    print(json.dumps(rep, indent=2))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
