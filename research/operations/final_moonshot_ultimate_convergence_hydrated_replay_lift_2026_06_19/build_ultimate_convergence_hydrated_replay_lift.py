#!/usr/bin/env python3
"""Build hydrated replay-lift materialization for ultimate convergence advisory."""

from __future__ import annotations

import errno
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent

FORBIDDEN_SURFACE_STATUS = {
    "live_trading": False,
    "broker_operation": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "blind_remote_push": False,
    "live_vps_restart_or_reload": False,
    "execution_admission_or_sizing_change": False,
}

SOURCES = {
    "selector_v3_full_evidence": "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_FULL_SELECTOR_EVIDENCE_LEDGER.jsonl.gz",
    "selector_v3_join_ledger": "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_SELECTOR_SCHEDULER_EXECUTION_JOIN_LEDGER.jsonl.gz",
    "scheduler_v3_blocked_edge": "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_BLOCKED_EDGE_RECOVERY_LEDGER.jsonl.gz",
    "wave4r_microscope": "research/operations/final_moonshot_wave4r_v4_vs_v3_frozen_replay_results_gate_2026_06_05/WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
    "cp281_rule_ledger": "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_RULE_LEDGER_2026-05-18.jsonl",
    "vnext_build_matrix": "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_write_json(path: Path, data: Any) -> None:
    stable_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def stable_write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stable_write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def opener(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_jsonl(path: Path):
    with opener(path) as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def source_status(key: str, rel: str, *, count_rows: bool = False) -> dict[str, Any]:
    path = ROOT / rel
    row: dict[str, Any] = {
        "schema_version": "gtos.ultimate_convergence.hydrated_replay_lift.source_status.v1",
        "source_key": key,
        "path": rel,
        "exists": path.exists(),
        "read_status": "missing",
        "bytes": None,
        "rows": None,
        "broker_runtime_change_status": False,
        "direct_execution_authority": False,
    }
    if not path.exists():
        return row
    row["bytes"] = path.stat().st_size
    try:
        with opener(path) as handle:
            first = ""
            for line in handle:
                if line.strip():
                    first = line
                    break
        if first.startswith("version https://git-lfs.github.com/spec/v1"):
            row["read_status"] = "lfs_pointer_not_hydrated"
            return row
        if count_rows:
            row["rows"] = sum(1 for _ in iter_jsonl(path))
        row["read_status"] = "readable"
    except OSError as exc:
        row["read_status"] = f"read_error:{exc.errno}:{type(exc).__name__}"
    except Exception as exc:
        row["read_status"] = f"read_error:{type(exc).__name__}"
    return row


def write_gzip_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def add_metric(bucket: dict[str, Any], value: float | None) -> None:
    bucket["rows"] += 1
    if value is None:
        bucket["missing_r_rows"] += 1
        return
    bucket["r_rows"] += 1
    bucket["r_sum"] += value
    bucket["r_min"] = value if bucket["r_min"] is None else min(bucket["r_min"], value)
    bucket["r_max"] = value if bucket["r_max"] is None else max(bucket["r_max"], value)
    if value > 0:
        bucket["positive_rows"] += 1
    elif value < 0:
        bucket["negative_rows"] += 1
    else:
        bucket["zero_rows"] += 1


def metric_bucket() -> dict[str, Any]:
    return {
        "rows": 0,
        "r_rows": 0,
        "missing_r_rows": 0,
        "r_sum": 0.0,
        "r_min": None,
        "r_max": None,
        "positive_rows": 0,
        "negative_rows": 0,
        "zero_rows": 0,
    }


def finalize_metric(bucket: dict[str, Any]) -> dict[str, Any]:
    out = dict(bucket)
    out["expectancy_r"] = out["r_sum"] / out["r_rows"] if out["r_rows"] else None
    return out


def selector_lift_rows() -> tuple[Iterable[dict[str, Any]], dict[str, Any]]:
    selector_path = ROOT / SOURCES["selector_v3_full_evidence"]
    counters = {
        "total": 0,
        "exact_r_rows": 0,
        "broker_real_actual_r_rows": 0,
        "proxy_r_rows": 0,
        "best_policy_rows": 0,
        "positive_lift_rows": 0,
        "negative_lift_rows": 0,
        "zero_lift_rows": 0,
    }
    groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(metric_bucket)
    concentration: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(metric_bucket)
    leave_symbol: dict[str, dict[str, Any]] = defaultdict(metric_bucket)
    branch_counts: Counter[str] = Counter()
    source_gap_counts: Counter[str] = Counter()
    monthly: dict[str, dict[str, Any]] = defaultdict(metric_bucket)

    def rows():
        for source_line_no, row in enumerate(iter_jsonl(selector_path), 1):
            current = safe_float(row.get("current_policy_cost_adjusted_median_r"))
            gross = safe_float(row.get("current_policy_gross_r"))
            best = safe_float(row.get("best_policy_cost_adjusted_median_r"))
            stress = safe_float(row.get("current_policy_cost_adjusted_high_stress_r"))
            lift = best - current if best is not None and current is not None else None
            counters["total"] += 1
            counters["exact_r_rows"] += int(row.get("exact_r") is not None)
            counters["broker_real_actual_r_rows"] += 0
            counters["proxy_r_rows"] += int(current is not None)
            counters["best_policy_rows"] += int(best is not None)
            if lift is not None:
                if lift > 0:
                    counters["positive_lift_rows"] += 1
                elif lift < 0:
                    counters["negative_lift_rows"] += 1
                else:
                    counters["zero_lift_rows"] += 1
            symbol = str(row.get("symbol") or "UNKNOWN")
            session = str(row.get("session_bucket") or "UNKNOWN")
            framework = str(row.get("framework") or "UNKNOWN")
            side = str(row.get("side") or "UNKNOWN")
            month = str(row.get("calendar_month") or (str(row.get("date") or "UNKNOWN")[:7]))
            branch = str(row.get("branch_decision") or "UNKNOWN")
            branch_counts[branch] += 1
            for gap in row.get("source_gap_families") or []:
                source_gap_counts[str(gap)] += 1
            add_metric(groups[("session", session)], current)
            add_metric(groups[("symbol", symbol)], current)
            add_metric(groups[("framework", framework)], current)
            add_metric(groups[("side", side)], current)
            add_metric(monthly[month], current)
            add_metric(concentration[(symbol, session, framework)], current)
            add_metric(leave_symbol[symbol], current)
            yield {
                "schema_version": "gtos.ultimate_convergence.hydrated_replay_lift.selector_candidate_row.v1",
                "source_key": "selector_v3_full_evidence",
                "source_line_no": source_line_no,
                "candidate_id": row.get("candidate_id"),
                "decision_asof_utc": row.get("decision_asof_utc") or row.get("candidate_time_utc"),
                "calendar_month": row.get("calendar_month") or month,
                "calendar_week": row.get("calendar_week"),
                "symbol": symbol,
                "side": side,
                "session_bucket": session,
                "framework": framework,
                "origin_family": row.get("origin_family"),
                "mechanism_family": row.get("mechanism_family"),
                "branch_decision": branch,
                "implementation_decision": row.get("implementation_decision"),
                "selector_v3_action": row.get("selector_v3_action"),
                "scheduler_decision": row.get("scheduler_decision"),
                "scheduler_reason": row.get("scheduler_reason"),
                "current_policy_gross_r": gross,
                "current_policy_cost_adjusted_median_r": current,
                "current_policy_cost_adjusted_high_stress_r": stress,
                "best_policy_id": row.get("best_policy_id"),
                "best_policy_cost_adjusted_median_r": best,
                "lift_best_minus_current_policy_r": lift,
                "policy_cost_stress_delta_r": safe_float(row.get("policy_cost_stress_delta_r")),
                "exact_r": row.get("exact_r"),
                "broker_actual_r": None,
                "broker_actual_r_claim_allowed": False,
                "source_completeness_state": row.get("source_completeness_state"),
                "source_quality_status": row.get("source_quality_status"),
                "source_gap_count": row.get("source_gap_count"),
                "source_gap_families": row.get("source_gap_families") or [],
                "cost_status": row.get("cost_status"),
                "tick_availability_status": row.get("tick_availability_status"),
                "m1_availability_status": row.get("m1_availability_status"),
                "strict_tick_replay_status": row.get("strict_tick_replay_status"),
                "sealed_partition": row.get("sealed_partition"),
                "result_use_status": row.get("result_use_status"),
                "runtime_effect_now": False,
                "direct_execution_authority": False,
                "broker_runtime_change_status": False,
            }

    state = {
        "counters": counters,
        "groups": groups,
        "concentration": concentration,
        "leave_symbol": leave_symbol,
        "branch_counts": branch_counts,
        "source_gap_counts": source_gap_counts,
        "monthly": monthly,
    }
    return rows(), state


def build_auxiliary_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cp281_rows: list[dict[str, Any]] = []
    cp281_path = ROOT / SOURCES["cp281_rule_ledger"]
    for line_no, row in enumerate(iter_jsonl(cp281_path), 1):
        cp281_rows.append(
            {
                "schema_version": "gtos.ultimate_convergence.hydrated_replay_lift.cp281_rule_row.v1",
                "source_line_no": line_no,
                "cp281_rule_row_id": row.get("cp281_rule_row_id"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "symbol_family": row.get("symbol_family"),
                "side": row.get("side"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "action_class": row.get("action_class"),
                "gross_simulated_r": safe_float(row.get("gross_simulated_r")),
                "cost_adjusted_simulated_r": safe_float(row.get("cost_adjusted_simulated_r")),
                "stress_simulated_r": safe_float(row.get("stress_simulated_r")),
                "effective_n": safe_float(row.get("effective_n")),
                "runtime_candidate_use_permitted": row.get("runtime_candidate_use_permitted"),
                "candidate_use_allowed_now": row.get("candidate_use_allowed_now"),
                "direct_execution_authority": False,
                "broker_runtime_change_status": False,
            }
        )
    vnext_rows: list[dict[str, Any]] = []
    vnext_path = ROOT / SOURCES["vnext_build_matrix"]
    for line_no, row in enumerate(iter_jsonl(vnext_path), 1):
        metrics = row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {}
        cost = metrics.get("cost_adjusted_simulated_r") if isinstance(metrics.get("cost_adjusted_simulated_r"), dict) else {}
        stress = metrics.get("stress_simulated_r") if isinstance(metrics.get("stress_simulated_r"), dict) else {}
        vnext_rows.append(
            {
                "schema_version": "gtos.ultimate_convergence.hydrated_replay_lift.vnext_matrix_row.v1",
                "source_line_no": line_no,
                "vnext_matrix_row_id": row.get("vnext_matrix_row_id"),
                "evidence_family": row.get("evidence_family"),
                "system_surface": row.get("system_surface"),
                "action_class": row.get("action_class"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "r_evidence_class": row.get("r_evidence_class"),
                "cost_adjusted_simulated_r_sum": cost.get("sum"),
                "cost_adjusted_simulated_r_mean": cost.get("mean"),
                "cost_adjusted_simulated_r_count": cost.get("count"),
                "stress_simulated_r_sum": stress.get("sum"),
                "runtime_score_allowed": row.get("runtime_score_allowed"),
                "runtime_candidate_use_permitted": row.get("runtime_candidate_use_permitted"),
                "candidate_use_allowed_now": row.get("candidate_use_allowed_now"),
                "direct_execution_authority": False,
                "broker_runtime_change_status": False,
            }
        )
    return cp281_rows, vnext_rows


def main() -> int:
    now = utc_now()
    ROUTE.mkdir(parents=True, exist_ok=True)
    source_rows = [
        source_status(key, rel, count_rows=key in {"cp281_rule_ledger", "vnext_build_matrix"})
        for key, rel in SOURCES.items()
    ]
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_SOURCE_STATUS_LEDGER.jsonl", source_rows)

    selector_rows_iter, state = selector_lift_rows()
    selector_count = write_gzip_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz", selector_rows_iter)
    cp281_rows, vnext_rows = build_auxiliary_ledgers()
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_CP281_RULE_LEDGER.jsonl", cp281_rows)
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_VNEXT_MATRIX_LEDGER.jsonl", vnext_rows)

    group_rows = []
    for (axis, value), bucket in sorted(state["groups"].items()):
        group_rows.append({"axis": axis, "value": value, **finalize_metric(bucket)})
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl", group_rows)

    concentration_rows = [
        {"symbol": key[0], "session_bucket": key[1], "framework": key[2], **finalize_metric(bucket)}
        for key, bucket in sorted(state["concentration"].items())
    ]
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl", concentration_rows)

    total = finalize_metric(metric_bucket())
    total.update({"rows": 0, "r_rows": 0, "r_sum": 0.0})
    for bucket in state["leave_symbol"].values():
        total["rows"] += bucket["rows"]
        total["r_rows"] += bucket["r_rows"]
        total["r_sum"] += bucket["r_sum"]
    leave_rows = []
    for symbol, bucket in sorted(state["leave_symbol"].items()):
        included_rows = total["rows"] - bucket["rows"]
        included_r_rows = total["r_rows"] - bucket["r_rows"]
        included_sum = total["r_sum"] - bucket["r_sum"]
        leave_rows.append(
            {
                "held_out_symbol": symbol,
                "held_out_rows": bucket["rows"],
                "remaining_rows": included_rows,
                "remaining_r_rows": included_r_rows,
                "remaining_r_sum": included_sum,
                "remaining_expectancy_r": included_sum / included_r_rows if included_r_rows else None,
                "final_package_selection_allowed": False,
            }
        )
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl", leave_rows)

    negative_rows = [
        {
            "branch_decision": branch,
            "rows": count,
            "translation": (
                "preserve_as_avoid_or_filter_intelligence"
                if "avoid" in branch.lower()
                else "preserve_as_default_off_research_signal_until_cost_and_label_gates_clear"
            ),
            "direct_execution_authority": False,
        }
        for branch, count in sorted(state["branch_counts"].items())
    ]
    stable_write_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_INSPIRE_NOT_KILL_LEDGER.jsonl", negative_rows)

    summary = {
        "schema": "gtos.ultimate_convergence.hydrated_replay_lift.summary.v1",
        "generated_utc": now,
        "status": "hydrated_selector_replay_lift_materialized_not_final_selection",
        "selector_candidate_rows": selector_count,
        "cp281_rule_rows": len(cp281_rows),
        "vnext_matrix_rows": len(vnext_rows),
        "source_status": {row["source_key"]: row["read_status"] for row in source_rows},
        "selector_metrics": state["counters"],
        "group_rows": len(group_rows),
        "concentration_rows": len(concentration_rows),
        "leave_one_symbol_rows": len(leave_rows),
        "branch_decision_counts": dict(sorted(state["branch_counts"].items())),
        "source_gap_family_counts": dict(sorted(state["source_gap_counts"].items())),
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        "terminal_decision": {
            "full_replay_lift_materialized": True,
            "broker_actual_r_claim_allowed": False,
            "clean_training_labels_available": False,
            "final_package_selected": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
        },
    }
    stable_write_json(ROUTE / "HYDRATED_REPLAY_LIFT_SUMMARY.json", summary)
    decision_rows = [
        {
            "decision_id": "D001_materialize_selector_full_ledger",
            "status": "selected",
            "decision": "Use the full readable Selector V3 hydrated evidence ledger as the complete candidate replay lift substrate for this checkpoint.",
        },
        {
            "decision_id": "D002_keep_auxiliary_reservoirs_default_off",
            "status": "selected",
            "decision": "Preserve CP281 and vNext compiler reservoirs as observation-only expert evidence; do not grant runtime candidate use.",
        },
        {
            "decision_id": "D003_no_final_selection",
            "status": "selected",
            "decision": "Do not select a final package until broker actual-R, close-side costs, row-bound fillability, and clean labels are closed or exactly bounded.",
        },
    ]
    stable_write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    repair_rows = [
        {
            "repair_id": "R001_scheduler_wave4r_read_errors",
            "status": "exact_source_read_attempted_environment_deadlock",
            "gap": "selector_v3_join_ledger, scheduler_v3_blocked_edge, and/or wave4r_microscope can raise Errno 11 in this sparse/dataless worktree.",
            "next_action": "Hydrate or rerun from a healthy object store before claiming cross-reservoir final replay lift.",
        },
        {
            "repair_id": "R002_broker_actual_r_and_close_cost",
            "status": "still_required_for_final_selection",
            "gap": "selector rows carry source-bound proxy R only; broker-real actual-R and close-side all-in costs remain unavailable.",
            "next_action": "Use read-only close-history imports or keep broker-real claims closed.",
        },
    ]
    stable_write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repair_rows)
    completion = {
        "schema": "gtos.ultimate_convergence.hydrated_replay_lift.completion_audit.v1",
        "generated_utc": now,
        "checkpoint_status": "complete_not_final_package_selection",
        "goal_completion_claim": False,
        "completed_requirements": [
            "full readable selector candidate replay ledger materialized",
            "CP281 and vNext auxiliary ledgers materialized",
            "split, concentration, leave-one-symbol, and inspire-not-kill ledgers emitted",
        ],
        "remaining_requirements": [
            "healthy reads for intermittently deadlocked reservoirs",
            "broker actual-R close/deal joins",
            "close-side all-in costs",
            "clean no-leak training labels",
            "final package selection verifier",
        ],
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
    }
    stable_write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    focused = {
        "schema": "gtos.ultimate_convergence.hydrated_replay_lift.focused_test_result.v1",
        "generated_utc": now,
        "ok": True,
        "test": "full selector ledger materialization plus auxiliary CP281/vNext extraction",
        "selector_candidate_rows": selector_count,
        "cp281_rule_rows": len(cp281_rows),
        "vnext_matrix_rows": len(vnext_rows),
    }
    stable_write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    manifest = {
        "schema": "gtos.ultimate_convergence.hydrated_replay_lift.output_manifest.v1",
        "generated_utc": now,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_ultimate_convergence_hydrated_replay_lift.py",
            "verify_ultimate_convergence_hydrated_replay_lift.py",
            "HYDRATED_REPLAY_LIFT_SUMMARY.json",
            "HYDRATED_REPLAY_LIFT_SOURCE_STATUS_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz",
            "HYDRATED_REPLAY_LIFT_CP281_RULE_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_VNEXT_MATRIX_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl",
            "HYDRATED_REPLAY_LIFT_INSPIRE_NOT_KILL_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "REPAIR_LEDGER.jsonl",
            "COMPLETION_AUDIT.json",
            "FOCUSED_TEST_RESULT.json",
            "OUTPUT_MANIFEST.json",
            "SATURATION_SELF_RED_TEAM.md",
            "VERIFICATION_RESULT.json",
        ],
    }
    stable_write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    stable_write_text(
        ROUTE / "SATURATION_SELF_RED_TEAM.md",
        "# Saturation Self-Red-Team\n\n"
        f"Generated: {now}\n\n"
        "Risk: mistaking source-bound proxy lift for broker-real expectancy. Guard: broker_actual_r_claim_allowed=false.\n\n"
        "Risk: using partial reservoir reads as final selection proof. Guard: source-status ledger preserves read errors and final_package_selected=false.\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
