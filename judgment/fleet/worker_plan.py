#!/usr/bin/env python3
"""Supervisor plan for the demo fleet: one relay + one worker per target.

Never includes Challenge login 0 / 0 or ``C:\\MT5\\FTMO``.
Used by ``vps_start_workers.ps1`` and health.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judgment.fleet.allowlist import FORBIDDEN_LOGINS, looks_like_challenge_path  # noqa: E402
from judgment.fleet.common import (  # noqa: E402
    DEFAULT_RELAY_STATE,
    MIRROR_LOG_DIR,
    MIRROR_RUN_DIR,
    SOURCE_LOGIN,
    resolve_outbox,
)
from judgment.fleet.observer_config import (  # noqa: E402
    fanout_targets,
    resolve_registry_path,
    targeted_observers,
)

RELAY_SCRIPT = ROOT / "judgment" / "fleet" / "fleet_relay.py"
FANOUT_SCRIPT = ROOT / "judgment" / "fleet" / "mirror" / "mirror_fanout.py"
FANOUT_FALLBACK = ROOT / "judgment" / "fleet" / "mirror_fanout.py"


def _fanout_script() -> Path:
    return FANOUT_SCRIPT if FANOUT_SCRIPT.is_file() else FANOUT_FALLBACK


def pid_path(worker_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in worker_id)
    return MIRROR_RUN_DIR / f"{safe}.pid"


def log_path(worker_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in worker_id)
    return MIRROR_LOG_DIR / f"{safe}.log"


def build_plan(
    *,
    registry: Path | None = None,
    outbox: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    registry_path = resolve_registry_path(registry)
    outbox_path = resolve_outbox(outbox)
    fanout = _fanout_script()
    workers: list[dict[str, Any]] = []
    for observer in targeted_observers(registry_path):
        if observer.demo_login in FORBIDDEN_LOGINS:
            continue
        if looks_like_challenge_path(observer.terminal_path):
            continue
        argv = [
            sys.executable,
            str(fanout),
            "--observer-id",
            observer.id,
            "--follow",
            "--registry",
            str(registry_path),
            "--outbox",
            str(outbox_path),
        ]
        if dry_run:
            argv.append("--dry-run")
        workers.append(
            {
                "id": observer.id,
                "kind": "mirror_fanout",
                "demo_login": observer.demo_login,
                "terminal_path": observer.terminal_path,
                "terminal_dir": observer.terminal_dir,
                "argv": argv,
                "pid_path": str(pid_path(observer.id)),
                "log_path": str(log_path(observer.id)),
                "place_on_challenge": False,
            }
        )
    relay_argv = [
        sys.executable,
        str(RELAY_SCRIPT),
        "--follow",
        "--outbox",
        str(outbox_path),
        "--state",
        str(DEFAULT_RELAY_STATE),
    ]
    return {
        "ok": True,
        "place_on_challenge": False,
        "source_login": SOURCE_LOGIN,
        "forbidden_logins": sorted(FORBIDDEN_LOGINS),
        "registry": str(registry_path),
        "outbox": str(outbox_path),
        "targets": fanout_targets(registry_path),
        "relay": {
            "id": "fleet_relay",
            "kind": "fleet_relay",
            "argv": relay_argv,
            "pid_path": str(pid_path("fleet_relay")),
            "log_path": str(log_path("fleet_relay")),
            "place_on_challenge": False,
        },
        "workers": workers,
        "note": "one detached PID per observer terminal; relay is the single producer",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--outbox", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args(argv)
    plan = build_plan(registry=args.registry, outbox=args.outbox, dry_run=args.dry_run)
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
