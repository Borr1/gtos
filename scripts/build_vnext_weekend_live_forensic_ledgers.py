from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28"

EXPECTED_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

PACKET_REQUIRED_FIELD_ALIASES = {
    "candidate_id": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "candidate_id"),
        ("moonshot_broader_origin_candidate", "candidate_id"),
        ("decision_pipeline", "gtos_vnext_runtime", "evidence", "broader_origin_candidate_id"),
    ],
    "symbol": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "symbol"),
        ("metadata", "symbol"),
    ],
    "broker_symbol": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "broker_symbol"),
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "broker_spec_snapshot", "broker_symbol"),
        ("moonshot_broader_origin_candidate", "source_symbol"),
        ("instrumentation", "broker_symbol"),
    ],
    "origin_family": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "candidate_origin_family"),
        ("moonshot_broader_origin_candidate", "candidate_origin_family"),
        ("decision_pipeline", "gtos_vnext_runtime", "event", "candidate_origin_family"),
    ],
    "side": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "side"),
        ("decision_pipeline", "ai_direction"),
    ],
    "session_or_kz": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "kill_zone"),
        ("metadata", "kill_zone"),
    ],
    "candle_time": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "candidate_identity", "candle_close_utc"),
        ("metadata", "candle_time"),
    ],
    "mso_context": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "mso_context"),
        ("mso",),
    ],
    "gate1_result": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "gates", "gate1_final_after_repair"),
        ("decision_pipeline", "gate1_result"),
    ],
    "gate3_result": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "gates", "gate3"),
        ("decision_pipeline", "gate3_result"),
    ],
    "dynamic_policy_selected": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "dynamic_policy", "selected_policy"),
        ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution", "selected_policy"),
        ("instrumentation", "gtos_vnext_dynamic_policy_selected"),
    ],
    "execution_policy_id": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "dynamic_policy", "execution_policy_id"),
        ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution", "execution_policy_id"),
        ("instrumentation", "gtos_vnext_execution_policy_id"),
    ],
    "selected_cell_risk_pct": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "selected_cell_risk_proof", "risk_pct"),
        ("decision_pipeline", "gtos_vnext_executable_geometry_repair", "selected_cell_risk_check", "risk_pct"),
        ("instrumentation", "gtos_vnext_selected_cell_risk_pct"),
    ],
    "selected_cell_risk_cell_id": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "selected_cell_risk_proof", "cell_id"),
        ("decision_pipeline", "gtos_vnext_executable_geometry_repair", "selected_cell_risk_check", "cell_id"),
        ("instrumentation", "gtos_vnext_selected_cell_risk_cell_id"),
    ],
    "prop_action": [
        ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "dynamic_policy", "prop_action"),
        ("decision_pipeline", "gtos_vnext_prop_safe_selector", "action"),
        ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution", "prop_action"),
        ("instrumentation", "gtos_vnext_prop_safe_selector_action"),
    ],
    "final_outcome": [("decision_pipeline", "final_outcome")],
    "old_primary_analyzer_called": [("decision_pipeline", "old_primary_analyzer_called")],
    "old_l2_required": [("decision_pipeline", "old_l2_required")],
}

OLD_SYSTEM_MARKERS = [
    "live_current_j46_j49",
    "fixed_1.5R",
    "fixed 1.5R",
    "static 1.5R",
    "old PrimaryAnalyzer",
    "old L2",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-05-28T00:00:00Z")
    parser.add_argument("--end", default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--expected-trade-records",
        type=int,
        default=590,
        help="May 28-30 forensic anchor floor; newer live records are included.",
    )
    parser.add_argument(
        "--expected-candidate-records",
        type=int,
        default=588,
        help="May 28-30 candidate anchor floor; newer live candidates are included.",
    )
    parser.add_argument("--expected-non-candidate-index-records", type=int, default=2)
    parser.add_argument("--expected-malformed-tmp-records", type=int, default=15)
    parser.add_argument("--expected-prop-deferrals", type=int, default=45)
    parser.add_argument("--expected-placed-orders", type=int, default=8)
    return parser.parse_args()


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_path(data: Any, path: tuple[str, ...], default=None):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def first_present(data: dict, paths: list[tuple[str, ...]], default=None):
    for path in paths:
        value = get_path(data, path)
        if value not in (None, "", []):
            return value
    return default


def packet_field(record: dict, name: str, default=None):
    return first_present(record, PACKET_REQUIRED_FIELD_ALIASES.get(name, []), default)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_contains(path: Path, text: str) -> bool:
    try:
        return text in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def current_code_repair_contracts() -> dict[str, Any]:
    orchestrator = ROOT / "src" / "components" / "orchestrator.py"
    permissions = ROOT / "src" / "components" / "permissions.py"
    execution = ROOT / "src" / "components" / "execution.py"
    return {
        "no_candidate_native_writer_present": source_contains(
            orchestrator,
            "native_live_no_candidate_writer",
        ),
        "pre_dynamic_prop_projection_only_present": source_contains(
            orchestrator,
            "pre_dynamic_projection_only_",
        ),
        "open_position_risk_not_defaulted_to_base_present": source_contains(
            orchestrator,
            "ticket_bound_vnext_risk_not_found_no_base_risk_default",
        ),
        "same_symbol_lifecycle_conflict_gate_present": source_contains(
            permissions,
            "same_symbol_position_conflict_multi_ticket_lifecycle_unsupported",
        ),
        "partial_close_residual_resolver_present": source_contains(
            execution,
            "_find_residual_position_after_partial",
        ) and not source_contains(execution, "our_positions[0]"),
        "sltp_modify_diagnostics_present": source_contains(
            execution,
            "_record_sltp_modify_diagnostic",
        ),
        "gate3_pre_dynamic_policy_intent_present": source_contains(
            orchestrator,
            "pre_dynamic_current_production_policy_intent",
        ),
    }


def stringify_counter(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.items()}


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def iter_jsonl(path: Path, start: datetime, end: datetime | None) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rows.append({
                    "parse_error": True,
                    "path": str(path),
                    "line_no": line_no,
                })
                continue
            dt = parse_dt(
                row.get("timestamp_utc")
                or row.get("created_at_utc")
                or row.get("candle_time_utc")
                or row.get("checked_candle_time_utc")
            )
            if dt is not None and dt < start:
                continue
            if dt is not None and end is not None and dt >= end:
                continue
            row["_source_path"] = str(path)
            row["_source_line"] = line_no
            rows.append(row)
    return rows


def record_time(record: dict, path: Path) -> datetime | None:
    metadata = record.get("metadata") or {}
    dt = parse_dt(
        metadata.get("candle_time")
        or metadata.get("candle_close_utc")
        or metadata.get("date")
    )
    if dt is not None:
        return dt
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)


def load_trade_records(start: datetime, end: datetime | None) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    malformed: list[dict] = []
    base = ROOT / "knowledge_base" / "trade_records"
    for path in sorted(base.glob("*/*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001
            malformed.append({
                "path": str(path),
                "parse_error": str(exc),
                "symbol": path.parent.name,
            })
            continue
        dt = record_time(record, path)
        if dt is not None and dt < start:
            continue
        if dt is not None and end is not None and dt >= end:
            continue
        record["_source_path"] = str(path)
        record["_record_time_utc"] = dt.isoformat() if dt else None
        if path.name == "_pending_records_index.json":
            record["_non_candidate_file_type"] = "pending_records_index"
        rows.append(record)
    for path in sorted(base.glob("*/*.tmp")):
        dt = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if dt < start:
            continue
        if end is not None and dt >= end:
            continue
        malformed.append({
            "path": str(path),
            "parse_error": "partial_tmp_trade_record_not_finalized_json",
            "symbol": path.parent.name,
            "record_time_utc": dt.isoformat(),
            "classification": "malformed_tmp_finalization_gap",
        })
    return rows, malformed


def terminal_state(outcome: str | None, record: dict) -> str:
    outcome = outcome or "UNKNOWN_OUTCOME"
    reason = str(
        first_present(
            record,
            [
                ("decision_pipeline", "permission_reason"),
                ("decision_pipeline", "gtos_vnext_runtime", "reason"),
                ("decision_pipeline", "final_outcome"),
            ],
            "",
        )
    )
    record_text = json.dumps(record, sort_keys=True)
    if outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN":
        return "order placed"
    if "DEFERRED_GTOS_VNEXT_PROP_RESET" in outcome:
        return "prop budget deferred/reduced/blocked"
    if "REJECTED_GATE1" in outcome:
        return "Gate1 rejected"
    if "REJECTED_GATE3" in outcome:
        return "Gate3 rejected"
    if "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC" in outcome:
        if "selected_cell_risk_not_verified_or_zero" in reason or "selected_cell_risk_not_verified_or_zero" in record_text:
            return "selected-cell risk missing/zero"
        if "framework_not_activated" in reason or "framework_not_activated" in record_text:
            return "selector/framework/session/hour/symbol alias mismatch"
        return "generated but dynamic refused"
    return outcome


def packet_missing_fields(record: dict) -> list[str]:
    missing: list[str] = []
    for name in PACKET_REQUIRED_FIELD_ALIASES:
        if packet_field(record, name) in (None, "", []):
            missing.append(name)
    return missing


def event_row(record: dict) -> dict:
    if record.get("_non_candidate_file_type") == "pending_records_index":
        return {
            "event_type": "trade_record_index_metadata",
            "source_path": record.get("_source_path"),
            "record_time_utc": record.get("_record_time_utc"),
            "trade_id": None,
            "candidate_id": None,
            "symbol": Path(str(record.get("_source_path") or "")).parent.name or None,
            "broker_symbol": None,
            "origin_family": None,
            "framework": None,
            "side": None,
            "session": None,
            "route_session": None,
            "kill_zone": None,
            "utc_hour_bucket": None,
            "candle_time_utc": None,
            "outcome": "NON_CANDIDATE_PENDING_RECORD_INDEX",
            "terminal_state": "NON_CANDIDATE_PENDING_RECORD_INDEX",
            "gate1_passed": None,
            "gate1_denial_reason": None,
            "gate3_passed": None,
            "gate3_denial_reason": None,
            "selected_policy": None,
            "execution_policy_id": None,
            "dynamic_trigger_r": None,
            "dynamic_final_target_r": None,
            "dynamic_pullback_r": None,
            "prop_action": None,
            "selected_cell_risk_allowed": None,
            "selected_cell_risk_pct": None,
            "selected_cell_risk_cell_id": None,
            "selected_cell_risk_match_reason": None,
            "broader_origin_allowed": None,
            "broader_origin_match_reason": None,
            "source_mode": None,
            "source_path_feature_status": None,
            "source_window_complete": None,
            "old_primary_analyzer_called": "not_applicable_non_candidate_index",
            "old_l2_required": "not_applicable_non_candidate_index",
            "missing_packet_fields": [],
            "old_system_marker_hits": [],
            "j46_j49_mentions": 0,
            "classification_proof": "metadata_index_file_not_live_candidate_packet",
        }
    metadata = record.get("metadata") or {}
    pipeline = record.get("decision_pipeline") or {}
    packet = pipeline.get("gtos_vnext_candidate_intelligence_packet") or {}
    dynamic_policy = packet.get("dynamic_policy") or {}
    selected_risk = packet.get("selected_cell_risk_proof") or {}
    geometry = packet.get("geometry") or {}
    dynamic_trigger = dynamic_policy.get("dynamic_trigger_final_pullback") or {}
    runtime = pipeline.get("gtos_vnext_runtime") or {}
    event = runtime.get("event") or {}
    evidence = runtime.get("evidence") or {}
    moonshot_candidate = record.get("moonshot_broader_origin_candidate") or {}
    dynamic_execution = pipeline.get("gtos_vnext_moonshot_dynamic_execution") or {}
    details = (
        event.get("gtos_vnext_source_event_details")
        or pipeline.get("gtos_vnext_source_event_details")
        or dynamic_execution.get("source_event")
        or moonshot_candidate
        or {}
    )
    outcome = pipeline.get("final_outcome")
    gate1 = pipeline.get("gate1_result") or {}
    gate3 = pipeline.get("gate3_result") or {}
    selected_policy = packet_field(record, "dynamic_policy_selected")
    execution_policy_id = packet_field(record, "execution_policy_id")
    candidate_id = packet_field(record, "candidate_id") or metadata.get("trade_id")
    text = json.dumps(record, sort_keys=True)
    dynamic_refusal_reasons = (
        dynamic_execution.get("refusal_reasons")
        or pipeline.get("gtos_vnext_moonshot_dynamic_refusal_reasons")
        or (packet.get("refusal_and_repair_reasons") or {}).get("recorded_dynamic_refusal_reasons")
        or []
    )
    if isinstance(dynamic_refusal_reasons, str):
        dynamic_refusal_reasons = [dynamic_refusal_reasons]
    return {
        "event_type": "trade_record",
        "source_path": record.get("_source_path"),
        "record_time_utc": record.get("_record_time_utc"),
        "trade_id": metadata.get("trade_id"),
        "candidate_id": candidate_id,
        "symbol": metadata.get("symbol"),
        "broker_symbol": packet_field(record, "broker_symbol"),
        "origin_family": packet_field(record, "origin_family"),
        "framework": pipeline.get("ai_framework") or event.get("framework"),
        "side": pipeline.get("ai_direction") or event.get("side"),
        "session": event.get("session") or metadata.get("kill_zone"),
        "route_session": event.get("route_session") or details.get("route_session"),
        "kill_zone": metadata.get("kill_zone"),
        "utc_hour_bucket": event.get("utc_hour_bucket") or details.get("utc_hour_bucket"),
        "candle_time_utc": metadata.get("candle_time") or event.get("candle_time_utc"),
        "outcome": outcome,
        "terminal_state": terminal_state(outcome, record),
        "gate1_passed": gate1.get("passed"),
        "gate1_denial_reason": get_path(gate1, ("details", "denial_reason")),
        "gate3_passed": gate3.get("passed"),
        "gate3_denial_reason": get_path(gate3, ("details", "denial_reason")),
        "selected_policy": selected_policy,
        "execution_policy_id": execution_policy_id,
        "dynamic_trigger_r": (
            dynamic_trigger.get("partial_trigger_r")
            or dynamic_trigger.get("be_trigger_r")
            or get_path(geometry, ("dynamic_target", "trigger_r"))
        ),
        "dynamic_final_target_r": (
            dynamic_trigger.get("partial_final_target_r")
            or dynamic_trigger.get("be_final_target_r")
            or get_path(geometry, ("dynamic_target", "final_target_r"))
        ),
        "dynamic_pullback_r": dynamic_trigger.get("momentum_pullback_r"),
        "prop_action": packet_field(record, "prop_action"),
        "dynamic_refusal_reasons": dynamic_refusal_reasons,
        "selected_cell_risk_allowed": selected_risk.get("allowed") or details.get("selected_cell_risk_allowed"),
        "selected_cell_risk_pct": packet_field(record, "selected_cell_risk_pct"),
        "selected_cell_risk_cell_id": packet_field(record, "selected_cell_risk_cell_id"),
        "selected_cell_risk_match_reason": (
            selected_risk.get("match_reason")
            or details.get("selected_cell_risk_match_reason")
        ),
        "broader_origin_allowed": details.get("broader_origin_allowed"),
        "broader_origin_match_reason": details.get("broader_origin_match_reason"),
        "source_mode": details.get("source_mode"),
        "source_path_feature_status": details.get("source_path_feature_status"),
        "source_window_complete": details.get("source_window_complete"),
        "old_primary_analyzer_called": pipeline.get("old_primary_analyzer_called"),
        "old_l2_required": pipeline.get("old_l2_required"),
        "missing_packet_fields": packet_missing_fields(record),
        "old_system_marker_hits": [marker for marker in OLD_SYSTEM_MARKERS if marker in text],
        "j46_j49_mentions": text.count("J46") + text.count("J49"),
    }


def build_prop_ledger(events: list[dict], records_by_path: dict[str, dict]) -> list[dict]:
    rows = []
    for event in events:
        if event.get("outcome") != "DEFERRED_GTOS_VNEXT_PROP_RESET":
            continue
        record = records_by_path.get(event["source_path"], {})
        details = (
            get_path(record, ("decision_pipeline", "gtos_vnext_runtime", "event", "gtos_vnext_source_event_details"), {})
            or get_path(record, ("decision_pipeline", "gtos_vnext_source_event_details"), {})
            or {}
        )
        prop_before = get_path(record, ("decision_pipeline", "gtos_vnext_prop_safe_selector"), {}) or {}
        prop_after = (
            get_path(record, ("decision_pipeline", "gtos_vnext_prop_safe_selector_after_geometry_repair"), {})
            or prop_before
        )
        external = prop_after.get("external_rule_projection") or {}
        reset = prop_after.get("reset_window") or {}
        exposure = (
            prop_after.get("exposure_breakdown")
            or prop_after.get("current_exposure")
            or prop_after.get("existing_risk")
            or {}
        )
        rows.append({
            **event,
            "prop_reconstruction_status": "row_level_raw_fields_extracted",
            "account_balance": (
                external.get("initial_balance")
                or first_present(record, [("account_balance",), ("trade_parameters", "account_balance")])
            ),
            "account_equity": (
                exposure.get("current_equity")
                or first_present(record, [("account_equity",), ("trade_parameters", "account_equity")])
            ),
            "day_start_baseline": (
                external.get("day_start_equity_or_balance_baseline")
                or details.get("day_start_baseline")
            ),
            "realized_broker_pnl": details.get("realized_broker_pnl"),
            "open_position_worst_case_risk": (
                exposure.get("open_position_risk_amount")
                or exposure.get("open_position_worst_case_risk")
                or details.get("open_position_worst_case_risk")
            ),
            "pending_order_worst_case_risk": (
                exposure.get("pending_order_risk_amount")
                or exposure.get("pending_order_worst_case_risk")
                or details.get("pending_order_worst_case_risk")
            ),
            "new_trade_sl_risk_amount": exposure.get("new_trade_sl_risk_amount"),
            "spread_slippage_commission_buffer_amount": exposure.get(
                "spread_slippage_commission_buffer_amount"
            ),
            "risk_base_amount": exposure.get("risk_base_amount"),
            "current_equity": exposure.get("current_equity"),
            "new_trade_risk_pct": event.get("selected_cell_risk_pct"),
            "prop_governor_action": prop_after.get("action") or details.get("prop_governor_action"),
            "prop_governor_reason": prop_after.get("reason") or details.get("prop_governor_reason"),
            "reset_window": reset,
            "external_rule_projection": external,
            "internal_overlay_projection": prop_after.get("internal_overlay_projection"),
            "max_allowed_new_trade_risk_pct": prop_after.get("max_allowed_new_trade_risk_pct"),
            "missing_money_fields": [
                name for name in [
                    "day_start_baseline",
                    "realized_broker_pnl",
                    "open_position_worst_case_risk",
                    "pending_order_worst_case_risk",
                ]
                if (
                    details.get(name) is None
                    and record.get(name) is None
                    and external.get(name) is None
                    and exposure.get(name) is None
                    and not (
                        name == "open_position_worst_case_risk"
                        and exposure.get("open_position_risk_amount") is not None
                    )
                    and not (
                        name == "pending_order_worst_case_risk"
                        and exposure.get("pending_order_risk_amount") is not None
                    )
                    and not (
                        name == "day_start_baseline"
                        and external.get("day_start_equity_or_balance_baseline") is not None
                    )
                )
            ],
        })
    return rows


def lifecycle_rows(start: datetime, end: datetime | None) -> list[dict]:
    paths = [
        ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl",
        ROOT / "shadow_logs" / "slippage.jsonl",
        ROOT / "shadow_logs" / "time_in_trade.jsonl",
        ROOT / "shadow_logs" / "daily_pnl_history.jsonl",
        ROOT / "shadow_logs" / "j46_j49_shadow_outcomes.jsonl",
        ROOT / "shadow_logs" / "notification_queue_dead_zone_status.jsonl",
    ]
    rows: list[dict] = []
    for path in paths:
        rows.extend(iter_jsonl(path, start, end))
    return rows


def build_order_reconciliation(events: list[dict], lifecycle: list[dict]) -> list[dict]:
    placed = [row for row in events if row.get("outcome") == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"]
    by_candidate: dict[str, list[dict]] = defaultdict(list)
    by_trade: dict[str, list[dict]] = defaultdict(list)
    for row in lifecycle:
        candidate_id = row.get("candidate_id")
        trade_id = row.get("trade_id")
        if candidate_id:
            by_candidate[str(candidate_id)].append(row)
        if trade_id:
            by_trade[str(trade_id)].append(row)
    out: list[dict] = []
    for row in placed:
        events_for_order = []
        if row.get("candidate_id"):
            events_for_order.extend(by_candidate.get(str(row["candidate_id"]), []))
        if row.get("trade_id"):
            events_for_order.extend(by_trade.get(str(row["trade_id"]), []))
        states = Counter(
            str(item.get("broker_fill_state") or item.get("event_type") or item.get("reason") or "unknown")
            for item in events_for_order
        )
        manual = any(
            "manual" in json.dumps(item, sort_keys=True).lower()
            or "ceo" in json.dumps(item, sort_keys=True).lower()
            for item in events_for_order
        )
        broker_realized = [
            item for item in events_for_order
            if item.get("broker_realized_pnl") is not None
            or item.get("profit") is not None
            or item.get("actual_r") is not None
        ]
        out.append({
            **row,
            "lifecycle_event_count": len(events_for_order),
            "lifecycle_state_counts": dict(states),
            "manual_intervention_detected": manual,
            "broker_realized_pnl_rows": len(broker_realized),
            "reconciliation_status": (
                "broker_realized_or_actual_rows_present"
                if broker_realized
                else "pending_broker_history_realized_pnl_join"
            ),
            "lifecycle_examples": events_for_order[:5],
        })
    return out


def load_runtime_rows(start: datetime, end: datetime | None) -> list[dict]:
    return iter_jsonl(ROOT / "shadow_logs" / "gtos_vnext_runtime_decisions.jsonl", start, end)


def build_forward_data(events: list[dict], runtime: list[dict]) -> list[dict]:
    try:
        m1_state = json.loads((ROOT / "pipeline_state" / "m1_capture_state.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        m1_state = {"symbols": {}}
    symbols_state = m1_state.get("symbols") or {}
    event_counts = Counter(row.get("symbol") for row in events)
    runtime_counts = Counter(row.get("symbol") for row in runtime)
    out = []
    for symbol in EXPECTED_SYMBOLS:
        tick_heartbeat_path = ROOT / "pipeline_state" / f"daemon_heartbeat_tick_capture_{symbol}.json"
        try:
            tick_heartbeat = json.loads(tick_heartbeat_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            tick_heartbeat = None
        m1_dir = ROOT / "data" / "m1" / symbol
        tick_dir = ROOT / "data" / "ticks" / symbol
        tick_parquet_count = len(list(tick_dir.glob("2026-05-2*.parquet"))) if tick_dir.exists() else 0
        trade_record_count = int(event_counts.get(symbol, 0))
        runtime_count = int(runtime_counts.get(symbol, 0))
        if trade_record_count == 0 and runtime_count > 0:
            terminal = "live_processing_without_trade_record_candidate"
        elif trade_record_count == 0:
            terminal = "no_vnext_trade_records_written"
        else:
            terminal = "vnext_trade_records_written"
        out.append({
            "symbol": symbol,
            "trade_record_count": trade_record_count,
            "runtime_decision_count": runtime_count,
            "terminal_forward_data_state": terminal,
            "m1_capture_state": symbols_state.get(symbol),
            "m1_dir_exists": m1_dir.exists(),
            "tick_dir_exists": tick_dir.exists(),
            "tick_parquet_count_may28_29": tick_parquet_count,
            "tick_heartbeat_path": str(tick_heartbeat_path),
            "tick_heartbeat_present": tick_heartbeat is not None,
            "tick_heartbeat": tick_heartbeat,
            "missing_or_zero_reasons": [
                reason for reason, condition in [
                    ("no_trade_records_for_symbol", trade_record_count == 0),
                    ("no_runtime_decisions_for_symbol", runtime_count == 0),
                    ("missing_m1_capture_state", symbol not in symbols_state),
                    ("missing_tick_heartbeat", tick_heartbeat is None),
                    ("missing_m1_dir", not m1_dir.exists()),
                    ("missing_tick_dir", not tick_dir.exists()),
                    ("zero_tick_parquet_count", tick_parquet_count == 0),
                ]
                if condition
            ],
        })
    return out


def build_summary(
    *,
    events: list[dict],
    malformed: list[dict],
    runtime: list[dict],
    prop: list[dict],
    orders: list[dict],
    forward: list[dict],
    output_paths: dict[str, Path],
    args: argparse.Namespace,
) -> dict:
    outcome_counts = Counter(row.get("outcome") for row in events)
    terminal_counts = Counter(row.get("terminal_state") for row in events)
    candidate_events = [
        row for row in events
        if row.get("event_type") == "trade_record"
    ]
    non_candidate_index_rows = [
        row for row in events
        if row.get("event_type") == "trade_record_index_metadata"
    ]
    by_symbol: dict[str, dict] = {}
    for symbol in EXPECTED_SYMBOLS:
        symbol_all_rows = [row for row in events if row.get("symbol") == symbol]
        symbol_rows = [row for row in candidate_events if row.get("symbol") == symbol]
        by_symbol[symbol] = {
            "all_records_including_metadata": len(symbol_all_rows),
            "trade_records": len(symbol_rows),
            "outcomes": stringify_counter(Counter(row.get("outcome") for row in symbol_rows)),
            "terminal_states": stringify_counter(Counter(row.get("terminal_state") for row in symbol_rows)),
            "placed_orders": sum(
                1 for row in symbol_rows
                if row.get("outcome") == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
            ),
        }
    old_pa_false = sum(row.get("old_primary_analyzer_called") is False for row in candidate_events)
    old_l2_false = sum(row.get("old_l2_required") is False for row in candidate_events)
    old_unknown = [
        row for row in candidate_events
        if row.get("old_primary_analyzer_called") is not False
        or row.get("old_l2_required") is not False
    ]
    missing_packet_counter = Counter(
        field for row in events for field in row.get("missing_packet_fields", [])
    )
    marker_hits = Counter(
        marker for row in events for marker in row.get("old_system_marker_hits", [])
    )
    repair_contracts = current_code_repair_contracts()
    dynamic_refusal_rows = [
        row for row in candidate_events
        if row.get("outcome") == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"
    ]
    selector_refusal_rows = [
        row for row in dynamic_refusal_rows
        if "framework_not_activated_in_stage13_full_moonshot_selector"
        in json.dumps(row, sort_keys=True)
        or row.get("terminal_state") == "selector/framework/session/hour/symbol alias mismatch"
    ]
    selected_risk_refusal_rows = [
        row for row in dynamic_refusal_rows
        if "selected_cell_risk_not_verified_or_zero" in json.dumps(row, sort_keys=True)
        or row.get("terminal_state") == "selected-cell risk missing/zero"
    ]
    gate3_policy_packet_gaps = [
        row for row in candidate_events
        if row.get("outcome") == "REJECTED_GATE3_CIRCUIT_BREAKER"
        and (
            not row.get("selected_policy")
            or not row.get("execution_policy_id")
        )
    ]
    silent_absence = [
        row for row in forward
        if "no_trade_records_for_symbol" in row.get("missing_or_zero_reasons", [])
    ]
    verification_failures = []
    if len(events) < args.expected_trade_records:
        verification_failures.append({
            "check": "trade_record_count_anchor_floor",
            "expected_minimum": args.expected_trade_records,
            "actual": len(events),
        })
    if len(candidate_events) < args.expected_candidate_records:
        verification_failures.append({
            "check": "candidate_trade_record_count_anchor_floor",
            "expected_minimum": args.expected_candidate_records,
            "actual": len(candidate_events),
        })
    if len(non_candidate_index_rows) != args.expected_non_candidate_index_records:
        verification_failures.append({
            "check": "non_candidate_index_record_count",
            "expected": args.expected_non_candidate_index_records,
            "actual": len(non_candidate_index_rows),
        })
    malformed_tmp_count = sum(
        1 for row in malformed
        if row.get("classification") == "malformed_tmp_finalization_gap"
    )
    if malformed_tmp_count != args.expected_malformed_tmp_records:
        verification_failures.append({
            "check": "malformed_tmp_record_count",
            "expected": args.expected_malformed_tmp_records,
            "actual": malformed_tmp_count,
        })
    if len(prop) < args.expected_prop_deferrals:
        verification_failures.append({
            "check": "prop_deferral_count_anchor_floor",
            "expected_minimum": args.expected_prop_deferrals,
            "actual": len(prop),
        })
    if len(orders) < args.expected_placed_orders:
        verification_failures.append({
            "check": "placed_order_count_anchor_floor",
            "expected_minimum": args.expected_placed_orders,
            "actual": len(orders),
        })
    for check, ok in repair_contracts.items():
        if not ok:
            verification_failures.append({
                "check": f"current_code_contract_missing:{check}",
                "expected": True,
                "actual": ok,
            })
    summary = {
        "schema_version": "vnext_weekend_live_forensic_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "window_start": args.start,
        "window_end": args.end,
        "trade_record_count": len(events),
        "trade_record_anchor_floor": args.expected_trade_records,
        "candidate_trade_record_count": len(candidate_events),
        "candidate_trade_record_anchor_floor": args.expected_candidate_records,
        "non_candidate_index_record_count": len(non_candidate_index_rows),
        "non_candidate_index_examples": non_candidate_index_rows[:5],
        "malformed_record_count": len(malformed),
        "runtime_decision_count": len(runtime),
        "outcome_counts": stringify_counter(outcome_counts),
        "terminal_state_counts": stringify_counter(terminal_counts),
        "by_symbol": by_symbol,
        "placed_order_symbols": stringify_counter(Counter(row.get("symbol") for row in orders)),
        "prop_deferral_count": len(prop),
        "old_primary_analyzer_false_count": old_pa_false,
        "old_l2_required_false_count": old_l2_false,
        "old_primary_or_l2_unknown_count": len(old_unknown),
        "old_primary_or_l2_unknown_examples": old_unknown[:5],
        "missing_packet_field_counts": stringify_counter(missing_packet_counter),
        "old_system_marker_hits": stringify_counter(marker_hits),
        "j46_j49_mention_rows": sum(1 for row in events if row.get("j46_j49_mentions", 0) > 0),
        "dynamic_refusal_count": len(dynamic_refusal_rows),
        "selector_framework_refusal_count": len(selector_refusal_rows),
        "selected_cell_risk_refusal_count": len(selected_risk_refusal_rows),
        "gate3_policy_packet_gap_count": len(gate3_policy_packet_gaps),
        "gate3_policy_packet_gap_examples": gate3_policy_packet_gaps[:10],
        "silent_absence_symbols": silent_absence,
        "silent_absence_classification": (
            "historical_no_candidate_logging_gap_repaired_by_current_code"
            if silent_absence and repair_contracts.get("no_candidate_native_writer_present")
            else "no_silent_absence"
            if not silent_absence
            else "silent_absence_unrepaired"
        ),
        "prop_deferral_classification": (
            "historical_pre_dynamic_budget_projection_repaired_by_current_code"
            if prop and repair_contracts.get("pre_dynamic_prop_projection_only_present")
            else "no_prop_deferrals"
            if not prop
            else "prop_deferral_route_unrepaired"
        ),
        "current_code_repair_contracts": repair_contracts,
        "verification_failures": verification_failures,
        "verification_status": "PASS" if not verification_failures else "FAIL",
        "outputs": {
            name: {
                "path": str(path),
                "sha256": sha256_file(path) if path.exists() else None,
            }
            for name, path in output_paths.items()
        },
    }
    return summary


def main() -> int:
    args = parse_args()
    start = parse_dt(args.start)
    if start is None:
        raise SystemExit("invalid --start")
    end = parse_dt(args.end) if args.end else None
    verification_path = ROUTE_DIR / "LIVE_WEEKEND_FORENSIC_VERIFICATION.json"
    if args.check:
        if not verification_path.exists():
            print(f"missing {verification_path}")
            return 1
        data = json.loads(verification_path.read_text(encoding="utf-8"))
        failures = data.get("verification_failures") or []
        if failures:
            print(json.dumps(failures, indent=2, sort_keys=True))
            return 1
        print("weekend forensic verification PASS")
        return 0

    records, malformed = load_trade_records(start, end)
    events = [event_row(record) for record in records]
    records_by_path = {record["_source_path"]: record for record in records}
    runtime = load_runtime_rows(start, end)
    lifecycle = lifecycle_rows(start, end)
    prop = build_prop_ledger(events, records_by_path)
    orders = build_order_reconciliation(events, lifecycle)
    forward = build_forward_data(events, runtime)

    output_paths = {
        "event_ledger": ROUTE_DIR / "LIVE_WEEKEND_FORENSIC_EVENT_LEDGER.jsonl",
        "prop_ledger": ROUTE_DIR / "LIVE_WEEKEND_PROP_RISK_DEFERRAL_LEDGER.jsonl",
        "order_reconciliation": ROUTE_DIR / "LIVE_WEEKEND_ORDER_RECONCILIATION_LEDGER.jsonl",
        "forward_data": ROUTE_DIR / "LIVE_WEEKEND_FORWARD_DATA_INTEGRITY_LEDGER.jsonl",
        "summary": ROUTE_DIR / "LIVE_WEEKEND_FORENSIC_FUNNEL_SUMMARY.json",
        "verification": verification_path,
    }

    write_jsonl(output_paths["event_ledger"], events)
    write_jsonl(output_paths["prop_ledger"], prop)
    write_jsonl(output_paths["order_reconciliation"], orders)
    write_jsonl(output_paths["forward_data"], forward)
    write_jsonl(ROUTE_DIR / "LIVE_WEEKEND_MALFORMED_TRADE_RECORDS.jsonl", malformed)

    summary = build_summary(
        events=events,
        malformed=malformed,
        runtime=runtime,
        prop=prop,
        orders=orders,
        forward=forward,
        output_paths=output_paths,
        args=args,
    )
    write_json(output_paths["summary"], summary)
    summary["outputs"]["summary"]["sha256"] = sha256_file(output_paths["summary"])
    write_json(output_paths["verification"], summary)
    print(json.dumps({
        "verification_status": summary["verification_status"],
        "trade_record_count": summary["trade_record_count"],
        "outcome_counts": summary["outcome_counts"],
        "placed_order_symbols": summary["placed_order_symbols"],
        "prop_deferral_count": summary["prop_deferral_count"],
        "verification_failures": summary["verification_failures"],
    }, indent=2, sort_keys=True))
    return 0 if summary["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
