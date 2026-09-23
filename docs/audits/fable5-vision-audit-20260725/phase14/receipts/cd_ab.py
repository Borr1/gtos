"""Session CD -- the scoped A/B, driven from Python and sha-verified both ways.

Why Python and not a shell loop: `zsh` does not word-split an unquoted variable,
so a file list passed through one reaches pytest as a single argument, the run
exits on a usage error, and BOTH captures come back empty while still looking
like a completed A/B. That is `IMPLEMENTATION_STATE.md` B2075 (AR section 8.9,
"reported the answer its author wanted"), and Session CB nearly repeated it.

Method, and the one thing it must get right:

1. record the sha256 of every file this session touched, at HEAD;
2. restore each to its state at BASE -- **deleting** the ones that do not exist
   there, because a new file left in place would run this session's tests
   against this session's code and call it a baseline;
3. capture the failure set;
4. restore HEAD, **verify every sha256 matches what was recorded in step 1**,
   and refuse to continue if one does not;
5. capture again and diff.

The new test file is captured SEPARATELY, because it does not exist at BASE and
a scope that contains it would show its whole contents as "new passes" while
telling you nothing about regression (Session BD's B2073).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]


def sh(*args: str, check: bool = True) -> str:
    out = subprocess.run(
        args, cwd=REPO, capture_output=True, text=True, check=False
    )
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> {out.returncode}\n{out.stderr[-2000:]}")
    return out.stdout


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def changed_paths(base: str) -> list[str]:
    text = sh("git", "diff", "--name-only", f"{base}...HEAD")
    return [line.strip() for line in text.splitlines() if line.strip()]


def exists_at(base: str, path: str) -> bool:
    out = subprocess.run(
        ["git", "cat-file", "-e", f"{base}:{path}"],
        cwd=REPO,
        capture_output=True,
    )
    return out.returncode == 0


def scope_without_new_files(scope: Path, base: str, out: Path) -> Path:
    """Drop test files that do not exist at BASE, and say which.

    A scope entry that is absent at BASE makes pytest exit on a usage error, so
    the BEFORE capture parses ZERO outcomes -- and an empty failure set reads
    exactly like a clean one. `pytest_failset` marks that capture
    `usable_as_baseline=false` and refuses to diff it, which is the only reason
    this was visible at all; the same shape is Session BD's B2073. Those files
    are captured separately by `--new-tests`, where "everything passed" means
    something.
    """

    import json

    payload = json.loads(scope.read_text())
    key = "pytest_args" if "pytest_args" in payload else "tests"
    kept, dropped = [], []
    for item in payload.get(key, []):
        (kept if exists_at(base, item) else dropped).append(item)
    payload[key] = kept
    payload["dropped_absent_at_base"] = dropped
    out.write_text(json.dumps(payload, indent=1))
    if dropped:
        print(f"[cd_ab] dropped {len(dropped)} scope file(s) absent at BASE: {dropped}")
    return out


def capture(scope: Path, out: Path, extra: list[str]) -> None:
    args = [
        sys.executable,
        "scripts/pytest_failset.py",
        "capture",
        "--scope",
        str(scope),
        "-o",
        str(out),
    ]
    if extra:
        args += ["--", *extra]
    subprocess.run(args, cwd=REPO, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--scope", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--new-tests", default="", help="comma-separated; captured apart")
    ns = ap.parse_args()

    paths = changed_paths(ns.base)
    head_digests = {p: digest(REPO / p) for p in paths}
    missing_at_base = [p for p in paths if not exists_at(ns.base, p)]
    print(f"[cd_ab] {len(paths)} changed path(s); {len(missing_at_base)} new at BASE")

    shared_scope = scope_without_new_files(
        Path(ns.scope), ns.base, Path(ns.scope).with_suffix(".shared.json")
    )

    # --- BEFORE ---------------------------------------------------------------
    for path in paths:
        if path in missing_at_base:
            (REPO / path).unlink(missing_ok=True)
        else:
            sh("git", "checkout", ns.base, "--", path)
    capture(shared_scope, Path(ns.before), [])

    # --- restore, and REFUSE if a byte moved ---------------------------------
    sh("git", "checkout", "HEAD", "--", ".")
    bad = [p for p in paths if digest(REPO / p) != head_digests[p]]
    if bad:
        raise SystemExit(
            "REFUSING to publish an A/B: the restore did not reproduce HEAD for "
            f"{len(bad)} path(s): {bad[:6]}"
        )
    print("[cd_ab] restore verified byte-for-byte on every changed path")

    # --- AFTER ----------------------------------------------------------------
    capture(shared_scope, Path(ns.after), [])

    new_tests = [t.strip() for t in ns.new_tests.split(",") if t.strip()]
    if new_tests:
        out = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--continue-on-collection-errors",
                *new_tests,
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        Path(ns.after).with_suffix(".newtests.txt").write_text(
            out.stdout[-4000:] + "\n" + out.stderr[-2000:]
        )
        print("[cd_ab] new-test file captured separately:", out.stdout.strip()[-200:])

    print(json.dumps({"changed": len(paths), "new_at_base": missing_at_base}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
