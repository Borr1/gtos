#!/usr/bin/env python3
"""Session CK copy-back A/B driver; never moves HEAD and never invokes checkout.

The ZERO side is produced by copying each changed path's blob from ``BASE`` into
the working tree. HEAD bytes are first copied to an isolated temporary directory
and are restored in ``finally``; every restored SHA-256 is verified before the
AFTER capture begins. Files absent at BASE are removed only by exact validated
path and tested separately after restoration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]


def _run(*args: str, check: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=REPO, capture_output=True, text=text, check=False)
    if check and result.returncode != 0:
        stderr = result.stderr if text else result.stderr.decode(errors="replace")
        raise RuntimeError(f"{' '.join(args)} -> {result.returncode}\n{stderr[-3000:]}")
    return result


def _safe_path(relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise RuntimeError(f"unsafe changed path: {relative!r}")
    path = REPO / rel
    if not path.resolve(strict=False).is_relative_to(REPO.resolve()):
        raise RuntimeError(f"changed path escapes repo: {relative!r}")
    return path


def _digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exists_at(revision: str, relative: str) -> bool:
    return _run("git", "cat-file", "-e", f"{revision}:{relative}", check=False).returncode == 0


def _blob_at(revision: str, relative: str) -> bytes:
    result = _run("git", "show", f"{revision}:{relative}", text=False)
    return bytes(result.stdout)


def _changed_paths(base: str) -> list[str]:
    output = _run("git", "diff", "--name-only", f"{base}...HEAD").stdout
    paths = [line.strip() for line in output.splitlines() if line.strip()]
    for relative in paths:
        _safe_path(relative)
    return paths


def _write_exact(path: Path, payload: bytes) -> None:
    if path.exists() and not path.is_file():
        raise RuntimeError(f"refusing to replace non-file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _remove_exact(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        raise RuntimeError(f"refusing to remove non-file: {path}")


def _capture(scope: Path, output: Path) -> None:
    result = _run(
        sys.executable,
        "scripts/pytest_failset.py",
        "capture",
        "--scope",
        str(scope),
        "-o",
        str(output),
        check=False,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if not output.is_file():
        raise RuntimeError(f"capture did not write {output}")
    record = json.loads(output.read_text())
    if not record.get("usable_as_baseline", True):
        raise RuntimeError(f"unusable capture {output}: {record.get('unusable_reasons')}")


def _shared_scope(scope: Path, base: str, output: Path) -> list[str]:
    payload = json.loads(scope.read_text())
    kept: list[str] = []
    dropped: list[str] = []
    for item in payload.get("pytest_args", []):
        (kept if _exists_at(base, item) else dropped).append(item)
    if not kept:
        raise RuntimeError("shared ZERO/HEAD scope is empty")
    payload["pytest_args"] = kept
    payload["dropped_absent_at_base"] = dropped
    output.write_text(json.dumps(payload, indent=1) + "\n")
    return dropped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--new-tests", default="")
    ns = parser.parse_args()

    paths = _changed_paths(ns.base)
    if not paths:
        raise SystemExit("no changed paths against ZERO base")
    original = {relative: _digest(_safe_path(relative)) for relative in paths}
    if any(value is None for value in original.values()):
        missing = [relative for relative, value in original.items() if value is None]
        raise SystemExit(f"HEAD changed paths absent before copy-back: {missing}")

    temp_root = Path(tempfile.mkdtemp(prefix="ck-copyback-ab-"))
    try:
        for relative in paths:
            saved = temp_root / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_safe_path(relative), saved)

        shared = Path(ns.scope).with_suffix(".shared.json")
        dropped = _shared_scope(Path(ns.scope), ns.base, shared)
        print(f"[ck-ab] {len(paths)} changed paths; {len(dropped)} scope paths absent at ZERO")

        try:
            for relative in paths:
                path = _safe_path(relative)
                if _exists_at(ns.base, relative):
                    _write_exact(path, _blob_at(ns.base, relative))
                else:
                    _remove_exact(path)
            _capture(shared, Path(ns.before))
        finally:
            for relative in paths:
                _write_exact(_safe_path(relative), (temp_root / relative).read_bytes())

        drifted = [
            relative for relative in paths
            if _digest(_safe_path(relative)) != original[relative]
        ]
        if drifted:
            raise SystemExit(f"HEAD byte restore failed for {drifted[:10]}")
        print("[ck-ab] HEAD restored byte-for-byte; checkout was never invoked")
        _capture(shared, Path(ns.after))

        new_tests = [item.strip() for item in ns.new_tests.split(",") if item.strip()]
        if new_tests:
            result = _run(
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--continue-on-collection-errors",
                *new_tests,
                check=False,
            )
            proof = Path(ns.after).with_suffix(".newtests.txt")
            proof.write_text(result.stdout + "\n" + result.stderr)
            if result.returncode != 0:
                raise SystemExit(f"new tests failed; see {proof}")
            print(f"[ck-ab] {len(new_tests)} HEAD-only test file(s) passed")
    finally:
        # Explicit mkdtemp child only. Never targets a workspace path.
        shutil.rmtree(temp_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
