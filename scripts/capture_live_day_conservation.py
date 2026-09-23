#!/usr/bin/env python3
"""Reconcile reset-window runtime flow against a broker-day truth capture.

The ledger reader works backwards from a fixed file-size snapshot so a large,
actively appended JSONL does not need to be materialized.  Packet validation,
candidate disposition, generation-slot conservation, and broker lifecycle
counts are kept distinct so a legacy aggregate boundary cannot masquerade as
exact row-level coverage.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.reconcile_live_flow_ledger import compact_reconciliation_row  # noqa: E402
from src.components.ultimate_book.live_flow import reconcile_live_flow_rows  # noqa: E402
from src.components.ultimate_book.runtime_learning_packet import (  # noqa: E402
    validate_runtime_learning_packet,
)


MAIN_LEDGER = Path("shadow_logs/ultimate_book_runtime_learning_packets.jsonl")
F5_LEDGER = Path(r"host-local\redacted_host\repo\shadow_logs\ultimate_book_runtime_learning_packets.jsonl")
DEFAULT_TRUTH = Path(
    "research/operations/live_system_forensic_repair_closure_2026_08_13/"
    "BROKER_DAY_TRUTH_LATEST.json"
)


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _reverse_lines(handle: Any, end_pos: int, *, block_size: int = 8 * 1024 * 1024) -> Iterable[bytes]:
    """Yield complete lines in reverse from an immutable file-size snapshot."""

    position = end_pos
    remainder = b""
    while position:
        take = min(block_size, position)
        position -= take
        handle.seek(position)
        chunk = handle.read(take)
        parts = (chunk + remainder).split(b"\n")
        remainder = parts[0]
        for line in reversed(parts[1:]):
            if line.strip():
                yield line
    if remainder.strip():
        yield remainder


def account_for_namespace(namespace: str, *, stream: str) -> str | None:
    value = namespace.lower()
    if stream == "f5":
        return "FTMO"
    if "redacted_account" in value:
        return "redacted_account"
    if "ftmo" in value:
        return "FTMO"
    return None


def _reason(row: Mapping[str, Any]) -> str | None:
    outcome = row.get("outcome") if isinstance(row.get("outcome"), Mapping) else {}
    live_flow = row.get("live_flow") if isinstance(row.get("live_flow"), Mapping) else {}
    for value in (
        row.get("skip_reason"),
        row.get("reject_reason"),
        outcome.get("skip_reason"),
        outcome.get("reject_reason"),
        outcome.get("reason"),
        live_flow.get("reason"),
    ):
        if value not in (None, ""):
            return str(value)
    return None


def _compact_event_path(events: Iterable[str]) -> str:
    compact: list[str] = []
    previous: str | None = None
    count = 0
    for event in events:
        if event == previous:
            count += 1
            continue
        if previous is not None:
            compact.append(f"{previous}[x{count}]" if count > 1 else previous)
        previous = event
        count = 1
    if previous is not None:
        compact.append(f"{previous}[x{count}]" if count > 1 else previous)
    return " -> ".join(compact)


def _legacy_generation_census(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    cycles: dict[tuple[str, str], tuple[int | None, int | None]] = {}
    conflicts: list[dict[str, Any]] = []
    for row in rows:
        if "live_flow" in row:
            continue
        bridge = row.get("bridge") if isinstance(row.get("bridge"), Mapping) else {}
        generation = (
            bridge.get("broker_profile_generation")
            if isinstance(bridge.get("broker_profile_generation"), Mapping)
            else None
        )
        if generation is None:
            continue
        key = (str(row.get("namespace") or ""), str(row.get("created_at_utc") or ""))
        active = generation.get("active_symbol_slot_count")
        candidates = bridge.get("n_candidates_in")
        value = (
            active if isinstance(active, int) else None,
            candidates if isinstance(candidates, int) else None,
        )
        previous = cycles.setdefault(key, value)
        if previous != value:
            conflicts.append({"namespace": key[0], "created_at_utc": key[1]})
    active_total = sum(row[0] for row in cycles.values() if row[0] is not None)
    candidate_total = sum(row[1] for row in cycles.values() if row[1] is not None)
    return {
        "status": "PASS" if not conflicts else "FAIL",
        "unique_cycles": len(cycles),
        "aggregate_active_symbol_slots": active_total,
        "aggregate_candidates_in": candidate_total,
        "aggregate_noncandidate_slot_arithmetic": active_total - candidate_total,
        "conflicts": conflicts,
        "evidence_boundary": (
            "Counts are source-bound aggregate cycle arithmetic. Legacy packets do not preserve "
            "per-slot terminal identity or an exact non-emission reason."
        ),
    }


def summarize_packets(rows: list[dict[str, Any]], compact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    events = Counter(str(row.get("event_type") or "unknown") for row in rows)
    namespaces = Counter(str(row.get("namespace") or "unknown") for row in rows)
    legacy_rows = sum("live_flow" not in row for row in rows)
    refusal_gates: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    generation_status: Counter[str] = Counter()
    generation_reasons: Counter[str] = Counter()
    event_by_namespace: dict[str, Counter[str]] = defaultdict(Counter)
    candidate_events: dict[tuple[str, str], list[str]] = defaultdict(list)
    close_by_sleeve: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "broker_realized_pnl_captured": 0, "broker_realized_pnl_missing": 0, "broker_realized_pnl": 0.0}
    )
    placed_by_sleeve: Counter[str] = Counter()

    for row in rows:
        event = str(row.get("event_type") or "unknown")
        namespace = str(row.get("namespace") or "unknown")
        event_by_namespace[namespace][event] += 1
        reason = _reason(row)
        if reason:
            reasons[reason] += 1
        live_flow = row.get("live_flow") if isinstance(row.get("live_flow"), Mapping) else {}
        gate = live_flow.get("terminal_refusal_gate")
        if gate not in (None, ""):
            refusal_gates[str(gate)] += 1
        flow_id = live_flow.get("flow_id")
        if flow_id not in (None, ""):
            candidate_events[(namespace, str(flow_id))].append(event)
        if event == "generation_cycle_complete":
            outcome = row.get("outcome") if isinstance(row.get("outcome"), Mapping) else {}
            terminals = outcome.get("generation_slot_terminals")
            if isinstance(terminals, list):
                for terminal in terminals:
                    if not isinstance(terminal, Mapping):
                        continue
                    generation_status[str(terminal.get("terminal_status") or "unknown")] += 1
                    terminal_reason = terminal.get("reason") or terminal.get("terminal_reason")
                    if terminal_reason not in (None, ""):
                        generation_reasons[str(terminal_reason)] += 1
        sleeve = str(row.get("sleeve") or "unknown")
        if event == "unit_placed":
            placed_by_sleeve[sleeve] += 1
        elif event == "position_closed":
            outcome = row.get("outcome") if isinstance(row.get("outcome"), Mapping) else {}
            bucket = close_by_sleeve[sleeve]
            bucket["count"] += 1
            pnl = outcome.get("broker_realized_pnl")
            if isinstance(pnl, (int, float)):
                bucket["broker_realized_pnl_captured"] += 1
                bucket["broker_realized_pnl"] += float(pnl)
            else:
                bucket["broker_realized_pnl_missing"] += 1

    candidate_flow_ids = {
        (str(row.get("namespace") or ""), str((row.get("live_flow") or {}).get("flow_id") or ""))
        for row in rows
        if row.get("event_type") == "candidate_generated" and isinstance(row.get("live_flow"), Mapping)
    }
    paths = Counter(
        _compact_event_path(candidate_events[key])
        for key in candidate_flow_ids
        if key in candidate_events
    )
    return {
        "event_counts": dict(sorted(events.items())),
        "event_counts_by_namespace": {
            namespace: dict(sorted(counter.items()))
            for namespace, counter in sorted(event_by_namespace.items())
        },
        "namespace_counts": dict(sorted(namespaces.items())),
        "legacy_packet_count": legacy_rows,
        "live_flow_packet_count": len(rows) - legacy_rows,
        "candidate_path_counts": dict(sorted(paths.items())),
        "reason_counts": dict(sorted(reasons.items())),
        "terminal_refusal_gate_counts": dict(sorted(refusal_gates.items())),
        "generation_terminal_status_counts": dict(sorted(generation_status.items())),
        "generation_terminal_reason_counts": dict(sorted(generation_reasons.items())),
        "placements_by_sleeve": dict(sorted(placed_by_sleeve.items())),
        "closes_by_sleeve": {
            sleeve: {
                **values,
                "broker_realized_pnl": round(float(values["broker_realized_pnl"]), 10),
            }
            for sleeve, values in sorted(close_by_sleeve.items())
        },
        "legacy_generation_census": _legacy_generation_census(rows),
        "live_flow_reconciliation": reconcile_live_flow_rows(compact_rows),
    }


def scan_ledger_window(
    path: Path,
    *,
    stream: str,
    starts: Mapping[str, datetime],
    end: datetime,
    validator: Callable[[Mapping[str, Any]], tuple[bool, list[str]]] = validate_runtime_learning_packet,
) -> dict[str, Any]:
    earliest = min(starts.values())
    stop_before = earliest - timedelta(hours=6)
    selected: list[dict[str, Any]] = []
    compact_rows: list[dict[str, Any]] = []
    parse_issues: list[dict[str, Any]] = []
    validation_issues: Counter[str] = Counter()
    unknown_namespaces: Counter[str] = Counter()
    packet_hashes: Counter[str] = Counter()
    rows_scanned = 0
    oldest_scanned: datetime | None = None
    boundary_reached = False

    with path.open("rb") as handle:
        handle.seek(0, 2)
        file_size = handle.tell()
        for raw in _reverse_lines(handle, file_size):
            rows_scanned += 1
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                if len(parse_issues) < 20:
                    parse_issues.append({"reverse_row": rows_scanned, "issue": type(exc).__name__})
                continue
            if not isinstance(row, dict):
                if len(parse_issues) < 20:
                    parse_issues.append({"reverse_row": rows_scanned, "issue": "row_not_object"})
                continue
            created = parse_utc(row.get("created_at_utc"))
            if created is None:
                if len(parse_issues) < 20:
                    parse_issues.append({"reverse_row": rows_scanned, "issue": "missing_or_invalid_created_at_utc"})
                continue
            oldest_scanned = created if oldest_scanned is None else min(oldest_scanned, created)
            if created < stop_before:
                boundary_reached = True
                break
            if created > end:
                continue
            namespace = str(row.get("namespace") or "")
            account = account_for_namespace(namespace, stream=stream)
            if account is None or account not in starts:
                if created >= earliest:
                    unknown_namespaces[namespace or "<missing>"] += 1
                continue
            if created < starts[account]:
                continue
            ok, issues = validator(row)
            if not ok:
                validation_issues.update(str(issue) for issue in issues)
            packet_hash = row.get("packet_hash_sha256")
            if packet_hash not in (None, ""):
                packet_hashes[str(packet_hash)] += 1
            selected.append(row)
            if "live_flow" in row:
                compact_rows.append(compact_reconciliation_row(row))

    selected.reverse()
    compact_rows.reverse()
    duplicate_hash_rows = sum(count - 1 for count in packet_hashes.values() if count > 1)
    summary = summarize_packets(selected, compact_rows)
    reconciliation = summary["live_flow_reconciliation"]
    legacy = summary["legacy_generation_census"]
    passed = (
        not parse_issues
        and not validation_issues
        and not unknown_namespaces
        and not duplicate_hash_rows
        and boundary_reached
        and reconciliation.get("status") == "PASS"
        and legacy.get("status") == "PASS"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "file_size_snapshot_bytes": file_size,
        "scan": {
            "rows_scanned_from_tail": rows_scanned,
            "selected_rows": len(selected),
            "oldest_timestamp_scanned": oldest_scanned.isoformat() if oldest_scanned else None,
            "required_stop_before_utc": stop_before.isoformat(),
            "boundary_reached": boundary_reached,
        },
        "parse_issues": parse_issues,
        "packet_validation_issue_counts": dict(sorted(validation_issues.items())),
        "duplicate_packet_hash_rows": duplicate_hash_rows,
        "unknown_namespace_counts": dict(sorted(unknown_namespaces.items())),
        "summary": summary,
    }


def _broker_counts(account: Mapping[str, Any], surface: str) -> dict[str, int]:
    groups = [
        row
        for row in (account.get("position_groups") or [])
        if surface in (row.get("surfaces") or [])
    ]
    positions = [row for row in (account.get("positions") or []) if row.get("surface") == surface]
    pending = [row for row in (account.get("pending_orders") or []) if row.get("surface") == surface]
    return {
        "entry_position_groups": sum(int(row.get("entry_deal_count") or 0) > 0 for row in groups),
        "exit_position_groups": sum(int(row.get("exit_deal_count") or 0) > 0 for row in groups),
        "position_groups": len(groups),
        "current_positions": len(positions),
        "current_pending_orders": len(pending),
    }


def broker_runtime_conservation(truth: Mapping[str, Any], ledgers: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    checks = []
    routes = (
        ("main", "FTMO", "ftmo", "production"),
        ("main", "redacted_account", "redacted_account", "production"),
        ("f5", "FTMO", None, "f5_minimal_experiment"),
    )
    for stream, account_name, namespace_hint, broker_surface in routes:
        account = (truth.get("accounts") or {}).get(account_name) or {}
        event_by_namespace = (
            ((ledgers.get(stream) or {}).get("summary") or {}).get("event_counts_by_namespace") or {}
        )
        selected_counters = [
            counter
            for namespace, counter in event_by_namespace.items()
            if namespace_hint is None or namespace_hint in namespace.lower()
        ]
        runtime_placed = sum(int(counter.get("unit_placed") or 0) for counter in selected_counters)
        runtime_closed = sum(int(counter.get("position_closed") or 0) for counter in selected_counters)
        broker = _broker_counts(account, broker_surface)
        placements_match = runtime_placed == broker["entry_position_groups"]
        closes_match = runtime_closed == broker["exit_position_groups"]
        checks.append(
            {
                "stream": stream,
                "account": account_name,
                "broker_surface": broker_surface,
                "runtime_unit_placed": runtime_placed,
                "broker_entry_position_groups": broker["entry_position_groups"],
                "runtime_position_closed": runtime_closed,
                "broker_exit_position_groups": broker["exit_position_groups"],
                "broker_position_groups": broker["position_groups"],
                "broker_current_positions": broker["current_positions"],
                "broker_current_pending_orders": broker["current_pending_orders"],
                "placements_match": placements_match,
                "closes_match": closes_match,
                "status": "PASS" if placements_match and closes_match else "FAIL",
            }
        )
    return {"status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL", "checks": checks}


def build_report(
    truth: Mapping[str, Any],
    *,
    main_ledger: Path,
    f5_ledger: Path,
) -> dict[str, Any]:
    accounts = truth.get("accounts") or {}
    starts = {
        name: parse_utc((account.get("reset_window") or {}).get("start_utc"))
        for name, account in accounts.items()
    }
    if not starts or any(value is None for value in starts.values()):
        raise ValueError("broker truth lacks an account reset-window start")
    typed_starts = {name: value for name, value in starts.items() if value is not None}
    end = parse_utc(truth.get("captured_at_utc"))
    if end is None:
        raise ValueError("broker truth lacks captured_at_utc")
    ledgers = {
        "main": scan_ledger_window(main_ledger, stream="main", starts=typed_starts, end=end),
        "f5": scan_ledger_window(f5_ledger, stream="f5", starts={"FTMO": typed_starts["FTMO"]}, end=end),
    }
    broker_join = broker_runtime_conservation(truth, ledgers)
    passed = (
        str(truth.get("status") or "").lower() == "passed"
        and all(row["status"] == "PASS" for row in ledgers.values())
        and broker_join["status"] == "PASS"
    )
    legacy_present = any(row["summary"]["legacy_packet_count"] for row in ledgers.values())
    return {
        "schema_version": "gtos.live_day_conservation.v1",
        "status": (
            "PASS_WITH_MEASURED_LEGACY_BOUNDARY" if passed and legacy_present else "PASS" if passed else "FAIL"
        ),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "broker_truth_captured_at_utc": truth.get("captured_at_utc"),
        "reset_window_starts_utc": {
            name: value.isoformat() for name, value in sorted(typed_starts.items())
        },
        "ledgers": ledgers,
        "broker_runtime_conservation": broker_join,
        "claim_boundary": (
            "All preserved packets in the broker-aligned window are validated and all candidate rows "
            "with live_flow are disposition-reconciled. Pre-live_flow generation cycles conserve only "
            "aggregate configured slots and candidate-in arithmetic; missing per-slot reasons are not invented."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker-truth", type=Path, default=DEFAULT_TRUTH)
    parser.add_argument("--main-ledger", type=Path, default=MAIN_LEDGER)
    parser.add_argument("--f5-ledger", type=Path, default=F5_LEDGER)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    truth = json.loads(args.broker_truth.read_text(encoding="utf-8"))
    report = build_report(truth, main_ledger=args.main_ledger, f5_ledger=args.f5_ledger)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 2 if args.strict and report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
