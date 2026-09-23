"""Build offline runtime-learning advisory and immutable packet repair evidence.

This script is observation-only. It reads append-only runtime-learning packets,
dedupes closed-position outcomes by hashed trade identity, emits daily sleeve
outcome summaries, and writes a repair ledger for legacy packets whose broker
exit order ticket was absent but not explicitly declared missing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ultimate_book.runtime_learning_packet import (
    DEFAULT_LOG_PATH,
    is_legacy_nonterminal_broker_realized_pnl_packet,
    nonterminal_broker_realized_pnl_fields,
    stable_hash,
    validate_runtime_learning_packet,
)


DEFAULT_OUTPUT_DIR = "pipeline_state/ultimate_book/runtime_learning_advisory"
MIN_LOOP_SECONDS = 60.0
TRADE_RECORD_ROOT = Path("pipeline_state") / "ultimate_book"
TRADE_RECORD_ENRICHMENT_FIELDS = (
    "closed_at_utc",
    "exit_reconciliation_status",
    "exit_reconciliation_attempted",
    "exit_reconciliation_source_status",
    "exit_reconciliation_missing_fields",
    "broker_exit_time_utc",
    "broker_exit_price",
    "broker_exit_profit",
    "broker_exit_commission",
    "broker_exit_swap",
    "broker_exit_fee",
    "broker_entry_commission",
    "broker_entry_swap",
    "broker_selected_exit_realized_pnl",
    "broker_position_accounting_coverage_status",
    "broker_position_deal_count",
    "broker_position_entry_deal_count",
    "broker_position_exit_deal_count",
    "broker_position_aggregate_profit",
    "broker_position_aggregate_commission",
    "broker_position_aggregate_swap",
    "broker_position_aggregate_fee",
    "broker_position_realized_pnl",
    "broker_realized_pnl_source",
    "broker_realized_pnl",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _iter_jsonl_rows(path: Path):
    if not path.exists():
        yield None, None, {"line": None, "error": "missing_packet_log"}
        return
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                yield line_no, None, {"line": line_no, "error": str(exc)}
                continue
            if isinstance(parsed, dict):
                yield line_no, parsed, None
            else:
                yield line_no, None, {"line": line_no, "error": "non_object_json"}


def _packet_processing_sort_key(item: tuple[int, dict[str, Any]]) -> tuple[str, int]:
    line_no, row = item
    ts = row.get("created_at_utc") or row.get("ts_utc") or row.get("ts") or ""
    try:
        parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        ts_key = parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        ts_key = str(ts or "")
    return ts_key, int(line_no or 0)


def _is_legacy_missing_exit_order(row: dict[str, Any]) -> bool:
    if row.get("event_type") != "position_closed":
        return False
    if row.get("exit_reconciliation_status") != "RECONCILED_FROM_ACCOUNT_HISTORY":
        return False
    missing = row.get("exit_reconciliation_missing_fields")
    if not isinstance(missing, list):
        missing = []
    return (
        row.get("broker_exit_deal_hash_sha256") not in (None, "")
        and row.get("broker_exit_position_hash_sha256") not in (None, "")
        and row.get("broker_exit_order_hash_sha256") in (None, "")
        and "broker_exit_order_ticket" not in missing
    )


def _repair_row(line_no: int, row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    identity = {
        "namespace": row.get("namespace"),
        "symbol": row.get("symbol"),
        "sleeve": row.get("sleeve"),
        "candidate_id": row.get("candidate_id"),
        "ticket_hash_sha256": row.get("ticket_hash_sha256"),
        "closed_at_utc": row.get("closed_at_utc"),
        "source_packet_hash_sha256": row.get("packet_hash_sha256"),
        "source_line_no": line_no,
    }
    return {
        "schema": "gtos.runtime_learning_packet_repair_ledger.v1",
        "generated_at_utc": generated_at,
        "repair_type": "legacy_reconciled_exit_missing_order_ticket_field",
        "repair_status": "normalized_by_declaring_missing_broker_exit_order_ticket",
        "runtime_effect_boundary": "offline_observation_no_broker_or_config_mutation",
        "identity": identity,
        "normalized_exit_reconciliation_missing_fields": ["broker_exit_order_ticket"],
        "repair_hash_sha256": stable_hash(identity, prefix="runtime_learning_packet_repair"),
    }


def _load_trade_record_enrichment_index(repo_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Index durable trade records by redacted runtime packet identity.

    Runtime-learning packets are append-only, so a close packet can honestly
    record missing broker-real PnL before a later repair reconciles account
    history into the durable trade record. The advisory is offline/read-only,
    so it can safely consume the repaired trade-record accounting without
    rewriting packets or touching broker state.
    """

    root = repo_root / TRADE_RECORD_ROOT
    if not root.exists():
        return {}

    index: dict[tuple[str, str], dict[str, Any]] = {}
    for record_path in root.glob("*/trade_records/*.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict):
            continue
        namespace = record_path.parent.parent.name
        execution = record.get("execution")
        if not isinstance(execution, dict):
            execution = {}
        ticket_hash = execution.get("ticket_hash_sha256") or record.get("ticket_hash_sha256")
        if not ticket_hash:
            continue
        index[(namespace, str(ticket_hash))] = record
    return index


def _enrich_closed_row_from_trade_record(
    row: dict[str, Any],
    trade_record_index: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    if row.get("event_type") != "position_closed":
        return row, False
    namespace = row.get("namespace")
    ticket_hash = row.get("ticket_hash_sha256")
    if not namespace or not ticket_hash:
        return row, False
    record = trade_record_index.get((str(namespace), str(ticket_hash)))
    if not record:
        return row, False

    execution = record.get("execution")
    if not isinstance(execution, dict):
        execution = {}

    enriched = dict(row)
    changed = False
    for field in TRADE_RECORD_ENRICHMENT_FIELDS:
        value = execution.get(field)
        if value in (None, ""):
            value = record.get(field)
        if value in (None, ""):
            continue
        current = enriched.get(field)
        if current in (None, "", "NO_EXIT_DEAL_FOUND", "source_required_for_broker_real_entry_label"):
            enriched[field] = value
            changed = True

    if changed:
        enriched["advisory_trade_record_enrichment_status"] = "enriched_from_durable_trade_record"
        enriched["advisory_trade_record_enrichment_source"] = "pipeline_state/ultimate_book/*/trade_records"
    return enriched, changed


def _close_identity(row: dict[str, Any]) -> str:
    material = {
        "ticket_hash_sha256": row.get("ticket_hash_sha256"),
        "candidate_id": row.get("candidate_id"),
        "namespace": row.get("namespace"),
        "symbol": row.get("symbol"),
        "sleeve": row.get("sleeve"),
        "closed_at_utc": row.get("closed_at_utc"),
        "close_action": row.get("close_action"),
    }
    return stable_hash(material, prefix="runtime_learning_close")


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _date_key(value: Any) -> str:
    text = str(value or "")
    if len(text) >= 10:
        return text[:10]
    return "unknown"


def _daily_sleeve_summary(closed_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str | None], list[dict[str, Any]]] = defaultdict(list)
    for row in closed_rows:
        day = _date_key(row.get("closed_at_utc") or row.get("created_at_utc"))
        grouped[(day, str(row.get("sleeve") or "unknown"), row.get("namespace"))].append(row)
    out: list[dict[str, Any]] = []
    for (day, sleeve, namespace), rows in sorted(grouped.items()):
        pnl_values = [_float_or_none(row.get("broker_realized_pnl")) for row in rows]
        captured = [value for value in pnl_values if value is not None]
        pnl_sum = sum(captured) if captured else None
        out.append({
            "day": day,
            "namespace": namespace,
            "sleeve": sleeve,
            "closed_trade_count": len(rows),
            "broker_realized_pnl_captured_count": len(captured),
            "broker_realized_pnl_sum": pnl_sum,
            "broker_realized_pnl_mean": (pnl_sum / len(captured)) if captured else None,
            "win_count": sum(1 for value in captured if value > 0),
            "loss_count": sum(1 for value in captured if value < 0),
            "flat_count": sum(1 for value in captured if value == 0),
            "learning_application_status": "advisory_only_owner_gated_no_live_rerate_mutation",
        })
    return out


def build_advisory(repo_root: Path, packet_log_path: str, output_dir: str) -> dict[str, Any]:
    generated_at = _utc_now_iso()
    packet_path = repo_root / packet_log_path
    out_dir = repo_root / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    repair_ledger_path = out_dir / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER.jsonl"
    repair_history_path = out_dir / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER_HISTORY.jsonl"
    packet_row_count = 0
    parse_error_count = 0
    validation_issue_count = 0
    repair_count = 0
    legacy_nonterminal_broker_realized_pnl_normalized_count = 0
    future_nonterminal_broker_realized_pnl_issue_count = 0
    parse_errors: list[dict[str, Any]] = []
    validation_issues: list[dict[str, Any]] = []
    legacy_nonterminal_broker_realized_pnl_examples: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    repair_ledger_lines: list[str] = []
    closed_by_identity: dict[str, tuple[tuple[str, int], int, dict[str, Any]]] = {}
    trade_record_index = _load_trade_record_enrichment_index(repo_root)
    closed_trade_record_enrichment_count = 0
    packet_log_line_count_at_source_read = 0
    packet_log_last_seen_created_at_utc = None
    packet_log_last_seen_event_type = None
    packet_event_type_counts: dict[str, int] = defaultdict(int)
    packet_log_last_modified_utc = None
    seen_packet_hashes: set[str] = set()
    packet_duplicate_hash_deduped_count = 0
    packet_processing_row_count_after_hash_dedupe = 0
    try:
        if packet_path.exists():
            packet_log_last_modified_utc = datetime.fromtimestamp(
                packet_path.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat()
    except OSError:
        packet_log_last_modified_utc = None

    for line_no, row, parse_error in _iter_jsonl_rows(packet_path):
        if line_no is not None:
            packet_log_line_count_at_source_read = max(
                packet_log_line_count_at_source_read,
                line_no,
            )
        if parse_error is not None:
            parse_error_count += 1
            if len(parse_errors) < 20:
                parse_errors.append(parse_error)
            continue
        if row is None or line_no is None:
            continue
        packet_row_count += 1
        packet_log_last_seen_created_at_utc = (
            row.get("created_at_utc")
            or row.get("ts_utc")
            or row.get("ts")
            or packet_log_last_seen_created_at_utc
        )
        packet_log_last_seen_event_type = row.get("event_type") or packet_log_last_seen_event_type
        packet_event_type_counts[str(row.get("event_type") or "unknown")] += 1
        packet_hash = str(row.get("packet_hash_sha256") or "")
        if packet_hash:
            if packet_hash in seen_packet_hashes:
                packet_duplicate_hash_deduped_count += 1
                continue
            seen_packet_hashes.add(packet_hash)
        packet_processing_row_count_after_hash_dedupe += 1
        nonterminal_pnl_fields = nonterminal_broker_realized_pnl_fields(row)
        if nonterminal_pnl_fields:
            if is_legacy_nonterminal_broker_realized_pnl_packet(row):
                legacy_nonterminal_broker_realized_pnl_normalized_count += 1
                if len(legacy_nonterminal_broker_realized_pnl_examples) < 20:
                    legacy_nonterminal_broker_realized_pnl_examples.append({
                        "line": line_no,
                        "created_at_utc": row.get("created_at_utc"),
                        "namespace": row.get("namespace"),
                        "event_type": row.get("event_type"),
                        "symbol": row.get("symbol"),
                        "sleeve": row.get("sleeve"),
                        "fields": nonterminal_pnl_fields,
                    })
            else:
                future_nonterminal_broker_realized_pnl_issue_count += 1
        ok, issues = validate_runtime_learning_packet(row)
        if not ok:
            validation_issue_count += 1
            if len(validation_issues) < 20:
                validation_issues.append({"line": line_no, "issues": issues})
        if _is_legacy_missing_exit_order(row):
            repair = _repair_row(line_no, row, generated_at)
            repair_ledger_lines.append(json.dumps(repair, sort_keys=True, default=str) + "\n")
            repairs.append(repair)
            repair_count += 1
        if row.get("event_type") == "position_closed":
            row, enriched = _enrich_closed_row_from_trade_record(row, trade_record_index)
            if enriched:
                closed_trade_record_enrichment_count += 1
            identity = _close_identity(row)
            sort_key = _packet_processing_sort_key((line_no, row))
            previous = closed_by_identity.get(identity)
            if previous is None or sort_key >= previous[0]:
                # Preserve the old "latest chronological close wins" contract
                # without retaining and sorting every full runtime packet.
                closed_by_identity[identity] = (sort_key, line_no, row)

    _write_text_atomic(repair_ledger_path, "".join(repair_ledger_lines))

    existing_repair_hashes: set[str] = set()
    if repair_history_path.exists():
        for _line_no, row, _parse_error in _iter_jsonl_rows(repair_history_path):
            if isinstance(row, dict) and row.get("repair_hash_sha256"):
                existing_repair_hashes.add(str(row.get("repair_hash_sha256")))
    with repair_history_path.open("a", encoding="utf-8") as history_handle:
        for repair in repairs:
            repair_hash = str(repair.get("repair_hash_sha256") or "")
            if repair_hash and repair_hash in existing_repair_hashes:
                continue
            history_handle.write(json.dumps(repair, sort_keys=True, default=str) + "\n")
            if repair_hash:
                existing_repair_hashes.add(repair_hash)

    closed_rows = [row for _sort_key, _line_no, row in closed_by_identity.values()]
    closed_pnl_captured_count = sum(
        1 for row in closed_rows if _float_or_none(row.get("broker_realized_pnl")) is not None
    )
    advisory = {
        "schema": "gtos.runtime_learning_daily_advisory.v1",
        "generated_at_utc": generated_at,
        "runtime_effect_boundary": "offline_observation_no_broker_or_config_mutation",
        "packet_log_path": packet_log_path,
        "packet_log_exists_at_source_read": packet_path.exists(),
        "packet_log_last_modified_utc": packet_log_last_modified_utc,
        "packet_log_line_count_at_source_read": packet_log_line_count_at_source_read,
        "packet_log_last_seen_created_at_utc": packet_log_last_seen_created_at_utc,
        "packet_log_last_seen_event_type": packet_log_last_seen_event_type,
        "packet_event_type_counts_at_source_read": dict(sorted(packet_event_type_counts.items())),
        "packet_row_count": packet_row_count,
        "packet_processing_order": (
            "single_pass_source_stream_deduped_by_packet_hash;"
            "closed_identity_selects_max_created_at_utc_then_source_line"
        ),
        "packet_processing_row_count_after_hash_dedupe": packet_processing_row_count_after_hash_dedupe,
        "packet_duplicate_hash_deduped_count": packet_duplicate_hash_deduped_count,
        "packet_parse_error_count": parse_error_count,
        "packet_validation_issue_count_after_legacy_normalization": validation_issue_count,
        "legacy_exit_order_missing_field_repair_count": repair_count,
        "legacy_nonterminal_broker_realized_pnl_normalized_count": (
            legacy_nonterminal_broker_realized_pnl_normalized_count
        ),
        "legacy_nonterminal_broker_realized_pnl_examples": legacy_nonterminal_broker_realized_pnl_examples,
        "future_nonterminal_broker_realized_pnl_issue_count": future_nonterminal_broker_realized_pnl_issue_count,
        "trade_record_enrichment_index_count": len(trade_record_index),
        "closed_trade_record_enrichment_count": closed_trade_record_enrichment_count,
        "deduped_closed_trade_count": len(closed_rows),
        "closed_trade_pnl_captured_count": closed_pnl_captured_count,
        "closed_trade_pnl_missing_after_enrichment_count": len(closed_rows) - closed_pnl_captured_count,
        "daily_sleeve_outcomes": _daily_sleeve_summary(closed_rows),
        "owner_gated_learning_rerate_candidate_map": {},
        "learning_rerate_application_status": "proposal_only_not_applied_to_live_config",
        "parse_errors": parse_errors,
        "validation_issues": validation_issues,
        "repair_ledger_path": str(Path(output_dir) / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER.jsonl"),
        "repair_history_ledger_path": str(
            Path(output_dir) / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER_HISTORY.jsonl"
        ),
    }

    _write_text_atomic(
        out_dir / "RUNTIME_LEARNING_DAILY_ADVISORY.json",
        json.dumps(advisory, indent=2, sort_keys=True, default=str) + "\n",
    )
    return advisory


def _summary(advisory: dict[str, Any], output_dir: str) -> dict[str, Any]:
    return {
        "ok": advisory["packet_parse_error_count"] == 0
        and advisory["packet_validation_issue_count_after_legacy_normalization"] == 0,
        "generated_at_utc": advisory.get("generated_at_utc"),
        "packet_row_count": advisory["packet_row_count"],
        "repair_count": advisory["legacy_exit_order_missing_field_repair_count"],
        "deduped_closed_trade_count": advisory["deduped_closed_trade_count"],
        "output_dir": output_dir,
    }


def _print_summary(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


def _build_requested_advisories(args) -> list[dict[str, Any]]:
    """Build the primary advisory and, when configured, one external experiment advisory."""
    requests = [(REPO_ROOT, args.packet_log_path, args.output_dir)]
    if args.additional_repo_root:
        requests.append((
            Path(args.additional_repo_root).resolve(),
            args.additional_packet_log_path or args.packet_log_path,
            args.additional_output_dir or args.output_dir,
        ))
    built = []
    for root, packet_log_path, output_dir in requests:
        advisory = build_advisory(root, packet_log_path, output_dir)
        built.append({
            "repo_root": str(root),
            "packet_log_path": packet_log_path,
            "output_dir": output_dir,
            "summary": _summary(advisory, output_dir),
        })
    return built


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-log-path", default=DEFAULT_LOG_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--additional-repo-root",
        default=None,
        help="Optional external experiment repo whose packet ledger is consumed in the same supervised loop.",
    )
    parser.add_argument("--additional-packet-log-path", default=None)
    parser.add_argument("--additional-output-dir", default=None)
    parser.add_argument(
        "--loop-seconds",
        type=float,
        default=0.0,
        help="Refresh advisory forever at this interval; 0 runs once.",
    )
    args = parser.parse_args()
    repo_root = REPO_ROOT
    loop_seconds = max(float(args.loop_seconds or 0.0), 0.0)
    if loop_seconds <= 0.0:
        built = _build_requested_advisories(args)
        _print_summary({"ok": all(item["summary"]["ok"] for item in built), "sources": built})
        return 0

    sleep_seconds = max(loop_seconds, MIN_LOOP_SECONDS)
    while True:
        try:
            built = _build_requested_advisories(args)
            _print_summary({"ok": all(item["summary"]["ok"] for item in built), "sources": built})
        except Exception as exc:  # pragma: no cover - daemon resilience path.
            _print_summary({
                "ok": False,
                "generated_at_utc": _utc_now_iso(),
                "error": repr(exc),
                "output_dir": args.output_dir,
            })
        time.sleep(sleep_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
