"""Verify that a staged checkpoint does not include live/runtime dirt.

The parallel-goal merge playbook requires scoped commits and explicitly forbids
staging broad live/runtime/shadow state. This script makes that rule executable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


BLOCKED_PREFIXES = (
    "shadow_logs/",
    "pipeline_state/",
    "data/ticks/",
    "logs/",
)
BLOCKED_EXACT = {
    ".context/LIVE_STATE.md",
    "heartbeat.json",
}


@dataclass(frozen=True)
class ScopeCheckResult:
    ok: bool
    checked_paths: tuple[str, ...]
    blocked_paths: tuple[str, ...]
    allowed_overrides: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checked_paths": list(self.checked_paths),
            "blocked_paths": list(self.blocked_paths),
            "allowed_overrides": list(self.allowed_overrides),
        }


def normalize_repo_path(path: str) -> str:
    normalized = str(PurePosixPath(path.replace("\\", "/")))
    return normalized.removeprefix("./")


def is_live_runtime_dirt(path: str) -> bool:
    normalized = normalize_repo_path(path)
    if normalized in BLOCKED_EXACT:
        return True
    return any(normalized.startswith(prefix) for prefix in BLOCKED_PREFIXES)


def verify_paths(paths: Iterable[str], *, allow: Iterable[str] = ()) -> ScopeCheckResult:
    checked = tuple(normalize_repo_path(path) for path in paths if str(path).strip())
    allowed = tuple(normalize_repo_path(path) for path in allow if str(path).strip())
    allowed_set = set(allowed)
    blocked = tuple(
        path for path in checked
        if is_live_runtime_dirt(path) and path not in allowed_set
    )
    return ScopeCheckResult(
        ok=not blocked,
        checked_paths=checked,
        blocked_paths=blocked,
        allowed_overrides=allowed,
    )


def staged_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Paths to verify. Defaults to staged paths.")
    parser.add_argument("--allow", action="append", default=[], help="Explicitly allowed blocked path.")
    args = parser.parse_args(argv)

    paths = tuple(args.paths) if args.paths else staged_paths()
    result = verify_paths(paths, allow=args.allow)
    print(json.dumps(result.to_dict(), sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
