#!/usr/bin/env python3
"""One-demo PLACE worker: tail fleet_events.jsonl onto one Free Trial terminal.

One process per observer terminal path. The relay stays the single producer.
Never ``order_send`` on Challenge path ``C:\\MT5\\FTMO`` or login 0.
Does not invent NEWS_PROTOCOL — file tail only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judgment.fleet.allowlist import PlaceVeto  # noqa: E402
from judgment.fleet.common import (  # noqa: E402
    MODULE_ROOT,
    SOURCE_LOGIN,
    atomic_write_json,
    load_json,
    resolve_outbox,
    validate_fleet_event,
)
from judgment.fleet.mirror_adapter import DemoMirrorAdapter  # noqa: E402
from judgment.fleet.mt5_demo import LiveMT5DemoClient  # noqa: E402
from judgment.fleet.observer_config import (  # noqa: E402
    Observer,
    get_observer,
    parse_dry_run,
    parse_micro_lot,
    require_placeable,
    resolve_registry_path,
    targeted_observers,
)

DEFAULT_FANOUT_STATE_DIR = MODULE_ROOT / "outbox"


def state_path_for(observer_id: str, directory: Path | None = None) -> Path:
    root = directory or DEFAULT_FANOUT_STATE_DIR
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in observer_id)
    return root / f"mirror_state_{safe}.json"


def _load_offset_state(path: Path, outbox: Path) -> dict[str, Any]:
    state = load_json(path, {"offset_bytes": 0, "path": None, "ticket_map": {}, "handled": 0})
    size = outbox.stat().st_size if outbox.is_file() else 0
    offset = int(state.get("offset_bytes") or 0)
    if state.get("path") != str(outbox) or offset > size:
        state = {
            "offset_bytes": 0,
            "path": str(outbox),
            "ticket_map": dict(state.get("ticket_map") or {}),
            "handled": int(state.get("handled") or 0),
        }
    state.setdefault("ticket_map", {})
    state["path"] = str(outbox)
    return state


def build_adapter(
    observer: Observer,
    *,
    mt5: Any | None,
    state_path: Path,
    state: dict[str, Any],
    micro_lot: float,
    dry_run: bool,
) -> DemoMirrorAdapter:
    return DemoMirrorAdapter(
        observer=observer,
        mt5=mt5,
        micro_lot=micro_lot,
        dry_run=dry_run,
        state=state,
        state_path=state_path,
    )


def _consume_new_lines(adapter: DemoMirrorAdapter, outbox: Path, state: dict[str, Any]) -> dict[str, Any]:
    handled = 0
    opened = 0
    closed = 0
    skipped = 0
    failed = 0
    results: list[dict[str, Any]] = []
    with outbox.open("rb") as handle:
        handle.seek(int(state.get("offset_bytes") or 0))
        while True:
            line = handle.readline()
            if not line:
                break
            state["offset_bytes"] = handle.tell()
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(row, dict):
                skipped += 1
                continue
            errors = validate_fleet_event(row)
            if errors:
                skipped += 1
                continue
            outcome = adapter.handle_event(row)
            results.append(outcome)
            handled += 1
            state["handled"] = int(state.get("handled") or 0) + 1
            if outcome.get("reason") in {"opened", "dry_run"} and outcome.get("action") == "sync_fill":
                opened += 1
            elif outcome.get("reason") in {"closed", "closed_dry_map", "dry_run"} and outcome.get("action") == "sync_close":
                closed += 1
            elif outcome.get("ok"):
                skipped += 1
            else:
                failed += 1
    adapter.state["offset_bytes"] = state["offset_bytes"]
    adapter.state["path"] = str(outbox)
    adapter.state["handled"] = state["handled"]
    adapter.state["observer_id"] = adapter.observer.id
    adapter.state["demo_login"] = adapter.observer.demo_login
    adapter.state["terminal_path"] = adapter.observer.terminal_path
    adapter.persist()
    return {
        "handled": handled,
        "opened": opened,
        "closed": closed,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


def fanout_once(
    *,
    observer: Observer,
    outbox: Path,
    state_path: Path,
    mt5: Any | None = None,
    micro_lot: float | None = None,
    dry_run: bool | None = None,
    connect: bool = True,
) -> dict[str, Any]:
    require_placeable(observer)
    lot = parse_micro_lot(micro_lot)
    dry = parse_dry_run(dry_run)
    if not outbox.is_file():
        return {
            "ok": True,
            "reason": "no_outbox",
            "outbox": str(outbox),
            "observer_id": observer.id,
            "handled": 0,
            "place_on_challenge": False,
            "source_login": SOURCE_LOGIN,
        }
    state = _load_offset_state(state_path, outbox)
    adapter = build_adapter(
        observer,
        mt5=mt5,
        state_path=state_path,
        state=state,
        micro_lot=lot,
        dry_run=dry,
    )
    connected = False
    try:
        if connect and not dry:
            adapter.connect()
            connected = True
        counts = _consume_new_lines(adapter, outbox, state)
        return {
            "ok": counts["failed"] == 0,
            "observer_id": observer.id,
            "demo_login": observer.demo_login,
            "terminal_path": observer.terminal_path,
            "outbox": str(outbox),
            "state": str(state_path),
            "offset": state["offset_bytes"],
            "handled": counts["handled"],
            "opened": counts["opened"],
            "closed": counts["closed"],
            "skipped": counts["skipped"],
            "failed": counts["failed"],
            "dry_run": dry,
            "micro_lot": lot,
            "place_on_challenge": False,
            "source_login": SOURCE_LOGIN,
            "connected": connected,
            "results": counts["results"],
        }
    finally:
        adapter.shutdown()


def launcher_command(observer: Observer, *, dry_run: bool = False) -> str:
    parts = [
        "python3",
        "judgment/fleet/mirror_fanout.py",
        "--observer-id",
        observer.id,
        "--follow",
    ]
    if dry_run:
        parts.append("--dry-run")
    return " ".join(parts)


def print_launchers(registry: Path | None, *, dry_run: bool) -> dict[str, Any]:
    observers = targeted_observers(registry)
    commands = [launcher_command(item, dry_run=dry_run) for item in observers]
    payload = {
        "ok": True,
        "count": len(commands),
        "commands": commands,
        "note": "one process per observer terminal path; relay stays singular",
        "place_on_challenge": False,
    }
    print(json.dumps(payload, indent=2))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observer-id", default="", help="registry row to PLACE on (one process)")
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--outbox", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--sleep-s", type=float, default=2.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--micro-lot", type=float, default=None)
    parser.add_argument("--print-launchers", action="store_true")
    args = parser.parse_args(argv)

    registry = resolve_registry_path(args.registry)
    dry = parse_dry_run(True if args.dry_run else None)
    if args.outbox is None:
        args.outbox = resolve_outbox()

    if args.print_launchers:
        print_launchers(registry, dry_run=dry)
        return 0

    if not args.observer_id:
        print(json.dumps({"ok": False, "reason": "observer_id_required", "place_on_challenge": False}))
        return 2

    try:
        observer = get_observer(args.observer_id, registry)
        require_placeable(observer)
    except KeyError as exc:
        print(json.dumps({"ok": False, "reason": "observer_not_found", "error": str(exc)}))
        return 2
    except PlaceVeto as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": exc.reason,
                    "place_on_challenge": False,
                    "extra": exc.extra,
                }
            )
        )
        return 2

    state_path = args.state or state_path_for(observer.id)
    mt5 = None
    if not dry:
        try:
            mt5 = LiveMT5DemoClient()
        except PlaceVeto as exc:
            print(json.dumps({"ok": False, "reason": exc.reason, "place_on_challenge": False}))
            return 2

    if not args.once and not args.follow:
        args.once = True

    def _run() -> dict[str, Any]:
        return fanout_once(
            observer=observer,
            outbox=args.outbox,
            state_path=state_path,
            mt5=mt5,
            micro_lot=args.micro_lot,
            dry_run=dry,
            connect=not dry,
        )

    if args.once and not args.follow:
        print(json.dumps(_run(), default=str))
        return 0

    while True:
        print(json.dumps(_run(), default=str), flush=True)
        time.sleep(max(0.2, float(args.sleep_s)))


if __name__ == "__main__":
    raise SystemExit(main())
