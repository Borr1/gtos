#!/usr/bin/env python3
"""Read-only health for the three Free Trial demo observers.

Prints per-observer login / balance / equity / positions, mirror-state age,
and whether the worker PID is alive. Never mutates Challenge 0 /
0 and never ``order_send``s.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judgment.fleet.allowlist import (  # noqa: E402
    FORBIDDEN_LOGINS,
    PlaceVeto,
    looks_like_challenge_path,
)
from judgment.fleet.common import (  # noqa: E402
    SOURCE_LOGIN,
    load_json,
    resolve_outbox,
    utc_now,
)
from judgment.fleet.mirror_fanout import state_path_for  # noqa: E402
from judgment.fleet.observer_config import (  # noqa: E402
    Observer,
    fanout_targets,
    load_observers,
    resolve_registry_path,
)
from judgment.fleet.worker_plan import build_plan, pid_path  # noqa: E402

FRESH_OUTBOX_S = 900.0
FRESH_STATE_S = 900.0


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_pid(path: Path) -> int | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    try:
        return int(text.split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _age_seconds(path: Path) -> float | None:
    if not path.is_file():
        return None
    return max(0.0, time.time() - path.stat().st_mtime)


def _cmdline_has_worker(observer_id: str) -> bool:
    proc = Path("/proc")
    if not proc.is_dir():
        return False
    needle = f"--observer-id {observer_id}"
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        cmdline = entry / "cmdline"
        try:
            text = cmdline.read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="replace")
        except OSError:
            continue
        if "mirror_fanout" in text and needle in text:
            return True
        if "fleet_relay" in text and observer_id == "fleet_relay":
            return True
    return False


def worker_alive(worker_id: str) -> dict[str, Any]:
    path = pid_path(worker_id)
    pid = _read_pid(path)
    alive = bool(pid and _pid_alive(pid))
    if not alive:
        alive = _cmdline_has_worker(worker_id)
    return {
        "id": worker_id,
        "alive": alive,
        "pid": pid,
        "pid_path": str(path),
        "pid_age_s": _age_seconds(path),
    }


def _outbox_health(path: Path) -> dict[str, Any]:
    age = _age_seconds(path)
    size = path.stat().st_size if path.is_file() else 0
    last: dict[str, Any] | None = None
    if path.is_file() and size:
        try:
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                row = json.loads(lines[-1])
                if isinstance(row, dict):
                    last = {
                        "kind": row.get("kind"),
                        "ticket": row.get("ticket"),
                        "symbol": row.get("symbol"),
                        "ts_utc": row.get("ts_utc") or row.get("relay_ts_utc"),
                    }
        except (OSError, json.JSONDecodeError):
            last = None
    return {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": size,
        "age_s": age,
        "fresh": age is not None and age <= FRESH_OUTBOX_S,
        "last_event": last,
    }


def _read_demo_account(observer: Observer, mt5: Any | None) -> dict[str, Any]:
    if observer.demo_login in FORBIDDEN_LOGINS:
        raise PlaceVeto("forbidden_login", login=observer.demo_login, place_on_challenge=False)
    if looks_like_challenge_path(observer.terminal_path):
        raise PlaceVeto("forbidden_challenge_path", path=observer.terminal_path, place_on_challenge=False)
    if mt5 is None:
        return {
            "ok": False,
            "reason": "offline",
            "login": observer.demo_login,
            "balance": None,
            "equity": None,
            "positions": None,
            "broker_mutate": False,
        }
    if not mt5.initialize(path=observer.terminal_path, login=observer.demo_login, portable=True):
        return {
            "ok": False,
            "reason": "mt5_init_failed",
            "login": observer.demo_login,
            "balance": None,
            "equity": None,
            "positions": None,
            "last_error": list(mt5.last_error() or ()),
            "broker_mutate": False,
        }
    try:
        info = mt5.account_info()
        if info is None:
            return {
                "ok": False,
                "reason": "no_account",
                "login": observer.demo_login,
                "balance": None,
                "equity": None,
                "positions": None,
                "broker_mutate": False,
            }
        connected_login = int(getattr(info, "login", 0) or 0)
        if connected_login in FORBIDDEN_LOGINS:
            raise PlaceVeto("connected_forbidden_login", login=connected_login, place_on_challenge=False)
        positions = mt5.positions_get() or ()
        return {
            "ok": True,
            "reason": "mt5",
            "login": connected_login,
            "balance": float(getattr(info, "balance", 0.0) or 0.0),
            "equity": float(getattr(info, "equity", 0.0) or 0.0),
            "positions": len(tuple(positions)),
            "broker_mutate": False,
        }
    finally:
        mt5.shutdown()


def _observer_row(
    observer: Observer,
    *,
    targets: list[str],
    mt5_factory: Any | None,
    offline: bool,
) -> dict[str, Any]:
    state = state_path_for(observer.id)
    payload = load_json(state, {})
    live: dict[str, Any]
    if offline or mt5_factory is None:
        live = {
            "ok": False,
            "reason": "offline",
            "login": observer.demo_login,
            "balance": None,
            "equity": None,
            "positions": None,
            "broker_mutate": False,
        }
    else:
        live = _read_demo_account(observer, mt5_factory())
    proc = worker_alive(observer.id)
    return {
        "id": observer.id,
        "display_name": observer.display_name,
        "login": observer.demo_login,
        "server": observer.server,
        "terminal_path": observer.terminal_path,
        "in_targets": observer.id in targets,
        "status": observer.status,
        "place_enabled": observer.place_enabled,
        "balance": live.get("balance"),
        "equity": live.get("equity"),
        "positions": live.get("positions"),
        "account_ok": bool(live.get("ok")),
        "account_reason": live.get("reason"),
        "mirror_state": str(state),
        "mirror_state_age_s": _age_seconds(state),
        "mirror_state_fresh": (_age_seconds(state) or 1e9) <= FRESH_STATE_S,
        "mirror_offset": payload.get("offset_bytes"),
        "mirror_handled": payload.get("handled"),
        "worker_alive": proc["alive"],
        "worker_pid": proc["pid"],
        "place_on_challenge": False,
    }


def collect_health(
    *,
    registry: Path | None = None,
    outbox: Path | None = None,
    offline: bool = True,
    mt5_factory: Any | None = None,
) -> dict[str, Any]:
    registry_path = resolve_registry_path(registry)
    outbox_path = resolve_outbox(outbox)
    targets = fanout_targets(registry_path)
    observers = load_observers(registry_path)
    rows = [
        _observer_row(item, targets=targets, mt5_factory=mt5_factory, offline=offline)
        for item in observers
        if item.channel.strip().lower() not in {"telegram", "note"}
    ]
    missing = [item for item in targets if item not in {row["id"] for row in rows}]
    missing_targets = [
        row["id"] for row in rows if row["id"] not in targets and row.get("place_enabled")
    ]
    outbox_info = _outbox_health(outbox_path)
    relay = worker_alive("fleet_relay")
    checklist = {
        "redacted_account_in_targets": "observer_redacted_account" in targets,
        "three_observers_registered": {row["id"] for row in rows}
        >= {"observer_sh", "observer_redacted_account", "observer_redacted_account"},
        "targets_cover_three": set(targets) >= {"observer_sh", "observer_redacted_account", "observer_redacted_account"},
        "relay_alive": relay["alive"],
        "workers_alive": all(
            row["worker_alive"] for row in rows if row["id"] in targets
        )
        if any(row["id"] in targets for row in rows)
        else False,
        "outbox_fresh": bool(outbox_info["fresh"]),
        "no_challenge_login_in_observers": all(
            row["login"] not in FORBIDDEN_LOGINS for row in rows
        ),
        "no_challenge_path_in_observers": all(
            not looks_like_challenge_path(str(row.get("terminal_path") or "")) for row in rows
        ),
    }
    ok = all(
        [
            checklist["redacted_account_in_targets"],
            checklist["targets_cover_three"],
            checklist["no_challenge_login_in_observers"],
            checklist["no_challenge_path_in_observers"],
        ]
    )
    return {
        "ok": ok,
        "ts_utc": utc_now(),
        "source_login": SOURCE_LOGIN,
        "place_on_challenge": False,
        "broker_mutate": False,
        "challenge_login_touched": False,
        "registry": str(registry_path),
        "outbox": outbox_info,
        "relay": relay,
        "targets": targets,
        "missing_observer_rows": missing,
        "active_not_in_targets": missing_targets,
        "observers": rows,
        "checklist": checklist,
        "plan": build_plan(registry=registry_path, outbox=outbox_path),
    }


def _print_text(report: dict[str, Any]) -> None:
    print(f"fleet_demo_health ts={report['ts_utc']} ok={report['ok']} place_on_challenge=false")
    outbox = report["outbox"]
    age = outbox.get("age_s")
    age_s = f"{age:.0f}s" if isinstance(age, (int, float)) else "missing"
    print(
        f"outbox {outbox['path']} size={outbox['size_bytes']} age={age_s} "
        f"fresh={outbox['fresh']} last={outbox.get('last_event')}"
    )
    print(f"relay alive={report['relay']['alive']} pid={report['relay']['pid']}")
    print(f"targets {report['targets']}")
    for row in report["observers"]:
        print(
            f"{row['id']} login={row['login']} bal={row['balance']} eq={row['equity']} "
            f"pos={row['positions']} in_targets={row['in_targets']} "
            f"worker_alive={row['worker_alive']} state_age_s={row['mirror_state_age_s']}"
        )
    print("checklist " + json.dumps(report["checklist"], sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--outbox", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--offline",
        action="store_true",
        default=True,
        help="default: do not open MT5 (safe on CI / Chair laptop)",
    )
    parser.add_argument(
        "--mt5",
        action="store_true",
        help="read demo bal/eq/pos via MetaTrader5 (still refuses Challenge)",
    )
    args = parser.parse_args(argv)
    offline = not args.mt5
    factory = None
    if args.mt5:
        try:
            from judgment.fleet.mt5_demo import LiveMT5DemoClient

            factory = LiveMT5DemoClient
        except PlaceVeto:
            factory = None
            offline = True
    report = collect_health(
        registry=args.registry,
        outbox=args.outbox,
        offline=offline,
        mt5_factory=factory,
    )
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_text(report)
    if not report["checklist"]["no_challenge_login_in_observers"]:
        return 2
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
