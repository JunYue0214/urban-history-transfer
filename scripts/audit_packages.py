"""Audit scientific/GIS package availability in the active Python interpreter.

Intended to be invoked explicitly through the project's official
environment, e.g.:

    conda run -n py311 python scripts/audit_packages.py --out results/1005-2/package_audit_before.json

Records, for each requested package: requested name, import name,
installed/not installed, and installed version if available. Does not
install anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from importlib import import_module
from importlib import metadata as importlib_metadata
from pathlib import Path

# (requested/distribution name, import module name)
PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("matplotlib", "matplotlib"),
    ("pyarrow", "pyarrow"),
    ("PyYAML", "yaml"),
    ("pytest", "pytest"),
    ("geopandas", "geopandas"),
    ("shapely", "shapely"),
    ("pyproj", "pyproj"),
    ("rasterio", "rasterio"),
    ("xarray", "xarray"),
    ("rioxarray", "rioxarray"),
]


def audit_packages() -> list[dict]:
    results = []
    for requested_name, import_name in PACKAGES:
        entry = {
            "requested_package": requested_name,
            "import_name": import_name,
            "installed": False,
            "version": None,
            "error": None,
        }
        try:
            module = import_module(import_name)
            entry["installed"] = True
            version = getattr(module, "__version__", None)
            if version is None:
                try:
                    version = importlib_metadata.version(requested_name)
                except importlib_metadata.PackageNotFoundError:
                    version = None
            entry["version"] = str(version) if version is not None else None
        except Exception as exc:  # noqa: BLE001 - we want to record any import failure
            entry["installed"] = False
            entry["error"] = f"{type(exc).__name__}: {exc}"
        results.append(entry)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--label",
        default="before",
        help="Label for this audit, e.g. 'before' or 'after'",
    )
    args = parser.parse_args()

    payload = {
        "label": args.label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "packages": audit_packages(),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Package audit ({args.label}) written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
