"""Tests for the project environment guard (src/urban_history_transfer/environment.py).

These tests validate the guard logic itself. They do not assert that the
process running pytest is necessarily py311 (that is a property of how
the test suite is invoked, verified separately via
scripts/verify_project_environment.py and documented in the execution
report), but they do include one check that the guard's self-report is
internally consistent with sys.version_info of the current interpreter.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from urban_history_transfer.environment import (  # noqa: E402
    REQUIRED_PYTHON_MAJOR,
    REQUIRED_PYTHON_MINOR,
    check_environment,
    require_environment,
)


def test_check_environment_matches_running_interpreter():
    result = check_environment()
    assert result.python_major == sys.version_info.major
    assert result.python_minor == sys.version_info.minor
    assert result.python_executable == sys.executable
    assert result.sys_prefix == sys.prefix


def test_check_environment_ok_iff_matches_policy():
    result = check_environment()
    expected_ok = (
        sys.version_info.major == REQUIRED_PYTHON_MAJOR
        and sys.version_info.minor == REQUIRED_PYTHON_MINOR
    )
    assert result.ok == expected_ok


def test_require_environment_raises_on_mismatch(monkeypatch):
    class FakeVersionInfo:
        major = 3
        minor = 99

    monkeypatch.setattr(sys, "version_info", FakeVersionInfo())
    try:
        import pytest as _pytest

        with _pytest.raises(RuntimeError):
            require_environment()
    finally:
        pass


def test_require_environment_succeeds_when_version_matches(monkeypatch):
    class FakeVersionInfo:
        major = REQUIRED_PYTHON_MAJOR
        minor = REQUIRED_PYTHON_MINOR

    monkeypatch.setattr(sys, "version_info", FakeVersionInfo())
    result = require_environment()
    assert result.ok is True


def test_message_mentions_conda_run_on_mismatch(monkeypatch):
    class FakeVersionInfo:
        major = 3
        minor = 8

    monkeypatch.setattr(sys, "version_info", FakeVersionInfo())
    result = check_environment()
    assert "conda run -n py311" in result.message
