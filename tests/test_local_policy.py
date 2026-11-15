# -*- coding: utf-8 -*-
from 更新.local_policy import (
    filter_local_only_files,
    filter_local_only_hashes,
    is_local_only_path,
)


def test_local_only_config_and_runtime_dirs():
    assert is_local_only_path("./工具/GetEntriesGUILocal/config.ini")
    assert is_local_only_path(r".\工具\GetEntriesGUILocal\config.ini")
    assert is_local_only_path("./工具/HBR伤害模拟/2.1.0_0/manifest.json")
    assert is_local_only_path("./工具/chrome/chrome-win64/chrome.exe")
    assert is_local_only_path("./音乐/下载/a.mp3")
    assert is_local_only_path("./日志/app.log")
    assert is_local_only_path("./关于/server_file_hashes.json")
    assert is_local_only_path("./更新/.hbr-download-abc.part")


def test_distributable_hbr_simulation_files_are_kept():
    assert not is_local_only_path("./工具/HBR伤害模拟/Load.py")
    assert not is_local_only_path("./工具/HBR伤害模拟/2.1.0_0.zip")


def test_filter_helpers_keep_order_and_strip_local_entries():
    files = [
        "./角色/31A/Karen/SSRstyles.json",
        "./工具/GetEntriesGUILocal/config.ini",
        "./工具/排轴/axle_calc.py",
    ]
    assert filter_local_only_files(files) == [
        "./角色/31A/Karen/SSRstyles.json",
        "./工具/排轴/axle_calc.py",
    ]

    hashes = {
        "./角色/31A/Karen/SSRstyles.json": "a" * 64,
        "./工具/GetEntriesGUILocal/config.ini": "b" * 64,
    }
    assert filter_local_only_hashes(hashes) == {
        "./角色/31A/Karen/SSRstyles.json": "a" * 64,
    }
