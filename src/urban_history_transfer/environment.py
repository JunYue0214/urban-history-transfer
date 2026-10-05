"""Project Python environment guard.

Verifies that code is running under the officially designated project
environment policy: Python 3.11.x (conda environment `py311`), as
established by execution 1005-2 and documented in
docs/ENVIRONMENT_POLICY.md.

The hard requirement is the Python major/minor version. The conda
environment name (`CONDA_DEFAULT_ENV`) is recorded for diagnostics but is
NOT required to be set, since `conda run -n py311 ...` does not reliably
set it in all cases, and the active environment name alone is not a
trustworthy guarantee of interpreter identity.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 11


@dataclass
class EnvironmentCheckResult:
    ok: bool
    python_major: int
    python_minor: int
    python_executable: str
    sys_prefix: str
    conda_default_env: str | None
    message: str


def check_environment() -> EnvironmentCheckResult:
    """Check whether the current interpreter satisfies the project's
    Python version policy (major 3, minor 11).

    Does not raise. Callers decide how to react to a failing result.
    """
    major, minor = sys.version_info.major, sys.version_info.minor
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    ok = major == REQUIRED_PYTHON_MAJOR and minor == REQUIRED_PYTHON_MINOR

    if ok:
        message = (
            f"OK: running under Python {major}.{minor} "
            f"(executable={sys.executable!r})."
        )
    else:
        message = (
            f"ENVIRONMENT MISMATCH: this project requires Python "
            f"{REQUIRED_PYTHON_MAJOR}.{REQUIRED_PYTHON_MINOR}.x (conda "
            f"environment 'py311'), but the running interpreter is Python "
            f"{major}.{minor} (executable={sys.executable!r}). "
            f"Re-run using: conda run -n py311 python ..."
        )

    return EnvironmentCheckResult(
        ok=ok,
        python_major=major,
        python_minor=minor,
        python_executable=sys.executable,
        sys_prefix=sys.prefix,
        conda_default_env=conda_env,
        message=message,
    )


def require_environment() -> EnvironmentCheckResult:
    """Like check_environment(), but raises RuntimeError if the Python
    version policy is violated. Use at the entry point of code that must
    not silently run under the wrong interpreter."""
    result = check_environment()
    if not result.ok:
        raise RuntimeError(result.message)
    return result
