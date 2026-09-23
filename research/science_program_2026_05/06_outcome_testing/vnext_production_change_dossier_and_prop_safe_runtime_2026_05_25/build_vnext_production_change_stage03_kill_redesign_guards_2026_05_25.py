from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage02_runtime_promotions_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage02", MODULE_PATH)
stage02 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage02)

stage01 = stage02.stage01
REPO_ROOT = stage02.REPO_ROOT
ROUTE_ID = stage02.ROUTE_ID
ROUTE_DIR = stage02.ROUTE_DIR
STATE_PATH = stage02.STATE_PATH
DECISION_SURFACE_LEDGER_PATH = stage02.DECISION_SURFACE_LEDGER_PATH
KILL_REDESIGN_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_KILL_REDESIGN_LEDGER_2026-05-25.jsonl"
)
STAGE03_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE03_KILL_REDESIGN_GUARD_SUMMARY_2026-05-25.json"
)
STAGE03_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE03_VERIFICATION_RESULT_2026-05-25.json"
)

KILL_DECISION = "KILL_OR_REDESIGN_BEFORE_USE"
GUARD_ONLY_DECISION = "KEEP_SHADOW_OR_GUARD_ONLY"
STAGE03_DECISIONS = {KILL_DECISION, GUARD_ONLY_DECISION}
EVIDENCE_FAMILY = "gtos_vnext_production_change_kill_redesign_guards"
SOURCE_NAME = "vnext_production_change_stage03_kill_redesign_guards"
EXPECTED_UNIQUE_STAGE03_DECISION_MAP_IDS = 1130


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage02.rel(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage02.atomic_json_write(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stage02.write_jsonl(path, rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_stage01_group_lookup() -> dict[tuple[str, ...], dict[str, Any]]:
    return stage02.load_stage01_group_lookup()


def stage01_group_for_row(
    row: dict[str, Any],
    group_lookup: dict[tuple[str, ...], dict[str, Any]],
) -> dict[str, Any] | None:
    return stage02.stage01_group_for_row(row, group_lookup)


def source_total(row: dict[str, Any]) -> tuple[float | None, float]:
    metrics = row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {}
    count = stage02.metric_count(row, metrics)
    return stage02.metric_total(metrics, count), count


def guard_decision(row: dict[str, Any], total: float | None) -> str:
    implementation_decision = str(row.get("implementation_decision") or "")
    action_class = str(row.get("action_class") or "").casefold()
    component = stage02.original_source_component(row)
    baseline = str(row.get("baseline_decision") or "").upper()
    if implementation_decision == GUARD_ONLY_DECISION:
        return "MIXED"
    if component == "unknown_component" or "unknown_action_class" in action_class:
        return "MIXED"
    if "stop_first" in action_class:
        return "AVOID"
    if "avoid" in action_class or "filter" in action_class or baseline == "AVOID":
        return "AVOID"
    if total is not None and total < 0:
        return "AVOID"
    return "MIXED"


def guard_source_component(row: dict[str, Any], decision: str) -> str:
    component = stage02.original_source_component(row)
    action_class = str(row.get("action_class") or "").casefold()
    if "stop_first" in action_class:
        return "nofill_far_miss_avoid"
    if component == "unknown_component":
        return "vnext_production_change_non_override_guard"
    if component == "nofill_pending_lifecycle" and decision == "AVOID":
        return "nofill_far_miss_avoid"
    return component


def guard_route_family(row: dict[str, Any], source_component: str) -> str:
    if source_component.startswith("nofill_"):
        return "nofill_mechanical"
    if source_component.startswith("rejected_candidate") or source_component.startswith("l2_"):
        return "numeric_router"
    return stage02.generated_route_family(row, source_component)


def guard_proxy_class(row: dict[str, Any], decision: str, total: float | None, count: float) -> str:
    action_class = str(row.get("action_class") or "").casefold()
    if decision == "AVOID" and ("stop_first" in action_class or total is None):
        return "STRONG_NEGATIVE_PROXY_R"
    if decision == "MIXED":
        return "GUARD_ONLY_PROXY_R"
    return stage02.proxy_class(total, count)


def guard_target_stop_class(row: dict[str, Any], decision: str, total: float | None) -> str:
    action_class = str(row.get("action_class") or "").casefold()
    if "stop_first" in action_class:
        return "STOP_FIRST_PROXY_DOMINANT"
    if decision == "MIXED":
        return "GUARD_ONLY_TARGET_STOP_CONTEXT"
    return stage02.target_stop_order_class(row, total)


def review_action(decision: str) -> str:
    if decision == "AVOID":
        return "DEFAULT_OFF_AVOID_FILTER_REVIEW"
    return "DEFAULT_OFF_MIXED_SOURCE_REPAIR_GUARD"


def implementation_action(row: dict[str, Any], decision: str) -> str:
    source_decision = str(row.get("implementation_decision") or "")
    if source_decision == GUARD_ONLY_DECISION:
        return "ENFORCE_GUARD_ONLY_NO_DIRECTIONAL_PRESSURE"
    if decision == "AVOID":
        return "ENFORCE_KILL_REDESIGN_AVOID_OR_NOFILL_GUARD"
    return "ENFORCE_KILL_REDESIGN_NON_OVERRIDE_GUARD"


def action_family(decision: str) -> str:
    return (
        "production_change_kill_avoid_guard"
        if decision == "AVOID"
        else "production_change_non_override_guard"
    )


def guard_runtime_row(
    *,
    row: dict[str, Any],
    meta: dict[str, Any],
    instance_index: int,
    duplicate_index: int,
    group: dict[str, Any] | None,
) -> dict[str, Any]:
    total, count = source_total(row)
    decision = guard_decision(row, total)
    source_component = guard_source_component(row, decision)
    route_family = guard_route_family(row, source_component)
    proxy_r_class = guard_proxy_class(row, decision, total, count)
    target_stop_class = guard_target_stop_class(row, decision, total)
    scope_candidate = stage02.build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=decision == "AVOID",
    )
    actionable = decision == "AVOID" and stage02.has_required_anchors(scope_candidate)
    if not actionable:
        decision = "MIXED"
        proxy_r_class = guard_proxy_class(row, decision, total, count)
        target_stop_class = guard_target_stop_class(row, decision, total)
    event_scope = stage02.build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=actionable,
    )
    decision_map_row_id = str(row.get("decision_map_row_id") or f"missing-{instance_index}")
    review_row_id = (
        f"prodchg_stage03_{instance_index:06d}_"
        f"{stage02.stable_hash([decision_map_row_id, duplicate_index])}"
    )
    runtime_surface = (
        group["group_key"]["runtime_surface"] if group else stage01.target_for_row(row)["runtime_surface"]
    )
    return {
        "schema_version": "vnext_production_change_kill_redesign_guard_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION",
        "row_type": "gtos_vnext_production_change_kill_redesign_guard_row",
        "review_row_id": review_row_id,
        "row_key": review_row_id,
        "source_row_id": decision_map_row_id,
        "source_row_instance_index": duplicate_index,
        "source_row_fingerprint": stage02.stable_hash(row),
        "stage01_group_id": group.get("group_id") if group else None,
        "event_scope": event_scope,
        "scope_key": "|".join(f"{key}={value}" for key, value in sorted(event_scope.items())),
        "review_action": review_action(decision),
        "computed_decision": decision,
        "implementation_action": implementation_action(row, decision),
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": runtime_surface,
        "source_role": "production_change_kill_redesign_guard",
        "system_surface": runtime_surface,
        "source_component": source_component,
        "original_source_component": stage02.original_source_component(row),
        "action_family": action_family(decision),
        "action_class": str(row.get("action_class") or "unknown_action_class"),
        "original_action_class": str(row.get("action_class") or "unknown_action_class"),
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
        "r_evidence_class": "STAGE06_KILL_REDESIGN_GUARD_PROXY_R",
        "r_metric_traces": stage02.r_metric_traces(row),
        "source_path": stage02.FINAL_DECISION_MAP_REL,
        "source_artifact": stage02.FINAL_DECISION_MAP_REL,
        "source_chunk_path": meta.get("chunk_path"),
        "source_chunk_sha256": meta.get("sha256"),
        "source_final_decision": row.get("implementation_decision"),
        "baseline_decision": row.get("baseline_decision"),
        "source_surface": row.get("surface"),
        "source_runtime_mode": row.get("runtime_mode"),
        "source_evidence_family": row.get("evidence_family"),
        "source_candidate_count": row.get("candidate_count"),
        "source_counterfactual_change_count": row.get("counterfactual_change_count"),
        "source_r_metrics": row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {},
        "runtime_candidate_use_permitted": actionable,
        "guard_only_no_directional_pressure": decision == "MIXED",
        "kill_redesign_avoid_guard": decision == "AVOID",
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


def build_guard_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    group_lookup = load_stage01_group_lookup()
    duplicate_counter: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    missing_group_ids: list[str] = []
    for meta, row in stage01.final_decision_rows():
        if row.get("implementation_decision") not in STAGE03_DECISIONS:
            continue
        decision_map_row_id = str(row.get("decision_map_row_id") or "")
        duplicate_counter[decision_map_row_id] += 1
        group = stage01_group_for_row(row, group_lookup)
        if group is None and decision_map_row_id:
            missing_group_ids.append(decision_map_row_id)
        rows.append(
            guard_runtime_row(
                row=row,
                meta=meta,
                instance_index=len(rows) + 1,
                duplicate_index=duplicate_counter[decision_map_row_id],
                group=group,
            )
        )
    summary = summarize_rows(rows, missing_group_ids)
    return rows, summary


def summarize_rows(rows: list[dict[str, Any]], missing_group_source_ids: list[str]) -> dict[str, Any]:
    source_id_counts = Counter(str(row.get("source_row_id") or "") for row in rows)
    decision_counts = Counter(str(row.get("computed_decision") or "") for row in rows)
    source_final_decision_counts = Counter(str(row.get("source_final_decision") or "") for row in rows)
    surface_counts = Counter(str(row.get("system_surface") or "") for row in rows)
    source_component_counts = Counter(str(row.get("source_component") or "") for row in rows)
    route_family_counts = Counter(str(row.get("route_family") or "") for row in rows)
    actionable_rows = [row for row in rows if row.get("runtime_candidate_use_permitted")]
    unanchored_rows = [
        row for row in rows if not stage02.has_required_anchors(row.get("event_scope") or {})
    ]
    return {
        "schema_version": "vnext_production_change_stage03_kill_redesign_guard_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "kill_redesign_ledger_path": rel(REPO_ROOT / KILL_REDESIGN_LEDGER_PATH),
        "expected_unique_stage03_decision_map_ids": EXPECTED_UNIQUE_STAGE03_DECISION_MAP_IDS,
        "stage03_runtime_row_instances": len(rows),
        "unique_stage03_decision_map_row_ids": len(source_id_counts),
        "duplicate_stage03_decision_map_row_id_count": sum(
            1 for _row_id, count in source_id_counts.items() if count > 1
        ),
        "duplicate_stage03_decision_map_row_id_extra_instances": sum(
            count - 1 for count in source_id_counts.values() if count > 1
        ),
        "runtime_candidate_use_permitted_rows": len(actionable_rows),
        "non_override_guard_rows": len(rows) - len(actionable_rows),
        "unanchored_guard_rows": len(unanchored_rows),
        "computed_decision_counts": dict(sorted(decision_counts.items())),
        "source_final_decision_counts": dict(sorted(source_final_decision_counts.items())),
        "system_surface_counts": dict(sorted(surface_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "route_family_counts": dict(sorted(route_family_counts.items())),
        "missing_stage01_group_source_ids": sorted(set(missing_group_source_ids)),
        "artifact_config_path": rel(REPO_ROOT / KILL_REDESIGN_LEDGER_PATH),
        "artifact_evidence_family": EVIDENCE_FAMILY,
    }


def verify_rows(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if summary["unique_stage03_decision_map_row_ids"] != EXPECTED_UNIQUE_STAGE03_DECISION_MAP_IDS:
        failures.append(
            "unique Stage03 decision-map ids expected "
            f"{EXPECTED_UNIQUE_STAGE03_DECISION_MAP_IDS} got "
            f"{summary['unique_stage03_decision_map_row_ids']}"
        )
    if summary["source_final_decision_counts"] != {
        GUARD_ONLY_DECISION: 272,
        KILL_DECISION: 858,
    }:
        failures.append(
            f"Stage03 source decision counts mismatch {summary['source_final_decision_counts']}"
        )
    if not rows:
        failures.append("no Stage03 kill/redesign guard rows generated")
    if summary["missing_stage01_group_source_ids"]:
        failures.append(
            "some Stage03 rows did not map back to a Stage01 group: "
            f"{summary['missing_stage01_group_source_ids'][:10]}"
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
                failures.append(f"{row.get('review_row_id')} has unsafe flag {field}={row.get(field)}")
        if row.get("requires_owner_review_before_runtime_effect") is not True:
            failures.append(f"{row.get('review_row_id')} does not preserve owner activation gate")
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        if row.get("runtime_candidate_use_permitted") and not stage02.has_required_anchors(scope):
            failures.append(f"{row.get('review_row_id')} is actionable without required anchors")
        if row.get("source_final_decision") == GUARD_ONLY_DECISION and row.get("computed_decision") != "MIXED":
            failures.append(f"{row.get('review_row_id')} guard-only row casts directional pressure")
        if row.get("computed_decision") == "FOLLOW":
            failures.append(f"{row.get('review_row_id')} Stage03 row produced FOLLOW")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = (
        "STAGE_04_MIXED_RESOLUTION" if complete else "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"
    )
    state["stage_status_table"]["STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_04_MIXED_RESOLUTION"] = "in_progress"
        state["active_invariant"] = "resolve_mixed_decision_surface_groups"
        state["first_incomplete_invariant"] = "STAGE_04_MIXED_RESOLUTION"
        state["exact_next_action"] = (
            "Resolve MIXED decision-surface groups using replay/source-repair evidence "
            "into promote, avoid, guard-only, source-repair, or shadow-only runtime dispositions."
        )
    else:
        state["active_invariant"] = "implement_kill_redesign_and_guard_only_decision_surface_groups"
        state["first_incomplete_invariant"] = "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"
        state["exact_next_action"] = (
            "Run Stage03 verifier and focused runtime/config tests for kill/redesign "
            "and guard-only runtime rows, then mark Stage03 complete if all checks pass."
        )
    state["output_artifact_paths"]["kill_redesign_ledger"] = rel(
        REPO_ROOT / KILL_REDESIGN_LEDGER_PATH
    )
    state["output_artifact_paths"]["stage03_kill_redesign_guard_summary"] = rel(
        REPO_ROOT / STAGE03_SUMMARY_PATH
    )
    state["output_artifact_paths"]["stage03_verification_result"] = rel(
        REPO_ROOT / STAGE03_VERIFICATION_RESULT_PATH
    )
    state["rows_groups_processed"]["stage03_runtime_row_instances"] = summary[
        "stage03_runtime_row_instances"
    ]
    state["rows_groups_processed"]["stage03_unique_decision_map_row_ids"] = summary[
        "unique_stage03_decision_map_row_ids"
    ]
    state["row_count_hash_coverage"]["stage03_kill_redesign_guard_summary"] = {
        "stage03_runtime_row_instances": summary["stage03_runtime_row_instances"],
        "unique_stage03_decision_map_row_ids": summary[
            "unique_stage03_decision_map_row_ids"
        ],
        "computed_decision_counts": summary["computed_decision_counts"],
        "source_final_decision_counts": summary["source_final_decision_counts"],
        "system_surface_counts": summary["system_surface_counts"],
        "source_component_counts": summary["source_component_counts"],
    }
    state["killed_redesigned_surfaces"] = [
        {
            "stage": "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION",
            "surface": surface,
            "runtime_row_count": count,
            "artifact": summary["kill_redesign_ledger_path"],
            "activation_gate": "gtos_vnext_runtime.apply_to_execution",
        }
        for surface, count in summary["system_surface_counts"].items()
    ]
    state["guard_only_surfaces"] = [
        {
            "stage": "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION",
            "source_final_decision": GUARD_ONLY_DECISION,
            "runtime_row_count": summary["source_final_decision_counts"].get(
                GUARD_ONLY_DECISION,
                0,
            ),
            "artifact": summary["kill_redesign_ledger_path"],
            "runtime_behavior": "MIXED non-override guard",
        }
    ]
    state["verification_status"]["stage03_kill_redesign_ledger_built"] = True
    state["verification_status"]["stage03_runtime_rows"] = summary[
        "stage03_runtime_row_instances"
    ]
    state["verification_status"]["stage03_unique_decision_map_row_ids"] = summary[
        "unique_stage03_decision_map_row_ids"
    ]
    state["verification_status"]["stage03_verifier_ok"] = complete
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows, summary = build_guard_rows()
    failures = verify_rows(rows, summary)
    write_jsonl(KILL_REDESIGN_LEDGER_PATH, rows)
    atomic_json_write(STAGE03_SUMMARY_PATH, summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage03_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION",
    }
    atomic_json_write(STAGE03_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
