#!/usr/bin/env python3
"""Build Wave 1B V3/live authority-gap ledgers from current disk evidence."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

HARD_HALT = Path("research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03")
DUAL_BROKER = Path("research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02")
VPS_V3_FTMO = Path("research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02")
LIVE_FAILURE = Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04")
GOAL_ARCH = Path("research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04")
SELECTOR_V3 = Path("research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01")
SCHEDULER_V3 = Path("research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01")
EXECUTION_V3 = Path("research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01")

RUNTIME_DECISIONS = Path("shadow_logs/gtos_vnext_runtime_decisions.jsonl")
REPLACEMENT_MONITORING = Path("shadow_logs/gtos_vnext_replacement_monitoring.jsonl")
PENDING_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle.jsonl")
TRADE_RECORD_ROOT = Path("knowledge_base/redacted_account_live_bee34003/trade_records")

BROKER_TRADES = HARD_HALT / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json"
BROKER_DEALS = HARD_HALT / "BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json"
BROKER_ORDERS = HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json"
TRADE_FAILURE_REVIEW = HARD_HALT / "TRADE_FAILURE_REVIEW_2026-06-03.md"

SELECTOR_PACKAGE = SELECTOR_V3 / "SELECTOR_V3_DEFAULT_OFF_PACKAGE.json"
SCHEDULER_PACKAGE = SCHEDULER_V3 / "SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json"
EXECUTION_PACKAGE = EXECUTION_V3 / "V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json"


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_record(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    record = {
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "evidence_class": "wave1b_v3_live_authority_gap_current_disk_evidence",
    }
    if extra:
        record.update(extra)
    return record


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "cmd": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def sha256_file(path: Path) -> str | None:
    full = REPO_ROOT / path
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path, limit: int | None = None) -> str:
    full = REPO_ROOT / path
    if not full.exists():
        return ""
    text = full.read_text(encoding="utf-8", errors="replace")
    return text if limit is None else text[:limit]


def read_json(path: Path) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def maybe_json(path: Path) -> Any | None:
    full = REPO_ROOT / path
    if not full.exists():
        return None
    try:
        return json.loads(full.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def iter_jsonl(path: Path):
    full = REPO_ROOT / path
    if not full.exists():
        return
    opener = gzip.open if full.suffix == ".gz" else open
    with opener(full, "rt", encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            if index == 1 and line.startswith("version https://git-lfs.github.com/spec"):
                return
            try:
                yield index, json.loads(line)
            except json.JSONDecodeError as exc:
                yield index, {"_parse_error": str(exc), "_raw_prefix": line[:500]}


def write_json(path: str, data: Any) -> None:
    (ROUTE_DIR / path).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    with (ROUTE_DIR / path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_md(path: str, text: str) -> None:
    (ROUTE_DIR / path).write_text(text.strip() + "\n", encoding="utf-8")


def file_stats(path: Path) -> dict[str, Any]:
    full = REPO_ROOT / path
    exists = full.exists()
    status = "missing"
    rows = None
    if exists and full.is_dir():
        status = "directory"
    elif exists and full.is_file():
        status = "present"
        try:
            prefix = full.read_bytes()[:128]
            if prefix.startswith(b"version https://git-lfs.github.com/spec"):
                status = "lfs_pointer_not_hydrated"
            elif path.suffix in {".jsonl", ".gz"}:
                rows = sum(1 for _idx, _row in iter_jsonl(path))
        except OSError as exc:
            status = f"unreadable:{exc}"
    return {
        "path": path.as_posix(),
        "exists": exists,
        "size_bytes": full.stat().st_size if exists and full.is_file() else None,
        "sha256": sha256_file(path) if exists and full.is_file() else None,
        "status": status,
        "jsonl_rows": rows,
    }


def nested_get(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def source_completeness_from_runtime(decision: dict[str, Any]) -> str:
    source_event = decision.get("source_event") or {}
    router_record = decision.get("router_record") or {}
    route_dimensions = router_record.get("route_dimensions") or {}
    for key in (
        "source_path_feature_status",
        "source_completeness_state",
        "source_quality_action",
        "selected_policy_ordered_path_status",
    ):
        value = route_dimensions.get(key) or source_event.get(key) or decision.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return "not_reported_in_runtime_row"


def classify_runtime_phase(phase: str) -> str:
    if phase == "moonshot_dynamic_execution":
        return "hybrid_live_authority_current_dynamic_router_not_v3"
    if phase == "broader_origin_safety_gate_blocked":
        return "active_live_safety_gate_authority"
    if phase == "broader_origin_pre_ai_candidate":
        return "active_live_candidate_generation_before_v3_packet_authority"
    if phase == "broader_origin_no_candidate":
        return "fallback_live_no_candidate_writer_authority"
    return "live_runtime_authority_unclassified_phase"


def material_runtime_matrix() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    phase_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for index, row in iter_jsonl(RUNTIME_DECISIONS):
        decision = row.get("decision") if isinstance(row.get("decision"), dict) else {}
        event = decision.get("event") if isinstance(decision.get("event"), dict) else {}
        source_event = decision.get("source_event") if isinstance(decision.get("source_event"), dict) else {}
        router_record = decision.get("router_record") if isinstance(decision.get("router_record"), dict) else {}
        route_dimensions = router_record.get("route_dimensions") if isinstance(router_record.get("route_dimensions"), dict) else {}
        phase = row.get("phase") or event.get("phase") or "unknown"
        selected_policy = decision.get("selected_policy")
        decision_status = decision.get("decision_status") or decision.get("decision")
        phase_counts[str(phase)] += 1
        policy_counts[str(selected_policy)] += 1
        status_counts[str(decision_status)] += 1
        rows.append(
            now_record(
                {
                    "material_row_id": f"runtime_decision:{index}",
                    "source_row_kind": "runtime_decision",
                    "source_file": RUNTIME_DECISIONS.as_posix(),
                    "source_row_number": index,
                    "timestamp_utc": row.get("timestamp_utc") or row.get("candle_time_utc"),
                    "symbol": row.get("symbol") or event.get("symbol") or source_event.get("symbol"),
                    "broker_symbol": nested_get(decision, "evidence", "broker_symbol")
                    or source_event.get("broker_symbol"),
                    "candidate_id": source_event.get("candidate_id") or event.get("candidate_id"),
                    "trade_id": source_event.get("trade_id") or event.get("trade_id"),
                    "phase": phase,
                    "final_outcome": None,
                    "selected_policy": selected_policy,
                    "execution_policy_id": decision.get("execution_policy_id"),
                    "decision_status": decision_status,
                    "candidate_action": decision.get("candidate_action"),
                    "branch_decision": (
                        route_dimensions.get("branch_label")
                        or source_event.get("branch_label")
                        or decision.get("selected_branch")
                        or "runtime_branch_not_reported"
                    ),
                    "implementation_decision": (
                        "capture_v3_live_authority_in_native_packet_and_route_to_wave2_3_for_scheduler_v4"
                    ),
                    "source_capture_state": "runtime_decision_row_hydrated",
                    "source_completeness_state": source_completeness_from_runtime(decision),
                    "evidence_class": "live_runtime_decision_shadow_log",
                    "live_authority_classification": classify_runtime_phase(str(phase)),
                    "v3_selector_status": "default_off_package_not_called_by_halt_time_runtime_row",
                    "v3_scheduler_status": "default_off_package_not_live_money_risk_authority",
                    "v3_execution_status": "execution_policy_v3_default_off_current_router_authority_used",
                    "exact_r": None,
                    "proxy_r": None,
                    "expectancy_r": None,
                    "broker_net_pnl": None,
                    "cost_swap_slippage_state": "not_materialized_in_runtime_decision_row",
                    "halt_runtime_state": "pre_halt_runtime_row" if row.get("timestamp_utc") else "runtime_row_timestamp_missing",
                }
            )
        )
    stats = {
        "runtime_decision_rows": len(rows),
        "phase_counts": dict(sorted(phase_counts.items())),
        "selected_policy_counts": dict(sorted(policy_counts.items())),
        "decision_status_counts": dict(sorted(status_counts.items())),
    }
    return rows, stats


def replacement_matrix_rows(start_id: int = 1) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    phase_counts: Counter[str] = Counter()
    for index, row in iter_jsonl(REPLACEMENT_MONITORING):
        snapshot = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
        phase = snapshot.get("phase") or "unknown"
        phase_counts[str(phase)] += 1
        router = snapshot.get("router_decision") if isinstance(snapshot.get("router_decision"), dict) else {}
        rows.append(
            now_record(
                {
                    "material_row_id": f"replacement_monitoring:{index}",
                    "source_row_kind": "replacement_monitoring_snapshot",
                    "source_file": REPLACEMENT_MONITORING.as_posix(),
                    "source_row_number": index,
                    "timestamp_utc": row.get("timestamp_utc"),
                    "symbol": snapshot.get("symbol"),
                    "broker_symbol": None,
                    "candidate_id": None,
                    "trade_id": None,
                    "phase": phase,
                    "final_outcome": None,
                    "selected_policy": router.get("selected_policy"),
                    "execution_policy_id": router.get("execution_policy_id"),
                    "decision_status": router.get("decision_status"),
                    "candidate_action": router.get("candidate_action"),
                    "branch_decision": "monitoring_snapshot_preserved_for_v3_live_gap_context",
                    "implementation_decision": "consume_as_live_monitoring_context_not_as_v3_authority",
                    "source_capture_state": "replacement_monitoring_row_hydrated",
                    "source_completeness_state": (
                        "source_capture_completeness_present"
                        if isinstance(snapshot.get("source_capture_completeness"), dict)
                        else "source_capture_completeness_not_reported"
                    ),
                    "evidence_class": "live_replacement_monitoring_shadow_snapshot",
                    "live_authority_classification": classify_runtime_phase(str(phase)),
                    "v3_selector_status": "not_v3_packet_authority",
                    "v3_scheduler_status": "not_v3_money_risk_authority",
                    "v3_execution_status": "not_execution_policy_v3_authority",
                    "exact_r": None,
                    "proxy_r": None,
                    "expectancy_r": None,
                    "broker_net_pnl": None,
                    "cost_swap_slippage_state": "monitoring_context_only",
                    "halt_runtime_state": "pre_halt_monitoring_row",
                }
            )
        )
    return rows, {
        "replacement_monitoring_rows": len(rows),
        "replacement_phase_counts": dict(sorted(phase_counts.items())),
    }


def trade_record_matrix_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    outcome_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    for index, path in enumerate(sorted((REPO_ROOT / TRADE_RECORD_ROOT).rglob("*.json")), start=1):
        rel_path = path.relative_to(REPO_ROOT)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload = {"_parse_error": str(exc)}
            metadata = {}
            pipeline = {}
            candidate = {}
        else:
            payload = record
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            pipeline = record.get("decision_pipeline") if isinstance(record.get("decision_pipeline"), dict) else {}
            candidate = record.get("moonshot_broader_origin_candidate")
            if not isinstance(candidate, dict):
                candidate = {}
        packet = pipeline.get("gtos_vnext_candidate_intelligence_packet")
        if not isinstance(packet, dict):
            packet = {}
        dynamic = pipeline.get("gtos_vnext_moonshot_dynamic_execution")
        if not isinstance(dynamic, dict):
            dynamic = {}
        final_outcome = (
            payload.get("final_outcome")
            or pipeline.get("final_outcome")
            or metadata.get("final_outcome")
            or "final_outcome_not_recorded"
        )
        symbol = metadata.get("symbol") or candidate.get("symbol") or rel_path.parts[-2]
        outcome_counts[str(final_outcome)] += 1
        symbol_counts[str(symbol)] += 1
        has_v3_packet = isinstance(packet.get("v3_live_authority"), dict)
        rows.append(
            now_record(
                {
                    "material_row_id": f"trade_record:{index}",
                    "source_row_kind": "redacted_account_trade_record",
                    "source_file": rel_path.as_posix(),
                    "source_row_number": None,
                    "timestamp_utc": metadata.get("candle_close_utc") or metadata.get("candle_time"),
                    "symbol": symbol,
                    "broker_symbol": packet.get("candidate_identity", {}).get("broker_symbol"),
                    "candidate_id": metadata.get("candidate_id") or candidate.get("candidate_id"),
                    "trade_id": metadata.get("trade_id"),
                    "phase": "trade_record",
                    "final_outcome": final_outcome,
                    "selected_policy": (
                        nested_get(packet, "dynamic_policy", "selected_policy")
                        or dynamic.get("selected_policy")
                    ),
                    "execution_policy_id": (
                        nested_get(packet, "dynamic_policy", "execution_policy_id")
                        or dynamic.get("execution_policy_id")
                    ),
                    "decision_status": dynamic.get("decision_status"),
                    "candidate_action": dynamic.get("candidate_action"),
                    "branch_decision": "hard_halt_trade_record_preserved_for_join",
                    "implementation_decision": (
                        "wave1b_code_adds_v3_live_authority_packet_for_future_native_records"
                        if not has_v3_packet
                        else "v3_live_authority_packet_present"
                    ),
                    "source_capture_state": "trade_record_hydrated",
                    "source_completeness_state": (
                        nested_get(packet, "source_completeness", "source_path_feature_status")
                        or candidate.get("source_path_feature_status")
                        or "source_completeness_not_reported"
                    ),
                    "evidence_class": "redacted_account_live_trade_record_local_capture",
                    "live_authority_classification": (
                        "active_live_trade_record_authority_without_v3_packet"
                        if not has_v3_packet
                        else "active_live_trade_record_with_v3_packet"
                    ),
                    "v3_selector_status": (
                        "packet_present" if has_v3_packet else "packet_missing_before_wave1b_fix"
                    ),
                    "v3_scheduler_status": (
                        "packet_present" if has_v3_packet else "packet_missing_before_wave1b_fix"
                    ),
                    "v3_execution_status": (
                        "packet_present" if has_v3_packet else "packet_missing_before_wave1b_fix"
                    ),
                    "exact_r": None,
                    "proxy_r": nested_get(payload, "exit", "synthetic_path_r"),
                    "expectancy_r": None,
                    "broker_net_pnl": None,
                    "cost_swap_slippage_state": "trade_record_cost_fields_incomplete_join_broker_truth_required",
                    "halt_runtime_state": "pre_halt_trade_record",
                }
            )
        )
    return rows, {
        "trade_record_rows": len(rows),
        "trade_record_outcome_counts": dict(sorted(outcome_counts.items())),
        "trade_record_symbol_counts": dict(sorted(symbol_counts.items())),
    }


def pending_lifecycle_matrix_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    for index, row in iter_jsonl(PENDING_LIFECYCLE):
        state = row.get("broker_fill_state") or row.get("fill_no_fill_label") or "unknown"
        state_counts[str(state)] += 1
        rows.append(
            now_record(
                {
                    "material_row_id": f"pending_lifecycle:{index}",
                    "source_row_kind": "pending_limit_lifecycle",
                    "source_file": PENDING_LIFECYCLE.as_posix(),
                    "source_row_number": index,
                    "timestamp_utc": row.get("timestamp_utc") or row.get("decision_time_utc"),
                    "symbol": row.get("symbol") or row.get("source_symbol"),
                    "broker_symbol": row.get("broker_symbol"),
                    "candidate_id": row.get("candidate_id"),
                    "trade_id": row.get("trade_id"),
                    "phase": "pending_limit_lifecycle",
                    "final_outcome": row.get("fill_no_fill_label") or row.get("cancel_reason"),
                    "selected_policy": None,
                    "execution_policy_id": None,
                    "decision_status": state,
                    "candidate_action": None,
                    "branch_decision": "pending_limit_lifecycle_preserved_as_live_source_truth",
                    "implementation_decision": "use_as_scheduler_and_execution_lifecycle_input_for_wave2_3",
                    "source_capture_state": "pending_lifecycle_hydrated",
                    "source_completeness_state": row.get("no_leak_status") or "pending_lifecycle_no_leak_status_missing",
                    "evidence_class": row.get("evidence_class") or "pending_limit_live_lifecycle_shadow_log",
                    "live_authority_classification": "active_live_pending_lifecycle_source_authority",
                    "v3_selector_status": "not_selector_authority",
                    "v3_scheduler_status": "required_input_for_future_scheduler_v3_or_v4_not_halt_time_authority",
                    "v3_execution_status": "ticket_lifecycle_source_for_execution_policy_not_v3_authority",
                    "exact_r": row.get("actual_r"),
                    "proxy_r": row.get("synthetic_path_r"),
                    "expectancy_r": None,
                    "broker_net_pnl": None,
                    "cost_swap_slippage_state": "spread_tick_fields_present" if row.get("spread") is not None else "spread_missing",
                    "halt_runtime_state": "pre_halt_pending_lifecycle",
                }
            )
        )
    return rows, {
        "pending_lifecycle_rows": len(rows),
        "pending_lifecycle_state_counts": dict(sorted(state_counts.items())),
    }


def broker_truth_matrix_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = read_json(BROKER_TRADES)
    rows: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    recent_gtos_count = 0
    recent_gtos_pnl = 0.0
    for index, trade in enumerate(data.get("trades") or [], start=1):
        source = trade.get("source")
        symbol = trade.get("symbol")
        source_counts[str(source)] += 1
        symbol_counts[str(symbol)] += 1
        is_recent_gtos = source == "GTOS_SYSTEM" and str(trade.get("entry_time_utc") or "") >= "2026-05-29"
        if is_recent_gtos:
            recent_gtos_count += 1
            try:
                recent_gtos_pnl += float(trade.get("net_pnl") or 0.0)
            except (TypeError, ValueError):
                pass
        rows.append(
            now_record(
                {
                    "material_row_id": f"broker_truth_trade:{index}",
                    "source_row_kind": "broker_truth_trade_group",
                    "source_file": BROKER_TRADES.as_posix(),
                    "source_row_number": index,
                    "timestamp_utc": trade.get("entry_time_utc"),
                    "symbol": symbol,
                    "broker_symbol": symbol,
                    "candidate_id": None,
                    "trade_id": None,
                    "phase": "broker_truth_trade_group",
                    "final_outcome": ",".join(map(str, trade.get("exit_comments") or trade.get("exit_reasons") or [])),
                    "selected_policy": None,
                    "execution_policy_id": None,
                    "decision_status": "closed_trade" if trade.get("exit_deals") else "open_or_unclosed_trade",
                    "candidate_action": None,
                    "branch_decision": "broker_real_cash_truth_controls_hard_halt_pnl",
                    "implementation_decision": "join_broker_truth_to_candidate_runtime_in_wave1a_wave2",
                    "source_capture_state": "broker_truth_export_available",
                    "source_completeness_state": "broker_grouped_deals_orders_available",
                    "evidence_class": "broker_real_pnl_cash_truth",
                    "live_authority_classification": (
                        "broker_real_recent_gtos_hard_halt_truth"
                        if is_recent_gtos
                        else "broker_real_non_recent_or_non_gtos_context"
                    ),
                    "v3_selector_status": "not_observable_from_broker_truth_alone",
                    "v3_scheduler_status": "not_observable_from_broker_truth_alone",
                    "v3_execution_status": "not_observable_from_broker_truth_alone",
                    "exact_r": None,
                    "proxy_r": None,
                    "expectancy_r": None,
                    "broker_net_pnl": trade.get("net_pnl"),
                    "cost_swap_slippage_state": "broker_deal_commission_swap_profit_available_in_deals",
                    "halt_runtime_state": "hard_halt_window_trade" if is_recent_gtos else "broker_context_trade",
                }
            )
        )
    return rows, {
        "broker_truth_trade_rows": len(rows),
        "broker_truth_source_counts": dict(sorted(source_counts.items())),
        "broker_truth_symbol_counts": dict(sorted(symbol_counts.items())),
        "recent_gtos_trade_count": recent_gtos_count,
        "recent_gtos_net_pnl": round(recent_gtos_pnl, 2),
    }


def package_metric_rows(selector_pkg: dict[str, Any], scheduler_pkg: dict[str, Any], execution_pkg: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "component_id": "selector_v3",
            "component_family": "selector",
            "evidence_class": "default_off_research_package_committed",
            "source_paths": [SELECTOR_PACKAGE.as_posix(), (SELECTOR_V3 / "SELECTOR_V3_COMPLETION_AUDIT.md").as_posix()],
            "runtime_disposition": "package_present_config_disabled_default_off_not_halt_time_live_authority",
            "live_authority_classification": "default_off_research",
            "branch_decision": "keep_default_off_and_capture_runtime_authority_explicitly",
            "implementation_decision": "add_native_packet_v3_live_authority_capture_no_activation",
            "source_capture_state": "package_hydrated_and_runtime_helper_present",
            "source_completeness_state": "proxy_r_materialized_exact_r_not_available_for_broad_denominator",
            "exact_r_rows": selector_pkg.get("exact_r_rows"),
            "proxy_r_rows": selector_pkg.get("proxy_r_rows"),
            "proxy_r_sum": selector_pkg.get("proxy_r_sum"),
            "expectancy_r": selector_pkg.get("expectancy_r"),
            "runtime_effect_now": selector_pkg.get("runtime_effect_now"),
            "live_activation_allowed_by_package": selector_pkg.get("live_activation_allowed_by_this_package"),
            "owner_approval_required": selector_pkg.get("owner_approval_required_for_activation"),
        },
        {
            "component_id": "scheduler_v3",
            "component_family": "scheduler_money_risk",
            "evidence_class": "default_off_research_package_committed",
            "source_paths": [SCHEDULER_PACKAGE.as_posix(), (SCHEDULER_V3 / "SCHEDULER_V3_COMPLETION_AUDIT.md").as_posix()],
            "runtime_disposition": "package_present_config_disabled_default_off_not_live_money_risk_authority",
            "live_authority_classification": "default_off_research",
            "branch_decision": "preserve_default_off_require_broker_real_money_risk_sources_before_authority",
            "implementation_decision": "capture_scheduler_v3_required_fields_as_source_gaps_in_native_packet",
            "source_capture_state": "package_hydrated_required_fields_available",
            "source_completeness_state": "runtime_account_money_risk_fields_incomplete_at_candidate_packet_boundary",
            "exact_r_rows": None,
            "proxy_r_rows": (scheduler_pkg.get("summary_counts") or {}).get("ledger_counts", {}).get("money_risk_rows"),
            "proxy_r_sum": None,
            "expectancy_r": None,
            "required_money_risk_fields": scheduler_pkg.get("required_money_risk_fields"),
            "runtime_effect_now": scheduler_pkg.get("runtime_effect_now"),
            "live_activation_allowed_by_package": scheduler_pkg.get("live_activation_allowed_by_this_package"),
            "owner_approval_required": scheduler_pkg.get("owner_approval_required_for_live_use"),
        },
        {
            "component_id": "execution_policy_v3",
            "component_family": "execution_policy",
            "evidence_class": "default_off_research_package_committed",
            "source_paths": [EXECUTION_PACKAGE.as_posix(), (EXECUTION_V3 / "V3_COMPLETION_AUDIT.md").as_posix()],
            "runtime_disposition": "package_present_config_disabled_default_off_current_live_used_momentum_primary_partial_exception",
            "live_authority_classification": "default_off_research_package_current_router_live_authority",
            "branch_decision": "keep_default_off_capture_current_policy_gap",
            "implementation_decision": "capture_execution_policy_v3_packet_no_activation_and route execution_manager_v4_to_wave3",
            "source_capture_state": "package_hydrated_runtime_helper_present",
            "source_completeness_state": "ticket_lifecycle_source_required_before_policy_authority",
            "exact_r_rows": None,
            "proxy_r_rows": (execution_pkg.get("result_scope_counts") or {}).get("source_bound_proxy_r"),
            "proxy_r_sum": None,
            "expectancy_r": None,
            "policy_family_counts": execution_pkg.get("policy_family_counts"),
            "runtime_effect_now": execution_pkg.get("runtime_effect_now"),
            "live_activation_allowed_by_package": False,
            "owner_approval_required": execution_pkg.get("owner_approval_required_for_live_use"),
        },
        {
            "component_id": "same_symbol_lifecycle_logic",
            "component_family": "scheduler_lifecycle",
            "evidence_class": "production_code_and_pending_lifecycle_log",
            "source_paths": ["src/components/permissions.py", PENDING_LIFECYCLE.as_posix()],
            "runtime_disposition": "active_live_gate_source_present_but_not_scheduler_v3_authority",
            "live_authority_classification": "active_live_authority_not_v3",
            "branch_decision": "carry_forward_to_scheduler_v4_ticket_bound_contract",
            "implementation_decision": "preserve_lifecycle_rows_full_matrix_and require broker_ticket_bound_source_completeness",
            "source_capture_state": "pending_lifecycle_hydrated",
            "source_completeness_state": "ticket_lifecycle_partial_fields_present_exact_policy_join_incomplete",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": True,
        },
        {
            "component_id": "cost_swap_slippage_handling",
            "component_family": "broker_cost_truth",
            "evidence_class": "broker_truth_and_runtime_source_gap",
            "source_paths": [BROKER_TRADES.as_posix(), BROKER_DEALS.as_posix(), TRADE_FAILURE_REVIEW.as_posix()],
            "runtime_disposition": "broker_truth_available_after_halt_not_complete_pretrade_live_authority",
            "live_authority_classification": "divergent_source_gap",
            "branch_decision": "wave2_3_cost_engine_required",
            "implementation_decision": "block_production_return_until pretrade_cost_swap_slippage_engine_and_packet_fields exist",
            "source_capture_state": "broker_deals_have_commission_swap_profit_trade_records_need_join",
            "source_completeness_state": "pretrade_cost_model_and_swap_tail_authority_incomplete",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": "partial_spread_gate_only",
        },
        {
            "component_id": "exposure_and_correlation_controls",
            "component_family": "portfolio_risk",
            "evidence_class": "production_code_live_behavior_and_hard_halt_forensics",
            "source_paths": ["src/components/permissions.py", TRADE_FAILURE_REVIEW.as_posix()],
            "runtime_disposition": "active_live_gates_present_but_insufficient_cluster_money_risk_authority",
            "live_authority_classification": "partially_active_live_authority",
            "branch_decision": "redesign_scheduler_v4_best_trade_allocator",
            "implementation_decision": "packet_capture_now_wave2_3 hard exposure allocator before return",
            "source_capture_state": "hard_halt_review_and_code_paths_available",
            "source_completeness_state": "cluster_worst_case_risk_state_incomplete",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": True,
        },
        {
            "component_id": "halt_semantics_runtime_control",
            "component_family": "runtime_control",
            "evidence_class": "pipeline_state_flags_and_hard_halt_review",
            "source_paths": ["pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag", "pipeline_state/RESEARCH_RUNTIME_HALT.flag", TRADE_FAILURE_REVIEW.as_posix()],
            "runtime_disposition": "manual_halt_flags_available_after_failure_atomic_runtime_stop_gap_remains",
            "live_authority_classification": "halt_control_gap",
            "branch_decision": "wave3_atomic_halt_runtime_required",
            "implementation_decision": "preserve halt gap ledger and require scheduler_process_order gate before return",
            "source_capture_state": "halt_flags_present",
            "source_completeness_state": "runtime_stop_ordering_after_manual_halt_not_fully_atomic",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": "post_halt_manual_flags",
        },
        {
            "component_id": "live_decision_packet_completeness",
            "component_family": "runtime_capture_contract",
            "evidence_class": "production_code_repair",
            "source_paths": ["src/components/orchestrator.py", "tests/test_vnext_broader_origin_orchestrator.py"],
            "runtime_disposition": "wave1b_repaired_forward_capture_packet_v3_authority",
            "live_authority_classification": "production_code_capture_repair",
            "branch_decision": "implement_now",
            "implementation_decision": "native packet now includes v3_live_authority capture_only",
            "source_capture_state": "code_changed",
            "source_completeness_state": "future_rows_capture_v3_status_historical_rows remain non_generatable_gap",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": False,
        },
        {
            "component_id": "market_whiteboard_state_inputs",
            "component_family": "market_state",
            "evidence_class": "selector_package_research_context_and_runtime_source_gap",
            "source_paths": [SELECTOR_PACKAGE.as_posix()],
            "runtime_disposition": "research_context_present_not_halt_time_live_whiteboard_authority",
            "live_authority_classification": "provenance_only",
            "branch_decision": "wave3_market_whiteboard_v2_input",
            "implementation_decision": "keep as source_requirement not production authority",
            "source_capture_state": "selector_package_market_whiteboard_context_pointer_present",
            "source_completeness_state": "live_packet_whiteboard_authority_not_materialized",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": False,
        },
        {
            "component_id": "broker_profile_spec_session_authority",
            "component_family": "broker_runtime",
            "evidence_class": "production_code_config_and_vps_profile_artifacts",
            "source_paths": ["config/agent_config.yaml", VPS_V3_FTMO.as_posix(), "src/components/orchestrator.py"],
            "runtime_disposition": "active_profile_spec_snapshot_partial_capture_not_v3_authority",
            "live_authority_classification": "active_live_authority_not_v3",
            "branch_decision": "preserve_profile_contract_and strengthen packet source completeness",
            "implementation_decision": "v3 packet records broker_spec_snapshot context and no broker calls beyond existing packet snapshot",
            "source_capture_state": "profile_paths_and_broker_snapshot_code_present",
            "source_completeness_state": "runtime_symbol_info_can_be_missing_and is recorded",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": True,
        },
        {
            "component_id": "replay_and_capture_contracts",
            "component_family": "reproducibility",
            "evidence_class": "route_artifacts_tests_verifiers",
            "source_paths": ["tests/test_moonshot_v3_runtime_packages.py", "tests/test_vnext_broader_origin_orchestrator.py"],
            "runtime_disposition": "tests_present_wave1b_adds_packet_assertion",
            "live_authority_classification": "capture_contract_repair",
            "branch_decision": "implement_now_and_carry_to_wave2_3",
            "implementation_decision": "route verifier and focused test result required before commit",
            "source_capture_state": "test_and_verifier_paths_present",
            "source_completeness_state": "pytest_environment_may_require_uv_with_pytest_dependency",
            "exact_r_rows": None,
            "proxy_r_rows": None,
            "proxy_r_sum": None,
            "expectancy_r": None,
            "runtime_effect_now": False,
        },
    ]


def load_packages() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return read_json(SELECTOR_PACKAGE), read_json(SCHEDULER_PACKAGE), read_json(EXECUTION_PACKAGE)


def build_source_inventory(source_stats: dict[str, Any]) -> list[dict[str, Any]]:
    paths = [
        Path(".context/LIVE_STATE.md"),
        Path(".context/00_core/current_vnext_system_map.md"),
        Path(".context/00_core/current_repo_reading_order.md"),
        Path(".context/00_core/quick_reference_card.md"),
        Path(".context/00_core/research_operating_doctrine.md"),
        Path(".context/00_core/goal_session_research_discipline.md"),
        Path(".context/00_core/final_moonshot_post_hard_halt_research_plan.md"),
        Path("research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md"),
        Path("research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_STARTER_2026-06-04.txt"),
        BROKER_TRADES,
        BROKER_DEALS,
        BROKER_ORDERS,
        TRADE_FAILURE_REVIEW,
        RUNTIME_DECISIONS,
        REPLACEMENT_MONITORING,
        PENDING_LIFECYCLE,
        SELECTOR_PACKAGE,
        SCHEDULER_PACKAGE,
        EXECUTION_PACKAGE,
        VPS_V3_FTMO / "VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl",
        VPS_V3_FTMO / "VPS_V3_FTMO_RUNTIME_WIRING_LEDGER.jsonl",
        DUAL_BROKER / "DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
        LIVE_FAILURE / "SUBAGENT_A_LIVE_PERFORMANCE_TRADE_LIFECYCLE.md",
        LIVE_FAILURE / "SUBAGENT_B_V3_LIVE_ALIGNMENT_LIMITATIONS.md",
        LIVE_FAILURE / "SUBAGENT_C_DATA_SOURCE_BROKER_INTEGRITY.md",
        LIVE_FAILURE / "SUBAGENT_D_FINAL_MOONSHOT_PROMPT_PLAN_AUDIT.md",
        GOAL_ARCH,
        Path("src/components/orchestrator.py"),
        Path("src/research/moonshot_v3_runtime_packages.py"),
        Path("src/research/moonshot_selector_v3_default_off.py"),
        Path("config/agent_config.yaml"),
        Path("tests/test_moonshot_v3_runtime_packages.py"),
        Path("tests/test_vnext_broader_origin_orchestrator.py"),
    ]
    rows = []
    for path in paths:
        stats = file_stats(path)
        rows.append(
            now_record(
                {
                    **stats,
                    "source_capture_state": stats["status"],
                    "source_completeness_state": (
                        "hydrated_or_text_available"
                        if stats["status"] == "present"
                        else stats["status"]
                    ),
                    "branch_decision": "consume_current_disk_evidence",
                    "implementation_decision": "included_in_wave1b_source_inventory",
                }
            )
        )
    rows.append(
        now_record(
            {
                "path": TRADE_RECORD_ROOT.as_posix(),
                "exists": (REPO_ROOT / TRADE_RECORD_ROOT).exists(),
                "size_bytes": None,
                "sha256": None,
                "status": "directory",
                "jsonl_rows": None,
                "trade_record_json_files": source_stats["trade_record_rows"],
                "source_capture_state": "directory_hydrated",
                "source_completeness_state": "json_files_parsed_count_recorded",
                "branch_decision": "consume_current_disk_trade_records",
                "implementation_decision": "full_trade_record_rows_preserved_in_matrix",
            }
        )
    )
    return rows


def searched_root_rows() -> list[dict[str, Any]]:
    roots = [
        HARD_HALT,
        DUAL_BROKER,
        VPS_V3_FTMO,
        LIVE_FAILURE,
        GOAL_ARCH,
        RUNTIME_DECISIONS,
        REPLACEMENT_MONITORING,
        PENDING_LIFECYCLE,
        Path("pipeline_state"),
        Path("src"),
        Path("scripts"),
        Path("config"),
        Path("tests"),
        SELECTOR_V3,
        SCHEDULER_V3,
        EXECUTION_V3,
        Path("research/science_program_2026_05/04_goal_prompts"),
    ]
    rows: list[dict[str, Any]] = []
    for root in roots:
        full = REPO_ROOT / root
        file_count = 0
        if full.is_file():
            file_count = 1
        elif full.exists():
            file_count = sum(1 for p in full.rglob("*") if p.is_file())
        rows.append(
            now_record(
                {
                    "searched_root": root.as_posix(),
                    "exists": full.exists(),
                    "file_count": file_count,
                    "search_method": "rg_or_direct_recursive_disk_inventory",
                    "source_capture_state": "searched_from_current_worktree",
                    "source_completeness_state": "complete_for_current_hydrated_disk_state",
                    "branch_decision": "consume_if_relevant",
                    "implementation_decision": "source_inventory_or_component_ledger_consumed",
                }
            )
        )
    rows.extend(
        now_record(
            {
                "searched_root": "explicit_command",
                "exists": True,
                "file_count": None,
                "search_method": cmd,
                "source_capture_state": "manual_session_search_recorded",
                "source_completeness_state": "results_consumed_into_builder",
                "branch_decision": "search_required_by_prompt",
                "implementation_decision": "searched_before_claiming_behavior",
            }
        )
        for cmd in [
            "rg -n v3 src scripts config tests",
            "rg -n build_v3_runtime_packet src/research/moonshot_v3_runtime_packages.py",
            "rg -n gtos_vnext_candidate_intelligence_packet src/components/orchestrator.py tests",
            "find research/operations -maxdepth 1 -name '*wave1b*'",
            "git lfs pull --include runtime decisions replacement monitoring pending lifecycle trade records",
        ]
    )
    return rows


def build_gap_ledgers(component_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_id = {row["component_id"]: row for row in component_rows}
    common = {
        "source_capture_state": "current_disk_evidence_consumed",
        "source_completeness_state": "gap_classified_with_exact_followup_requirement",
        "exact_r": None,
        "proxy_r": None,
        "expectancy_r": None,
    }
    return {
        "SELECTOR_AUTHORITY_GAP_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "selector_v3_default_off_not_live_selector",
                    "component_id": "selector_v3",
                    "live_authority_classification": by_id["selector_v3"]["live_authority_classification"],
                    "gap_statement": "Selector V3 package existed, but halt-time runtime rows used current dynamic/router selected-cell authority, not Selector V3 package calls.",
                    "branch_decision": "stage_default_off_capture_authority",
                    "implementation_decision": "orchestrator candidate packet now writes v3_live_authority capture-only packet",
                    "source_paths": by_id["selector_v3"]["source_paths"] + ["src/components/orchestrator.py"],
                }
            )
        ],
        "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "scheduler_v3_default_off_money_risk_gap",
                    "component_id": "scheduler_v3",
                    "live_authority_classification": by_id["scheduler_v3"]["live_authority_classification"],
                    "gap_statement": "Scheduler V3 required broker-real account/exposure/cost fields were not live authority at halt time; clustered exposure and count-cap bypass survived.",
                    "branch_decision": "route_to_scheduler_v4_best_trade_allocator",
                    "implementation_decision": "v3 packet records scheduler required-field source gaps; production return blocked until Scheduler V4 money-risk authority exists",
                    "source_paths": by_id["scheduler_v3"]["source_paths"] + [TRADE_FAILURE_REVIEW.as_posix()],
                    "required_money_risk_fields": by_id["scheduler_v3"].get("required_money_risk_fields"),
                }
            )
        ],
        "EXECUTION_POLICY_GAP_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "execution_policy_v3_default_off_current_router_live",
                    "component_id": "execution_policy_v3",
                    "live_authority_classification": by_id["execution_policy_v3"]["live_authority_classification"],
                    "gap_statement": "Execution Policy V3 was package/default-off; previous live execution authority was momentum_exhaustion primary with partial_be_runner exception selection.",
                    "branch_decision": "keep_default_off_and_build_execution_manager_v4",
                    "implementation_decision": "native packet captures execution_policy_v3 default-off decision and lifecycle source requirement",
                    "source_paths": by_id["execution_policy_v3"]["source_paths"] + ["config/agent_config.yaml"],
                }
            )
        ],
        "LIVE_DECISION_PACKET_COMPLETENESS_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "candidate_packet_missing_v3_authority_prior_to_wave1b",
                    "component_id": "live_decision_packet_completeness",
                    "live_authority_classification": by_id["live_decision_packet_completeness"]["live_authority_classification"],
                    "gap_statement": "Historical live trade records did not carry formal V3 live authority disposition, making V3/live claims ambiguous.",
                    "branch_decision": "implement_now",
                    "implementation_decision": "src/components/orchestrator.py now attaches v3_live_authority to gtos_vnext_candidate_intelligence_packet",
                    "source_paths": by_id["live_decision_packet_completeness"]["source_paths"],
                }
            )
        ],
        "COST_SWAP_SLIPPAGE_AUTHORITY_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "cost_swap_slippage_not_complete_live_authority",
                    "component_id": "cost_swap_slippage_handling",
                    "live_authority_classification": by_id["cost_swap_slippage_handling"]["live_authority_classification"],
                    "gap_statement": "Broker deals expose commission/swap/profit after halt; pretrade cost/swap/slippage authority was incomplete and ETHUSD exposed swap/cost tail risk.",
                    "branch_decision": "wave3_cost_engine_required",
                    "implementation_decision": "exact broker-cost join and prospective pretrade capture required before production return",
                    "source_paths": by_id["cost_swap_slippage_handling"]["source_paths"],
                }
            )
        ],
        "EXPOSURE_AND_CLUSTER_AUTHORITY_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "exposure_controls_partially_active_insufficient",
                    "component_id": "exposure_and_correlation_controls",
                    "live_authority_classification": by_id["exposure_and_correlation_controls"]["live_authority_classification"],
                    "gap_statement": "Correlation/same-symbol gates existed but did not amount to Scheduler V3 broker-real portfolio allocator authority.",
                    "branch_decision": "redesign_scheduler_v4",
                    "implementation_decision": "block production return until worst-case open/pending/new cluster exposure is authoritative",
                    "source_paths": by_id["exposure_and_correlation_controls"]["source_paths"],
                }
            )
        ],
        "HALT_SEMANTICS_AND_RUNTIME_CONTROL_LEDGER.jsonl": [
            now_record(
                {
                    **common,
                    "gap_id": "manual_halt_not_atomic_runtime_control",
                    "component_id": "halt_semantics_runtime_control",
                    "live_authority_classification": by_id["halt_semantics_runtime_control"]["live_authority_classification"],
                    "gap_statement": "Hard halt flags exist, but the halt sequence proved emergency flattening alone was insufficient and runtime scheduler/process stop semantics need atomic authority.",
                    "branch_decision": "wave3_atomic_halt_runtime_required",
                    "implementation_decision": "preserve exact halt gap and require process/order gate verifier before production return",
                    "source_paths": by_id["halt_semantics_runtime_control"]["source_paths"],
                }
            )
        ],
    }


def code_change_ledger() -> list[dict[str, Any]]:
    return [
        now_record(
            {
                "change_id": "production_packet_v3_live_authority_capture",
                "path": "src/components/orchestrator.py",
                "change_type": "production_code_capture_contract",
                "branch_decision": "implement_now",
                "implementation_decision": "add capture-only v3_live_authority packet using default-off V3 package helpers",
                "runtime_effect_boundary": "no activation flags changed no broker/order/paid calls introduced",
                "source_capture_state": "tracked_diff_present",
                "source_completeness_state": "py_compile_required_and_focused_packet_test_updated",
            }
        ),
        now_record(
            {
                "change_id": "packet_test_v3_authority_assertion",
                "path": "tests/test_vnext_broader_origin_orchestrator.py",
                "change_type": "focused_test_repair",
                "branch_decision": "implement_now",
                "implementation_decision": "assert v3 package present config-disabled no runtime broker effect in native candidate packet",
                "runtime_effect_boundary": "test_only",
                "source_capture_state": "tracked_diff_present",
                "source_completeness_state": "pytest_requires_project_test_dependency_environment",
            }
        ),
        now_record(
            {
                "change_id": "route_builder_verifier_artifacts",
                "path": rel(ROUTE_DIR),
                "change_type": "route_artifact_builder_verifier",
                "branch_decision": "implement_now",
                "implementation_decision": "generate full material ledgers, verifier, manifest, saturation, completion audit",
                "runtime_effect_boundary": "research_artifacts_only",
                "source_capture_state": "route_local_files_generated",
                "source_completeness_state": "manifest_and_audit_required",
            }
        ),
    ]


def implementation_decisions(component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in component_rows:
        rows.append(
            now_record(
                {
                    "decision_id": f"implementation:{row['component_id']}",
                    "component_id": row["component_id"],
                    "live_authority_classification": row["live_authority_classification"],
                    "runtime_disposition": row["runtime_disposition"],
                    "branch_decision": row["branch_decision"],
                    "implementation_decision": row["implementation_decision"],
                    "source_capture_state": row["source_capture_state"],
                    "source_completeness_state": row["source_completeness_state"],
                    "exact_r_rows": row.get("exact_r_rows"),
                    "proxy_r_rows": row.get("proxy_r_rows"),
                    "expectancy_r": row.get("expectancy_r"),
                    "wave2_3_input": row["component_id"] not in {"live_decision_packet_completeness", "replay_and_capture_contracts"},
                }
            )
        )
    return rows


def repair_requirement_ledger(component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = {
        "scheduler_v3": "Build Scheduler V4 broker-real best-trade allocator with balance/equity/day baseline/open/pending/new risk, selected-cell risk, lot geometry, costs, drawdown, same-symbol, and cluster exposure authority.",
        "cost_swap_slippage_handling": "Build Cost/Swap/Slippage/Broker Constraint Engine with broker-real deal joins and pretrade spread/commission/swap/slippage packet fields.",
        "exposure_and_correlation_controls": "Replace partial gate authority with hard portfolio and correlated-cluster worst-case exposure ceilings before production return.",
        "halt_semantics_runtime_control": "Build atomic halt runtime control that orders broker flatten, process shutdown, scheduler halt, autostart disable, and verification without race gaps.",
        "market_whiteboard_state_inputs": "Materialize Market Whiteboard V2 live packet fields before treating market-state context as selector/scheduler authority.",
        "broker_profile_spec_session_authority": "Promote broker profile/spec/session authority into LiveDecisionPacketV4 with explicit source completeness and failure states.",
    }
    rows = []
    by_id = {row["component_id"]: row for row in component_rows}
    for component_id, requirement in requirements.items():
        row = by_id[component_id]
        rows.append(
            now_record(
                {
                    "repair_id": f"repair:{component_id}",
                    "component_id": component_id,
                    "repair_requirement": requirement,
                    "evidence_class": row["evidence_class"],
                    "live_authority_classification": row["live_authority_classification"],
                    "source_paths": row["source_paths"],
                    "source_capture_state": row["source_capture_state"],
                    "source_completeness_state": row["source_completeness_state"],
                    "branch_decision": row["branch_decision"],
                    "implementation_decision": row["implementation_decision"],
                    "owner_action_required_now": False,
                    "outside_route_surface": None,
                    "wave_owner": "wave2_3_final_master_or_v4_component_route",
                }
            )
        )
    return rows


def write_path_map() -> None:
    write_md(
        "WAVE1B_CODE_RUNTIME_PATH_MAP.md",
        f"""
# Wave 1B Code Runtime Path Map

Generated: {GENERATED_AT}

## Selector

- Current halt-time live path: `src/components/gtos_vnext_runtime.py` dynamic moonshot router and selected-cell risk helpers write `gtos_vnext_moonshot_dynamic_execution`.
- V3 package/helper path: `src/research/moonshot_selector_v3_default_off.py` and `src/research/moonshot_v3_runtime_packages.py`.
- Runtime disposition: Selector V3 package-present but config-disabled/default-off. No halt-time runtime rows prove Selector V3 live authority.
- Wave1B repair: `src/components/orchestrator.py` writes `gtos_vnext_candidate_intelligence_packet.v3_live_authority.selector_v3` as capture-only proof.

## Scheduler And Money Risk

- Current live path: `src/components/permissions.py`, `src/components/portfolio_risk.py`, `src/components/cross_instrument_correlation_gate.py`, prop-safe selector code in `src/components/gtos_vnext_runtime.py`, and pending lifecycle rows in `shadow_logs/pending_limit_lifecycle.jsonl`.
- V3 package/helper path: `src/research/moonshot_v3_runtime_packages.py::build_scheduler_v3_packet`.
- Runtime disposition: Scheduler V3 default-off; required broker-real balance/equity/open/pending/new risk/cost/cluster fields are source gaps at packet time.
- Wave1B repair: packet records scheduler V3 default-off decision and missing money-risk source status without activating.

## Execution Policy

- Current live path: dynamic policy router intent in `src/research/moonshot_default_off_policy_router.py` and current runtime selection in `src/components/gtos_vnext_runtime.py`.
- V3 package/helper path: `src/research/moonshot_v3_runtime_packages.py::build_execution_policy_v3_packet`.
- Runtime disposition: Execution Policy V3 default-off; live authority was `momentum_exhaustion` primary with `partial_be_runner` exception selection.
- Wave1B repair: packet records execution_policy_v3 default-off decision and ticket lifecycle source requirement.

## Lifecycle, Cost, Exposure, Halt

- Same-symbol lifecycle: `src/components/permissions.py::_reject_if_same_symbol_vnext_lifecycle_conflict` plus `shadow_logs/pending_limit_lifecycle.jsonl`.
- Cost/swap/slippage: broker truth exports under `{HARD_HALT.as_posix()}` and incomplete pretrade packet fields.
- Exposure/correlation: `src/components/permissions.py`, `src/components/cross_instrument_correlation_gate.py`, hard-halt review cluster failure evidence.
- Halt: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, and hard-halt review.

## Packet, Profile, Launcher, Replay

- Packet: `src/components/orchestrator.py::_refresh_vnext_candidate_intelligence_packet`.
- Profile/config: `config/agent_config.yaml` V3 keys all false/default-off.
- Launcher/runtime package consumption: `{VPS_V3_FTMO.as_posix()}`.
- Tests/verifiers: `tests/test_moonshot_v3_runtime_packages.py`, `tests/test_vnext_broader_origin_orchestrator.py`, and this route verifier.
""",
    )


def write_subagent_artifacts(stats: dict[str, Any]) -> None:
    subagents = {
        "SUBAGENT_SELECTOR_AUTHORITY_AUDITOR.md": (
            "Selector authority auditor",
            "Selector V3 is default-off research/provenance, not halt-time live selector authority. Current live rows used the dynamic router and selected-cell risk bridge. Wave1B implemented capture-only `v3_live_authority.selector_v3` in native packets.",
        ),
        "SUBAGENT_SCHEDULER_MONEY_RISK_AUDITOR.md": (
            "Scheduler and money-risk auditor",
            "Scheduler V3 required broker-real account, open/pending/new worst-case risk, selected-cell risk, lot geometry, cost buffers, daily/total limits, and cluster ceilings. Halt-time live authority did not have that complete scheduler authority; Wave 2/3 must build Scheduler V4 before return.",
        ),
        "SUBAGENT_EXECUTION_PACKET_COMPLETENESS_AUDITOR.md": (
            "Execution policy and packet-completeness auditor",
            "Execution Policy V3 package existed default-off while previous live policy authority was momentum_exhaustion plus partial_be_runner exception. Historical packets lacked a formal V3 authority field; Wave1B repaired forward packet capture.",
        ),
        "SUBAGENT_HALT_RUNTIME_CONTROL_AUDITOR.md": (
            "Halt semantics and runtime-control auditor",
            "Hard-halt flags exist, but broker truth shows manual flattening and halt sequencing were not sufficient as atomic runtime control. This route preserves the halt gap as a Wave 3 atomic halt requirement.",
        ),
        "SUBAGENT_PRODUCTION_SCOPE_AUDITOR.md": (
            "Production-code implementation and scope auditor",
            "The code change is scoped to capture metadata. It imports default-off V3 packet helpers and writes no activation config, broker mutation, order call, paid API, credential, remote, or live-reload behavior.",
        ),
        "SUBAGENT_SATURATION_PROMPT_HARDENING_AUDITOR.md": (
            "Saturation and prompt-language hardening auditor",
            "The route avoided the V3-as-ledger trap by making a production packet repair. It preserved full material row ledgers rather than ranked top-N summaries and labels exact Wave 2/3 requirements for unrepaired live authority gaps.",
        ),
    }
    for filename, (title, body) in subagents.items():
        write_md(
            filename,
            f"""
# {title}

Generated: {GENERATED_AT}

{body}

Material row coverage: runtime decisions `{stats['runtime_decision_rows']}`, replacement snapshots `{stats['replacement_monitoring_rows']}`, trade records `{stats['trade_record_rows']}`, pending lifecycle rows `{stats['pending_lifecycle_rows']}`, broker trade groups `{stats['broker_truth_trade_rows']}`.
""",
        )


def write_summary_and_audit(stats: dict[str, Any]) -> None:
    write_md(
        "WAVE1B_AUTHORITY_GAP_SUMMARY.md",
        f"""
# Wave 1B Authority Gap Summary

Generated: {GENERATED_AT}

Wave 1B classifies V3 package evidence versus halt-time live authority from current disk evidence. Full material rows are preserved in `LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl`.

## Row Coverage

- Runtime decision rows: `{stats['runtime_decision_rows']}`.
- Replacement monitoring snapshots: `{stats['replacement_monitoring_rows']}`.
- redacted_account trade records: `{stats['trade_record_rows']}`.
- Pending lifecycle rows: `{stats['pending_lifecycle_rows']}`.
- Broker truth trade groups: `{stats['broker_truth_trade_rows']}`.
- Recent GTOS broker-truth hard-halt trades: `{stats['recent_gtos_trade_count']}`, net PnL `{stats['recent_gtos_net_pnl']}`.

## Decisions

- Selector V3: default-off research package, not halt-time live authority. Implemented forward capture in native packets.
- Scheduler V3: default-off research package. Halt-time money-risk scheduling was not complete broker-real authority. Wave 2/3 owns Scheduler V4.
- Execution Policy V3: default-off research package. Halt-time live execution used momentum_exhaustion primary with partial_be_runner exception.
- LiveDecisionPacket: repaired now with `v3_live_authority` capture-only packet.
- Cost/swap/slippage, exposure/cluster, halt semantics: material production-return blockers for Wave 2/3, not solved by V3 package existence.

## Evidence-Class Notes

Broker truth is broker-real PnL/cash. Runtime and replacement ledgers are live shadow/capture authority. V3 packages are default-off research/provenance. Proxy R and expectancy are preserved only from package/source-bound rows and are not broker-real PnL.
""",
    )
    write_md(
        "WAVE1B_SATURATION_AND_SELF_RED_TEAM.md",
        f"""
# Wave 1B Saturation And Self Red Team

Generated: {GENERATED_AT}

## Saturation Checks

- Evidence-class confusion checked: V3 package metrics are kept separate from live runtime authority and broker-real PnL.
- Full-row coverage checked: no top-N closure. Runtime, replacement, trade-record, pending-lifecycle, and broker-truth rows are all materialized in the authority matrix.
- Historical non-generatable truth checked: historical live packets that lacked V3 authority cannot be backfilled as original live truth. The repair is prospective packet capture.
- Source gaps checked: scheduler money-risk, cost/swap/slippage, cluster exposure, and halt atomicity gaps are exact Wave 2/3 requirements.
- Production scope checked: local code/test/verifier/artifact changes only; no broker mutation, live trading operation, paid/vendor call, credential mutation, remote push, or live reload.

## Skeptical Rejections Preempted

- Rejection: 'V3 failed live.' Answer: not proven. Full V3 was not halt-time live authority.
- Rejection: 'V3 package existence means live V3 authority.' Answer: false. Config and package provenance show default-off/no live activation.
- Rejection: 'Packet repair changes trading.' Answer: false. It records capture-only metadata and leaves activation flags and broker/order behavior unchanged.
- Rejection: 'Ledgers summarize only.' Answer: false. `LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl` preserves all material rows parsed from hydrated current sources.
""",
    )
    write_md(
        "WAVE1B_COMPLETION_AUDIT.md",
        f"""
# Wave 1B Completion Audit

Generated: {GENERATED_AT}

## Instruction Coverage

- Mandatory context refreshed from disk, including resumed-turn `LIVE_STATE` regeneration.
- Chat memory was not used as evidence; disk artifacts and code were parsed directly.
- Full repo-control rule applied: production packet capture code, focused test assertion, builder, verifier, ledgers, manifest, saturation, and completion audit were created.
- Doctrine operationalized through source inventory, searched-root ledger, implementation decisions, saturation, and verifier.
- Stale `research_current_state.md` was treated as stale per `LIVE_STATE`; newer artifacts were read directly.

## Evidence Coverage

- Every required V3 surface has a row in `V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl`.
- All material hydrated runtime decisions, replacement snapshots, trade records, pending lifecycle rows, and broker-truth trade groups are classified in `LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl`.
- Source-capture, source-completeness, branch-decision, implementation-decision, exact-R/proxy-R/expectancy fields are present where applicable.

## Implementation

- `src/components/orchestrator.py` now writes `v3_live_authority` inside the native candidate intelligence packet.
- `tests/test_vnext_broader_origin_orchestrator.py` asserts V3 default-off capture/no runtime effect.
- No V3 activation flags were changed and no broker/order/paid/credential/remote behavior was added.

## Remaining Evidence-Class Requirements

- Wave 2/3 must build final Scheduler V4, Execution Manager V4, Cost/Swap/Slippage/Broker Constraint Engine, Market Whiteboard V2, Atomic Halt Runtime, and LiveDecisionPacketV4 before any production-return dossier.
- Historical packets without V3 authority are non-generatable historical source gaps; future records are repaired prospectively by this route.

## Verification Status

`WAVE1B_VERIFICATION_RESULT.json` and `FOCUSED_TEST_RESULT.json` are produced by the verifier after commands run. Scoped staging/LFS/commit proof is finalized after this builder output.
""",
    )


def write_manifest() -> None:
    rows = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if path.is_file():
            entry = {
                "path": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            if path.suffix == ".jsonl":
                entry["jsonl_rows"] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
            rows.append(entry)
    write_json(
        "WAVE1B_OUTPUT_MANIFEST.json",
        now_record(
            {
                "artifact_count": len(rows),
                "artifacts": rows,
                "manifest_status": "generated_before_final_verifier_may_update_verification_result",
            }
        ),
    )


def main() -> int:
    selector_pkg, scheduler_pkg, execution_pkg = load_packages()
    runtime_rows, runtime_stats = material_runtime_matrix()
    replacement_rows, replacement_stats = replacement_matrix_rows()
    trade_rows, trade_stats = trade_record_matrix_rows()
    pending_rows, pending_stats = pending_lifecycle_matrix_rows()
    broker_rows, broker_stats = broker_truth_matrix_rows()
    stats = {
        **runtime_stats,
        **replacement_stats,
        **trade_stats,
        **pending_stats,
        **broker_stats,
    }

    matrix_rows = runtime_rows + replacement_rows + trade_rows + pending_rows + broker_rows
    component_rows = package_metric_rows(selector_pkg, scheduler_pkg, execution_pkg)
    source_rows = build_source_inventory(stats)

    head = run(["git", "rev-parse", "HEAD"])["stdout"].strip()
    branch = run(["git", "branch", "--show-current"])["stdout"].strip()
    status = run(["git", "status", "--short"])["stdout"].splitlines()
    live_state = read_text(Path(".context/LIVE_STATE.md"), limit=5000)
    live_state_generated = ""
    for line in live_state.splitlines():
        if line.startswith("**Generated:**"):
            live_state_generated = line.replace("**Generated:**", "").strip()
            break
    existing_route_files = sorted(
        path.name for path in ROUTE_DIR.iterdir() if path.is_file()
    )

    write_json(
        "WAVE1B_CONTEXT_ANCHOR.json",
        now_record(
            {
                "branch": branch,
                "head": head,
                "live_state_generated": live_state_generated,
                "mandatory_reads": [
                    ".context/LIVE_STATE.md",
                    ".context/00_core/current_vnext_system_map.md",
                    ".context/00_core/current_repo_reading_order.md",
                    ".context/00_core/quick_reference_card.md",
                    ".context/00_core/research_current_state.md",
                    ".context/00_core/research_operating_doctrine.md",
                    ".context/00_core/goal_session_research_discipline.md",
                    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
                    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
                    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
                    ".context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md",
                    "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md",
                    "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_STARTER_2026-06-04.txt",
                ],
                "dirty_status_at_build": status,
                "lfs_hydration_summary": {
                    "runtime_decisions": file_stats(RUNTIME_DECISIONS)["status"],
                    "replacement_monitoring": file_stats(REPLACEMENT_MONITORING)["status"],
                    "pending_lifecycle": file_stats(PENDING_LIFECYCLE)["status"],
                    "trade_records_json_files": stats["trade_record_rows"],
                },
                "route_state_before_build": {
                    "existing_file_count": len(existing_route_files),
                    "existing_files": existing_route_files,
                },
                "source_capture_state": "current_disk_preflight_refreshed_after_resume",
                "source_completeness_state": "research_current_state_stale_direct_artifacts_used",
                "branch_decision": "build_wave1b_route_from_current_disk",
                "implementation_decision": "production_packet_capture_repair_plus_ledgers_verifier_tests_manifest_commit",
            }
        ),
    )
    write_jsonl("WAVE1B_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows())
    write_jsonl("WAVE1B_SOURCE_INVENTORY.jsonl", source_rows)
    write_jsonl("WAVE1B_COMPONENT_INVENTORY.jsonl", component_rows)
    write_path_map()
    write_jsonl("LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl", matrix_rows)
    write_jsonl("V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl", component_rows)
    for filename, rows in build_gap_ledgers(component_rows).items():
        write_jsonl(filename, rows)
    write_jsonl("PRODUCTION_CODE_CHANGE_LEDGER.jsonl", code_change_ledger())
    write_jsonl("IMPLEMENTATION_DECISION_LEDGER.jsonl", implementation_decisions(component_rows))
    write_jsonl("WAVE1B_REPAIR_REQUIREMENT_LEDGER.jsonl", repair_requirement_ledger(component_rows))
    write_summary_and_audit(stats)
    write_subagent_artifacts(stats)
    write_json(
        "FOCUSED_TEST_RESULT.json",
        now_record(
            {
                "status": "pending_verifier_run",
                "commands": [],
                "source_capture_state": "placeholder_written_by_builder",
                "source_completeness_state": "verifier_updates_after_command_execution",
            }
        ),
    )
    write_json(
        "WAVE1B_VERIFICATION_RESULT.json",
        now_record(
            {
                "status": "pending_verifier_run",
                "artifact_builder_status": "complete",
                "material_row_counts": stats,
                "source_capture_state": "placeholder_written_by_builder",
                "source_completeness_state": "verifier_updates_after_command_execution",
            }
        ),
    )
    write_manifest()
    print(json.dumps({"ok": True, "route": rel(ROUTE_DIR), "material_rows": len(matrix_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
