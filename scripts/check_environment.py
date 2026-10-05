"""Environment check for a given execution.

Collects only non-sensitive environment information (timestamp, project
root, Python version/executable, sys.prefix, detected conda environment,
platform, Git availability/status, and relevant installed package
versions) and writes it to a JSON file.

This script intentionally does NOT collect passwords, tokens, API keys,
SSH keys, credentials, unrelated personal data, or secret environment
variable values.

Updated in execution 1005-2 to additionally record python_executable,
sys_prefix, and conda_default_env, so that future runs can confirm which
interpreter/environment actually produced a given environment.json. This
update does not alter or regenerate the historical output recorded by
execution 1005-1 (results/1005-1/environment.json).

Usage:
    python scripts/check_environment.py [--execution-id 1005-1] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RELEVANT_PACKAGES = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "pyarrow",
    "PyYAML",
    "geopandas",
    "shapely",
    "pyproj",
    "rasterio",
    "xarray",
    "rioxarray",
    "scikit-learn",
    "pytest",
]


def _git_info(project_root: Path) -> dict:
    git_path = shutil.which("git")
    info = {
        "git_available": git_path is not None,
        "is_git_repository": False,
        "commit_hash": None,
    }
    if git_path is None:
        return info

    def run(args: list[str]) -> str | None:
        try:
            result = subprocess.run(
                [git_path, *args],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return None
            return result.stdout.strip()
        except Exception:
            return None

    is_repo = run(["rev-parse", "--is-inside-work-tree"])
    info["is_git_repository"] = is_repo == "true"
    if info["is_git_repository"]:
        info["commit_hash"] = run(["rev-parse", "HEAD"])
    return info


def _package_versions(packages: list[str]) -> dict:
    versions: dict[str, str | None] = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib_metadata.version(pkg)
        except importlib_metadata.PackageNotFoundError:
            versions[pkg] = None
    return versions


def collect_environment(execution_id: str, project_root: Path) -> dict:
    return {
        "execution_id": execution_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "python_version": sys.version,
        "python_version_info": list(sys.version_info),
        "python_executable": sys.executable,
        "sys_prefix": sys.prefix,
        "conda_default_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "git": _git_info(project_root),
        "package_versions": _package_versions(RELEVANT_PACKAGES),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-id", default="1005-1")
    parser.add_argument(
        "--out",
        default=None,
        help="Output path for environment.json (defaults to "
        "results/<execution-id>/environment.json)",
    )
    args = parser.parse_args()

    out_path = (
        Path(args.out)
        if args.out
        else PROJECT_ROOT / "results" / args.execution_id / "environment.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    env_info = collect_environment(args.execution_id, PROJECT_ROOT)
    out_path.write_text(json.dumps(env_info, indent=2), encoding="utf-8")

    print(f"Environment information written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
