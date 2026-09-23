from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage03_kill_redesign_guards_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage03", MODULE_PATH)
stage03 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage03)

stage02 = stage03.stage02
stage01 = stage03.stage01
REPO_ROOT = stage03.REPO_ROOT
ROUTE_ID = stage03.ROUTE_ID
ROUTE_DIR = stage03.ROUTE_DIR
STATE_PATH = stage03.STATE_PATH
MIXED_RESOLUTION_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_MIXED_RESOLUTION_LEDGER_2026-05-25.jsonl"
)
STAGE04_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE04_MIXED_RESOLUTION_SUMMARY_2026-05-25.json"
)
STAGE04_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE04_VERIFICATION_RESULT_2026-05-25.json"
)

EVIDENCE_FAMILY = "gtos_vnext_production_change_mixed_resolution"
SOURCE_NAME = "vnext_production_change_stage04_mixed_resolution"
SOURCE_ARTIFACT_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "VNEXT_FULL_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl"
)
EXPECTED_MIXED_RESOLUTION_ROWS = 1018
EXPECTED_RESOLUTION_CLASS_COUNTS = {
    "ambiguous_but_replay_measured": 374,
    "harmful_overblock_context": 32,
    "replay_resolvable_into_avoid_candidate": 74,
    "replay_resolvable_into_follow_candidate": 86,
    "useful_avoid_context": 452,
}

SESSION_ALIASES = {
    "london": "london_core",
    "london_core": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "ny_core": "ny_core",
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "off_kz": "off_core_session",
    "off_core": "off_core_session",
    "off_core_session": "off_core_session",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage02.rel(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage02.atomic_json_write(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stage02.write_jsonl(path, rows)


def source_count(row: dict[str, Any]) -> float:
    for key in ("best_available_simulated_r_count", "candidate_count", "dominance_row_count"):
        value = stage02.as_float(row.get(key))
        if value is not None and value > 0:
            return value
    return 1.0


def source_total(row: dict[str, Any], count: float) -> float | None:
    mean = stage02.as_float(row.get("best_available_simulated_r_mean"))
    if mean is None:
        return None
    return mean * count


def metric_trace(total: float | None, count: float) -> dict[str, Any]:
    if total is None:
        return {
            "sum": None,
            "mean": None,
            "match_rows_with_metric": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
        }
    return {
        "sum": round(total, 12),
        "mean": round(total / count, 12) if count else None,
        "match_rows_with_metric": count,
        "positive_rows": count if total > 0 else 0,
        "negative_rows": count if total < 0 else 0,
        "zero_rows": count if total == 0 else 0,
    }


def r_metric_traces(row: dict[str, Any]) -> dict[str, Any]:
    count = source_count(row)
    total = source_total(row, count)
    return {
        "cost_adjusted_simulated_r": metric_trace(total, count),
        "proxy_score": metric_trace(total, count),
        "stress_simulated_r": metric_trace(total, count),
        "effective_n": {
            "sum": count,
            "mean": count,
            "match_rows_with_metric": 1,
            "positive_rows": 1 if count > 0 else 0,
            "negative_rows": 0,
            "zero_rows": 1 if count == 0 else 0,
        },
    }


def canonical_session(value: Any) -> str:
    raw = str(value or "").strip()
    return SESSION_ALIASES.get(raw.casefold().replace("-", "_"), raw)


def runtime_decision(row: dict[str, Any]) -> str:
    resolution_class = str(row.get("resolution_class") or "")
    if resolution_class == "replay_resolvable_into_follow_candidate":
        return "FOLLOW"
    if resolution_class in {
        "replay_resolvable_into_avoid_candidate",
        "useful_avoid_context",
    }:
        return "AVOID"
    return "MIXED"


def review_action(decision: str) -> str:
    if decision == "FOLLOW":
        return "DEFAULT_OFF_FOLLOW_SCORER_REVIEW"
    if decision == "AVOID":
        return "DEFAULT_OFF_AVOID_FILTER_REVIEW"
    return "DEFAULT_OFF_MIXED_SOURCE_REPAIR_GUARD"


def implementation_action(row: dict[str, Any], decision: str) -> str:
    resolution_class = str(row.get("resolution_class") or "")
    if resolution_class == "harmful_overblock_context":
        return "KILL_OR_REDESIGN_HARMFUL_OVERBLOCK_AS_NON_OVERRIDE_GUARD"
    if resolution_class == "ambiguous_but_replay_measured":
        return "RESOLVE_MIXED_REPLAY_MEASURED_AS_CONTEXT_GUARD"
    if decision == "FOLLOW":
        return "RESOLVE_MIXED_REPLAY_FOLLOW_PRESSURE_ACTIVATION_GATED"
    if resolution_class == "useful_avoid_context":
        return "RESOLVE_MIXED_USEFUL_AVOID_CONTEXT_ACTIVATION_GATED"
    return "RESOLVE_MIXED_REPLAY_AVOID_PRESSURE_ACTIVATION_GATED"


def action_family(decision: str) -> str:
    if decision == "FOLLOW":
        return "production_change_mixed_follow_pressure"
    if decision == "AVOID":
        return "production_change_mixed_avoid_pressure"
    return "production_change_mixed_non_override_guard"


def route_family_for_row(row: dict[str, Any]) -> str:
    component = str(row.get("source_component") or "")
    if component.startswith("rejected_candidate") or component.startswith("l2_"):
        return "numeric_router"
    return stage02.generated_route_family(row, component)


def proxy_class(row: dict[str, Any], decision: str, total: float | None, count: float) -> str:
    resolution_class = str(row.get("resolution_class") or "")
    if resolution_class == "harmful_overblock_context":
        return "HARMFUL_OVERBLOCK_GUARD_PROXY_R"
    if decision == "MIXED":
        return "MIXED_REPLAY_MEASURED_PROXY_R"
    if decision == "AVOID" and resolution_class == "useful_avoid_context":
        return "USEFUL_AVOID_CONTEXT_PROXY_R"
    return stage02.proxy_class(total, count)


def target_stop_order_class(row: dict[str, Any], decision: str) -> str:
    resolution_class = str(row.get("resolution_class") or "")
    if resolution_class == "harmful_overblock_context":
        return "HARMFUL_OVERBLOCK_REDESIGN_GUARD"
    if decision == "MIXED":
        return "MIXED_REPLAY_MEASURED_CONTEXT"
    if decision == "AVOID":
        return "MIXED_RESOLUTION_AVOID_CONTEXT"
    return "MIXED_RESOLUTION_FOLLOW_CONTEXT"


def build_event_scope(
    row: dict[str, Any],
    *,
    source_component: str,
    route_family: str,
    proxy_r_class: str,
    target_stop_class: str,
    actionable: bool,
) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "")
    session = canonical_session(row.get("route_session"))
    side = str(row.get("side") or "")
    framework = stage02.normalized_framework(row)
    scope: dict[str, Any] = {}
    if symbol:
        scope["symbol"] = symbol
        scope["source_symbol"] = symbol
        family = stage02.symbol_family(symbol)
        if family:
            scope["symbol_family"] = family
        scope["market"] = symbol
    if session:
        scope["route_session"] = session
    if side:
        scope["side"] = side
    if framework:
        scope["framework"] = framework
    if route_family:
        scope["route_family"] = route_family
    scope["market_timeframe"] = "M15"
    scope["timeframe"] = "M15"
    if actionable:
        scope["source_component"] = source_component
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class
    if target_stop_class:
        scope["target_stop_order_class"] = target_stop_class
    return {key: value for key, value in scope.items() if value not in (None, "")}


def runtime_row(
    *,
    row: dict[str, Any],
    instance_index: int,
) -> dict[str, Any]:
    count = source_count(row)
    total = source_total(row, count)
    decision = runtime_decision(row)
    source_component = str(row.get("source_component") or "mixed_resolution_unknown_component")
    route_family = route_family_for_row(row)
    proxy_r_class = proxy_class(row, decision, total, count)
    target_stop_class = target_stop_order_class(row, decision)
    scope_candidate = build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=decision in {"FOLLOW", "AVOID"},
    )
    actionable = decision in {"FOLLOW", "AVOID"} and stage02.has_required_anchors(
        scope_candidate
    )
    if not actionable:
        decision = "MIXED"
        proxy_r_class = proxy_class(row, decision, total, count)
        target_stop_class = target_stop_order_class(row, decision)
    event_scope = build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=actionable,
    )
    source_row_id = str(row.get("mixed_resolution_row_id") or f"mixed-{instance_index}")
    review_row_id = f"prodchg_stage04_{instance_index:06d}_{stage02.stable_hash(row)}"
    runtime_surface = stage01.target_for_row(row)["runtime_surface"]
    resolution_class = str(row.get("resolution_class") or "")
    missed_counts = (
        row.get("missed_winner_avoided_loser_classification_counts")
        if isinstance(row.get("missed_winner_avoided_loser_classification_counts"), dict)
        else {}
    )
    return {
        "schema_version": "vnext_production_change_mixed_resolution_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_04_MIXED_RESOLUTION",
        "row_type": "gtos_vnext_production_change_mixed_resolution_row",
        "review_row_id": review_row_id,
        "row_key": review_row_id,
        "source_row_id": source_row_id,
        "source_row_instance_index": instance_index,
        "source_row_fingerprint": stage02.stable_hash(row),
        "event_scope": event_scope,
        "scope_key": "|".join(f"{key}={value}" for key, value in sorted(event_scope.items())),
        "review_action": review_action(decision),
        "computed_decision": decision,
        "implementation_action": implementation_action(row, decision),
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": runtime_surface,
        "source_role": "production_change_mixed_resolution",
        "system_surface": runtime_surface,
        "source_component": source_component,
        "original_source_component": source_component,
        "action_family": action_family(decision),
        "action_class": str(row.get("action_class") or "mixed_resolution_context_guard"),
        "original_action_class": str(row.get("action_class") or "mixed_resolution_context_guard"),
        "framework": stage02.normalized_framework(row),
        "route_family": route_family,
        "market_timeframe": event_scope.get("market_timeframe"),
        "timeframe": event_scope.get("timeframe"),
        "route_session": event_scope.get("route_session"),
        "side": event_scope.get("side"),
        "symbol": event_scope.get("symbol"),
        "source_symbol": event_scope.get("source_symbol"),
        "symbol_family": event_scope.get("symbol_family"),
        "market": event_scope.get("market"),
        "proxy_r_class": proxy_r_class,
        "target_stop_order_class": target_stop_class,
        "r_evidence_class": "STAGE05_MIXED_RESOLUTION_REPLAY_PROXY_R",
        "r_metric_traces": r_metric_traces(row),
        "source_path": SOURCE_ARTIFACT_REL,
        "source_artifact": SOURCE_ARTIFACT_REL,
        "source_full_replay_source_path": row.get("source_path"),
        "source_index": row.get("source_index"),
        "source_shard_id": row.get("stage04_shard_id"),
        "mixed_resolution_class": resolution_class,
        "resolution_class": resolution_class,
        "resolution_scope": row.get("resolution_scope"),
        "resolution_rationale": row.get("resolution_rationale"),
        "baseline_decision_counts": row.get("baseline_decision_counts"),
        "dominance_row_count": row.get("dominance_row_count"),
        "candidate_count": row.get("candidate_count"),
        "variant_change_count": row.get("variant_change_count"),
        "ltf_execution_change_count": row.get("ltf_execution_change_count"),
        "current_source_bound_rows": row.get("current_source_bound_rows"),
        "source_required_rows": row.get("source_required_rows"),
        "broad_unanchored_rows": row.get("broad_unanchored_rows"),
        "stale_legacy_rows": row.get("stale_legacy_rows"),
        "missed_winner_avoided_loser_classification_counts": missed_counts,
        "best_available_simulated_r_mean": row.get("best_available_simulated_r_mean"),
        "best_available_simulated_r_count": row.get("best_available_simulated_r_count"),
        "runtime_candidate_use_permitted": actionable,
        "mixed_resolution_follow_pressure": decision == "FOLLOW",
        "mixed_resolution_avoid_pressure": decision == "AVOID",
        "mixed_resolution_non_override_guard": decision == "MIXED",
        "harmful_overblock_killed_or_redesigned": resolution_class == "harmful_overblock_context",
        "activation_gated": True,
        "production_activation_gate": "gtos_vnext_runtime.apply_to_execution",
        "pre_ai_activation_gate": "gtos_vnext_runtime.pre_ai_apply_to_ai_call",
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "production_change_allowed_by_this_row": False,
        "requires_owner_review_before_runtime_effect": True,
        "no_live_trading": True,
        "no_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
    }


def build_mixed_resolution_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [
        runtime_row(row=row, instance_index=index)
        for index, row in enumerate(stage01.mixed_resolution_rows(), start=1)
    ]
    return rows, summarize_rows(rows)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(str(row.get("computed_decision") or "") for row in rows)
    class_counts = Counter(str(row.get("mixed_resolution_class") or "") for row in rows)
    surface_counts = Counter(str(row.get("system_surface") or "") for row in rows)
    class_decision_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        cls = str(row.get("mixed_resolution_class") or "")
        class_decision_counts.setdefault(cls, Counter())
        class_decision_counts[cls][str(row.get("computed_decision") or "")] += 1
    class_decision_counts = {
        key: dict(sorted(value.items()))
        for key, value in sorted(class_decision_counts.items())
    }
    actionable_rows = [row for row in rows if row.get("runtime_candidate_use_permitted")]
    unanchored_rows = [
        row for row in rows if not stage02.has_required_anchors(row.get("event_scope") or {})
    ]
    return {
        "schema_version": "vnext_production_change_stage04_mixed_resolution_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "mixed_resolution_ledger_path": rel(REPO_ROOT / MIXED_RESOLUTION_LEDGER_PATH),
        "source_mixed_resolution_ledger_path": SOURCE_ARTIFACT_REL,
        "expected_mixed_resolution_rows": EXPECTED_MIXED_RESOLUTION_ROWS,
        "mixed_resolution_runtime_row_instances": len(rows),
        "unique_mixed_resolution_row_ids": len({row.get("source_row_id") for row in rows}),
        "runtime_candidate_use_permitted_rows": len(actionable_rows),
        "non_override_guard_rows": len(rows) - len(actionable_rows),
        "unanchored_guard_rows": len(unanchored_rows),
        "computed_decision_counts": dict(sorted(decision_counts.items())),
        "mixed_resolution_class_counts": dict(sorted(class_counts.items())),
        "mixed_resolution_class_decision_counts": class_decision_counts,
        "system_surface_counts": dict(sorted(surface_counts.items())),
        "source_component_counts": dict(
            sorted(Counter(str(row.get("source_component") or "") for row in rows).items())
        ),
        "route_family_counts": dict(
            sorted(Counter(str(row.get("route_family") or "") for row in rows).items())
        ),
        "harmful_overblock_rows": class_counts.get("harmful_overblock_context", 0),
        "harmful_overblock_avoid_rows": sum(
            1
            for row in rows
            if row.get("mixed_resolution_class") == "harmful_overblock_context"
            and row.get("computed_decision") == "AVOID"
        ),
        "source_required_rows": sum(int(row.get("source_required_rows") or 0) for row in rows),
        "broad_unanchored_rows": sum(int(row.get("broad_unanchored_rows") or 0) for row in rows),
        "stale_legacy_rows": sum(int(row.get("stale_legacy_rows") or 0) for row in rows),
        "artifact_config_path": rel(REPO_ROOT / MIXED_RESOLUTION_LEDGER_PATH),
        "artifact_evidence_family": EVIDENCE_FAMILY,
    }


def verify_rows(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if summary["mixed_resolution_runtime_row_instances"] != EXPECTED_MIXED_RESOLUTION_ROWS:
        failures.append(
            "Stage04 mixed-resolution row count expected "
            f"{EXPECTED_MIXED_RESOLUTION_ROWS} got "
            f"{summary['mixed_resolution_runtime_row_instances']}"
        )
    if summary["mixed_resolution_class_counts"] != EXPECTED_RESOLUTION_CLASS_COUNTS:
        failures.append(
            "Stage04 mixed-resolution class counts mismatch "
            f"{summary['mixed_resolution_class_counts']}"
        )
    if summary["unique_mixed_resolution_row_ids"] != EXPECTED_MIXED_RESOLUTION_ROWS:
        failures.append("Stage04 mixed-resolution row ids are not unique")
    if summary["harmful_overblock_avoid_rows"] != 0:
        failures.append("harmful overblock context casts AVOID pressure")
    expected_class_decisions = {
        "ambiguous_but_replay_measured": {"MIXED": 374},
        "harmful_overblock_context": {"MIXED": 32},
        "replay_resolvable_into_avoid_candidate": {"AVOID": 74},
        "replay_resolvable_into_follow_candidate": {"FOLLOW": 86},
        "useful_avoid_context": {"AVOID": 452},
    }
    if summary["mixed_resolution_class_decision_counts"] != expected_class_decisions:
        failures.append(
            "Stage04 class decision counts mismatch "
            f"{summary['mixed_resolution_class_decision_counts']}"
        )
    for row in rows:
        for field in (
            "live_effect",
            "broker_operation",
            "paid_api_or_vendor_call",
            "runtime_trading_or_live_broker_effect",
            "production_change_allowed_by_this_row",
        ):
            if row.get(field) is not False:
                failures.append(f"{row.get('review_row_id')} has unsafe flag {field}")
        if row.get("requires_owner_review_before_runtime_effect") is not True:
            failures.append(f"{row.get('review_row_id')} lacks owner activation gate")
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        if row.get("runtime_candidate_use_permitted") and not stage02.has_required_anchors(scope):
            failures.append(f"{row.get('review_row_id')} is actionable without anchors")
        if row.get("mixed_resolution_class") == "harmful_overblock_context":
            if row.get("computed_decision") != "MIXED":
                failures.append(f"{row.get('review_row_id')} harmful overblock is not MIXED")
            if row.get("runtime_candidate_use_permitted"):
                failures.append(f"{row.get('review_row_id')} harmful overblock is actionable")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = "STAGE_05_PROP_SAFE_SELECTOR" if complete else "STAGE_04_MIXED_RESOLUTION"
    state["stage_status_table"]["STAGE_04_MIXED_RESOLUTION"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_05_PROP_SAFE_SELECTOR"] = "in_progress"
        state["active_invariant"] = "build_prop_safe_selector_and_trade_throttle"
        state["first_incomplete_invariant"] = "STAGE_05_PROP_SAFE_SELECTOR"
        state["exact_next_action"] = (
            "Build and test the prop-safe selector/throttle layer using the replay "
            "prop-risk failure metrics and implemented route decisions."
        )
    else:
        state["active_invariant"] = "resolve_mixed_decision_surface_groups"
        state["first_incomplete_invariant"] = "STAGE_04_MIXED_RESOLUTION"
        state["exact_next_action"] = (
            "Run Stage04 verifier and focused runtime/config tests for mixed-resolution "
            "runtime rows, then mark Stage04 complete if all checks pass."
        )
    state["output_artifact_paths"]["mixed_resolution_ledger"] = rel(
        REPO_ROOT / MIXED_RESOLUTION_LEDGER_PATH
    )
    state["output_artifact_paths"]["stage04_mixed_resolution_summary"] = rel(
        REPO_ROOT / STAGE04_SUMMARY_PATH
    )
    state["output_artifact_paths"]["stage04_verification_result"] = rel(
        REPO_ROOT / STAGE04_VERIFICATION_RESULT_PATH
    )
    state["rows_groups_processed"]["stage04_mixed_resolution_runtime_row_instances"] = summary[
        "mixed_resolution_runtime_row_instances"
    ]
    state["rows_groups_processed"]["stage04_unique_mixed_resolution_row_ids"] = summary[
        "unique_mixed_resolution_row_ids"
    ]
    state["row_count_hash_coverage"]["stage04_mixed_resolution_summary"] = {
        "mixed_resolution_runtime_row_instances": summary[
            "mixed_resolution_runtime_row_instances"
        ],
        "unique_mixed_resolution_row_ids": summary["unique_mixed_resolution_row_ids"],
        "computed_decision_counts": summary["computed_decision_counts"],
        "mixed_resolution_class_counts": summary["mixed_resolution_class_counts"],
        "mixed_resolution_class_decision_counts": summary[
            "mixed_resolution_class_decision_counts"
        ],
        "system_surface_counts": summary["system_surface_counts"],
    }
    state["mixed_dispositions"] = {
        cls: {
            "stage": "STAGE_04_MIXED_RESOLUTION",
            "computed_decision_counts": counts,
            "artifact": summary["mixed_resolution_ledger_path"],
            "activation_gate": "gtos_vnext_runtime.apply_to_execution",
            "runtime_behavior": (
                "directional_follow_pressure"
                if counts.get("FOLLOW")
                else "directional_avoid_pressure"
                if counts.get("AVOID")
                else "non_override_context_guard"
            ),
        }
        for cls, counts in summary["mixed_resolution_class_decision_counts"].items()
    }
    state["verification_status"]["stage04_mixed_resolution_ledger_built"] = True
    state["verification_status"]["stage04_runtime_rows"] = summary[
        "mixed_resolution_runtime_row_instances"
    ]
    state["verification_status"]["stage04_unique_mixed_resolution_row_ids"] = summary[
        "unique_mixed_resolution_row_ids"
    ]
    state["verification_status"]["stage04_verifier_ok"] = complete
    state["remaining_executable_actions"] = (
        [
            "STAGE_05 prop-safe selector",
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
        if complete
        else [
            "STAGE_04 MIXED resolution",
            "STAGE_05 prop-safe selector",
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows, summary = build_mixed_resolution_rows()
    failures = verify_rows(rows, summary)
    write_jsonl(MIXED_RESOLUTION_LEDGER_PATH, rows)
    atomic_json_write(STAGE04_SUMMARY_PATH, summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage04_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_04_MIXED_RESOLUTION",
    }
    atomic_json_write(STAGE04_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
