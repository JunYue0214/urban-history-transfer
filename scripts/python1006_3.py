"""Execution 1006-3: bounded public-source metadata audit, never a data downloader.

Run with ``conda run -n py311 python scripts/python1006_3.py --refresh-sources``.
The opt-in refresh reads public documentation, repository inventories and at most
64 KiB of one TIFF header. It performs no raster aggregation or model fitting.
Existing audit outputs are never overwritten; use a fresh --output-dir to rerun.
"""

from __future__ import annotations

import argparse
import base64
import calendar
import csv
import hashlib
import json
import shutil
import struct
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from python1006_2 import parse_date_from_name, sha256_file

ROOT = Path(__file__).resolve().parent.parent
RUN_ID = "1006-3"
TPDC_ID = "2f302c7f-00bc-4ace-af30-5fa9277ed16e"
TPDC = "https://data.tpdc.ac.cn"
AUTHOR_REPO = "https://api.github.com/repos/Xiang-junhao/Gapless-Daily-Mean-LST-GEE"
FROZEN = {
    "results/1005-9/gate2_decision.json": "aa55dd87e3dfc9d17db9aab9f68113ca8779b191c49f6771fd8b5df25f4e00c4",
    "results/1006-1/gate2_negative_result_freeze.md": "1fa60afd9583e7846e36806823ff6f18b9c97d4b05f8b53a51c9d5332c4c6b60",
}


def expected_dates(year: int) -> set[date]:
    """Gregorian calendar including leap days, independent of file bounds."""
    return {
        date(year, 1, 1) + timedelta(days=i)
        for i in range(366 if calendar.isleap(year) else 365)
    }


def calendar_audit(year: int, files: list[dict]) -> dict:
    """Validate actual dated members, names, bytes and full annual coverage."""
    parsed = [parse_date_from_name(f["name"]) for f in files]
    counts = Counter(d for d in parsed if d is not None)
    expected = expected_dates(year)
    actual = set(counts)
    malformed = [f["name"] for f, d in zip(files, parsed) if d is None]
    wrong_names = [
        f["name"] for f, d in zip(files, parsed)
        if d is not None and f["name"] != d.strftime("%Y_%m_%d_DMLST.tif")
    ]
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    duplicate = sorted(d for d, count in counts.items() if count > 1)
    return {
        "year": year,
        "expected_days": len(expected),
        "listed_files": len(files),
        "unique_dates": len(actual),
        "first_date": min(actual).isoformat() if actual else None,
        "last_date": max(actual).isoformat() if actual else None,
        "leap_day_present": date(year, 2, 29) in actual if calendar.isleap(year) else None,
        "missing_dates": [d.isoformat() for d in missing],
        "unexpected_dates": [d.isoformat() for d in extra],
        "duplicate_dates": [d.isoformat() for d in duplicate],
        "malformed_names": malformed,
        "wrong_canonical_names": wrong_names,
        "bytes": sum(int(f["size"]) for f in files),
        "complete_calendar": not (missing or extra or duplicate or malformed or wrong_names)
        and len(files) == len(expected),
    }


def tiff_header(blob: bytes) -> dict:
    """Decode only header tags; never interpret downloaded bytes as pixel data."""
    if blob[:2] not in (b"II", b"MM"):
        raise ValueError("Public endpoint did not return TIFF bytes")
    endian = "<" if blob[:2] == b"II" else ">"
    magic, offset = struct.unpack_from(endian + "HI", blob, 2)
    if magic != 42:
        raise ValueError("Expected classic TIFF header")
    count = struct.unpack_from(endian + "H", blob, offset)[0]
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8}
    selected = {256, 257, 258, 259, 277, 322, 323, 339, 33550, 33922, 34735, 34736, 34737, 42112, 42113}
    tags = {}
    for i in range(count):
        at = offset + 2 + i * 12
        tag, kind, n, ptr = struct.unpack_from(endian + "HHII", blob, at)
        if tag not in selected:
            continue
        size = sizes[kind] * n
        start = at + 8 if size <= 4 else ptr
        data = blob[start:start + size]
        if len(data) != size:
            raise ValueError(f"Header prefix insufficient for tag {tag}")
        if kind == 2:
            value = data.decode("ascii").rstrip("\x00")
        elif kind in (3, 4, 12):
            value = list(struct.unpack(endian + str(n) + {3: "H", 4: "I", 12: "d"}[kind], data))
        else:
            value = data.hex()
        tags[str(tag)] = value
    return {"bytes_inspected": len(blob), "classic_tiff_magic": magic, "tags": tags}


class MetadataReader:
    """Bounded HTTP reader; credentials and research-data bodies are not persisted."""

    def __init__(self):
        self.session = requests.Session()
        # Direct reads avoid Nature's cookie/proxy redirect; no global proxy changes.
        self.session.trust_env = False
        self.session.headers["User-Agent"] = "urban-history-transfer/1006-3-metadata-audit"
        self.observations = []

    def read(self, url: str, *, method: str = "GET", payload=None, header_only=False) -> bytes:
        limit = 65536 if header_only else 6 * 1024 * 1024
        headers = {"Range": "bytes=0-65535"} if header_only else {}
        with self.session.request(
            method, url, json=payload, headers=headers, stream=True, timeout=(15, 40)
        ) as response:
            response.raise_for_status()
            body = response.raw.read(limit if header_only else limit + 1, decode_content=True)
            if len(body) > limit:
                raise ValueError("Metadata request exceeded size cap")
            self.observations.append({
                "method": method, "url": url, "final_url": response.url,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "advertised_content_length": response.headers.get("Content-Length"),
                "content_range": response.headers.get("Content-Range"),
                "bytes_read": len(body), "prefix_only": header_only,
                "sha256_of_bytes_read": hashlib.sha256(body).hexdigest(),
            })
        return body

    def json(self, url: str, **kwargs) -> dict:
        return json.loads(self.read(url, **kwargs))


def run(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a fresh output directory; provenance outputs are immutable")
    frozen = {p: sha256_file(ROOT / p) for p in FROZEN}
    if frozen != FROZEN:
        raise ValueError("Frozen Gate 2 artifacts do not match handoff hashes")

    reader = MetadataReader()
    product = reader.json(
        TPDC + "/view/metadataView/detail/", method="POST",
        payload={"metadataId": TPDC_ID, "userId": ""},
    )["context"]
    roots = reader.json(TPDC + f"/file/file/getRootFileDataList?metadataId={TPDC_ID}")["data"]
    roots = sorted(roots, key=lambda f: int(f["name"]))
    if [int(f["name"]) for f in roots] != list(range(2003, 2024)):
        raise ValueError("Expected exactly 2003-2023 year directories")
    rows, years = [], []
    sample_id = None
    for directory in roots:
        year = int(directory["name"])
        files = reader.json(TPDC + "/file/file/getFileDataList?parentId=" + directory["id"])["data"]
        audit = calendar_audit(year, files)
        audit["directory_reported_bytes"] = int(directory["size"])
        audit["directory_size_matches_members"] = audit["bytes"] == int(directory["size"])
        years.append(audit)
        for f in sorted(files, key=lambda f: f["name"]):
            d = parse_date_from_name(f["name"])
            rows.append({"date": d.isoformat() if d else "", "name": f["name"],
                         "file_id": f["id"], "bytes": int(f["size"]), "year": year})
            if year == 2018 and sample_id is None:
                sample_id = f["id"]
        print(f"{year}: {audit['listed_files']} files; calendar={audit['complete_calendar']}", flush=True)

    header = tiff_header(reader.read(
        TPDC + f"/file/file/batchDownloadByFileId?fileId={sample_id}",
        method="POST", payload={"noToken": True}, header_only=True,
    ))
    header["representative_file_id"] = sample_id
    header["representative_name"] = next(r["name"] for r in rows if r["file_id"] == sample_id)
    app = reader.read(TPDC + "/static/js/app.6e057abc.js").decode("utf-8")
    snippets = {}
    for key, marker in {
        "license_code_mapping": 'license:function(){return[',
        "open_access_policy_mapping": 'policy:function(){return[',
        "login_free_ftp_route": 'this.getFtpInfo("/ftp/createNoLoginDownloadFtpUser',
        "ftp_size_guidance": 'ftpTips:"',
    }.items():
        start = app.index(marker)
        snippets[key] = app[start:start + (1350 if key.endswith("mapping") else 850)]
    zenodo = reader.json("https://zenodo.org/api/records/17778992")
    author_tree = reader.json(AUTHOR_REPO + "/git/trees/main?recursive=1")
    author_readme = reader.json(AUTHOR_REPO + "/contents/README.md")
    readme_text = base64.b64decode(author_readme["content"]).decode("utf-8")

    sample = json.loads((ROOT / "results/python1006_2/python1006_2_summary.json").read_text(encoding="utf-8"))
    meta_fields = ("id", "title", "titleEn", "description", "instructions", "useTerms", "east", "west",
                   "south", "north", "startTime", "endTime", "fileSize", "projection", "doi", "cstr",
                   "license", "spatialResolution", "temporalResolution", "shareType", "sharePolicy", "status",
                   "tsUpdated", "tsPublish")
    tpdc_metadata = {k: product["metadataVO"].get(k) for k in meta_fields}
    target = [y for y in years if 2018 <= y["year"] <= 2023]
    total_bytes, target_bytes = sum(y["bytes"] for y in years), sum(y["bytes"] for y in target)
    height, width = header["tags"]["257"][0], header["tags"]["256"][0]
    pixel_count = height * width
    summary = {
        "execution_id": RUN_ID, "calendars": years,
        "full_period": {"listed_files": sum(y["listed_files"] for y in years), "bytes": total_bytes},
        "target_period": {"listed_files": sum(y["listed_files"] for y in target), "bytes": target_bytes,
                          "decimal_gb": target_bytes / 1e9, "gib": target_bytes / 2**30},
        "all_calendars_complete": all(y["complete_calendar"] for y in years),
        "all_directory_sizes_match": all(y["directory_size_matches_members"] for y in years),
        "metadata_size_matches_inventory": total_bytes == int(tpdc_metadata["fileSize"]),
        "sample_archive_prior_execution": sample["archive"],
        "hardware_scenarios": {
            "drive_free_bytes_at_audit": {drive: shutil.disk_usage(drive).free for drive in ("C:/", "D:/")},
            "largest_single_year_bytes": max(y["bytes"] for y in target),
            "native_pixels_per_raster": pixel_count,
            "int16_single_full_raster_bytes": pixel_count * 2,
            "int16_target_full_stack_bytes": pixel_count * 2 * sum(y["listed_files"] for y in target),
            "city_day_rows_upper_bound": 10915 * sum(y["listed_files"] for y in target),
            "city_day_three_numeric_fields_bytes": 10915 * sum(y["listed_files"] for y in target) * 3 * 8,
            "transfer_hours_at_MiB_per_second": {
                str(rate): target_bytes / (rate * 2**20) / 3600 for rate in (1, 5, 10, 25)
            },
            "note": "Storage/throughput arithmetic only; not a benchmark or a RAM guarantee.",
        },
        "frozen_hashes_verified": frozen,
        "gate2b_run": False, "full_raster_downloads": 0,
        "inventory_verification_level": "PUBLIC_FILE_METADATA; payload checksums not yet verified",
    }
    evidence = {
        "execution_id": RUN_ID, "tpdc_metadata": tpdc_metadata,
        "tpdc_english_documentation": product["metadataWordVO"],
        "tpdc_article_references": product["literatureVOList"],
        "tpdc_ui_public_snippets": snippets, "representative_full_source_tiff_header": header,
        "zenodo": {"doi": zenodo.get("doi"), "metadata": zenodo["metadata"], "files": zenodo["files"]},
        "author_repository_tree": author_tree,
        "author_readme_blob_sha": author_readme["sha"], "author_readme_text": readme_text,
        "http_observations": reader.observations,
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, obj in (("inventory_audit.json", summary), ("source_evidence.json", evidence)):
        (output / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "daily_file_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["date", "name", "file_id", "bytes", "year"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"full_files": summary["full_period"]["listed_files"],
                      "target_files": summary["target_period"]["listed_files"], "target_bytes": target_bytes,
                      "complete": summary["all_calendars_complete"]}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh-sources", action="store_true", help="opt in to bounded public metadata reads")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/1006-3")
    args = parser.parse_args()
    if not args.refresh_sources:
        parser.error("No network reads without --refresh-sources")
    run(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
