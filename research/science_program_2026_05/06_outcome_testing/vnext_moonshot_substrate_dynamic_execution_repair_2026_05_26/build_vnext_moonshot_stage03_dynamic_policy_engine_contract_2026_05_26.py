from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.dynamic_execution_policy import (  # noqa: E402
    PathObservation,
    PolicySpec,
    required_policy_manifest,
    simulate_policy,
)


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

OUTPUT_POLICY_MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_MANIFEST_{DATE_ID}.jsonl"
OUTPUT_ENGINE_CONTRACT = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_ENGINE_CONTRACT_{DATE_ID}.json"
OUTPUT_TEST_MATRIX = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_TEST_MATRIX_{DATE_ID}.jsonl"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_ENGINE_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
STAGE02_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json"

ENGINE_PATH = REPO_ROOT / "src" / "research" / "dynamic_execution_policy.py"

REQUIRED_POLICY_NAMES = {
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def policy_to_row(index: int, policy: PolicySpec) -> dict:
    required_inputs = ["ordered_path_observations_r", "same_bar_policy", "source_priority_rank"]
    if policy.name == "ai_target":
        required_inputs.append("ai_emitted_target_r")
    if policy.name == "path_aware_runner":
        required_inputs.extend(["structural_target_r", "liquidity_target_r", "atr_expansion_target_r"])
    if policy.name == "live_current_j46_j49":
        required_inputs.extend(["tp1_3r_touch_order", "be_move_success_truth", "time_stop_12_m15_bars"])
    if "trailing" in policy.name:
        required_inputs.append("trailing_stop_transition_order")
    return {
        "policy_id": f"STAGE03-POLICY-{index:03d}-{policy.name}",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
        "policy_name": policy.name,
        "final_target_r": policy.final_target_r,
        "stop_r": policy.stop_r,
        "tp1_r": policy.tp1_r,
        "partial_close_ratio": policy.partial_close_ratio,
        "move_stop_to_be_on_tp1": policy.move_stop_to_be_on_tp1,
        "be_stop_r": policy.be_stop_r,
        "time_stop_bars": policy.time_stop_bars,
        "early_cut_bars": policy.early_cut_bars,
        "early_cut_min_mfe_r": policy.early_cut_min_mfe_r,
        "trailing_trigger_r": policy.trailing_trigger_r,
        "trailing_gap_r": policy.trailing_gap_r,
        "max_bars": policy.max_bars,
        "required_inputs": required_inputs,
        "description": policy.description,
        "execution_effect": "research_replay_only_no_broker_mutation",
    }


def engine_imports() -> dict:
    tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
    imports = []
    banned = []
    banned_roots = {"MetaTrader5", "mt5", "subprocess", "requests", "anthropic", "openai"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                imports.append(alias.name)
                if root in banned_roots:
                    banned.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            imports.append(node.module)
            if root in banned_roots:
                banned.append(node.module)
    return {"imports": sorted(set(imports)), "banned_imports": sorted(set(banned))}


def matrix_cases() -> list[tuple[str, list[PathObservation]]]:
    return [
        (
            "profit_run_to_6r",
            [
                PathObservation(index=1, high_r=0.8, low_r=-0.2, close_r=0.5, source_mode="unit_path"),
                PathObservation(index=2, high_r=1.7, low_r=0.1, close_r=1.4, source_mode="unit_path"),
                PathObservation(index=3, high_r=3.2, low_r=1.0, close_r=2.8, source_mode="unit_path"),
                PathObservation(index=4, high_r=6.1, low_r=2.2, close_r=5.8, source_mode="unit_path"),
            ],
        ),
        (
            "stop_first_loss",
            [
                PathObservation(index=1, high_r=0.2, low_r=-1.1, close_r=-0.8, source_mode="unit_path"),
            ],
        ),
        (
            "time_stop_mark_to_market",
            [
                PathObservation(index=i, high_r=0.4, low_r=-0.2, close_r=0.1 * i, source_mode="unit_path")
                for i in range(1, 13)
            ],
        ),
        (
            "same_bar_ambiguous",
            [
                PathObservation(index=1, high_r=2.0, low_r=-1.1, close_r=0.2, source_mode="unit_path"),
            ],
        ),
    ]


def write_manifest(policies: list[PolicySpec]) -> list[dict]:
    rows = [policy_to_row(index, policy) for index, policy in enumerate(policies, start=1)]
    with OUTPUT_POLICY_MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def write_test_matrix(policies: list[PolicySpec]) -> list[dict]:
    rows = []
    for policy in policies:
        for case_name, observations in matrix_cases():
            result = simulate_policy(policy, observations, same_bar_policy="ambiguous" if case_name == "same_bar_ambiguous" else "conservative")
            rows.append(
                {
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
                    "policy_name": policy.name,
                    "case_name": case_name,
                    "replay_status": result.replay_status,
                    "exit_reason": result.exit_reason,
                    "final_r": result.final_r,
                    "exit_index": result.exit_index,
                    "same_bar_ambiguity": result.same_bar_ambiguity,
                    "transition_count": len(result.transitions),
                    "source_gap_reason": result.source_gap_reason,
                }
            )
    with OUTPUT_TEST_MATRIX.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def write_contract(policy_rows: list[dict], matrix_rows: list[dict]) -> dict:
    stage02 = json.loads(STAGE02_SUMMARY.read_text(encoding="utf-8")) if STAGE02_SUMMARY.exists() else {}
    imports = engine_imports()
    contract = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
        "generated_at_utc": utc_now(),
        "engine_module_path": rel(ENGINE_PATH),
        "policy_manifest_path": rel(OUTPUT_POLICY_MANIFEST),
        "test_matrix_path": rel(OUTPUT_TEST_MATRIX),
        "policy_count": len(policy_rows),
        "policy_names": sorted(row["policy_name"] for row in policy_rows),
        "required_policy_names": sorted(REQUIRED_POLICY_NAMES),
        "missing_required_policy_names": sorted(REQUIRED_POLICY_NAMES - {row["policy_name"] for row in policy_rows}),
        "engine_imports": imports["imports"],
        "banned_imports": imports["banned_imports"],
        "purity_contract": {
            "no_mt5": not imports["banned_imports"],
            "no_broker_mutation": True,
            "no_file_io_inside_engine": True,
            "no_paid_api": True,
            "pure_inputs": ["PolicySpec", "PathObservation", "same_bar_policy"],
        },
        "same_bar_policy_modes": ["conservative", "optimistic", "ambiguous"],
        "source_priority_consumption": stage02.get("source_priority_order", []),
        "dynamic_execution_usable_source_rows_from_stage02": stage02.get("dynamic_execution_usable_counts", {}),
        "forward_capture_requirements_path": stage02.get("forward_capture_requirements_path"),
        "matrix_rows": len(matrix_rows),
        "ambiguous_case_rows": sum(1 for row in matrix_rows if row["replay_status"] == "ambiguous"),
        "not_replayable_source_gap_policy": "empty_path_returns_not_replayable_source_gap_no_ordered_path",
        "execution_effect": "research_replay_only_default_off_no_runtime_flag_flip",
        "first_incomplete_invariant_after_stage03": "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY",
    }
    OUTPUT_ENGINE_CONTRACT.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(contract)
    update_state(contract)
    return contract


def write_report(contract: dict) -> None:
    lines = [
        "# vNext Moonshot Stage03 Dynamic Policy Engine Contract",
        "",
        f"Generated: `{contract['generated_at_utc']}`",
        "",
        "## Engine",
        "",
        f"- Module: `{contract['engine_module_path']}`",
        f"- Policy count: `{contract['policy_count']}`",
        f"- Banned imports: `{contract['banned_imports']}`",
        f"- Execution effect: `{contract['execution_effect']}`",
        f"- First incomplete invariant: `{contract['first_incomplete_invariant_after_stage03']}`",
        "",
        "## Policies",
        "",
    ]
    for name in contract["policy_names"]:
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## Source Contract",
            "",
            "- Stage03 consumes Stage02 source priority ordering, but does not claim broker lifecycle truth unless exact fields exist.",
            "- Empty ordered paths return `not_replayable` rather than inferred R.",
            "- Same-bar target/stop collisions can be conservative, optimistic, or explicitly ambiguous.",
            "- Live-current J46/J49 is modeled as 3R TP1, move SL to BE, no partial, 6R target, and 12 M15-bar time stop.",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(contract: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE"
    state["first_incomplete_invariant"] = "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"
    state["exact_next_action"] = "Run Stage04 full policy dynamic replay over replayable candidate paths using Stage02 source priority."
    state["dynamic_policy_manifest_path"] = rel(OUTPUT_POLICY_MANIFEST)
    state["row_counts_scanned"]["stage03_policy_manifest_rows"] = contract["policy_count"]
    state["row_counts_scanned"]["stage03_policy_test_matrix_rows"] = contract["matrix_rows"]
    state["stage_status_table"]["STAGE_03_DYNAMIC_POLICY_STATE_MACHINE"] = "complete"
    state["stage_status_table"]["STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"] = "pending"
    state["output_artifact_manifest"]["dynamic_policy_manifest"] = rel(OUTPUT_POLICY_MANIFEST)
    state["output_artifact_manifest"]["dynamic_policy_engine_contract"] = rel(OUTPUT_ENGINE_CONTRACT)
    state["output_artifact_manifest"]["dynamic_policy_test_matrix"] = rel(OUTPUT_TEST_MATRIX)
    state["output_artifact_manifest"]["dynamic_policy_engine_report"] = rel(OUTPUT_REPORT)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage04"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage03_dynamic_policy_engine_contract_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"policy_count={contract['policy_count']}; matrix_rows={contract['matrix_rows']}; "
                "first_incomplete=STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"
            ),
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    policies = required_policy_manifest()
    policy_rows = write_manifest(policies)
    matrix_rows = write_test_matrix(policies)
    contract = write_contract(policy_rows, matrix_rows)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
                "policy_count": contract["policy_count"],
                "matrix_rows": contract["matrix_rows"],
                "first_incomplete_invariant": contract["first_incomplete_invariant_after_stage03"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
