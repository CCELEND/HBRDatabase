# -*- coding: utf-8 -*-
"""Build a staged source/data payload and deploy it atomically per file.

Usage (run from the repository root):
    python scripts/deploy_sync.py --host 47.96.235.36 --dry-run
    python scripts/deploy_sync.py --host 47.96.235.36

The default payload contains source/config/data text files only. Add
``--include-assets`` when image/background assets really changed.

The upload is extracted in a staging directory first. Each file is then moved
into the target with ``os.replace`` so a network failure cannot leave a
half-written file. The existing server file watcher updates its hash manifest
after the files settle.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from 更新.local_policy import HASH_SKIP_DIRS, is_local_only_path  # noqa: E402

TEXT_EXTENSIONS = {
    ".py", ".pyw", ".json", ".qss", ".txt", ".bat", ".cfg", ".md",
    ".crt", ".js", ".css", ".html", ".ico", ".svg",
}

DEPLOY_SKIP_DIRS = {
    "tests",
    "scripts",
    ".pytest_cache",
    ".mimocode",
    ".deploy",
    ".idea",
}

# These are runtime/download/working copies even in "assets" mode.
DEPLOY_SKIP_PREFIXES = {
    "音乐/下载",
    "工具/chrome",
    "工具/HBR伤害模拟",
    "venv",
    ".venv",
    "node_modules",
}

REMOTE_APPLY = r'''
import os
import shutil
import sys
import tarfile

stage = os.environ["HBR_STAGE"]
target = os.path.abspath(os.environ["HBR_TARGET"])
archive = os.path.join(stage, "payload.tar.gz")
extract_dir = os.path.join(stage, "payload")
os.makedirs(extract_dir, exist_ok=True)

with tarfile.open(archive, "r:gz") as tf:
    members = tf.getmembers()
    for member in members:
        name = member.name.replace("\\", "/")
        parts = [p for p in name.split("/") if p not in ("", ".")]
        if name.startswith("/") or ".." in parts:
            raise RuntimeError("unsafe tar member: %s" % name)
        if member.issym() or member.islnk():
            raise RuntimeError("links are not allowed: %s" % name)
    tf.extractall(extract_dir)

count = 0
for dirpath, _, filenames in os.walk(extract_dir):
    for filename in filenames:
        source = os.path.join(dirpath, filename)
        relative = os.path.relpath(source, extract_dir)
        destination = os.path.abspath(os.path.join(target, relative))
        if destination != target and not destination.startswith(target + os.sep):
            raise RuntimeError("target path escapes deployment root: %s" % relative)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        os.replace(source, destination)
        count += 1

print("applied %d files" % count)
shutil.rmtree(stage)
'''


def _should_skip_relative(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in HASH_SKIP_DIRS or part in DEPLOY_SKIP_DIRS for part in parts):
        return True
    for prefix in DEPLOY_SKIP_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def collect_files(root: Path, include_assets: bool) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames
            if not _should_skip_relative(
                os.path.relpath(os.path.join(dirpath, name), root))
        ]
        for filename in filenames:
            path = Path(dirpath) / filename
            relative = os.path.relpath(path, root).replace("\\", "/")
            if _should_skip_relative(relative):
                continue
            if is_local_only_path(relative):
                continue
            if not include_assets and path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            files.append(path)
    return sorted(files)


def build_archive(root: Path, files: list[Path], output: Path) -> None:
    with tarfile.open(output, "w:gz") as archive:
        for path in files:
            relative = os.path.relpath(path, root).replace("\\", "/")
            archive.add(path, arcname=relative)


def run(command: list[str], *, input_text: str | None = None) -> None:
    print("+", " ".join(shlex.quote(str(part)) for part in command))
    subprocess.run(command, input=input_text, text=True, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("HBR_DEPLOY_HOST", ""),
                        help="server IP/hostname (or HBR_DEPLOY_HOST)")
    parser.add_argument("--user", default=os.getenv("HBR_DEPLOY_USER", "root"))
    parser.add_argument("--key", default=os.getenv(
        "HBR_DEPLOY_KEY", str(ROOT.parent / "HBRDatabase.pem")))
    parser.add_argument("--remote", default=os.getenv(
        "HBR_DEPLOY_REMOTE", "/root/HBRDatabaseServer/HBRDatabase"))
    parser.add_argument("--include-assets", action="store_true",
                        help="also upload non-text assets (may be large)")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and report the payload without connecting")
    args = parser.parse_args(argv)

    if not args.host:
        parser.error("--host is required (or set HBR_DEPLOY_HOST)")
    key = Path(args.key).expanduser().resolve()
    if not key.is_file():
        parser.error("SSH key not found: %s" % key)

    files = collect_files(ROOT, args.include_assets)
    print("payload files: %d" % len(files))
    print("payload mode: %s" % ("assets" if args.include_assets else "text/data"))
    for path in files[:20]:
        print("  ", os.path.relpath(path, ROOT))
    if len(files) > 20:
        print("  ...")

    with tempfile.TemporaryDirectory(prefix="hbr-deploy-") as temp_dir:
        archive = Path(temp_dir) / "payload.tar.gz"
        build_archive(ROOT, files, archive)
        size_mb = archive.stat().st_size / 1024 / 1024
        print("archive: %.2f MB" % size_mb)
        if args.dry_run:
            print("dry-run: not uploading")
            return 0

        stamp = time.strftime("%Y%m%d-%H%M%S")
        remote_stage = "/root/HBRDatabaseServer/.deploy-%s" % stamp
        ssh_base = [
            "ssh", "-i", str(key),
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=15",
            "%s@%s" % (args.user, args.host),
        ]
        remote = "%s@%s" % (args.user, args.host)

        run(ssh_base + ["mkdir -p %s" % shlex.quote(remote_stage)])
        run([
            "scp", "-i", str(key),
            "-o", "StrictHostKeyChecking=accept-new",
            str(archive), "%s:%s/payload.tar.gz" % (remote, remote_stage),
        ])
        run(
            ssh_base + [
                "HBR_STAGE=%s HBR_TARGET=%s python3 -"
                % (shlex.quote(remote_stage), shlex.quote(args.remote))
            ],
            input_text=REMOTE_APPLY,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
