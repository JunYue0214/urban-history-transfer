"""Download helper for the Gate 2 thermal-response dataset (execution 1005-6).

THIS SCRIPT IS FOR HUMAN-OPERATED USE ONLY. Claude Code is not authorized
to run it against any real research-data URL. It was tested only against
local loopback HTTP servers serving synthetic bytes.

Importing this module has no side effects. Nothing runs unless `main()` is
invoked from the command line.

Design:
- the source URL is a REQUIRED explicit argument. No file URL is hard-coded,
  because the exact file listing must first be confirmed by the human
  operator on the dataset landing page (see results/1005-6/download_plan.md);
- candidate dataset identities are exposed as PROVENANCE METADATA only, each
  with an explicit verification status (nothing here is a trusted fact);
- a non-loopback URL is refused unless --confirm-human-operator is passed;
- the original filename from the URL is preserved; existing files are never
  overwritten;
- resumable via HTTP Range when a ".part" file exists; retries with backoff
  on transient errors; fails clearly on HTTP errors;
- optional bearer token is read from a named environment variable and is
  stripped on cross-host redirects (never written to disk or logs);
- proxy settings come only from the session variables HTTP_PROXY /
  HTTPS_PROXY (never written to disk or global config);
- a JSON log record (timestamp, URL, size, SHA-256) is written next to the
  file; format verification is delegated to scripts/verify_thermal_response.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Candidate dataset identities for provenance logging only. "status" records
# how well the identity was verified in execution 1005-6 (web metadata only,
# WebFetch was blocked, so landing pages were NOT read directly).
CANDIDATE_DATASETS = {
    "yceo_suhi_v4": {
        "name": "Yale Center for Earth Observation (YCEO) Surface Urban Heat Islands, Version 4, 2003-2018",
        "doi": "10.7927/S5M5-ZK14",
        "landing_page": "https://sedac.ciesin.columbia.edu/data/set/sdei-yceo-sfc-uhi-v4/data-download",
        "status": "identity corroborated by several search results; file schema NOT verified",
    },
    "yang2024_uhii": {
        "name": "Global Urban Heat Island Intensity Dataset (Yang, Xu, Chakraborty et al. 2024)",
        "doi": "10.6084/m9.figshare.24821538",
        "landing_page": "https://doi.org/10.6084/m9.figshare.24821538",
        "status": "DOI corroborated; Figshare record is a README plus links to Baidu/Google Drive; "
                  "city-level file format NOT verified",
    },
}
CHUNK = 1024 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class DownloadError(RuntimeError):
    pass


def filename_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    name = Path(urllib.parse.unquote(path)).name
    if not name:
        raise DownloadError(f"Cannot derive a filename from URL: {url}")
    return name


def is_loopback(url: str) -> bool:
    return (urllib.parse.urlparse(url).hostname or "") in LOOPBACK_HOSTS


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


class _StripAuthOnCrossHostRedirect(urllib.request.HTTPRedirectHandler):
    """Forward the Authorization header only to the original host:port."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            if urllib.parse.urlparse(newurl).netloc != urllib.parse.urlparse(req.full_url).netloc:
                new.headers.pop("Authorization", None)
                new.unredirected_hdrs.pop("Authorization", None)
        return new


def _open(url: str, start: int, timeout: float, token: str | None):
    req = urllib.request.Request(url)
    if start > 0:
        req.add_header("Range", f"bytes={start}-")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    opener = urllib.request.build_opener(_StripAuthOnCrossHostRedirect)
    return opener.open(req, timeout=timeout)


def download(url: str, dest_dir: Path, retries: int = 3, backoff: float = 2.0,
             timeout: float = 60.0, token: str | None = None,
             dataset_key: str | None = None) -> dict:
    """Download `url` into `dest_dir`, preserving the original filename.

    Returns a log record. Raises DownloadError on failure.
    """
    if dataset_key is not None and dataset_key not in CANDIDATE_DATASETS:
        raise DownloadError(f"Unknown dataset key {dataset_key!r}; choose from {sorted(CANDIDATE_DATASETS)}")
    name = filename_from_url(url)
    dest_dir.mkdir(parents=True, exist_ok=True)
    final_path = dest_dir / name
    part_path = dest_dir / (name + ".part")
    if final_path.exists():
        raise DownloadError(
            f"Refusing to overwrite existing file: {final_path} "
            "(raw research files are never modified; remove it manually if intended)."
        )

    started = datetime.now(timezone.utc).isoformat()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            start = part_path.stat().st_size if part_path.exists() else 0
            with _open(url, start, timeout, token) as resp:
                status = getattr(resp, "status", resp.getcode())
                if status not in (200, 206):
                    raise DownloadError(f"Unexpected HTTP status {status} for {url}")
                mode = "ab" if (start > 0 and status == 206) else "wb"
                with part_path.open(mode) as out:
                    for block in iter(lambda: resp.read(CHUNK), b""):
                        out.write(block)
            part_path.replace(final_path)
            record = {
                "source_url": url,
                "dataset_key": dataset_key,
                "dataset_identity": CANDIDATE_DATASETS.get(dataset_key) if dataset_key else None,
                "filename": name,
                "path": str(final_path),
                "bytes": final_path.stat().st_size,
                "sha256": sha256_of(final_path),
                "started_at": started,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "attempts": attempt,
                "authenticated": bool(token),
            }
            log_path = dest_dir / (name + ".download_log.json")
            log_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            return record
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500 and exc.code != 429:
                raise DownloadError(f"HTTP {exc.code} {exc.reason} for {url}") from exc
            last_error = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise DownloadError(f"Download failed after {retries} attempts: {last_error}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--url", required=True, help="Exact file URL confirmed on the dataset landing page.")
    p.add_argument("--dest", required=True, help="Destination directory (e.g. data/raw/thermal_response).")
    p.add_argument("--dataset-key", choices=sorted(CANDIDATE_DATASETS), default=None,
                   help="Provenance label recorded in the download log.")
    p.add_argument("--auth-env", default=None,
                   help="Name of an environment variable holding a bearer token (e.g. an Earthdata token).")
    p.add_argument("--confirm-human-operator", action="store_true",
                   help="Required for any non-loopback URL: asserts a human is running this deliberately.")
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--timeout", type=float, default=60.0)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not is_loopback(args.url) and not args.confirm_human_operator:
        print("REFUSED: non-loopback URL requires --confirm-human-operator "
              "(real research-data transfers are human-operated only).", file=sys.stderr)
        return 2
    token = os.environ.get(args.auth_env) if args.auth_env else None
    if args.auth_env and not token:
        print(f"REFUSED: environment variable {args.auth_env} is not set.", file=sys.stderr)
        return 2
    try:
        record = download(args.url, Path(args.dest), retries=args.retries, timeout=args.timeout,
                          token=token, dataset_key=args.dataset_key)
    except DownloadError as exc:
        print(f"DOWNLOAD FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, indent=2))
    print("Next: run scripts/verify_thermal_response.py on the downloaded file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
