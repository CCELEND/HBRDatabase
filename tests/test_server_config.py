# -*- coding: utf-8 -*-
import pytest

import 更新.server_config as server_config


def test_http_does_not_require_ca(monkeypatch):
    monkeypatch.setattr(server_config, "SCHEME", "http")
    assert server_config.verify() is True


def test_https_with_ca_uses_ca(monkeypatch, tmp_path):
    ca = tmp_path / "server_ca.crt"
    ca.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(server_config, "SCHEME", "https")
    monkeypatch.setattr(server_config, "CA_FILE", str(ca))
    assert server_config.verify() == str(ca)


def test_https_without_ca_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(server_config, "SCHEME", "https")
    monkeypatch.setattr(server_config, "CA_FILE", str(tmp_path / "missing.crt"))
    with pytest.raises(server_config.TLSConfigurationError):
        server_config.verify()
