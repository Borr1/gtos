from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
STAGE_ID = "STAGE_11_SEMANTIC_VERIFIER_HARDENING"

STAGE10_INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
STAGE11_INTEGRATION_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"
ROW_REPLAY_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_ROW_REPLAY_LEDGER_{DATE}.jsonl"
REFUSAL_SPLIT_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_REFUSAL_REPAIR_SPLIT_LEDGER_{DATE}.jsonl"
CHALLENGE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_CHALLENGE_LEDGER_{DATE}.jsonl"
PROP_COMPARISON_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_PROP_AWARE_ROUTER_COMPARISON_{DATE}.jsonl"
SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"
ROUTE_CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_ROUTE_CONTROL_NUDGE_LEDGER_{DATE}.jsonl"
RESULT_PATH = ROUTE_DIR / f"VNEXT_MOONSHOT_SEMANTIC_VERIFIER_RESULT_{DATE}.json"
CONFIG = REPO_ROOT / "config" / "agent_config.yaml"


class SemanticVerificationError(AssertionError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _mean(total: float, rows: int) -> float | None:
    return round(total / rows, 12) if rows else None


def verify_semantic_contract(
    *,
    route_dir: Path = ROUTE_DIR,
    repo_root: Path = REPO_ROOT,
    write_result: bool = True,
    check_config: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    stage10 = read_json(route_dir / STAGE10_INTEGRATION_MAP.name)
    stage11 = read_json(route_dir / STAGE11_INTEGRATION_MAP.name)
    state = read_json(route_dir / SESSION_STATE.name)

    expected_rows = int(stage10["row_level_evidence"]["router_replay_rows"])
    expected_refusals = int(stage10["router_replay_summary"]["decision_status_counts"]["refuse_live_use_until_source_or_scope_repaired"])
    _require(errors, stage11.get("stage_id") == STAGE_ID, "Stage11 integration map has wrong stage_id")
    _require(errors, stage11.get("row_replay_rows") == expected_rows, "Stage11 map row count does not match Stage10 rows")
    _require(errors, stage11.get("refusal_repair_split_rows") == expected_refusals, "Stage11 map refusal count does not match Stage10 refusals")
    _require(errors, not stage11.get("forbidden_boundaries_crossed"), "Stage11 claims a forbidden boundary was crossed")
    _require(errors, stage11.get("no_live_trading_or_broker_mutation") is True, "Stage11 no-live boundary missing")
    _require(errors, stage11.get("no_paid_api_or_vendor_call") is True, "Stage11 no-paid-call boundary missing")

    row_count = 0
    condition_sum = be_sum = live_sum = fixed_sum = 0.0
    fvg_rows = 0
    fvg_condition_sum = fvg_be_sum = 0.0
    selector_expost_rows = 0
    condition_policy_counts: Counter[str] = Counter()
    for _line_no, row in iter_jsonl(route_dir / ROW_REPLAY_LEDGER.name):
        row_count += 1
        _require(errors, row.get("schema_version") == "vnext_moonshot_stage11_condition_router_row_replay_v1", f"bad row schema at {row_count}")
        policy = row.get("condition_selected_policy")
        condition_policy_counts[str(policy)] += 1
        condition_sum += float(row["condition_selected_policy_final_r"])
        be_sum += float(row["global_be_after_trigger_final_r"])
        live_sum += float(row["live_current_j46_j49_final_r"])
        fixed_sum += float(row["fixed_1_5r_final_r"])
        if row.get("framework") == "fvg_fill":
            fvg_rows += 1
            fvg_condition_sum += float(row["condition_selected_policy_final_r"])
            fvg_be_sum += float(row["global_be_after_trigger_final_r"])
        if not row.get("selector_uses_only_asof_feature_columns") or not row.get("selector_excludes_expost_same_bar_outcome"):
            selector_expost_rows += 1
    _require(errors, row_count == expected_rows, f"Stage11 row replay count {row_count} != expected {expected_rows}")
    _require(errors, selector_expost_rows == 0, f"{selector_expost_rows} rows use invalid selector inputs")
    condition_mean = _mean(condition_sum, row_count)
    be_mean = _mean(be_sum, row_count)
    live_mean = _mean(live_sum, row_count)
    fixed_mean = _mean(fixed_sum, row_count)
    fvg_condition_mean = _mean(fvg_condition_sum, fvg_rows)
    fvg_be_mean = _mean(fvg_be_sum, fvg_rows)
    _require(errors, condition_mean is not None and be_mean is not None and condition_mean > be_mean, "condition router does not beat global be_after_trigger on all rows")
    _require(errors, condition_mean is not None and live_mean is not None and condition_mean > live_mean, "condition router does not beat live_current_j46_j49")
    _require(errors, condition_mean is not None and fixed_mean is not None and condition_mean > fixed_mean, "condition router does not beat fixed 1.5R")
    _require(errors, fvg_condition_mean is not None and fvg_be_mean is not None and fvg_condition_mean > fvg_be_mean, "condition router does not beat global be in primary FVG scope")
    _require(errors, condition_policy_counts.get("trailing_runner", 0) > 0, "condition router never selects trailing_runner")
    _require(errors, condition_policy_counts.get("be_after_trigger", 0) > 0, "condition router never retains be_after_trigger")

    challenge_rows = [row for _line_no, row in iter_jsonl(route_dir / CHALLENGE_LEDGER.name)]
    _require(errors, len(challenge_rows) == stage11.get("condition_challenge_rows"), "condition challenge row count mismatch")
    oof_rows = [row for row in challenge_rows if row.get("row_type") == "chrono_oof_condition_router_challenge"]
    _require(errors, len(oof_rows) == 1, "missing chrono out-of-fold condition-router challenge row")
    if oof_rows:
        oof = oof_rows[0]
        _require(errors, oof.get("row_count") == expected_rows, "OOF challenge does not cover all rows")
        _require(errors, oof.get("condition_vs_global_be_delta_r", 0) > 0, "OOF condition router does not beat global be")
        _require(errors, oof.get("selector_excludes_expost_same_bar_outcome") is True, "OOF selector uses ex-post same-bar outcome")

    refusal_rows = 0
    local_repairable_now = 0
    terminal_counts: Counter[str] = Counter()
    repair_tags: Counter[str] = Counter()
    for _line_no, row in iter_jsonl(route_dir / REFUSAL_SPLIT_LEDGER.name):
        refusal_rows += 1
        terminal = row.get("terminal_repair_class")
        terminal_counts[str(terminal)] += 1
        for tag in row.get("repair_class_tags") or []:
            repair_tags[str(tag)] += 1
        if row.get("locally_repairable_now"):
            local_repairable_now += 1
            _require(errors, row.get("action_taken") == "repaired_and_replayed", f"locally repairable row not repaired: {row.get('router_replay_row_id')}")
    _require(errors, refusal_rows == expected_refusals, f"refusal split rows {refusal_rows} != expected {expected_refusals}")
    _require(errors, local_repairable_now == 0, "locally repairable rows remain unresolved")
    _require(errors, repair_tags.get("ordered_ltf_or_tick_required", 0) > 0, "ordered LTF/tick required rows were not split")
    _require(errors, repair_tags.get("forward_capture_required", 0) > 0, "forward-capture rows were not split")
    _require(errors, terminal_counts.get("activation_excluded_secondary_branch_pending_prop_default_not_source_repair", 0) > 0, "activation-excluded rows were not split")

    prop_rows = [row for _line_no, row in iter_jsonl(route_dir / PROP_COMPARISON_LEDGER.name)]
    _require(errors, len(prop_rows) == stage11.get("prop_aware_comparison_rows"), "prop comparison row count mismatch")
    by_policy = {row.get("policy_name"): row for row in prop_rows}
    be_prop = by_policy.get("be_after_trigger_prop_pass_default")
    condition_prop = by_policy.get("condition_asof_displacement_v1_account_restart")
    _require(errors, be_prop is not None, "missing be_after_trigger prop default row")
    _require(errors, condition_prop is not None, "missing condition router prop comparison row")
    if be_prop and condition_prop:
        _require(
            errors,
            be_prop["reference_ev_per_terminal_day_usd_fee599_payout8000"]
            > condition_prop["reference_ev_per_terminal_day_usd_fee599_payout8000"],
            "condition router row-level improvement was not adjudicated against prop EV",
        )
        _require(errors, be_prop["allowed_trades"] > condition_prop["allowed_trades"], "condition prop row does not prove be default captures more accepted trades")
    terminal = stage11.get("prop_aware_terminal_decision", {})
    _require(errors, terminal.get("prop_default_retained") is True, "Stage11 prop decision did not retain or reject default explicitly")
    _require(
        errors,
        terminal.get("terminal_classification")
        == "condition_router_beats_global_row_expectancy_but_is_rejected_as_primary_prop_default_from_local_prop_replay",
        "Stage11 prop terminal classification missing or weak",
    )

    route_rows = [row for _line_no, row in iter_jsonl(route_dir / ROUTE_CONTROL_LEDGER.name)]
    _require(
        errors,
        any(row.get("steer_id") == "stage11_semantic_verifier_hardening_active_challenge_steer_2026_05_26" and row.get("classification") == "applied_now" for row in route_rows),
        "Stage11 active challenge steer was not recorded as applied_now",
    )
    _require(errors, state.get("first_incomplete_invariant") == "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION", "session state did not advance to Stage12")
    _require(errors, state.get("completion_gate_status") == "not_complete_first_incomplete_stage12", "completion gate does not identify Stage12 as first incomplete")

    if check_config:
        cfg = yaml.safe_load((repo_root / "config" / "agent_config.yaml").read_text(encoding="utf-8"))
        runtime_cfg = cfg.get("gtos_vnext_runtime", {})
        _require(errors, runtime_cfg.get("moonshot_dynamic_execution_router_enabled") is False, "moonshot router enabled flag is not false")
        _require(errors, runtime_cfg.get("moonshot_dynamic_execution_router_apply_to_execution") is False, "moonshot router apply_to_execution flag is not false")
        _require(errors, runtime_cfg.get("moonshot_dynamic_execution_router_policy") == "be_after_trigger", "prop-pass default policy changed without Stage11 prop proof")
        _require(errors, runtime_cfg.get("moonshot_dynamic_execution_router_condition_challenger_policy") == "condition_asof_displacement_v1", "condition challenger config key missing")

    result = {
        "schema_version": "vnext_moonshot_semantic_verifier_result_v1",
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "ok": not errors,
        "errors": errors,
        "row_replay_rows": row_count,
        "expected_rows": expected_rows,
        "refusal_split_rows": refusal_rows,
        "expected_refusal_rows": expected_refusals,
        "condition_router_expectancy_r": condition_mean,
        "global_be_after_trigger_expectancy_r": be_mean,
        "live_current_j46_j49_expectancy_r": live_mean,
        "fixed_1_5r_expectancy_r": fixed_mean,
        "condition_vs_global_be_delta_r": round((condition_mean or 0.0) - (be_mean or 0.0), 12),
        "primary_fvg_condition_vs_global_be_delta_r": round((fvg_condition_mean or 0.0) - (fvg_be_mean or 0.0), 12),
        "condition_policy_counts": dict(sorted(condition_policy_counts.items())),
        "refusal_terminal_counts": dict(sorted(terminal_counts.items())),
        "refusal_repair_tag_counts": dict(sorted(repair_tags.items())),
        "local_repairable_now_rows": local_repairable_now,
        "prop_rows": len(prop_rows),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    if write_result:
        (route_dir / RESULT_PATH.name).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        raise SemanticVerificationError("; ".join(errors))
    if write_result:
        state_path = route_dir / SESSION_STATE.name
        state_doc = read_json(state_path)
        command = (
            "py -3 research/science_program_2026_05/06_outcome_testing/"
            "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
            "verify_vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26.py"
        )
        entries = state_doc.setdefault("verifiers_tests_run", [])
        if not any(entry.get("command") == command for entry in entries):
            entries.append(
                {
                    "command": command,
                    "status": "passed",
                    "result": (
                        f"ok=true; rows={row_count}; refusals={refusal_rows}; "
                        f"condition_vs_be_delta_r={result['condition_vs_global_be_delta_r']}; "
                        f"local_repairable_now_rows={local_repairable_now}"
                    ),
                }
            )
            state_path.write_text(json.dumps(state_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    try:
        result = verify_semantic_contract(write_result=True, check_config=True)
    except SemanticVerificationError as exc:
        result_path = RESULT_PATH
        if result_path.exists():
            print(result_path.read_text(encoding="utf-8"))
        raise SystemExit(str(exc))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
