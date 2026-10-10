"""Offline calendar safeguards against accepting sparse or duplicated data."""

from datetime import date, timedelta
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import python1006_3 as audit  # noqa: E402


def files_2020():
    return [
        {"name": (date(2020, 1, 1) + timedelta(days=i)).strftime("%Y_%m_%d_DMLST.tif"),
         "size": 100}
        for i in range(366)
    ]


@pytest.mark.parametrize("missing", ["2020_01_01", "2020_02_29", "2020_12_31"])
def test_missing_calendar_endpoints_or_leap_day_block(missing):
    files = files_2020()
    assert audit.calendar_audit(2020, files)["complete_calendar"]
    files = [f for f in files if not f["name"].startswith(missing)]
    result = audit.calendar_audit(2020, files)
    assert not result["complete_calendar"]
    assert result["missing_dates"] == [missing.replace("_", "-")]


def test_correct_count_and_bounds_cannot_hide_duplicate_and_gap():
    files = files_2020()
    files[100] = files[99].copy()
    result = audit.calendar_audit(2020, files)
    assert result["listed_files"] == 366
    assert result["first_date"] == "2020-01-01"
    assert result["last_date"] == "2020-12-31"
    assert not result["complete_calendar"]
    assert result["duplicate_dates"] == ["2020-04-09"]
    assert result["missing_dates"] == ["2020-04-10"]


def test_wrong_year_or_noncanonical_product_name_blocks():
    files = files_2020()
    files[10] = {"name": "2021_01_11_DMLST.tif", "size": 100}
    result = audit.calendar_audit(2020, files)
    assert not result["complete_calendar"]
    assert result["unexpected_dates"] == ["2021-01-11"]
    files[10] = {"name": "2020_01_11_OTHER.tif", "size": 100}
    result = audit.calendar_audit(2020, files)
    assert not result["complete_calendar"]
    assert result["wrong_canonical_names"] == ["2020_01_11_OTHER.tif"]
