#!/usr/bin/env python3
"""Build a no-top-N final-package synthesis checkpoint from current discovery evidence."""

from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]

HYDRATED_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19"
CANDIDATE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_convergence_candidate_level_match_materialization_2026_06_19"
SCHEDULER_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19"
WAVE_F_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19"
FINAL_SELECTION_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19"
SUCCESSOR_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19"
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def iter_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                yield json.loads(text)


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    (ROUTE / name).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def fnum(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if number == number else 0.0


def axis_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("framework") or "unknown_framework"),
        str(row.get("origin_family") or row.get("mechanism_family") or "unknown_origin_family"),
        str(row.get("symbol") or "ALL"),
        str(row.get("session_bucket") or "ALL"),
        str(row.get("side") or "ALL"),
    )


def new_axis() -> dict[str, Any]:
    return {
        "selector_rows": 0,
        "selector_positive_lift_rows": 0,
        "selector_zero_lift_rows": 0,
        "selector_lift_sum": 0.0,
        "selector_current_policy_r_sum": 0.0,
        "selector_best_policy_r_sum": 0.0,
        "selector_branch_decisions": Counter(),
        "selector_implementation_decisions": Counter(),
        "selector_source_gap_families": Counter(),
        "candidate_level_rows": 0,
        "candidate_level_source_bound_r_sum": 0.0,
        "candidate_level_known_proxy_r_rows": 0,
        "scheduler_rows": 0,
        "scheduler_result_r_sum": 0.0,
        "scheduler_missed_result_r_sum": 0.0,
        "scheduler_action_classes": Counter(),
        "scheduler_decisions": Counter(),
    }


def score_axis(key: tuple[str, str, str, str, str], stats: dict[str, Any]) -> dict[str, Any]:
    selector_rows = int(stats["selector_rows"])
    candidate_rows = int(stats["candidate_level_rows"])
    scheduler_rows = int(stats["scheduler_rows"])
    selector_lift = round(float(stats["selector_lift_sum"]), 9)
    candidate_r = round(float(stats["candidate_level_source_bound_r_sum"]), 9)
    scheduler_r = round(float(stats["scheduler_result_r_sum"]), 9)
    total_signal = round(selector_lift + candidate_r + scheduler_r, 9)
    branch_counts = dict(stats["selector_branch_decisions"])
    action_counts = dict(stats["scheduler_action_classes"])
    source_gaps = dict(stats["selector_source_gap_families"].most_common())
    adverse_scheduler_rows = (
        action_counts.get("conflict_net", 0)
        + action_counts.get("reject", 0)
        + action_counts.get("require_source", 0)
    )
    recoverable_scheduler_rows = (
        action_counts.get("queue", 0)
        + action_counts.get("delay", 0)
        + action_counts.get("admit_reduced_risk", 0)
        + action_counts.get("replace", 0)
    )
    positive_sources = sum(1 for value in [selector_lift, candidate_r, scheduler_r] if value > 0)
    negative_sources = sum(1 for value in [selector_lift, candidate_r, scheduler_r] if value < 0)
    promote_like = branch_counts.get("promote_default_off", 0) + branch_counts.get("merge", 0)
    redesign_like = branch_counts.get("redesign", 0) + branch_counts.get("capture", 0) + branch_counts.get("source_required_before_selector_decision", 0)
    avoid_like = branch_counts.get("avoid", 0) + branch_counts.get("kill_current_unsupported_claim_preserve_mechanism", 0)

    if total_signal <= 0 or negative_sources > positive_sources or avoid_like > promote_like + redesign_like:
        disposition = "avoid_or_preserve_as_failure_feature"
        next_action = "Use as avoid/inverse/failure-intelligence feature unless a later source route changes the evidence."
    elif positive_sources >= 2 and adverse_scheduler_rows == 0 and promote_like >= redesign_like:
        disposition = "promote_default_off_package_candidate"
        next_action = "Promote as default-off candidate package axis after residual gates are verified; no live authority yet."
    elif positive_sources >= 2 and recoverable_scheduler_rows > 0:
        disposition = "merge_with_scheduler_lifecycle_controls"
        next_action = "Merge signal with queue/delay/reduced-risk/replacement lifecycle controls before final selection."
    elif positive_sources >= 1 and (redesign_like > 0 or adverse_scheduler_rows > 0):
        disposition = "redesign_or_source_repair_candidate"
        next_action = "Redesign package use or repair source/lifecycle blockers before promotion."
    else:
        disposition = "source_required_before_package_disposition"
        next_action = "Keep as exact source requirement before package disposition."

    return {
        "schema_version": "gtos.final_moonshot.final_package_synthesis.axis_score_row.v1",
        "framework": key[0],
        "origin_family": key[1],
        "symbol": key[2],
        "session_bucket": key[3],
        "side": key[4],
        "selector_rows": selector_rows,
        "selector_positive_lift_rows": int(stats["selector_positive_lift_rows"]),
        "selector_zero_lift_rows": int(stats["selector_zero_lift_rows"]),
        "selector_lift_sum": selector_lift,
        "candidate_level_rows": candidate_rows,
        "candidate_level_source_bound_r_sum": candidate_r,
        "candidate_level_known_proxy_r_rows": int(stats["candidate_level_known_proxy_r_rows"]),
        "scheduler_rows": scheduler_rows,
        "scheduler_result_r_sum": scheduler_r,
        "scheduler_missed_result_r_sum": round(float(stats["scheduler_missed_result_r_sum"]), 9),
        "combined_source_bound_signal_r": total_signal,
        "positive_signal_source_count": positive_sources,
        "negative_signal_source_count": negative_sources,
        "selector_branch_decision_counts": branch_counts,
        "scheduler_action_class_counts": action_counts,
        "source_gap_family_counts": source_gaps,
        "disposition": disposition,
        "final_package_selection_allowed": False,
        "next_action": next_action,
    }


def main() -> int:
    generated_utc = utc_now()
    hydrated_summary = read_json(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_SUMMARY.json")
    candidate_summary = read_json(CANDIDATE_ROUTE / "CANDIDATE_LEVEL_MATCH_SUMMARY.json")
    scheduler_summary = read_json(SCHEDULER_ROUTE / "SCHEDULER_MATCH_REPAIR_SUMMARY.json")
    wave_f_summary = read_json(WAVE_F_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json")
    final_selection_summary = read_json(FINAL_SELECTION_ROUTE / "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json")

    axes: defaultdict[tuple[str, str, str, str, str], dict[str, Any]] = defaultdict(new_axis)
    selector_rows = 0
    selector_positive_lift_rows = 0
    selector_zero_lift_rows = 0
    selector_lift_sum = 0.0
    branch_decisions = Counter()
    source_gap_families = Counter()

    for row in iter_jsonl_gz(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz"):
        selector_rows += 1
        lift = fnum(row.get("lift_best_minus_current_policy_r"))
        if lift > 0:
            selector_positive_lift_rows += 1
        elif lift == 0:
            selector_zero_lift_rows += 1
        selector_lift_sum += lift
        key = axis_key(row)
        stats = axes[key]
        stats["selector_rows"] += 1
        stats["selector_lift_sum"] += lift
        stats["selector_current_policy_r_sum"] += fnum(row.get("current_policy_cost_adjusted_median_r"))
        stats["selector_best_policy_r_sum"] += fnum(row.get("best_policy_cost_adjusted_median_r"))
        if lift > 0:
            stats["selector_positive_lift_rows"] += 1
        elif lift == 0:
            stats["selector_zero_lift_rows"] += 1
        branch = str(row.get("branch_decision") or "missing")
        impl = str(row.get("implementation_decision") or "missing")
        branch_decisions[branch] += 1
        stats["selector_branch_decisions"][branch] += 1
        stats["selector_implementation_decisions"][impl] += 1
        for gap in row.get("source_gap_families") or []:
            source_gap_families[str(gap)] += 1
            stats["selector_source_gap_families"][str(gap)] += 1

    candidate_rows = 0
    candidate_source_bound_r_sum = 0.0
    for row in iter_jsonl(CANDIDATE_ROUTE / "CANDIDATE_LEVEL_MATCH_LEDGER.jsonl"):
        candidate_rows += 1
        key = axis_key(row)
        value = fnum(row.get("source_bound_r_value"))
        axes[key]["candidate_level_rows"] += 1
        axes[key]["candidate_level_source_bound_r_sum"] += value
        axes[key]["candidate_level_known_proxy_r_rows"] += int(row.get("known_proxy_r_rows") or 0)
        candidate_source_bound_r_sum += value

    scheduler_rows = 0
    scheduler_result_r_sum = 0.0
    scheduler_missed_result_r_sum = 0.0
    scheduler_action_classes = Counter()
    for row in iter_jsonl_gz(SCHEDULER_ROUTE / "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz"):
        scheduler_rows += 1
        key = axis_key(row)
        result_r = fnum(row.get("result_r"))
        missed_r = fnum(row.get("missed_result_r"))
        action_class = str(row.get("scheduler_v3_action_class") or "missing")
        decision = str(row.get("scheduler_v3_decision") or "missing")
        axes[key]["scheduler_rows"] += 1
        axes[key]["scheduler_result_r_sum"] += result_r
        axes[key]["scheduler_missed_result_r_sum"] += missed_r
        axes[key]["scheduler_action_classes"][action_class] += 1
        axes[key]["scheduler_decisions"][decision] += 1
        scheduler_action_classes[action_class] += 1
        scheduler_result_r_sum += result_r
        scheduler_missed_result_r_sum += missed_r

    axis_rows = [score_axis(key, stats) for key, stats in sorted(axes.items())]
    disposition_counts = Counter(row["disposition"] for row in axis_rows)

    split_rows = iter_jsonl(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl")
    split_stress_rows: list[dict[str, Any]] = []
    for row in split_rows:
        expectancy = fnum(row.get("expectancy_r"))
        disposition = "support_package_axis" if expectancy > 0 else "avoid_or_redesign_axis"
        split_stress_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_synthesis.split_stress_row.v1",
                "source": "hydrated_replay_lift_split",
                "axis": row.get("axis"),
                "value": row.get("value"),
                "rows": row.get("rows"),
                "r_rows": row.get("r_rows"),
                "r_sum": row.get("r_sum"),
                "expectancy_r": row.get("expectancy_r"),
                "positive_rows": row.get("positive_rows"),
                "negative_rows": row.get("negative_rows"),
                "disposition": disposition,
                "final_package_selection_allowed": False,
            }
        )
    for row in iter_jsonl(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl"):
        split_stress_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_synthesis.split_stress_row.v1",
                "source": "hydrated_replay_lift_leave_one_symbol",
                "axis": "held_out_symbol",
                "value": row.get("held_out_symbol"),
                "rows": row.get("remaining_rows"),
                "r_rows": row.get("remaining_r_rows"),
                "r_sum": row.get("remaining_r_sum"),
                "expectancy_r": row.get("remaining_expectancy_r"),
                "positive_rows": None,
                "negative_rows": None,
                "disposition": "survives_leave_one_symbol" if fnum(row.get("remaining_expectancy_r")) > 0 else "fails_leave_one_symbol",
                "final_package_selection_allowed": False,
            }
        )
    split_stress_rows.append(
        {
            "schema_version": "gtos.final_moonshot.final_package_synthesis.split_stress_row.v1",
            "source": "wave_f_validation_stress",
            "axis": "validation_stress_materialization",
            "value": "time_walk_forward_leave_one_symbol_side_adversarial_mc",
            "rows": wave_f_summary.get("input_row_count"),
            "r_rows": wave_f_summary.get("nonzero_proxy_row_count"),
            "r_sum": None,
            "expectancy_r": None,
            "positive_rows": None,
            "negative_rows": None,
            "disposition": "materialized_proxy_validation_checkpoint_not_final_selection",
            "final_package_selection_allowed": False,
            "time_split_rows": wave_f_summary.get("time_split_rows"),
            "walk_forward_rows": wave_f_summary.get("walk_forward_rows"),
            "leave_one_symbol_side_rows": wave_f_summary.get("leave_one_symbol_side_rows"),
            "monte_carlo_proxy_rows": wave_f_summary.get("monte_carlo_proxy_rows"),
            "adversarial_baseline_rows": wave_f_summary.get("adversarial_baseline_rows"),
        }
    )

    concentration_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl"):
        expectancy = fnum(row.get("expectancy_r"))
        if expectancy > 0 and int(row.get("rows") or 0) >= 2:
            disposition = "support_with_concentration_cap"
        elif expectancy > 0:
            disposition = "support_but_small_cell_watch"
        else:
            disposition = "avoid_or_reduce_concentrated_cell"
        concentration_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_synthesis.concentration_row.v1",
                "framework": row.get("framework"),
                "symbol": row.get("symbol"),
                "session_bucket": row.get("session_bucket"),
                "rows": row.get("rows"),
                "r_rows": row.get("r_rows"),
                "r_sum": row.get("r_sum"),
                "expectancy_r": row.get("expectancy_r"),
                "positive_rows": row.get("positive_rows"),
                "negative_rows": row.get("negative_rows"),
                "disposition": disposition,
                "final_package_selection_allowed": False,
            }
        )

    source_rows = [
        {
            "source_id": "hydrated_selector_candidate_ledger",
            "path": str(HYDRATED_ROUTE / "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz"),
            "rows": selector_rows,
            "r_sum": round(selector_lift_sum, 9),
            "status": "streamed_full_denominator",
        },
        {
            "source_id": "candidate_level_match_ledger",
            "path": str(CANDIDATE_ROUTE / "CANDIDATE_LEVEL_MATCH_LEDGER.jsonl"),
            "rows": candidate_rows,
            "r_sum": round(candidate_source_bound_r_sum, 9),
            "status": "streamed_full_denominator",
        },
        {
            "source_id": "scheduler_match_candidate_ledger",
            "path": str(SCHEDULER_ROUTE / "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz"),
            "rows": scheduler_rows,
            "r_sum": round(scheduler_result_r_sum, 9),
            "status": "streamed_full_denominator",
        },
        {
            "source_id": "wave_f_validation_stress",
            "path": str(WAVE_F_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json"),
            "rows": wave_f_summary.get("input_row_count"),
            "r_sum": None,
            "status": "proxy_validation_stress_checkpoint_absorbed",
        },
    ]

    successor_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(SUCCESSOR_ROUTE / "WAVE_F_SUCCESSOR_EXPERIMENT_SELECTION_LEDGER.jsonl"):
        successor_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_synthesis.successor_primitive_row.v1",
                "primitive": row.get("primitive"),
                "selection_disposition": row.get("selection_disposition"),
                "source_coverage_status": row.get("source_coverage_status"),
                "material_row_count": row.get("material_row_count"),
                "local_source_match_count": row.get("local_source_match_count"),
                "next_action": row.get("next_action"),
                "final_package_selection_allowed": False,
            }
        )

    residual_gates = [
        {
            "gate_id": "FPSG001",
            "gate": "broker_actual_r_and_close_cost_claim_quality",
            "status": "calibration_gate_partial_not_edge_source",
            "evidence": f"{final_selection_summary.get('broker_actual_r_joined_rows')} broker actual-R row and {final_selection_summary.get('close_side_all_in_cost_joined_rows')} close-cost row; {final_selection_summary.get('remaining_required_close_history_rows')} unresolved close-history rows",
            "required_repair": "Use broker actual-R/close-cost for claim-quality calibration only; import remaining read-only close history before broker-real expectancy claims.",
        },
        {
            "gate_id": "FPSG002",
            "gate": "fillability_order_type_denominator",
            "status": "open_exact_denominator_bridge_required",
            "evidence": f"final-selection order_type_exact_join_rows={final_selection_summary.get('order_type_exact_join_rows')}",
            "required_repair": "Bridge selected-package lifecycle/fillability/order-type labels before final package selection.",
        },
        {
            "gate_id": "FPSG003",
            "gate": "clean_labels_and_model_training",
            "status": "open_clean_label_requirement",
            "evidence": f"training_ready_label_count={final_selection_summary.get('training_ready_label_count')}",
            "required_repair": "Create clean no-leak labels and deterministic baselines before model training or model promotion.",
        },
        {
            "gate_id": "FPSG004",
            "gate": "package_selection_verifier",
            "status": "open_final_selection_not_yet_proven",
            "evidence": "This route emits candidate package dispositions but does not select the final package.",
            "required_repair": "Run final acceptance once residual gates close; keep final_package_selected=false now.",
        },
    ]

    summary = {
        "schema": "gtos.final_moonshot.final_package_synthesis.summary.v1",
        "generated_utc": generated_utc,
        "status": "candidate_final_package_synthesis_checkpoint_not_final_selection",
        "result_scope": "full_denominator_candidate_package_disposition_synthesis_from_big_discovery_evidence_not_deployment_readiness",
        "selector_candidate_rows": selector_rows,
        "selector_positive_lift_rows": selector_positive_lift_rows,
        "selector_zero_lift_rows": selector_zero_lift_rows,
        "selector_lift_sum": round(selector_lift_sum, 9),
        "candidate_level_rows": candidate_rows,
        "candidate_level_source_bound_r_sum": round(candidate_source_bound_r_sum, 9),
        "scheduler_rows": scheduler_rows,
        "scheduler_result_r_sum": round(scheduler_result_r_sum, 9),
        "scheduler_missed_result_r_sum": round(scheduler_missed_result_r_sum, 9),
        "axis_score_rows": len(axis_rows),
        "candidate_package_shortlist_rows": len(axis_rows),
        "split_stress_rows": len(split_stress_rows),
        "concentration_rows": len(concentration_rows),
        "successor_primitive_rows": len(successor_rows),
        "residual_gate_rows": len(residual_gates),
        "disposition_counts": dict(disposition_counts),
        "selector_branch_decision_counts": dict(branch_decisions),
        "scheduler_action_class_counts": dict(scheduler_action_classes),
        "source_gap_family_counts": dict(source_gap_families.most_common()),
        "forbidden_surface_status": {
            "blind_remote_push": False,
            "broker_account_order_history_deal_position_mutation": False,
            "broker_operation": False,
            "credential_mutation_or_disclosure": False,
            "execution_admission_or_sizing_change": False,
            "live_trading": False,
            "live_vps_restart_or_reload": False,
            "paid_api_vendor_call": False,
        },
        "terminal_decision": {
            "broker_actual_r_is_edge_source": False,
            "broker_actual_r_claim_allowed": False,
            "candidate_final_package_shortlist_materialized": True,
            "deployment_dossier_allowed": False,
            "final_package_selected": False,
            "live_execution_activation_allowed": False,
            "model_training_allowed": False,
        },
    }

    decisions = [
        {
            "decision_id": "FPSD001",
            "status": "selected",
            "decision": "Use the large discovery evidence as the package-synthesis driver, not the single broker-R row.",
            "reason": "Selector lift, candidate-level source-bound signal, and scheduler result signal all cover broad denominators; broker actual-R/close-cost remain calibration gates.",
        },
        {
            "decision_id": "FPSD002",
            "status": "selected",
            "decision": "Emit every candidate package context axis with a deterministic promote/merge/redesign/avoid/source-required disposition.",
            "reason": "No top-N cap is used; every axis key found in selector, candidate-level, or scheduler evidence is preserved.",
        },
        {
            "decision_id": "FPSD003",
            "status": "selected",
            "decision": "Keep final_package_selected=false.",
            "reason": "The route creates a candidate final-package shortlist, but residual fillability, label, broker-calibration, and final acceptance gates remain open.",
        },
    ]

    completion = {
        "schema": "gtos.final_moonshot.final_package_synthesis.completion_audit.v1",
        "generated_utc": generated_utc,
        "status": "not_complete_continue",
        "goal_completion_claim": False,
        "instruction_coverage": {
            "current_disk_evidence": "regenerated LIVE_STATE and consumed current synthesis source route artifacts from disk",
            "no_top_n_shortlist": "candidate package shortlist rows equal every merged context axis; no rank cap applied",
            "broker_r_cost_role": "broker actual-R and close-cost are recorded only as calibration/claim-quality residual gates",
            "big_discovery_evidence_used": "streamed selector, candidate-level, and scheduler full-denominator ledgers",
            "forbidden_surfaces": "no live trading, broker operation, mutation, credential, paid API, blind push, execution admission/sizing change, or VPS reload performed",
        },
        "remaining_work": [row["required_repair"] for row in residual_gates],
        "verification": {"final_package_synthesis": "pending"},
    }

    manifest = {
        "schema": "gtos.final_moonshot.final_package_synthesis.output_manifest.v1",
        "generated_utc": generated_utc,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_final_package_synthesis.py",
            "verify_final_package_synthesis.py",
            "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json",
            "FINAL_PACKAGE_SYNTHESIS_SOURCE_LEDGER.jsonl",
            "FINAL_PACKAGE_AXIS_SCORE_LEDGER.jsonl",
            "FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl",
            "FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl",
            "FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl",
            "FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_LEDGER.jsonl",
            "FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "COMPLETION_AUDIT.json",
            "OUTPUT_MANIFEST.json",
            "FOCUSED_TEST_RESULT.json",
            "SATURATION_SELF_RED_TEAM.md",
            "VERIFICATION_RESULT.json",
        ],
    }

    focused = {
        "schema": "gtos.final_moonshot.final_package_synthesis.focused_test_result.v1",
        "generated_utc": generated_utc,
        "status": "pending",
        "verification_result": {},
        "checks": [
            "full selector/candidate/scheduler row counts",
            "source-bound signal sums",
            "no-top-N axis shortlist equality",
            "terminal boundary false fields",
        ],
    }

    saturation = (
        "# Saturation Self-Red-Team\n\n"
        "- Checked for over-focusing on broker-R/cost: residual gates label them calibration only, not edge source.\n"
        "- Checked for top-N truncation: every merged context axis is emitted to both axis-score and candidate-shortlist ledgers.\n"
        "- Checked for concentration: every hydrated concentration row is preserved with support/reduce/avoid disposition.\n"
        "- Checked for validation: split, leave-one-symbol, and Wave F stress rows are absorbed while final selection remains blocked.\n"
        "- Checked forbidden surfaces: no live/broker/credential/paid/remote/VPS action and no execution admission or sizing change.\n"
    )

    write_json("FINAL_PACKAGE_SYNTHESIS_SUMMARY.json", summary)
    write_jsonl("FINAL_PACKAGE_SYNTHESIS_SOURCE_LEDGER.jsonl", source_rows)
    write_jsonl("FINAL_PACKAGE_AXIS_SCORE_LEDGER.jsonl", axis_rows)
    write_jsonl("FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl", axis_rows)
    write_jsonl("FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl", split_stress_rows)
    write_jsonl("FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl", concentration_rows)
    write_jsonl("FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_LEDGER.jsonl", successor_rows)
    write_jsonl("FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl", residual_gates)
    write_jsonl("DECISION_LEDGER.jsonl", decisions)
    write_json("COMPLETION_AUDIT.json", completion)
    write_json("OUTPUT_MANIFEST.json", manifest)
    write_json("FOCUSED_TEST_RESULT.json", focused)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
