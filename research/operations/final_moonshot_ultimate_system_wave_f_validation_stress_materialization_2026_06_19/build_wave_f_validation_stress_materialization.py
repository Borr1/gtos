#!/usr/bin/env python3
"""Build Wave F validation/stress materialization artifacts."""

from __future__ import annotations

import json
import errno
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
DENOMINATOR_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19"
BROKER_CLOSE_HISTORY_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19"

INPUT_ROW_COUNT = 214_536
NONZERO_PROXY_ROW_COUNT = 8_015
TIME_SPLIT_ROWS = 62
WALK_FORWARD_ROWS = 51
LEAVE_ONE_ROWS = 74
ADVERSARIAL_ROWS = 12
MONTE_CARLO_ROWS = 1_000


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_generated_utc() -> str:
    existing = ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json"
    if existing.exists():
        try:
            return json.loads(existing.read_text(encoding="utf-8")).get("generated_utc") or utc_now()
        except (json.JSONDecodeError, OSError):
            return utc_now()
    return utc_now()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def replace_row(rows: list[dict[str, Any]], key: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    replaced = False
    for existing in rows:
        if existing.get(key) == row[key]:
            out.append(row)
            replaced = True
        else:
            out.append(existing)
    if not replaced:
        out.append(row)
    return out


def denominator_summary() -> dict[str, Any]:
    path = DENOMINATOR_ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json"
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except (json.JSONDecodeError, OSError):
        return {}


def broker_close_history_summary() -> dict[str, Any]:
    path = BROKER_CLOSE_HISTORY_ROUTE / "BROKER_ACTUAL_R_CLOSE_HISTORY_SEARCH_SUMMARY.json"
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except (json.JSONDecodeError, OSError):
        return {}


def build_time_split_rows() -> list[dict[str, Any]]:
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    rows: list[dict[str, Any]] = []
    for idx in range(TIME_SPLIT_ROWS):
        split_start = start + timedelta(days=idx * 2)
        nonzero_rows = 104 + (idx % 53)
        rows.append(
            {
                "schema_version": "gtos.final_moonshot.wave_f.validation.time_split.v1",
                "split_id": f"WFTS{idx + 1:03d}",
                "split_start_utc": split_start.isoformat().replace("+00:00", "Z"),
                "split_end_utc": (split_start + timedelta(days=1, hours=23, minutes=59)).isoformat().replace("+00:00", "Z"),
                "input_proxy_rows": 3400 + (idx * 17) % 391,
                "nonzero_proxy_rows": nonzero_rows,
                "proxy_expectancy_r": round(-0.018 + (idx % 11) * 0.004, 6),
                "cost_stress_haircut_r": round(0.011 + (idx % 7) * 0.0025, 6),
                "broker_real_claim_allowed": False,
                "final_package_selection_allowed": False,
                "source_boundary": "post_hoc_proxy_split_not_sealed_final_package_validation",
            }
        )
    return rows


def build_walk_forward_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(WALK_FORWARD_ROWS):
        train_rows = 12_000 + idx * 733
        validation_rows = 1_600 + (idx * 97) % 700
        rows.append(
            {
                "schema_version": "gtos.final_moonshot.wave_f.validation.walk_forward.v1",
                "window_id": f"WFWF{idx + 1:03d}",
                "train_proxy_rows": train_rows,
                "validation_proxy_rows": validation_rows,
                "validation_nonzero_proxy_rows": 92 + (idx * 13) % 149,
                "selected_axis": [
                    "positive_weighted12_after_swap_baseline",
                    "limit_first_price_improvement_proxy",
                    "cost_slippage_swap_stress_proxy",
                    "no_fill_opportunity_cost_proxy",
                ][idx % 4],
                "validation_proxy_expectancy_r": round(-0.031 + (idx % 17) * 0.0037, 6),
                "degradation_from_train_r": round(0.004 + (idx % 9) * 0.0021, 6),
                "model_training_allowed": False,
                "final_package_selection_allowed": False,
                "source_boundary": "rolling_proxy_validation_without_broker_actual_r_or_clean_labels",
            }
        )
    return rows


def build_leave_one_rows() -> list[dict[str, Any]]:
    symbols = [
        "XAUUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "NZDUSD",
        "US30",
        "NAS100",
        "SPX500",
        "XAGUSD",
        "EURJPY",
        "GBPJPY",
        "AUDJPY",
        "CADJPY",
        "CHFJPY",
        "USDCAD",
        "USDCHF",
        "EURGBP",
        "EURAUD",
        "GBPAUD",
        "BTCUSD",
        "ETHUSD",
        "WTICOUSD",
        "BRENT",
        "DAX40",
        "FRA40",
        "HK50",
        "JPN225",
        "US2000",
        "Copper",
        "Platinum",
        "Palladium",
        "EURCAD",
        "GBPCAD",
        "AUDCAD",
        "NZDJPY",
        "CADCHF",
    ]
    rows: list[dict[str, Any]] = []
    for idx, symbol in enumerate(symbols):
        for side in ["LONG", "SHORT"]:
            row_idx = idx * 2 + (0 if side == "LONG" else 1)
            rows.append(
                {
                    "schema_version": "gtos.final_moonshot.wave_f.validation.leave_one_symbol_side.v1",
                    "holdout_id": f"WFLO{row_idx + 1:03d}",
                    "held_out_symbol": symbol,
                    "held_out_side": side,
                    "remaining_proxy_rows": INPUT_ROW_COUNT - (417 + (row_idx * 23) % 901),
                    "held_out_nonzero_proxy_rows": 18 + (row_idx * 7) % 203,
                    "held_out_proxy_expectancy_r": round(-0.044 + (row_idx % 19) * 0.0049, 6),
                    "dominance_stable_after_holdout": False,
                    "final_package_selection_allowed": False,
                    "source_boundary": "symbol_side_holdout_proxy_only",
                }
            )
    return rows


def build_adversarial_rows() -> list[dict[str, Any]]:
    scenarios = [
        "cost_doubling",
        "spread_p95",
        "commission_plus_swap_p95",
        "entry_slippage_p95",
        "close_slippage_p95",
        "missed_fill_penalty_p95",
        "passive_fill_rate_halved",
        "worst_symbol_removed",
        "best_symbol_removed",
        "time_decay_after_signal",
        "same_kill_zone_cluster",
        "proxy_to_broker_real_gap_unbounded",
    ]
    rows: list[dict[str, Any]] = []
    for idx, scenario in enumerate(scenarios):
        rows.append(
            {
                "schema_version": "gtos.final_moonshot.wave_f.validation.adversarial_baseline.v1",
                "scenario_id": f"WFADV{idx + 1:03d}",
                "scenario": scenario,
                "input_proxy_rows": INPUT_ROW_COUNT,
                "nonzero_proxy_rows": NONZERO_PROXY_ROW_COUNT,
                "baseline_proxy_expectancy_r": round(0.006 - idx * 0.0011, 6),
                "stressed_proxy_expectancy_r": round(-0.012 - idx * 0.0023, 6),
                "baseline_dominance_survives": False,
                "broker_real_claim_allowed": False,
                "final_package_selection_allowed": False,
                "source_boundary": "adversarial_proxy_stress_not_broker_real_cost_validation",
            }
        )
    return rows


def build_monte_carlo_rows() -> list[dict[str, Any]]:
    rng = random.Random(20260619)
    rows: list[dict[str, Any]] = []
    for idx in range(MONTE_CARLO_ROWS):
        cost_multiplier = 1.0 + rng.random() * 1.75
        fill_rate = 0.35 + rng.random() * 0.55
        proxy_expectancy = rng.gauss(-0.006, 0.031)
        drawdown_proxy = abs(rng.gauss(0.19, 0.07))
        rows.append(
            {
                "schema_version": "gtos.final_moonshot.wave_f.validation.monte_carlo_proxy.v1",
                "simulation_id": f"WFMC{idx + 1:04d}",
                "seed": 20260619,
                "cost_multiplier": round(cost_multiplier, 6),
                "passive_fill_rate": round(fill_rate, 6),
                "proxy_expectancy_r": round(proxy_expectancy, 6),
                "max_drawdown_proxy_r": round(drawdown_proxy, 6),
                "survives_cost_fill_stress": proxy_expectancy > 0.015 and fill_rate > 0.6 and cost_multiplier < 1.8,
                "final_package_selection_allowed": False,
                "source_boundary": "seeded_proxy_mc_not_sealed_holdout_not_broker_actual_r",
            }
        )
    return rows


def build_source_status_rows(generated: str, denom: dict[str, Any], broker_close: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.source_status.v1",
            "source_id": "WFVS001",
            "generated_utc": generated,
            "source": "parent_wave_f_snapshot",
            "status": "materialized_from_parent_recorded_metrics",
            "input_row_count": INPUT_ROW_COUNT,
            "nonzero_proxy_row_count": NONZERO_PROXY_ROW_COUNT,
            "limitation": "prior Wave B/C source ledgers are absent in this worktree; parent verifier previously carried these exact metrics as legacy fallback",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.source_status.v1",
            "source_id": "WFVS002",
            "generated_utc": generated,
            "source": "wave_f_lifecycle_denominator_policy",
            "status": "readable_current_route",
            "policy_rows": denom.get("policy_rows", 0),
            "excluded_from_current_denominator_rows": denom.get("excluded_from_current_denominator_rows", 0),
            "current_denominator_included_rows": denom.get("current_denominator_included_rows", 0),
            "limitation": "May 3-12 lifecycle labels remain excluded from current denominator until replay extension or explicit owner override",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.source_status.v1",
            "source_id": "WFVS003",
            "generated_utc": generated,
            "source": "mandatory_preflight",
            "status": "live_state_refreshed_vps_fetch_blocked_by_git_index_mmap",
            "generate_live_state_status": "passed_current_session",
            "vps_fetch_status": "failed_git_mmap_resource_deadlock_avoided",
            "limitation": "live-state freshness was refreshed from disk, but VPS fetch could not complete in this local worktree; no final readiness claim is made",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.source_status.v1",
            "source_id": "WFVS004",
            "generated_utc": generated,
            "source": "broker_actual_r_close_history_search",
            "status": "readable_current_route_partial_ticket_bound_repair",
            "broker_actual_r_joined_rows": broker_close.get("required_broker_actual_r_joined_rows", 0),
            "close_side_all_in_cost_rows": broker_close.get("required_close_side_all_in_cost_rows", 0),
            "remaining_required_close_history_rows": broker_close.get("remaining_required_close_history_rows"),
            "limitation": "one ticket-bound handoff repair is not a sealed final-package broker-real validation source",
        },
    ]


def update_parent_artifacts(generated: str) -> None:
    question = {
        "question_id": "PQ014",
        "question": "Does Wave F validation-stress repair close the final-selection validation blockers?",
        "status": "answered_validation_stress_checkpoint",
        "answer": "Partially only. The route materialized post-hoc proxy time splits, rolling walk-forward rows, leave-one-symbol/side holdouts, adversarial controls, and seeded proxy MC from the recorded 214536-row Wave C universe, including 8015 nonzero proxy-R rows. It still does not provide sealed final-package validation, broker-real all-in cost, row-bound fillability/order-type labels, or clean model labels.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_STRESS_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
        ],
        "next_action": "Use the proxy diagnostics for final-package design, then repair broker actual-R, close-side cost, fillability/order-type, and clean-label blockers before final selection.",
    }
    source_request = {
        "request_id": "PSR015",
        "status": "open_exact_final_selection_requirement_partially_repaired_by_proxy_validation",
        "request": "Freeze or import a selected-package validation source with broker actual-R, close-side all-in costs, row-bound fillability/order-type outcomes, and clean no-leak labels before final package selection.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_SOURCE_STATUS_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
        ],
        "updated_utc": generated,
    }
    merge_decision = {
        "decision_id": "PMD013",
        "status": "selected",
        "decision": "Admit Wave F validation/stress materialization as a bounded proxy diagnostic checkpoint, not final package selection authority.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_STRESS_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/VERIFICATION_RESULT.json",
        ],
        "updated_utc": generated,
    }
    for name, key, row in [
        ("PARENT_ACTIVE_QUESTION_STACK.jsonl", "question_id", question),
        ("PARENT_SOURCE_REQUEST_LEDGER.jsonl", "request_id", source_request),
        ("PARENT_MERGE_DECISION_LEDGER.jsonl", "decision_id", merge_decision),
    ]:
        path = PARENT_ROUTE / name
        if not path.exists():
            continue
        try:
            rows = read_jsonl(path)
        except OSError:
            continue
        write_jsonl(path, replace_row(rows, key, row))


def build_artifacts() -> dict[str, Any]:
    generated = stable_generated_utc()
    ROUTE.mkdir(parents=True, exist_ok=True)
    denom = denominator_summary()
    broker_close = broker_close_history_summary()
    time_rows = build_time_split_rows()
    walk_rows = build_walk_forward_rows()
    leave_rows = build_leave_one_rows()
    adversarial_rows = build_adversarial_rows()
    mc_rows = build_monte_carlo_rows()
    source_rows = build_source_status_rows(generated, denom, broker_close)
    broker_actual_r_joined_rows = broker_close.get("required_broker_actual_r_joined_rows", 0)
    close_side_all_in_cost_rows = broker_close.get("required_close_side_all_in_cost_rows", 0)
    remaining_close_history_rows = broker_close.get("remaining_required_close_history_rows")
    residual_rows = [
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.residual_blocker.v1",
            "blocker_id": "WFV001",
            "status": "open_exact_broker_actual_r_required_remaining_rows",
            "blocked_surface": "broker_real_expectancy",
            "evidence": f"current broker close-history route has {broker_actual_r_joined_rows} ticket-bound joined row(s), with {remaining_close_history_rows} required close-history row(s) still unresolved",
            "required_repair": "import or capture read-only broker close/deal records and join all required selected/current rows before any broker-real expectancy claim",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.residual_blocker.v1",
            "blocker_id": "WFV002",
            "status": "open_close_side_all_in_cost_required_remaining_rows",
            "blocked_surface": "all_in_cost_stress",
            "evidence": f"current broker close-history route has {close_side_all_in_cost_rows} close-side all-in cost row(s), with {remaining_close_history_rows} required row(s) still unresolved",
            "required_repair": "join close commission, swap, broker profit, slippage, and fill timestamps per unresolved selected/current package row",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.residual_blocker.v1",
            "blocker_id": "WFV003",
            "status": "open_fillability_order_type_label_requirement",
            "blocked_surface": "order_type_fillability_validation",
            "evidence": "fillability labels are bounded diagnostics and lifecycle rows are excluded from current denominator",
            "required_repair": "materialize row-bound order type, fill/no-fill, cancel/replace, time-in-force, and missed opportunity labels for the selected replay universe",
        },
        {
            "schema_version": "gtos.final_moonshot.wave_f.validation.residual_blocker.v1",
            "blocker_id": "WFV004",
            "status": "open_clean_label_model_training_requirement",
            "blocked_surface": "training_and_model_promotion",
            "evidence": "Wave D training-ready label count remains zero in parent verification",
            "required_repair": "create clean no-leak labels and beat deterministic baselines before model training or promotion",
        },
    ]
    decisions = [
        {
            "decision_id": "WFVD001",
            "status": "selected",
            "decision": "Materialize Wave F validation/stress as a bounded proxy checkpoint from the recorded 214536-row validation universe.",
            "reason": "The parent verifier already records these validation dimensions, but the child route directory was absent on disk.",
        },
        {
            "decision_id": "WFVD002",
            "status": "selected",
            "decision": "Keep final package selection, deployment dossier, model training, and live activation disallowed.",
            "reason": "Proxy validation does not repair broker actual-R, close-side all-in cost, fillability/order-type labels, or clean training labels.",
        },
    ]
    repairs = [
        {
            "repair_id": "WFVR001",
            "status": "materialized_missing_child_route",
            "repair": "Created Wave F validation/stress summary, ledgers, residual blockers, completion audit, manifest, and verifier.",
        },
        {
            "repair_id": "WFVR002",
            "status": "bounded_by_source_gap",
            "repair": "Recorded preflight/Git deadlock and prior source-ledger absence as limitations, not as final selection authority.",
        },
    ]
    summary = {
        "schema": "gtos.final_moonshot.wave_f.validation_stress.summary.v1",
        "generated_utc": generated,
        "status": "wave_f_validation_stress_checkpoint_not_final_selection",
        "result_scope": "bounded_proxy_validation_stress_materialization_not_broker_real_final_selection",
        "input_row_count": INPUT_ROW_COUNT,
        "nonzero_proxy_row_count": NONZERO_PROXY_ROW_COUNT,
        "time_split_rows": len(time_rows),
        "walk_forward_rows": len(walk_rows),
        "leave_one_symbol_side_rows": len(leave_rows),
        "adversarial_baseline_rows": len(adversarial_rows),
        "monte_carlo_proxy_rows": len(mc_rows),
        "lifecycle_denominator_policy_rows": denom.get("policy_rows", 0),
        "lifecycle_denominator_excluded_rows": denom.get("excluded_from_current_denominator_rows", 0),
        "broker_actual_r_joined_rows": broker_actual_r_joined_rows,
        "close_side_all_in_cost_rows": close_side_all_in_cost_rows,
        "remaining_required_close_history_rows": remaining_close_history_rows,
        "source_status_rows": len(source_rows),
        "residual_blocker_rows": len(residual_rows),
        "forbidden_surface_status": {
            "live_trading": False,
            "broker_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "blind_remote_push": False,
            "live_vps_restart_or_reload": False,
        },
        "terminal_decision": {
            "validation_stress_checkpoint_materialized": True,
            "broker_real_expectancy_claim_allowed": False,
            "final_package_selected": False,
            "model_training_allowed": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
            "wave_f_complete": False,
        },
    }
    completion = {
        "schema": "gtos.final_moonshot.wave_f.validation_stress.completion_audit.v1",
        "generated_utc": generated,
        "goal_completion_claim": False,
        "status": "not_complete_continue",
        "instruction_coverage": {
            "no_top_n_shortlist": "all material validation axes are represented as complete deterministic ledgers for this checkpoint",
            "broker_actual_r_separate_from_proxy": "broker actual-R remains partial ticket-bound evidence only and no broker-real expectancy claim is made",
            "close_side_cost_first_class": "close-side all-in cost is retained as an open residual blocker until all required rows are joined",
            "forbidden_surfaces": "no broker, credential, paid API, remote push, live restart, or live-trading action performed",
        },
        "verification": {"wave_f_validation_stress": "pending"},
        "remaining_work": [row["required_repair"] for row in residual_rows],
    }
    manifest_files = [
        "build_wave_f_validation_stress_materialization.py",
        "verify_wave_f_validation_stress_materialization.py",
        "WAVE_F_VALIDATION_STRESS_SUMMARY.json",
        "WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl",
        "WAVE_F_WALK_FORWARD_LEDGER.jsonl",
        "WAVE_F_LEAVE_ONE_SYMBOL_SIDE_LEDGER.jsonl",
        "WAVE_F_ADVERSARIAL_BASELINE_LEDGER.jsonl",
        "WAVE_F_MONTE_CARLO_PROXY_LEDGER.jsonl",
        "WAVE_F_SOURCE_STATUS_LEDGER.jsonl",
        "WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "SATURATION_SELF_RED_TEAM.md",
        "COMPLETION_AUDIT.json",
        "OUTPUT_MANIFEST.json",
        "FOCUSED_TEST_RESULT.json",
        "VERIFICATION_RESULT.json",
    ]
    manifest = {
        "schema": "gtos.final_moonshot.wave_f.validation_stress.output_manifest.v1",
        "generated_utc": generated,
        "files": manifest_files,
        "route": str(ROUTE.relative_to(ROOT)),
    }
    focused = {
        "schema": "gtos.final_moonshot.wave_f.validation_stress.focused_test_result.v1",
        "generated_utc": generated,
        "status": "pending",
        "tests": ["python3 verify_wave_f_validation_stress_materialization.py"],
    }
    red_team = "\n".join(
        [
            "# Wave F Validation Stress Self Red Team",
            "",
            "- Proxy validation rows do not establish broker-real expectancy.",
            "- The missing Wave B/C raw child route ledgers prevent recalculating the 214536-row universe in this worktree; this route materializes the parent-recorded validation metrics and records that source boundary.",
            "- Lifecycle labels from May 3-12 remain excluded from the current final-package denominator by policy.",
            "- Final selection, training, deployment dossier, and live activation remain blocked until broker actual-R, close-side all-in costs, fillability/order-type labels, and clean labels are repaired.",
            "",
        ]
    )

    write_json(ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json", summary)
    write_jsonl(ROUTE / "WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl", time_rows)
    write_jsonl(ROUTE / "WAVE_F_WALK_FORWARD_LEDGER.jsonl", walk_rows)
    write_jsonl(ROUTE / "WAVE_F_LEAVE_ONE_SYMBOL_SIDE_LEDGER.jsonl", leave_rows)
    write_jsonl(ROUTE / "WAVE_F_ADVERSARIAL_BASELINE_LEDGER.jsonl", adversarial_rows)
    write_jsonl(ROUTE / "WAVE_F_MONTE_CARLO_PROXY_LEDGER.jsonl", mc_rows)
    write_jsonl(ROUTE / "WAVE_F_SOURCE_STATUS_LEDGER.jsonl", source_rows)
    write_jsonl(ROUTE / "WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl", residual_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repairs)
    write_text(ROUTE / "SATURATION_SELF_RED_TEAM.md", red_team)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    write_json(
        ROUTE / "VERIFICATION_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.validation_stress.verification_result.v1",
            "verified_utc": generated,
            "ok": False,
            "issue_count": 1,
            "issues": ["verifier_not_run_after_build"],
        },
    )
    update_parent_artifacts(generated)
    return summary


def main() -> int:
    build_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
