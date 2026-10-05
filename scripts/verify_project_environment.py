"""CLI check that the current interpreter satisfies the project's official
Python environment policy (Python 3.11.x, conda environment `py311`).

Usage:
    conda run -n py311 python scripts/verify_project_environment.py

Exits non-zero if the Python major/minor requirement is violated.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from urban_history_transfer.environment import check_environment  # noqa: E402


def main() -> int:
    result = check_environment()
    print(result.message)
    print(f"  python_major: {result.python_major}")
    print(f"  python_minor: {result.python_minor}")
    print(f"  python_executable: {result.python_executable}")
    print(f"  sys_prefix: {result.sys_prefix}")
    print(f"  conda_default_env: {result.conda_default_env}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
