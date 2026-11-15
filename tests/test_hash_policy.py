# -*- coding: utf-8 -*-
from 更新.hash import calculate_file_hashes


def test_hash_walk_skips_local_config_and_simulation_runtime(tmp_path, monkeypatch):
    (tmp_path / "工具" / "GetEntriesGUILocal").mkdir(parents=True)
    (tmp_path / "工具" / "GetEntriesGUILocal" / "config.ini").write_text(
        "[Count]\n", encoding="utf-8")
    (tmp_path / "角色").mkdir()
    normal = tmp_path / "角色" / "data.json"
    normal.write_text('{"ok": true}', encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    hashes = calculate_file_hashes("./", use_cache=False)

    assert "./角色/data.json" in hashes
    assert "./工具/GetEntriesGUILocal/config.ini" not in hashes
