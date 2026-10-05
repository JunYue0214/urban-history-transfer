"""Tests for scripts/download_thermal_response.py and verify_thermal_response.py.

All tests use local loopback HTTP servers serving SYNTHETIC bytes. No real
research-data URL is ever contacted.
"""

from __future__ import annotations

import hashlib
import http.server
import importlib.util
import io
import json
import struct
import sys
import threading
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


dl = _load("download_thermal_response")
vf = _load("verify_thermal_response")

PAYLOAD = b"city_id,name,suhi\n1,Alpha,1.5\n2,Beta,2.5\n" * 50
SEEN_AUTH: list = []


class _Handler(http.server.BaseHTTPRequestHandler):
    redirect_to: str | None = None

    def log_message(self, *a):
        pass

    def do_GET(self):
        SEEN_AUTH.append((self.server.server_address[1], self.headers.get("Authorization")))
        if self.path.startswith("/missing"):
            self.send_error(404, "Not Found")
            return
        if self.path.startswith("/redirect") and self.server.redirect_to:
            self.send_response(302)
            self.send_header("Location", self.server.redirect_to)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            start = int(rng[6:].split("-")[0])
            body = PAYLOAD[start:]
            self.send_response(206)
        else:
            body = PAYLOAD
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _start():
    httpd = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    httpd.redirect_to = None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


@pytest.fixture()
def server():
    httpd = _start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _dbf(fields: list[str], n_records: int = 3) -> bytes:
    header = bytearray(32)
    header[0] = 0x03
    struct.pack_into("<I", header, 4, n_records)
    desc = b"".join(f.encode("latin-1").ljust(11, b"\x00") + b"N" + b"\x00" * 20 for f in fields)
    return bytes(header) + desc + b"\x0d"


def _zip_bytes(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for k, v in members.items():
            zf.writestr(k, v)
    return buf.getvalue()


def test_import_has_no_side_effects():
    assert callable(dl.main) and callable(vf.main)


def test_filename_from_url_preserves_original_name():
    assert dl.filename_from_url("https://example.org/a/b/My%20File.csv?x=1") == "My File.csv"


def test_filename_from_url_rejects_empty():
    with pytest.raises(dl.DownloadError):
        dl.filename_from_url("https://example.org/")


def test_download_roundtrip_and_sha(server, tmp_path):
    rec = dl.download(f"{server}/data/synthetic.csv", tmp_path, retries=1, dataset_key="yceo_suhi_v4")
    assert (tmp_path / "synthetic.csv").read_bytes() == PAYLOAD
    assert rec["sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
    assert rec["bytes"] == len(PAYLOAD)
    log = json.loads((tmp_path / "synthetic.csv.download_log.json").read_text(encoding="utf-8"))
    assert log["filename"] == "synthetic.csv" and log["dataset_key"] == "yceo_suhi_v4"
    assert log["started_at"] and log["completed_at"]


def test_download_fails_clearly_on_http_error(server, tmp_path):
    with pytest.raises(dl.DownloadError, match="404"):
        dl.download(f"{server}/missing/x.csv", tmp_path, retries=1)


def test_download_refuses_to_overwrite(server, tmp_path):
    (tmp_path / "synthetic.csv").write_bytes(b"existing")
    with pytest.raises(dl.DownloadError, match="overwrite"):
        dl.download(f"{server}/data/synthetic.csv", tmp_path, retries=1)
    assert (tmp_path / "synthetic.csv").read_bytes() == b"existing"


def test_download_resumes_partial_file(server, tmp_path):
    (tmp_path / "synthetic.csv.part").write_bytes(PAYLOAD[: len(PAYLOAD) // 2])
    dl.download(f"{server}/data/synthetic.csv", tmp_path, retries=1)
    assert (tmp_path / "synthetic.csv").read_bytes() == PAYLOAD


def test_unknown_dataset_key_rejected(server, tmp_path):
    with pytest.raises(dl.DownloadError, match="Unknown dataset key"):
        dl.download(f"{server}/data/x.csv", tmp_path, dataset_key="nope")


def test_candidate_identities_flag_verification_status():
    for meta in dl.CANDIDATE_DATASETS.values():
        assert meta["doi"] and meta["status"] and "NOT verified" in meta["status"]


def test_bearer_token_sent_to_origin_but_stripped_on_cross_host_redirect(tmp_path):
    origin, target = _start(), _start()
    try:
        origin.redirect_to = f"http://127.0.0.1:{target.server_address[1]}/final/synthetic.csv"
        SEEN_AUTH.clear()
        dl.download(f"http://127.0.0.1:{origin.server_address[1]}/redirect/synthetic.csv",
                    tmp_path, retries=1, token="SECRET")
        by_port = dict(SEEN_AUTH)
        assert by_port[origin.server_address[1]] == "Bearer SECRET"
        assert by_port[target.server_address[1]] is None
        log = (tmp_path / "synthetic.csv.download_log.json").read_text(encoding="utf-8")
        assert "SECRET" not in log
    finally:
        origin.shutdown()
        target.shutdown()


def test_cli_refuses_non_loopback_without_confirmation(tmp_path, capsys):
    rc = dl.main(["--url", "https://example.org/real/data.zip", "--dest", str(tmp_path)])
    assert rc == 2 and not list(tmp_path.iterdir())
    assert "REFUSED" in capsys.readouterr().err


def test_cli_loopback_download_works(server, tmp_path):
    assert dl.main(["--url", f"{server}/data/synthetic.csv", "--dest", str(tmp_path)]) == 0


def test_cli_refuses_missing_auth_env(server, tmp_path, monkeypatch):
    monkeypatch.delenv("NOPE_TOKEN", raising=False)
    assert dl.main(["--url", f"{server}/data/s.csv", "--dest", str(tmp_path), "--auth-env", "NOPE_TOKEN"]) == 2


def test_verify_ok_with_matching_sha_and_columns(tmp_path):
    f = tmp_path / "t.csv"
    f.write_bytes(PAYLOAD)
    rep = vf.verify(f, hashlib.sha256(PAYLOAD).hexdigest(), 10, ["city_id", "suhi"])
    assert rep["ok"] and rep["checks"]["required_columns"]


def test_verify_detects_sha_mismatch(tmp_path):
    f = tmp_path / "t.csv"
    f.write_bytes(PAYLOAD)
    rep = vf.verify(f, "0" * 64)
    assert not rep["ok"] and not rep["checks"]["sha256"]


def test_verify_detects_missing_file_and_missing_columns(tmp_path):
    assert not vf.verify(tmp_path / "nope.csv")["ok"]
    f = tmp_path / "t.csv"
    f.write_bytes(PAYLOAD)
    rep = vf.verify(f, required_columns=["not_a_column"])
    assert not rep["ok"] and not rep["checks"]["required_columns"]


def test_verify_detects_empty_csv(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_bytes(b"")
    assert not vf.verify(f, min_bytes=0)["ok"]


def test_dbf_fields_parses_synthetic_header():
    names, n = vf.dbf_fields(_dbf(["CLUSTER_ID", "ANN_NIGHT", "ANN_DAY"], n_records=7))
    assert names == ["CLUSTER_ID", "ANN_NIGHT", "ANN_DAY"] and n == 7


def test_verify_zipped_shapefile_ok_and_columns(tmp_path):
    z = tmp_path / "synthetic_clusters.zip"
    z.write_bytes(_zip_bytes({"a/c.shp": b"x", "a/c.shx": b"x", "a/c.dbf": _dbf(["ID", "SUHI_N"]), "a/c.prj": b"x"}))
    rep = vf.verify(z, required_columns=["ID", "SUHI_N"])
    assert rep["ok"] and rep["checks"]["zip_integrity"] and rep["checks"]["shapefile_members"]
    assert rep["columns"] == ["ID", "SUHI_N"] and rep["dbf_records"] == 3
    assert not vf.verify(z, required_columns=["MISSING"])["ok"]


def test_verify_zip_missing_sidecar_and_corrupt(tmp_path):
    z = tmp_path / "bad.zip"
    z.write_bytes(_zip_bytes({"c.shp": b"x", "c.dbf": _dbf(["ID"])}))
    rep = vf.verify(z)
    assert not rep["ok"] and not rep["checks"]["shapefile_members"]
    junk = tmp_path / "junk.zip"
    junk.write_bytes(b"this is not a zip")
    assert not vf.verify(junk)["checks"]["zip_integrity"]
