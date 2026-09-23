#!/usr/bin/env python3
"""Run no-AI/no-execution shadow observers for registered extra symbols."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.safety.runtime_halt import read_runtime_halt_state

load_dotenv(override=True)

RUNTIME_HALT_CONFIG = {
    "runtime_control": {
        "enabled": True,
        "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
    }
}


def _halt_result(snapshot) -> dict:
    return {
        "schema_version": "shadow_observer_cycle_result_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": snapshot.status.upper(),
        "reason": "shadow observer disabled while runtime halt is active",
        "halt_flags": snapshot.to_dict().get("active_flags", []),
        "checked": 0,
        "emitted": 0,
    }


if __name__ == "__main__":
    _startup_halt_snapshot = read_runtime_halt_state(
        RUNTIME_HALT_CONFIG,
        repo_root=ROOT,
    )
else:
    _startup_halt_snapshot = None

if _startup_halt_snapshot is not None and _startup_halt_snapshot.active:
    print(
        json.dumps(_halt_result(_startup_halt_snapshot), sort_keys=True)
    )
    raise SystemExit(0)

from src.mt5 import create_mt5
from src.components.mt5_daemon_runtime import (
    acquire_single_instance_lock,
    release_single_instance_lock,
)
from src.research_infra.shadow_observer import (
    append_status,
    load_registry,
    observe_cycle,
    status_row,
    validate_registry,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="config/shadow_observer_registry.yaml")
    parser.add_argument("--config", default="config/agent_config.yaml")
    parser.add_argument("--profile", default=None)
    parser.add_argument(
        "--mode",
        choices=["mock", "demo", "live"],
        default=os.environ.get("GTOS_MODE", "live"),
        help="MT5 connection mode. Observer is read-only regardless of mode.",
    )
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated symbols or observer_ids to run. Empty means all registry entries.",
    )
    parser.add_argument(
        "--include-inactive-status",
        action="store_true",
        help="Also write status rows for disabled/deferred registry entries.",
    )
    parser.add_argument("--once", action="store_true", help="Run one observation cycle and exit.")
    parser.add_argument("--max-cycles", type=int, default=0, help="0 means unlimited.")
    parser.add_argument("--poll-seconds", type=float, default=None)
    parser.add_argument("--output-path", default=None)
    parser.add_argument("--status-path", default=None)
    parser.add_argument("--state-path", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--log-path", default="logs/shadow_observer.log")
    return parser.parse_args(argv)


def write_connect_failure_statuses(
    *,
    registry,
    symbols: list[str],
    status_path: str | None,
    state_path: str | None,
    observer_run_id: str,
    reason: str = "mt5_connect_failed",
) -> dict[str, object]:
    wanted = {s.upper() for s in symbols or []}
    status_target = Path(status_path or registry.defaults.get("status_path") or "shadow_logs/shadow_observer_status.jsonl")
    checked = 0
    skipped_by_filter = 0
    for entry in registry.active_entries:
        if wanted and entry.symbol.upper() not in wanted and entry.observer_id.upper() not in wanted:
            skipped_by_filter += 1
            continue
        checked += 1
        append_status(
            status_target,
            status_row(
                entry,
                lifecycle_status="BLOCKED_MT5_CONNECT_FAILED",
                observer_run_id=observer_run_id,
                reason=reason,
                details={"mt5_connect": "failed", "fail_open": True},
            ),
        )
    return {
        "schema_version": "shadow_observer_cycle_result_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "checked": checked,
        "emitted": 0,
        "skipped_by_filter": skipped_by_filter,
        "output_path": str(registry.defaults.get("output_path") or "shadow_logs/strategy_follow_evaluations.jsonl"),
        "status_path": str(status_target),
        "state_path": str(state_path or registry.defaults.get("state_path") or "pipeline_state/shadow_observer_state.json"),
        "observer_run_id": observer_run_id,
        "status": "BLOCKED_MT5_CONNECT_FAILED_STATUS_RECORDED",
        "reason": reason,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    halt_snapshot = read_runtime_halt_state(RUNTIME_HALT_CONFIG, repo_root=ROOT)
    if halt_snapshot.active:
        print(json.dumps(_halt_result(halt_snapshot), sort_keys=True))
        return 0
    Path(args.log_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(args.log_path, encoding="utf-8"),
        ],
    )

    registry = load_registry(args.registry)
    errors = validate_registry(registry)
    if errors:
        for error in errors:
            logging.error("registry error: %s", error)
        return 2

    acquired, conflicting_pid = acquire_single_instance_lock(
        "shadow_observer",
        argv_marker="run_shadow_observer.py",
    )
    if not acquired:
        logging.info(
            "shadow observer already running pid=%s; exiting cleanly",
            conflicting_pid,
        )
        return 0

    poll_seconds = (
        args.poll_seconds
        if args.poll_seconds is not None
        else float(registry.defaults.get("poll_seconds", 20))
    )
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    observer_run_id = args.run_id or "shadow_observer_{pid}_{ts}".format(
        pid=os.getpid(),
        ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )

    mt5 = None
    try:
        mt5 = create_mt5(mode=args.mode)
        if not mt5.connect():
            logging.error("Failed to connect to MT5 in read-only shadow observer mode")
            result = write_connect_failure_statuses(
                registry=registry,
                symbols=symbols,
                status_path=args.status_path,
                state_path=args.state_path,
                observer_run_id=observer_run_id,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        logging.info(
            "shadow observer started mode=%s active_entries=%d once=%s run_id=%s",
            args.mode,
            len(registry.active_entries),
            args.once,
            observer_run_id,
        )
        cycles = 0
        while True:
            result = observe_cycle(
                registry=registry,
                mt5=mt5,
                symbols=symbols or None,
                include_inactive=args.include_inactive_status,
                base_config_path=args.config,
                profile=args.profile,
                output_path=args.output_path,
                status_path=args.status_path,
                state_path=args.state_path,
                observer_run_id=observer_run_id,
            )
            cycles += 1
            logging.info("cycle %d: %s", cycles, json.dumps(result, sort_keys=True))
            if args.once or (args.max_cycles and cycles >= args.max_cycles):
                print(json.dumps(result, indent=2, sort_keys=True))
                return 0
            time.sleep(max(1.0, poll_seconds))
    finally:
        if mt5 is not None:
            mt5.disconnect()
        release_single_instance_lock("shadow_observer")


if __name__ == "__main__":
    raise SystemExit(main())
