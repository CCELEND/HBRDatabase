# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path

import pytest

from 更新 import download_utils


class FakeResponse:
    def __init__(self, data: bytes, status_code: int = 200):
        self._data = data
        self.status_code = status_code
        self.headers = {"content-length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_content(self, chunk_size=8192):
        for start in range(0, len(self._data), chunk_size):
            yield self._data[start:start + chunk_size]

    def json(self):
        return {"error": "bad request"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_download_writes_verified_file_atomically(tmp_path, monkeypatch):
    data = b"new content"
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(data))

    target = download_utils.download_file(
        "https://example.test",
        "./目录/a.bin",
        base_dir=str(tmp_path),
        expected_hash=_sha(data),
        require_hash=True,
    )

    assert Path(target).read_bytes() == data
    assert not list(tmp_path.rglob(".hbr-download-*.part"))


def test_hash_mismatch_keeps_old_file(tmp_path, monkeypatch):
    old = tmp_path / "目录" / "a.bin"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"old content")
    data = b"new content"
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(data))

    with pytest.raises(download_utils.DownloadError):
        download_utils.download_file(
            "https://example.test",
            "./目录/a.bin",
            base_dir=str(tmp_path),
            expected_hash="0" * 64,
            require_hash=True,
        )

    assert old.read_bytes() == b"old content"
    assert not list(tmp_path.rglob(".hbr-download-*.part"))


def test_missing_hash_is_rejected_before_network(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: called.append(1))

    with pytest.raises(download_utils.DownloadError):
        download_utils.download_file(
            "https://example.test",
            "./a.bin",
            base_dir=str(tmp_path),
            require_hash=True,
        )
    assert not called


def test_path_traversal_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse(b"x"))
    with pytest.raises(ValueError):
        download_utils.download_file(
            "https://example.test",
            "../../outside.bin",
            base_dir=str(tmp_path),
        )


def test_expected_hash_lookup_accepts_normalized_paths():
    hashes = {
        "./工具/GetEntriesGUILocal/config.ini": "a" * 64,
    }
    assert download_utils.expected_hash_for(
        hashes, "./工具/GetEntriesGUILocal/config.ini") == "a" * 64
    assert download_utils.expected_hash_for(hashes, "./不存在") is None
