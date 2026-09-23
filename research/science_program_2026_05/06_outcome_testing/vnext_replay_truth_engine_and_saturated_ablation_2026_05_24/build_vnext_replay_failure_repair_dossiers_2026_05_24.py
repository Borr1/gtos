"""Build Stage 08 failure and repair dossiers.

This offline dossier builder consumes the replay truth-engine artifacts through
Stage 07 and materializes exact limitation, failure-anatomy, and repair-action
rows. It does not mutate production config, prompts, broker state, accounts,
orders, deals, positions, or live runtime behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BUILDER_PATH = Path(__file__).resolve()
SATURATED_REPLAY_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json"
STAGE05_METRICS_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_METRICS_SUMMARY_2026-05-24.json"
STAGE06_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_MIXED_SUMMARY_2026-05-24.json"
PROP_FIRM_METRICS_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json"
ROBUSTNESS_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_ROBUSTNESS_LEDGER_2026-05-24.jsonl"
STAGE07_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_ROBUSTNESS_SUMMARY_2026-05-24.json"
SOURCE_GAP_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_SOURCE_GAP_LEDGER_2026-05-24.jsonl"
PATH_OUTCOME_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_PATH_OUTCOME_LEDGER_2026-05-24.jsonl"
EVENT_PATH_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_EVENT_PATH_RECONSTRUCTION_SUMMARY_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
FAILURE_REPAIR_DOSSIER_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_DOSSIER_2026-05-24.json"
FAILURE_REPAIR_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_LEDGER_2026-05-24.jsonl"
STAGE08_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_SUMMARY_2026-05-24.json"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)

STAGE_ID = "STAGE_08_FAILURE_AND_REPAIR_DOSSIERS"
NEXT_STAGE_ID = "STAGE_09_FINAL_TRUTH_FREEZE"
LOWER_PATH_MODES = {
    "m1_path_aware",
    "m5_path_aware",
    "tick_or_sierra_path_aware",
    "ohlc_only_proxy",
}
BROKER_EXECUTION_FIELDS = [
    "order_ticket",
    "deal_ticket",
    "broker_fill_time_utc",
    "executed_entry_price",
    "executed_exit_price",
    "executed_stop_price",
    "executed_target_price",
    "executed_lot_size",
    "commission",
    "swap",
    "slippage_price",
    "partial_exit_lifecycle",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")


def stable_hash(payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def current_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def current_commit_label() -> str:
    return run_git(["log", "-1", "--oneline"])


def current_git_status_short() -> list[str]:
    status = run_git(["status", "--short"])
    return [line for line in status.splitlines() if line.strip()]


def sorted_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def terminal_bucket(value: Any) -> str:
    text = str(value or "")
    lowered = text.lower()
    if text == "MISSING_SOURCE" or "missing" in lowered:
        return "missing_source"
    if "ambiguous" in lowered:
        return "ambiguous"
    if "target_first" in lowered or "tp1" in lowered and "before_sl" in lowered:
        return "target_first_or_tp"
    if "stop_first" in lowered or "sl" in lowered and "before_tp" in lowered:
        return "stop_first_or_sl"
    if "no_entry_touch" in lowered or "no_touch" in lowered or "without_entry_touch" in lowered:
        return "no_entry_touch"
    if "timeout" in lowered or "unresolved" in lowered or "still_pending" in lowered:
        return "timeout_or_unresolved"
    if "decision_trace" in lowered or "broker_ticket_known" in lowered:
        return "reference_only"
    return text or "unknown"


def repair_row(
    *,
    family: str,
    evidence_scope: str,
    severity: str,
    status: str,
    impact_metrics: dict[str, Any],
    evidence_artifacts: list[str],
    failure_anatomy: str,
    repair_action: str,
    current_session_feasibility: str,
    owner_access_or_capture_requirement: str,
    decision_map_candidate: str,
    next_stage_use: str,
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_replay_stage08_failure_repair_row_v1",
        "stage_id": STAGE_ID,
        "repair_row_id": "rep_" + stable_hash([family, evidence_scope, status, impact_metrics]),
        "family": family,
        "evidence_scope": evidence_scope,
        "severity": severity,
        "status": status,
        "impact_metrics": impact_metrics,
        "evidence_artifacts": evidence_artifacts,
        "failure_anatomy": failure_anatomy,
        "repair_action": repair_action,
        "current_session_feasibility": current_session_feasibility,
        "owner_access_or_capture_requirement": owner_access_or_capture_requirement,
        "decision_map_candidate": decision_map_candidate,
        "next_stage_use": next_stage_use,
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }


def source_gap_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aggregate: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    rows_seen = 0
    for row in iter_jsonl(SOURCE_GAP_LEDGER_PATH):
        rows_seen += 1
        gap_class = str(row.get("source_gap_class") or row.get("gap_type") or "unknown_gap_class")
        symbol = str(row.get("symbol") or "ALL")
        evidence_type = str(row.get("source_evidence_type") or "unknown_source_evidence")
        missing_fields = tuple(sorted(map(str, row.get("missing_fields") or [])))
        key = (gap_class, symbol, evidence_type, "|".join(missing_fields) or "none")
        item = aggregate.setdefault(
            key,
            {
                "rows": 0,
                "affected_event_count": 0,
                "searched_paths": set(),
                "statuses": Counter(),
                "next_actions": Counter(),
                "missing_fields": set(),
            },
        )
        item["rows"] += 1
        item["affected_event_count"] += int(row.get("affected_event_count") or 0)
        item["statuses"][str(row.get("status") or row.get("terminal_status") or "unknown_status")] += 1
        item["next_actions"][str(row.get("next_action") or "none")] += 1
        item["missing_fields"].update(map(str, row.get("missing_fields") or []))
        item["searched_paths"].update(map(str, row.get("searched_paths") or []))

    output: list[dict[str, Any]] = []
    for (gap_class, symbol, evidence_type, _fields), item in sorted(aggregate.items()):
        fields = sorted(item["missing_fields"])
        source_truth = "historical_market_data_recoverable_or_requestable"
        if any("intent" in field or "order" in field or "lifecycle" in field for field in fields):
            source_truth = "historical_system_state_non_generatable_if_not_logged"
        action = (
            "Use approved local-heavy roots and read-only MT5/Sierra/OHLC/tick export if available; "
            "otherwise preserve exact searched paths and add prospective capture contract."
        )
        if not fields:
            action = "No repair required for this preregistration/root-coverage class."
        output.append(
            repair_row(
                family="source_gap_data_coverage",
                evidence_scope=f"{gap_class}::{symbol}::{evidence_type}",
                severity="high" if item["affected_event_count"] else "info",
                status="source_repair_required" if fields else "covered_or_no_missing_source",
                impact_metrics={
                    "source_gap_rows": item["rows"],
                    "affected_event_count": item["affected_event_count"],
                    "missing_fields": fields,
                    "searched_path_count": len(item["searched_paths"]),
                    "searched_paths": sorted(item["searched_paths"]),
                    "status_counts": sorted_counter(item["statuses"]),
                    "next_action_counts": sorted_counter(item["next_actions"]),
                    "source_truth_class": source_truth,
                },
                evidence_artifacts=[rel(SOURCE_GAP_LEDGER_PATH), rel(EVENT_PATH_SUMMARY_PATH)],
                failure_anatomy=(
                    "Replay could not bind all requested source windows or source-state fields for this class. "
                    "Rows remain source-bound only to the searched artifacts and strongest available proxy."
                )
                if fields
                else "Configured runtime artifacts and preregistered roots were present for this class.",
                repair_action=action,
                current_session_feasibility=(
                    "bounded_in_current_session_by_recorded_searches_and_no_live_broker_mutation"
                    if fields
                    else "complete_no_current_repair_needed"
                ),
                owner_access_or_capture_requirement=(
                    "Provide or approve read-only export for the exact missing symbol/window/source fields, or add forward capture for non-generatable system-state truth."
                    if fields
                    else "none"
                ),
                decision_map_candidate="source-repair required" if fields else "keep shadow/default-off",
                next_stage_use="feed Stage09 data-required/source-repair decisions",
            )
        )
    summary = {
        "source_gap_input_rows": rows_seen,
        "source_gap_repair_rows": len(output),
        "source_gap_total_affected_events": sum(row["impact_metrics"]["affected_event_count"] for row in output),
    }
    return output, summary


def path_diagnostics() -> dict[str, Any]:
    path_rows = 0
    mode_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()
    source_type_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    groups: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in iter_jsonl(PATH_OUTCOME_LEDGER_PATH):
        path_rows += 1
        mode = str(row.get("replay_mode") or "unknown_mode")
        mode_counts[mode] += 1
        status_counts[str(row.get("path_source_status") or "unknown_status")] += 1
        terminal_counts[str(row.get("terminal_order") or "unknown_terminal")] += 1
        source_type_counts[str(row.get("source_evidence_type") or "unknown_source")] += 1
        symbol_counts[str(row.get("symbol") or row.get("source_symbol") or "unknown_symbol")] += 1
        group_id = str(row.get("duplicate_group_id") or row.get("event_id") or row.get("path_row_id"))
        groups[group_id][mode].append(row)

    comparison_counts: Counter[str] = Counter()
    mode_pair_counts: Counter[str] = Counter()
    m15_ambiguous_resolved = 0
    m15_missing_lower_available = 0
    comparable_groups = 0
    disagreement_groups = set()
    for group_id, by_mode in groups.items():
        m15_rows = by_mode.get("bar_close_m15") or []
        if not m15_rows:
            continue
        lower_modes = sorted(set(by_mode).intersection(LOWER_PATH_MODES))
        if not lower_modes:
            continue
        comparable_groups += 1
        m15_bucket = terminal_bucket(m15_rows[0].get("terminal_order"))
        for mode in lower_modes:
            lower_bucket = terminal_bucket(by_mode[mode][0].get("terminal_order"))
            key = f"bar_close_m15:{m15_bucket}->{mode}:{lower_bucket}"
            comparison_counts[key] += 1
            mode_pair_counts[f"bar_close_m15_vs_{mode}"] += 1
            if lower_bucket != m15_bucket:
                disagreement_groups.add(group_id)
            if m15_bucket == "ambiguous" and lower_bucket not in {"ambiguous", "missing_source"}:
                m15_ambiguous_resolved += 1
            if m15_bucket == "missing_source" and lower_bucket != "missing_source":
                m15_missing_lower_available += 1

    return {
        "path_rows": path_rows,
        "path_mode_counts": sorted_counter(mode_counts),
        "path_status_counts": sorted_counter(status_counts),
        "terminal_order_counts": sorted_counter(terminal_counts),
        "source_evidence_type_counts": sorted_counter(source_type_counts),
        "symbol_path_counts": sorted_counter(symbol_counts),
        "groups_with_m15_and_lower_path": comparable_groups,
        "m15_lower_path_disagreement_groups": len(disagreement_groups),
        "m15_lower_path_disagreement_rate": round(len(disagreement_groups) / comparable_groups, 12)
        if comparable_groups
        else None,
        "m15_ambiguous_resolved_by_lower_path_pairs": m15_ambiguous_resolved,
        "m15_missing_but_lower_path_available_pairs": m15_missing_lower_available,
        "m15_lower_path_comparison_counts": sorted_counter(comparison_counts),
        "m15_lower_mode_pair_counts": sorted_counter(mode_pair_counts),
    }


def robustness_split_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(ROBUSTNESS_LEDGER_PATH):
        if row.get("row_type") not in {"split_metric", "holdout_metric", "stress_cost_metric", "stress_path_metric"}:
            continue
        total = row.get("effective_r_total")
        if isinstance(total, (int, float)):
            rows.append({
                "row_type": row.get("row_type"),
                "activation_mode": row.get("runtime_activation_mode"),
                "split_type": row.get("split_type"),
                "split_value": row.get("split_value"),
                "effective_r_total": total,
                "trade_count_entry_touched": row.get("trade_count_entry_touched"),
                "win_rate_terminal": row.get("win_rate_terminal"),
                "max_drawdown_r": row.get("max_drawdown_r"),
            })
    return sorted(rows, key=lambda item: (item["effective_r_total"], str(item["split_type"]), str(item["split_value"])))


def build_core_dossiers(
    *,
    stage05_summary: dict[str, Any],
    stage05_metrics: dict[str, Any],
    stage06_summary: dict[str, Any],
    prop_metrics: dict[str, Any],
    stage07_summary: dict[str, Any],
    path_diag: dict[str, Any],
    source_gap_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    current = prop_metrics["mode_metrics"]["current_config_shadow"]["overall"]
    activated = prop_metrics["mode_metrics"]["hypothetical_activated_vnext"]["overall"]
    runtime_summary = stage05_summary.get("runtime_mode_summary", {})
    current_runtime = runtime_summary.get("current_config_shadow", {})
    activated_runtime = runtime_summary.get("hypothetical_activated_vnext", {})
    split_rows = robustness_split_rows()

    return [
        repair_row(
            family="runtime_system_limitation",
            evidence_scope="stage05_runtime_surface_coverage_and_denominator",
            severity="high",
            status="replay_measured_with_partial_runtime_surface_gaps",
            impact_metrics={
                "candidate_events": stage05_metrics.get("candidate_events"),
                "evaluated_events": stage05_metrics.get("evaluated_events"),
                "replay_rows": stage05_summary.get("replay_rows"),
                "current_replay_disposition_counts": current_runtime.get("replay_disposition_counts"),
                "activated_replay_disposition_counts": activated_runtime.get("replay_disposition_counts"),
                "pre_ai_only_insufficient_rows_per_mode": (
                    current_runtime.get("replay_disposition_counts", {}).get("PRE_AI_ONLY_INSUFFICIENT_POST_L2_FIELDS")
                ),
                "runtime_reference_only_rows_per_mode": (
                    current_runtime.get("replay_disposition_counts", {}).get("RUNTIME_REFERENCE_ONLY_NOT_PERFORMANCE_DENOMINATOR")
                ),
            },
            evidence_artifacts=[
                rel(SATURATED_REPLAY_SUMMARY_PATH),
                rel(STAGE05_METRICS_SUMMARY_PATH),
                rel(PROP_FIRM_METRICS_PATH),
            ],
            failure_anatomy=(
                "A large candidate subset is measurable only through pre-AI routing because post-L2 fields "
                "needed for direct/risk/pending surfaces were absent. Those rows are counted as candidates "
                "and skips but excluded from broker-style performance denominators."
            ),
            repair_action=(
                "Add forward candidate/trade-record capture for post-L2 side, framework, entry, stop, "
                "target, pending-intent, route evidence, and vNext decision payload before using this class "
                "as a full execution-performance denominator."
            ),
            current_session_feasibility="historical_GTOS_post_L2_state_not_generatable_when_unlogged",
            owner_access_or_capture_requirement="forward logger/capture contract; no owner broker action required for historical fabrication",
            decision_map_candidate="source-repair required",
            next_stage_use="feed Stage09 runtime/system limitation section",
        ),
        repair_row(
            family="m15_blindness_path_resolution",
            evidence_scope="bar_close_m15_vs_m1_m5_tick_ohlc_path_aware",
            severity="high",
            status="path_aware_modes_materially_change_or_resolve_m15_path_labels",
            impact_metrics=path_diag,
            evidence_artifacts=[rel(PATH_OUTCOME_LEDGER_PATH), rel(EVENT_PATH_SUMMARY_PATH)],
            failure_anatomy=(
                "M15 bar-close labels lose path ordering inside the candle and can be ambiguous or materially "
                "different from M1/M5/tick-aware reconstructions. Lower-timeframe rows are therefore required "
                "for stop-first/target-first/fillability interpretation where present."
            ),
            repair_action=(
                "Keep M15-only metrics labeled as coarse proxy; prefer M1/tick/Sierra path-aware rows for "
                "decision-map evidence; add prospective tick/Sierra capture for symbols/windows still falling "
                "back to M15/missing_source."
            ),
            current_session_feasibility="computed_from_available_path_rows; remaining gaps require source acquisition/capture",
            owner_access_or_capture_requirement="read-only tick/Sierra/OHLC export for missing symbol windows or forward tick capture",
            decision_map_candidate="keep shadow/default-off",
            next_stage_use="feed Stage09 M15-blindness and source-quality answers",
        ),
        repair_row(
            family="entry_execution_fill_no_fill",
            evidence_scope="entry_touch_fill_miss_pending_and_broker_geometry",
            severity="high",
            status="proxy_path_complete_but_broker_execution_geometry_absent",
            impact_metrics={
                "current_order_attempt_count": current.get("order_attempt_count"),
                "current_trade_count_entry_touched": current.get("trade_count_entry_touched"),
                "current_no_fill_rows": current.get("no_fill_rows"),
                "current_timeout_or_unresolved_rows": current.get("timeout_or_unresolved_rows"),
                "activated_order_attempt_count": activated.get("order_attempt_count"),
                "activated_trade_count_entry_touched": activated.get("trade_count_entry_touched"),
                "pending_lifecycle_path_rows": path_diag["path_status_counts"].get("PENDING_LIMIT_LIFECYCLE_ROW"),
                "broker_execution_fields_required": BROKER_EXECUTION_FIELDS,
            },
            evidence_artifacts=[rel(PROP_FIRM_METRICS_PATH), rel(PATH_OUTCOME_LEDGER_PATH)],
            failure_anatomy=(
                "Replay can measure entry touch, no-entry-touch, stop/target ordering, and pending lifecycle "
                "from source-bound path rows, but it cannot claim broker-realized fill, slippage, commission, "
                "swap, partial-exit, or exact account R where those fields were not captured."
            ),
            repair_action=(
                "Wire or verify forward slippage/fill lifecycle rows carrying order/deal tickets, executed "
                "prices, lot size, commission, swap, slippage, partial-exit lifecycle, and source-repair identity."
            ),
            current_session_feasibility="historical_broker_execution_truth_not_reconstructed_from_price",
            owner_access_or_capture_requirement="future broker/demo-live observation or existing source-safe execution logs with listed fields",
            decision_map_candidate="broker/demo-live observation required",
            next_stage_use="feed Stage09 execution and repair-map sections",
        ),
        repair_row(
            family="ai_prompt_routing_limitation",
            evidence_scope="pre_ai_routing_without_paid_ai_historical_replay",
            severity="medium",
            status="ai_effect_measured_as_routing_policy_not_paid_model_replay",
            impact_metrics={
                "current_pre_ai_action_distribution": stage05_metrics.get("pre_ai_action_distribution", {}).get("current_config_shadow"),
                "activated_pre_ai_action_distribution": stage05_metrics.get("pre_ai_action_distribution", {}).get("hypothetical_activated_vnext"),
                "ai_calls_allowed_skipped_narrowed": stage05_metrics.get("ai_calls_allowed_skipped_narrowed"),
                "pre_ai_action_changed": stage05_summary.get("activation_delta_counts", {}).get("pre_ai_action_changed"),
                "paid_api_or_vendor_call": prop_metrics.get("paid_api_or_vendor_call"),
            },
            evidence_artifacts=[rel(STAGE05_METRICS_SUMMARY_PATH), rel(PROP_FIRM_METRICS_PATH)],
            failure_anatomy=(
                "Stage05-Stage07 measured vNext pre-AI skip/narrow decisions and downstream proxy effects, "
                "not a paid historical replay of model completions. AI output quality, schema drift, and "
                "route-mismatch behavior require cached/stratified AI evaluation or forward capture."
            ),
            repair_action=(
                "Use a minimal-budget, stratified AI decision-value route with prompt hashes and cache keys "
                "only if Stage09 assigns AI minimal-budget evaluation; otherwise keep AI routing default-off."
            ),
            current_session_feasibility="paid_API_calls_for_AI_replay_forbidden_without_explicit_owner_approval",
            owner_access_or_capture_requirement="explicit owner approval and budget manifest for any paid AI evaluation",
            decision_map_candidate="AI minimal-budget evaluation required",
            next_stage_use="feed Stage09 AI decision-map section",
        ),
        repair_row(
            family="risk_prop_firm_behavior",
            evidence_scope="risk_zero_blocks_and_prop_firm_stress",
            severity="high",
            status="hypothetical_activation_blocks_losses_but_collapses_trade_count",
            impact_metrics={
                "current_total_r": current.get("effective_r_total"),
                "activated_total_r": activated.get("effective_r_total"),
                "activation_delta": prop_metrics.get("activation_delta"),
                "current_max_drawdown_r": current.get("max_drawdown_r"),
                "activated_max_drawdown_r": activated.get("max_drawdown_r"),
                "risk_multiplier_distribution": stage05_metrics.get("risk_multiplier_distribution"),
                "zero_risk_blocks": stage05_metrics.get("zero_risk_blocks"),
                "active_blocked_rows": activated.get("active_blocked_rows"),
                "robustness_split_rows_preserved": len(split_rows),
                "robustness_split_rows": split_rows,
            },
            evidence_artifacts=[rel(PROP_FIRM_METRICS_PATH), rel(ROBUSTNESS_LEDGER_PATH)],
            failure_anatomy=(
                "Default-off activation would have avoided most measured losses and improved proxy drawdown, "
                "but the same policy reduced entry-touched trades from 100 to 1. The result is protective, "
                "not yet a production-ready profit engine."
            ),
            repair_action=(
                "Treat activation as a keep-shadow/default-off risk-block candidate; run demo/forward "
                "observation and refine source-specific overblocking before any production-change dossier."
            ),
            current_session_feasibility="measured_from_replay; production_activation_forbidden_in_this_session",
            owner_access_or_capture_requirement="separate implementation/production-change dossier and demo observation",
            decision_map_candidate="keep shadow/default-off",
            next_stage_use="feed Stage09 risk/profitability decision map",
        ),
        repair_row(
            family="market_coverage_and_regime_data",
            evidence_scope="symbol_session_side_framework_regime_news_coverage",
            severity="medium",
            status="broad_symbol_session_coverage_but_regime_news_fields_absent",
            impact_metrics={
                "coverage_by_symbol_session_side_framework": stage05_metrics.get("coverage_by_symbol_session_side_framework"),
                "source_gap_summary": source_gap_summary,
                "regime_volatility_news_split_status": prop_metrics.get("data_quality_source_limitations", {}).get(
                    "regime_volatility_news_split_status"
                ),
                "symbol_path_counts": path_diag.get("symbol_path_counts"),
            },
            evidence_artifacts=[rel(STAGE05_METRICS_SUMMARY_PATH), rel(PROP_FIRM_METRICS_PATH), rel(SOURCE_GAP_LEDGER_PATH)],
            failure_anatomy=(
                "Replay spans the available symbol/session/side/framework universe, but source-bound regime, "
                "volatility-state, and news-state fields were not present in Stage05 rows and were not invented."
            ),
            repair_action=(
                "Add as-of regime/volatility/news enrichment fields to future replay rows or a separate "
                "source-safe enrichment lane before claiming regime/news robustness."
            ),
            current_session_feasibility="current_stage_records_absence_without_fabrication",
            owner_access_or_capture_requirement="source-safe as-of regime/news enrichment data or capture contract",
            decision_map_candidate="data-required",
            next_stage_use="feed Stage09 market coverage and methodology limitation sections",
        ),
        repair_row(
            family="mixed_resolution_remaining",
            evidence_scope="Stage06_MIXED_classifications",
            severity="medium",
            status="most_mixed_rows_replay_resolvable_some_source_required",
            impact_metrics={
                "mixed_summary": prop_metrics.get("mixed_summary"),
                "mixed_classification_counts": stage07_summary.get("mixed_classification_counts"),
                "mixed_source_required_rows": stage07_summary.get("mixed_source_required_rows"),
                "mixed_replay_resolvable_rows": stage07_summary.get("mixed_replay_resolvable_rows"),
                "stage06_reconstruction_status_counts": stage06_summary.get("reconstruction_status_counts"),
            },
            evidence_artifacts=[rel(STAGE06_SUMMARY_PATH), rel(ROBUSTNESS_LEDGER_PATH)],
            failure_anatomy=(
                "MIXED pressure is often explainable by replay deltas, but source-required MIXED families remain "
                "where evidence cannot safely collapse to FOLLOW/AVOID without missing fields or source repair."
            ),
            repair_action=(
                "Carry replay-resolvable MIXED rows into Stage09 decisions; mark source-required MIXED rows as "
                "source-repair/data-required rather than forcing directional promotion."
            ),
            current_session_feasibility="computed_from_Stage06_and_Stage07_ledgers",
            owner_access_or_capture_requirement="source repair only for source-required MIXED rows",
            decision_map_candidate="replay-inconclusive",
            next_stage_use="feed Stage09 MIXED map",
        ),
    ]


def build_outputs() -> dict[str, Any]:
    stage05_summary = read_json(SATURATED_REPLAY_SUMMARY_PATH)
    stage05_metrics = read_json(STAGE05_METRICS_SUMMARY_PATH)
    stage06_summary = read_json(STAGE06_SUMMARY_PATH)
    prop_metrics = read_json(PROP_FIRM_METRICS_PATH)
    stage07_summary = read_json(STAGE07_SUMMARY_PATH)
    path_diag = path_diagnostics()
    source_gap_repair_rows, source_gap_summary = source_gap_rows()
    core_rows = build_core_dossiers(
        stage05_summary=stage05_summary,
        stage05_metrics=stage05_metrics,
        stage06_summary=stage06_summary,
        prop_metrics=prop_metrics,
        stage07_summary=stage07_summary,
        path_diag=path_diag,
        source_gap_summary=source_gap_summary,
    )
    ledger_rows = core_rows + source_gap_repair_rows
    family_counts = Counter(row["family"] for row in ledger_rows)
    decision_counts = Counter(row["decision_map_candidate"] for row in ledger_rows)
    severity_counts = Counter(row["severity"] for row in ledger_rows)
    current_session_feasibility_counts = Counter(row["current_session_feasibility"] for row in ledger_rows)

    dossier = {
        "schema_version": "vnext_replay_stage08_failure_repair_dossier_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "dossier_scope": (
            "Failure and repair anatomy from Stage05 saturated replay, Stage06 ablation/MIXED, "
            "Stage07 prop-firm/robustness, path outcome, and source-gap artifacts."
        ),
        "families": {row["family"]: row for row in core_rows},
        "source_gap_summary": source_gap_summary,
        "path_diagnostics": path_diag,
        "decision_map_candidate_counts": sorted_counter(decision_counts),
        "family_counts": sorted_counter(family_counts),
        "severity_counts": sorted_counter(severity_counts),
        "current_session_feasibility_counts": sorted_counter(current_session_feasibility_counts),
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }
    summary = {
        "schema_version": "vnext_replay_stage08_failure_repair_summary_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "repair_rows": len(ledger_rows),
        "core_dossier_rows": len(core_rows),
        "source_gap_repair_rows": len(source_gap_repair_rows),
        "family_counts": sorted_counter(family_counts),
        "decision_map_candidate_counts": sorted_counter(decision_counts),
        "severity_counts": sorted_counter(severity_counts),
        "source_gap_summary": source_gap_summary,
        "m15_lower_path_disagreement_groups": path_diag.get("m15_lower_path_disagreement_groups"),
        "m15_lower_path_disagreement_rate": path_diag.get("m15_lower_path_disagreement_rate"),
        "stage09_next": "final report, completion audit, and promotion/kill/repair/keep-shadow map remain next-stage work",
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }
    write_json(FAILURE_REPAIR_DOSSIER_PATH, dossier)
    write_jsonl(FAILURE_REPAIR_LEDGER_PATH, ledger_rows)
    write_json(STAGE08_SUMMARY_PATH, summary)
    update_output_manifest()
    update_session_state(summary)
    return summary


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [BUILDER_PATH, FAILURE_REPAIR_DOSSIER_PATH, FAILURE_REPAIR_LEDGER_PATH, STAGE08_SUMMARY_PATH]:
        existing_paths[rel(path)] = {
            "path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "lines": line_count(path),
            "sha256": sha256_file(path),
            "source_kind": "generated_replay_builder" if path == BUILDER_PATH else "generated_replay_output",
        }
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": NEXT_STAGE_ID,
        },
    )


def update_session_state(summary: dict[str, Any]) -> None:
    if not SESSION_STATE_PATH.exists():
        return
    state = read_json(SESSION_STATE_PATH)
    completed = list(state.get("completed_stage_ids") or [])
    if STAGE_ID not in completed:
        completed.append(STAGE_ID)
    outputs = list(state.get("current_output_artifacts") or [])
    for path in [BUILDER_PATH, FAILURE_REPAIR_DOSSIER_PATH, FAILURE_REPAIR_LEDGER_PATH, STAGE08_SUMMARY_PATH]:
        item = rel(path)
        if item not in outputs:
            outputs.append(item)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "build_vnext_replay_failure_repair_dossiers_2026_05_24.py -> "
        f"pass; {summary.get('repair_rows')} repair rows; "
        f"{summary.get('source_gap_repair_rows')} source-gap repair rows"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_stage_id": NEXT_STAGE_ID,
            "current_shard_id": "STAGE_09_FINAL_TRUTH_FREEZE__ALL_OUTPUTS__FINAL_REPORT_AND_DECISION_MAP__000",
            "current_objective": (
                "Write the final replay truth-freeze report, completion audit, LFS/test manifest, "
                "and promotion/kill/repair/keep-shadow decision map from Stage01-Stage08 artifacts."
            ),
            "current_output_artifacts": outputs,
            "completed_stage_ids": completed,
            "next_executable_action": (
                "Build and run the STAGE_09 final truth-freeze builder over the full output manifest, "
                "VNEXT_REPLAY_FAILURE_REPAIR_DOSSIER_2026-05-24.json, "
                "VNEXT_REPLAY_FAILURE_REPAIR_LEDGER_2026-05-24.jsonl, prop-firm metrics, "
                "robustness ledger, MIXED ledger, source-gap ledger, and session spine."
            ),
            "last_tests_or_verifiers": tests,
            "last_commit": current_commit_label(),
            "last_verified_head": current_head(),
            "last_verified_git_status": current_git_status_short(),
            "open_questions_remaining": [
                "STAGE_09 not yet complete: no final report, completion audit, or promotion/kill/repair/keep-shadow map exists yet.",
                "Final completion remains unproven until Stage09 verifies every prompt requirement against disk artifacts.",
            ],
            "resume_instruction": (
                "On resume or uncertainty: regenerate/read .context/LIVE_STATE.md; reread the controlling prompt, "
                "starter, this session-state file, goal_session_research_discipline.md, research_operating_doctrine.md, "
                "orchestrator hardening files, latest handoff, active config, freeze report, freeze ledger, master/batch "
                "ledgers, and current runtime/tests from disk; verify HEAD/config/runtime artifact manifest hashes and "
                "git status; repair this JSON if stale; then execute next_executable_action for STAGE_09 without "
                "restarting broad planning."
            ),
        }
    )
    stage_invariants = dict(state.get("stage_invariants") or {})
    stage_invariants[STAGE_ID] = [
        "failure/repair dossier artifact exists for runtime/system limitations, M15-blindness/path-resolution limits, entry/execution/fill/no-fill limits, source-gap/data coverage limits, AI/prompt-routing limits, risk/prop-firm limits, and market-coverage limits",
        "machine-readable failure/repair ledger preserves every material dossier family and all source-gap classes without arbitrary top-N truncation, with row counts, evidence artifacts, impact metrics, repair action, owner/access/source/capture requirement, and current-session feasibility",
        "dossiers distinguish source-bound proxy/replay evidence from broker-realized/account/order truth and do not promote production changes",
        "summary advances the session spine to Stage09 and records no broker/account/order/deal/position mutation, production config mutation, paid API call, or remote push occurred",
    ]
    state["stage_invariants"] = stage_invariants
    write_json(SESSION_STATE_PATH, state)


def check_outputs() -> None:
    dossier = read_json(FAILURE_REPAIR_DOSSIER_PATH)
    summary = read_json(STAGE08_SUMMARY_PATH)
    ledger_count = line_count(FAILURE_REPAIR_LEDGER_PATH)
    if dossier.get("stage_id") != STAGE_ID or summary.get("stage_id") != STAGE_ID:
        raise AssertionError("Stage08 output has wrong stage_id")
    if not dossier.get("pass") or not summary.get("pass"):
        raise AssertionError("Stage08 output did not pass")
    if summary.get("repair_rows") != ledger_count:
        raise AssertionError("Stage08 repair ledger count does not match summary")
    required_families = {
        "runtime_system_limitation",
        "m15_blindness_path_resolution",
        "entry_execution_fill_no_fill",
        "source_gap_data_coverage",
        "ai_prompt_routing_limitation",
        "risk_prop_firm_behavior",
        "market_coverage_and_regime_data",
        "mixed_resolution_remaining",
    }
    seen_families = set()
    for row in iter_jsonl(FAILURE_REPAIR_LEDGER_PATH):
        if row.get("stage_id") != STAGE_ID:
            raise AssertionError("Stage08 repair row has wrong stage_id")
        if not row.get("repair_action") or not row.get("owner_access_or_capture_requirement"):
            raise AssertionError("Stage08 repair row missing action or owner/source requirement")
        seen_families.add(str(row.get("family")))
    missing = required_families - seen_families
    if missing:
        raise AssertionError(f"Stage08 repair ledger missing families: {sorted(missing)}")
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    manifest_paths = {item.get("path") for item in manifest.get("outputs", []) if isinstance(item, dict)}
    for path in [BUILDER_PATH, FAILURE_REPAIR_DOSSIER_PATH, FAILURE_REPAIR_LEDGER_PATH, STAGE08_SUMMARY_PATH]:
        if rel(path) not in manifest_paths:
            raise AssertionError(f"Output manifest missing {rel(path)}")
    state = read_json(SESSION_STATE_PATH)
    if STAGE_ID not in set(state.get("completed_stage_ids") or []):
        raise AssertionError("Session state missing completed Stage08")
    if state.get("current_stage_id") != NEXT_STAGE_ID:
        raise AssertionError("Session state did not advance to Stage09")
    state_outputs = set(state.get("current_output_artifacts") or [])
    if rel(BUILDER_PATH) not in state_outputs:
        raise AssertionError("Session state missing Stage08 builder artifact")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext Stage08 failure/repair dossier check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
