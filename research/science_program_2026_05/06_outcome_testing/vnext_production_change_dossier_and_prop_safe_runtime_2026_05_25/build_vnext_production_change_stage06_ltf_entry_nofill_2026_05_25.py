from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage05_prop_safe_selector_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage05", MODULE_PATH)
stage05 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage05)

stage02 = stage05.stage02
REPO_ROOT = stage05.REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    GTOSVNextRuntimeDecision,
    evaluate_vnext_ltf_path_execution,
)


ROUTE_ID = stage05.ROUTE_ID
ROUTE_DIR = stage05.ROUTE_DIR
STATE_PATH = stage05.STATE_PATH
FULL_REPLAY_DIR = stage05.FULL_REPLAY_DIR
M15_LTF_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_2026-05-24.jsonl"
)
NOFILL_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl"
)
PATH_OUTCOME_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl"
)
MISSED_WINNER_INDEX_PATH = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_2026-05-24.jsonl"
)
STAGE02_RUNTIME_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_RUNTIME_CHANGE_LEDGER_2026-05-25.jsonl"
STAGE03_KILL_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_KILL_REDESIGN_LEDGER_2026-05-25.jsonl"
STAGE06_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_LTF_ENTRY_NOFILL_LEDGER_2026-05-25.jsonl"
)
STAGE06_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE06_LTF_ENTRY_NOFILL_SUMMARY_2026-05-25.json"
)
STAGE06_DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_LTF_ENTRY_AND_NOFILL_DOSSIER_2026-05-25.md"
)
STAGE06_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE06_VERIFICATION_RESULT_2026-05-25.json"
)

REQUIRED_SCENARIOS = {
    "shadow_market_entry_touch_records_would_action",
    "active_market_entry_on_ltf_touch",
    "active_monitor_until_ltf_touch",
    "active_adjust_limit_entry_from_offset_evidence",
    "active_skip_ltf_nofill_avoid",
    "active_skip_target_without_entry",
    "active_monitor_source_gap",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage02.rel(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage02.atomic_json_write(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stage02.write_jsonl(path, rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def iter_gzip_index(index_path: Path) -> Iterable[dict[str, Any]]:
    for index_row in read_jsonl(index_path):
        chunk_path = REPO_ROOT / str(index_row["chunk_path"])
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def _counter_to_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted((str(key), int(value)) for key, value in counter.items()))


def _numeric_delta_stats() -> dict[str, Any]:
    return {"count": 0, "sum": 0.0, "positive": 0, "negative": 0, "zero": 0}


def _update_delta(stats: dict[str, Any], value: float) -> None:
    stats["count"] += 1
    stats["sum"] += value
    if value > 0:
        stats["positive"] += 1
    elif value < 0:
        stats["negative"] += 1
    else:
        stats["zero"] += 1


def summarize_m15_ltf() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    indexes = read_jsonl(M15_LTF_INDEX_PATH)
    row_count = 0
    symbols: Counter[str] = Counter()
    frameworks: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    outcome_pairs: Counter[str] = Counter()
    would_change: Counter[str] = Counter()
    flags: Counter[str] = Counter()
    delta_stats = _numeric_delta_stats()
    for row in iter_gzip_index(M15_LTF_INDEX_PATH):
        row_count += 1
        symbols[str(row.get("symbol"))] += 1
        frameworks[str(row.get("framework"))] += 1
        sides[str(row.get("side"))] += 1
        modes[str(row.get("ltf_replay_mode"))] += 1
        pair = f"{row.get('m15_terminal_outcome')}->{row.get('ltf_terminal_outcome')}"
        outcome_pairs[pair] += 1
        would_change[str(bool(row.get("would_change_execution_or_decision")))] += 1
        for key, value in (row.get("change_reason_flags") or {}).items():
            if value:
                flags[str(key)] += 1
        m15_r = row.get("m15_simulated_r")
        ltf_r = row.get("ltf_simulated_r")
        if isinstance(m15_r, (int, float)) and isinstance(ltf_r, (int, float)):
            _update_delta(delta_stats, float(ltf_r) - float(m15_r))
    if delta_stats["count"]:
        delta_stats["mean"] = delta_stats["sum"] / delta_stats["count"]
    else:
        delta_stats["mean"] = None
    ledger_rows = [
        {
            "schema_version": "vnext_production_change_stage06_ltf_aggregate_row_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
            "row_type": "m15_ltf_outcome_pair",
            "outcome_pair": key,
            "row_count": value,
        }
        for key, value in sorted(outcome_pairs.items())
    ]
    return (
        {
            "source_path": rel(M15_LTF_INDEX_PATH),
            "chunk_count": len(indexes),
            "logical_row_count": sum(int(row.get("row_count") or 0) for row in indexes),
            "scanned_row_count": row_count,
            "symbols": _counter_to_dict(symbols),
            "frameworks": _counter_to_dict(frameworks),
            "sides": _counter_to_dict(sides),
            "ltf_replay_modes": _counter_to_dict(modes),
            "would_change_execution_or_decision": _counter_to_dict(would_change),
            "change_reason_flags": _counter_to_dict(flags),
            "outcome_pairs": _counter_to_dict(outcome_pairs),
            "ltf_minus_m15_simulated_r": delta_stats,
        },
        ledger_rows,
    )


def summarize_nofill_lifecycle() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    indexes = read_jsonl(NOFILL_INDEX_PATH)
    row_count = 0
    symbols: Counter[str] = Counter()
    frameworks: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    lifecycle: Counter[str] = Counter()
    no_fill: Counter[str] = Counter()
    timeout: Counter[str] = Counter()
    source_gaps: Counter[str] = Counter()
    for row in iter_gzip_index(NOFILL_INDEX_PATH):
        row_count += 1
        symbols[str(row.get("symbol"))] += 1
        frameworks[str(row.get("framework"))] += 1
        sides[str(row.get("side"))] += 1
        modes[str(row.get("best_available_replay_mode"))] += 1
        lifecycle[str(row.get("pending_lifecycle_state"))] += 1
        no_fill[str(bool(row.get("no_fill")))] += 1
        timeout[str(bool(row.get("timeout")))] += 1
        source_gaps[str(row.get("source_gap_class"))] += 1
    ledger_rows = [
        {
            "schema_version": "vnext_production_change_stage06_ltf_aggregate_row_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
            "row_type": "pending_lifecycle_state",
            "pending_lifecycle_state": key,
            "row_count": value,
        }
        for key, value in sorted(lifecycle.items())
    ]
    return (
        {
            "source_path": rel(NOFILL_INDEX_PATH),
            "chunk_count": len(indexes),
            "logical_row_count": sum(int(row.get("row_count") or 0) for row in indexes),
            "scanned_row_count": row_count,
            "symbols": _counter_to_dict(symbols),
            "frameworks": _counter_to_dict(frameworks),
            "sides": _counter_to_dict(sides),
            "best_available_replay_modes": _counter_to_dict(modes),
            "pending_lifecycle_states": _counter_to_dict(lifecycle),
            "no_fill": _counter_to_dict(no_fill),
            "timeout": _counter_to_dict(timeout),
            "source_gap_class": _counter_to_dict(source_gaps),
        },
        ledger_rows,
    )


def summarize_missed_winners() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    indexes = read_jsonl(MISSED_WINNER_INDEX_PATH)
    row_count = 0
    classifications: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    would_change: Counter[str] = Counter()
    for row in iter_gzip_index(MISSED_WINNER_INDEX_PATH):
        row_count += 1
        classifications[str(row.get("classification"))] += 1
        modes[str(row.get("best_available_replay_mode"))] += 1
        would_change[str(bool(row.get("would_change_decision_or_execution_with_ltf_source")))] += 1
    ledger_rows = [
        {
            "schema_version": "vnext_production_change_stage06_ltf_aggregate_row_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
            "row_type": "missed_winner_avoided_loser_classification",
            "classification": key,
            "row_count": value,
        }
        for key, value in sorted(classifications.items())
    ]
    return (
        {
            "source_path": rel(MISSED_WINNER_INDEX_PATH),
            "chunk_count": len(indexes),
            "logical_row_count": sum(int(row.get("row_count") or 0) for row in indexes),
            "scanned_row_count": row_count,
            "classification_counts": _counter_to_dict(classifications),
            "best_available_replay_modes": _counter_to_dict(modes),
            "would_change_decision_or_execution_with_ltf_source": _counter_to_dict(
                would_change
            ),
        },
        ledger_rows,
    )


def summarize_path_outcome() -> dict[str, Any]:
    indexes = read_jsonl(PATH_OUTCOME_INDEX_PATH)
    row_count = 0
    replay_modes: Counter[str] = Counter()
    source_modes: Counter[str] = Counter()
    source_timeframes: Counter[str] = Counter()
    terminal_outcomes: Counter[str] = Counter()
    route_decisions: Counter[str] = Counter()
    pending_actions: Counter[str] = Counter()
    simulated = _numeric_delta_stats()
    for row in iter_gzip_index(PATH_OUTCOME_INDEX_PATH):
        row_count += 1
        replay_modes[str(row.get("replay_mode"))] += 1
        source_modes[str(row.get("source_mode"))] += 1
        source_timeframes[str(row.get("source_timeframe"))] += 1
        terminal_outcomes[str(row.get("terminal_outcome"))] += 1
        route_decisions[str(row.get("route_decision"))] += 1
        pending_actions[str(row.get("pending_would_action"))] += 1
        simulated_r = row.get("simulated_r")
        if isinstance(simulated_r, (int, float)):
            _update_delta(simulated, float(simulated_r))
    simulated["mean"] = simulated["sum"] / simulated["count"] if simulated["count"] else None
    return {
        "source_path": rel(PATH_OUTCOME_INDEX_PATH),
        "chunk_count": len(indexes),
        "logical_row_count": sum(int(row.get("row_count") or 0) for row in indexes),
        "scanned_row_count": row_count,
        "replay_modes": _counter_to_dict(replay_modes),
        "source_modes": _counter_to_dict(source_modes),
        "source_timeframes": _counter_to_dict(source_timeframes),
        "terminal_outcomes": _counter_to_dict(terminal_outcomes),
        "route_decisions": _counter_to_dict(route_decisions),
        "pending_would_actions": _counter_to_dict(pending_actions),
        "simulated_r": simulated,
    }


def summarize_route_ltf_surface() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = []
    for source_path, source_stage in (
        (STAGE02_RUNTIME_PATH, "STAGE_02_PROMOTION_IMPLEMENTATION"),
        (STAGE03_KILL_PATH, "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"),
    ):
        for row in read_jsonl(source_path):
            if row.get("system_surface") == "ltf_path_nofill_pending_lifecycle_engine":
                rows.append((source_stage, row))
    by_stage: Counter[str] = Counter()
    components: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    action_classes: Counter[str] = Counter()
    ledger_rows: list[dict[str, Any]] = []
    for stage, row in rows:
        by_stage[stage] += 1
        components[str(row.get("source_component"))] += 1
        decisions[str(row.get("computed_decision"))] += 1
        action_classes[str(row.get("action_class"))] += 1
    for key, value in sorted(components.items()):
        ledger_rows.append(
            {
                "schema_version": "vnext_production_change_stage06_ltf_aggregate_row_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
                "row_type": "production_change_ltf_surface_component",
                "source_component": key,
                "row_count": value,
            }
        )
    return (
        {
            "row_count": len(rows),
            "by_stage": _counter_to_dict(by_stage),
            "source_components": _counter_to_dict(components),
            "computed_decisions": _counter_to_dict(decisions),
            "action_classes": _counter_to_dict(action_classes),
            "runtime_effect": (
                "Stage06 adds an activation-gated LTF path execution decision "
                "and pending monitor that consumes these surface rows."
            ),
        },
        ledger_rows,
    )


def _runtime_decision(
    *,
    decision: str,
    source_component_counts: dict[str, int],
    component_decisions: dict[str, dict[str, int]] | None = None,
    proxy_counts: dict[str, int] | None = None,
    target_stop_counts: dict[str, int] | None = None,
    apply_to_execution: bool = True,
) -> GTOSVNextRuntimeDecision:
    return GTOSVNextRuntimeDecision(
        decision=decision,  # type: ignore[arg-type]
        event={"symbol": "XAUUSD", "side": "LONG", "route_session": "ny_kz"},
        enabled=True,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason="stage06_ltf_path_scenario",
        evidence={
            "matched_rows": sum(source_component_counts.values()),
            "source_component_counts": source_component_counts,
            "source_component_decision_counts": component_decisions or {},
            "proxy_r_class_counts": proxy_counts or {},
            "target_stop_order_class_counts": target_stop_counts or {},
        },
    )


def _config(*, apply: bool) -> dict[str, Any]:
    return {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "ltf_path_execution_enabled": True,
            "ltf_path_execution_apply_to_execution": apply,
            "ltf_path_execution_min_component_rows": 1,
            "ltf_path_monitor_timeframe": "M1",
            "ltf_path_market_entry_requires_path_touch": True,
            "ltf_path_adjusted_entry_enabled": True,
            "ltf_path_adjusted_entry_offset_r": 0.5,
        }
    }


def scenario_rows() -> list[dict[str, Any]]:
    scenarios = [
        {
            "scenario_id": "shadow_market_entry_touch_records_would_action",
            "decision": _runtime_decision(
                decision="FOLLOW",
                source_component_counts={"nofill_near_miss_market_entry": 2},
                component_decisions={"nofill_near_miss_market_entry": {"FOLLOW": 2}},
                proxy_counts={"STRONG_POSITIVE_PROXY_R": 2},
                target_stop_counts={"TARGET_FIRST_PROXY_DOMINANT": 2},
            ),
            "config": _config(apply=False),
            "path_state": {"source_complete": True, "entry_touched": True},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_market_entry_on_ltf_touch",
            "decision": _runtime_decision(
                decision="FOLLOW",
                source_component_counts={"nofill_near_miss_market_entry": 2},
                component_decisions={"nofill_near_miss_market_entry": {"FOLLOW": 2}},
                proxy_counts={"STRONG_POSITIVE_PROXY_R": 2},
                target_stop_counts={"TARGET_FIRST_PROXY_DOMINANT": 2},
            ),
            "config": _config(apply=True),
            "path_state": {"source_complete": True, "entry_touched": True},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_monitor_until_ltf_touch",
            "decision": _runtime_decision(
                decision="FOLLOW",
                source_component_counts={"nofill_near_miss_market_entry": 2},
                component_decisions={"nofill_near_miss_market_entry": {"FOLLOW": 2}},
                proxy_counts={"STRONG_POSITIVE_PROXY_R": 2},
                target_stop_counts={"TARGET_FIRST_PROXY_DOMINANT": 2},
            ),
            "config": _config(apply=True),
            "path_state": {"source_complete": True, "entry_touched": False},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_adjust_limit_entry_from_offset_evidence",
            "decision": _runtime_decision(
                decision="AVOID",
                source_component_counts={"nofill_near_miss_offset": 4},
                component_decisions={"nofill_near_miss_offset": {"AVOID": 4}},
                proxy_counts={"STRONG_NEGATIVE_PROXY_R": 4},
            ),
            "config": _config(apply=True),
            "path_state": {"source_complete": True},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_skip_ltf_nofill_avoid",
            "decision": _runtime_decision(
                decision="AVOID",
                source_component_counts={"nofill_far_miss_avoid": 3},
                component_decisions={"nofill_far_miss_avoid": {"AVOID": 3}},
                proxy_counts={"STRONG_NEGATIVE_PROXY_R": 3},
            ),
            "config": _config(apply=True),
            "path_state": {"source_complete": True},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_skip_target_without_entry",
            "decision": _runtime_decision(
                decision="FOLLOW",
                source_component_counts={"main_orch24_structural_ltf_positive_follow": 1},
                component_decisions={
                    "main_orch24_structural_ltf_positive_follow": {"FOLLOW": 1}
                },
                proxy_counts={"POSITIVE_PROXY_R": 1},
            ),
            "config": _config(apply=True),
            "path_state": {
                "source_complete": True,
                "target_touched_without_entry": True,
            },
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
        {
            "scenario_id": "active_monitor_source_gap",
            "decision": _runtime_decision(
                decision="MIXED",
                source_component_counts={"ltf_path_source_blocked_guard": 1},
                component_decisions={"ltf_path_source_blocked_guard": {"MIXED": 1}},
            ),
            "config": _config(apply=True),
            "path_state": {"source_complete": False, "path_source_status": "no_closed_ltf_candle"},
            "trade_params": {"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        },
    ]
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        decision = evaluate_vnext_ltf_path_execution(
            decision=scenario["decision"],
            config=scenario["config"],
            trade_params=scenario.get("trade_params"),
            path_state=scenario.get("path_state"),
        )
        rows.append(
            {
                "schema_version": "vnext_production_change_stage06_ltf_scenario_row_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
                "row_type": "runtime_scenario",
                "scenario_id": scenario["scenario_id"],
                "action": decision.action,
                "would_action": decision.would_action,
                "applied": decision.applied,
                "reason": decision.reason,
                "monitor_timeframe": decision.monitor_timeframe,
                "replay_mode": decision.replay_mode,
                "adjusted_entry_price": decision.adjusted_entry_price,
                "decision_record": decision.to_record(),
                "activation_gate": "gtos_vnext_runtime.ltf_path_execution_apply_to_execution",
                "no_live_trading": True,
                "no_broker_mutation": True,
            }
        )
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    m15_ltf, m15_rows = summarize_m15_ltf()
    nofill, nofill_rows = summarize_nofill_lifecycle()
    missed, missed_rows = summarize_missed_winners()
    path_outcome = summarize_path_outcome()
    surface, surface_rows = summarize_route_ltf_surface()
    ledger_rows = [*rows, *m15_rows, *nofill_rows, *missed_rows, *surface_rows]
    write_jsonl(STAGE06_LEDGER_PATH, ledger_rows)
    action_counts = Counter(str(row.get("action")) for row in rows)
    would_counts = Counter(str(row.get("would_action")) for row in rows)
    return {
        "schema_version": "vnext_production_change_stage06_ltf_entry_nofill_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ltf_entry_nofill_ledger_path": rel(STAGE06_LEDGER_PATH),
        "ltf_entry_nofill_dossier_path": rel(STAGE06_DOSSIER_PATH),
        "scenario_row_count": len(rows),
        "required_scenario_count": len(REQUIRED_SCENARIOS),
        "missing_required_scenarios": sorted(
            REQUIRED_SCENARIOS - {str(row["scenario_id"]) for row in rows}
        ),
        "runtime_scenario_action_counts": _counter_to_dict(action_counts),
        "runtime_scenario_would_action_counts": _counter_to_dict(would_counts),
        "m15_vs_ltf_disagreement": m15_ltf,
        "nofill_pending_lifecycle": nofill,
        "missed_winner_avoided_loser": missed,
        "path_outcome_r": path_outcome,
        "production_change_ltf_surface": surface,
        "runtime_behavior": {
            "implemented_function": "evaluate_vnext_ltf_path_execution",
            "orchestrator_hook": "post-L2/pre-prop-selector candidate execution path",
            "pending_monitor_hook": "_check_pending_limit_ltf_path during monitored sleep/outside KZ",
            "default_current_config": "shadow telemetry only; ltf_path_execution_apply_to_execution=false",
            "active_actions": [
                "MONITOR_LTF_PATH",
                "MARKET_ENTRY_NOW",
                "ADJUST_LIMIT_ENTRY",
                "SKIP_LTF_NOFILL_AVOID",
            ],
        },
    }


def write_dossier(summary: dict[str, Any]) -> None:
    m15 = summary["m15_vs_ltf_disagreement"]
    nofill = summary["nofill_pending_lifecycle"]
    missed = summary["missed_winner_avoided_loser"]
    path = summary["path_outcome_r"]
    surface = summary["production_change_ltf_surface"]
    lines = [
        "# vNext Production Change Stage06 LTF Entry And No-Fill Dossier",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Runtime Change",
        "",
        "- Added `evaluate_vnext_ltf_path_execution` as a replay-backed Stage06 decision surface.",
        "- Added orchestrator post-L2/pre-prop-selector handling for LTF skip, monitor, market entry, and adjusted limit entry.",
        "- Added an activation-gated LTF pending monitor that can check M1/M5 candles during monitored sleep and outside-KZ pending checks.",
        "- Current config keeps `ltf_path_execution_apply_to_execution=false`, so no broker-facing activation occurs by default.",
        "",
        "## Replay Evidence Consumed",
        "",
        f"- M15-vs-LTF disagreement rows: {m15['logical_row_count']}.",
        f"- Would change execution/decision: {json.dumps(m15['would_change_execution_or_decision'], sort_keys=True)}.",
        f"- LTF modes: {json.dumps(m15['ltf_replay_modes'], sort_keys=True)}.",
        f"- Change flags: {json.dumps(m15['change_reason_flags'], sort_keys=True)}.",
        f"- LTF minus M15 simulated R mean: {m15['ltf_minus_m15_simulated_r']['mean']:.6f}.",
        f"- No-fill/pending lifecycle rows: {nofill['logical_row_count']}.",
        f"- Pending lifecycle states: {json.dumps(nofill['pending_lifecycle_states'], sort_keys=True)}.",
        f"- Missed-winner/avoided-loser rows: {missed['logical_row_count']}.",
        f"- Classification counts: {json.dumps(missed['classification_counts'], sort_keys=True)}.",
        f"- Path outcome/R rows: {path['logical_row_count']}.",
        f"- Simulated R count/sum/mean: {path['simulated_r']['count']} / {path['simulated_r']['sum']:.6f} / {path['simulated_r']['mean']:.6f}.",
        "",
        "## Runtime Surface Coverage",
        "",
        f"- Production-change LTF surface rows consumed: {surface['row_count']}.",
        f"- Rows by prior stage: {json.dumps(surface['by_stage'], sort_keys=True)}.",
        f"- Source components: {json.dumps(surface['source_components'], sort_keys=True)}.",
        f"- Computed decisions: {json.dumps(surface['computed_decisions'], sort_keys=True)}.",
        "",
        "## Scenario Coverage",
        "",
        f"- Runtime scenario rows: {summary['scenario_row_count']}.",
        f"- Action counts: {json.dumps(summary['runtime_scenario_action_counts'], sort_keys=True)}.",
        f"- Would-action counts: {json.dumps(summary['runtime_scenario_would_action_counts'], sort_keys=True)}.",
        "- Scenarios cover shadow would-action, active market entry on touch, active monitor, adjusted limit entry, no-fill skip, target-without-entry skip, and source-gap monitoring.",
        "",
        "## Activation Boundary",
        "",
        "- The engine is activation-gated by global `gtos_vnext_runtime.apply_to_execution` and `ltf_path_execution_apply_to_execution`.",
        "- The pending monitor uses read-only candle/tick state and only calls the existing execution path when a configured active pending intent touches the entry.",
        "- No live trading, broker mutation, paid API, source deletion, remote push, or activation flip is performed by this stage.",
        "",
    ]
    STAGE06_DOSSIER_PATH.write_text("\n".join(lines), encoding="utf-8")


def verify_summary(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    scenario_ids = {str(row["scenario_id"]) for row in rows}
    if scenario_ids != REQUIRED_SCENARIOS:
        failures.append(f"scenario coverage mismatch: {sorted(REQUIRED_SCENARIOS - scenario_ids)}")
    required_would = {
        "MONITOR_LTF_PATH",
        "MARKET_ENTRY_NOW",
        "ADJUST_LIMIT_ENTRY",
        "SKIP_LTF_NOFILL_AVOID",
    }
    would_actions = {str(row["would_action"]) for row in rows}
    missing_would = sorted(required_would - would_actions)
    if missing_would:
        failures.append(f"missing Stage06 would actions: {missing_would}")
    if summary["m15_vs_ltf_disagreement"]["logical_row_count"] != 405729:
        failures.append("M15-vs-LTF disagreement row count mismatch")
    if summary["nofill_pending_lifecycle"]["logical_row_count"] != 253234:
        failures.append("no-fill pending lifecycle row count mismatch")
    if summary["missed_winner_avoided_loser"]["logical_row_count"] != 253234:
        failures.append("missed winner / avoided loser row count mismatch")
    if summary["path_outcome_r"]["logical_row_count"] != 1978947:
        failures.append("path outcome/R row count mismatch")
    if summary["production_change_ltf_surface"]["row_count"] != 1064:
        failures.append("production-change LTF surface row count mismatch")
    if not summary["m15_vs_ltf_disagreement"]["would_change_execution_or_decision"].get("True"):
        failures.append("M15-vs-LTF rows do not show execution-changing cases")
    if summary["runtime_scenario_action_counts"].get("PLACE_LIMIT", 0) <= 0:
        failures.append("current/shadow config did not preserve default PLACE_LIMIT action")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = "STAGE_07_AI_POLICY" if complete else "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"
    state["stage_status_table"]["STAGE_06_LTF_ENTRY_NOFILL_ENGINE"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_07_AI_POLICY"] = "in_progress"
        state["active_invariant"] = "define_and_implement_ai_role"
        state["first_incomplete_invariant"] = "STAGE_07_AI_POLICY"
        state["exact_next_action"] = (
            "Implement the Stage07 mechanical-first AI policy and no-paid-call "
            "prompt/schema reliability harness without restarting Stage00-06."
        )
    else:
        state["active_invariant"] = "fix_m15_blindness_with_ltf_path_aware_execution"
        state["first_incomplete_invariant"] = "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"
        state["exact_next_action"] = (
            "Run Stage06 verifier and focused runtime/config tests for the "
            "LTF path-aware entry/no-fill engine, then mark Stage06 complete."
        )
    outputs = state.setdefault("output_artifact_paths", {})
    outputs["ltf_entry_nofill_ledger"] = rel(STAGE06_LEDGER_PATH)
    outputs["stage06_ltf_entry_nofill_summary"] = rel(STAGE06_SUMMARY_PATH)
    outputs["ltf_entry_nofill_dossier"] = rel(STAGE06_DOSSIER_PATH)
    outputs["stage06_verification_result"] = rel(STAGE06_VERIFICATION_RESULT_PATH)
    state.setdefault("rows_groups_processed", {})[
        "stage06_ltf_runtime_scenarios"
    ] = summary["scenario_row_count"]
    state["rows_groups_processed"]["stage06_m15_ltf_disagreement_rows"] = summary[
        "m15_vs_ltf_disagreement"
    ]["logical_row_count"]
    state["rows_groups_processed"]["stage06_nofill_pending_lifecycle_rows"] = summary[
        "nofill_pending_lifecycle"
    ]["logical_row_count"]
    state["row_count_hash_coverage"]["stage06_ltf_entry_nofill_summary"] = {
        "scenario_row_count": summary["scenario_row_count"],
        "m15_vs_ltf_disagreement_rows": summary["m15_vs_ltf_disagreement"][
            "logical_row_count"
        ],
        "nofill_pending_lifecycle_rows": summary["nofill_pending_lifecycle"][
            "logical_row_count"
        ],
        "missed_winner_avoided_loser_rows": summary["missed_winner_avoided_loser"][
            "logical_row_count"
        ],
        "path_outcome_r_rows": summary["path_outcome_r"]["logical_row_count"],
        "production_change_ltf_surface_rows": summary[
            "production_change_ltf_surface"
        ]["row_count"],
        "runtime_scenario_action_counts": summary["runtime_scenario_action_counts"],
        "runtime_scenario_would_action_counts": summary[
            "runtime_scenario_would_action_counts"
        ],
    }
    state["verification_status"]["stage06_ltf_entry_nofill_built"] = True
    state["verification_status"]["stage06_ltf_runtime_scenarios"] = summary[
        "scenario_row_count"
    ]
    state["verification_status"]["stage06_verifier_ok"] = complete
    implemented = state.setdefault("implemented_surfaces", [])
    surface_entry = {
        "stage": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
        "surface": "ltf_path_aware_execution_state_machine_and_pending_monitor",
        "runtime_row_count": summary["production_change_ltf_surface"]["row_count"],
        "activation_gate": "gtos_vnext_runtime.ltf_path_execution_apply_to_execution",
        "artifact": rel(STAGE06_LEDGER_PATH),
    }
    if surface_entry not in implemented:
        implemented.append(surface_entry)
    state["remaining_executable_actions"] = (
        [
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
        if complete
        else [
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows = scenario_rows()
    summary = build_summary(rows)
    failures = verify_summary(summary, rows)
    atomic_json_write(STAGE06_SUMMARY_PATH, summary)
    write_dossier(summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage06_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
    }
    atomic_json_write(STAGE06_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
