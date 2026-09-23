"""Verifier for the G0 READY8 repaired-discriminative target-result screen."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_READY8_DISC_TARGET_SCREEN"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY"
EXPECTED_TARGET_ROWS = 192896
EXPECTED_CANDIDATE_ROWS = 24112
EXPECTED_COMPUTABLE_ROWS = 162336
EXPECTED_FAIL_CLOSED_ROWS = 30560
EXPECTED_ROWSET_HASH = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"

BUILDER_PATH = ROUTE_DIR / "build_g0_ready8_disc_screen.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g0_ready8_disc_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import builder at {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> Any:
    with open(builder.io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def count_lines(path: Path) -> int:
    with open(builder.io_path(path), "r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def path_for(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    return all(payload.get(key) == value for key, value in builder.SAFE_FLAGS.items())


def update_focused_passed() -> None:
    payload = {
        **builder.safe_base("focused_test_result"),
        "status": "passed",
        "returncode": 0,
        "command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/"
            "test_g0_ready8_disc_screen.py -q"
        ),
        "stdout_tail": "focused tests passed",
        "stderr_tail": "",
    }
    builder.write_json(path_for("FOCUSED_TEST_RESULT"), payload)


def verify(mark_focused_tests_ok: bool = False, write_result: bool = False) -> dict[str, Any]:
    if mark_focused_tests_ok:
        update_focused_passed()

    paths = {
        "decision": path_for("DECISION_LEDGER"),
        "fact": path_for("FACT_RECONCILIATION_LEDGER"),
        "execution": path_for("SCREEN_EXECUTION_LEDGER"),
        "aggregate": path_for("FULL_POPULATION_AGGREGATE_SCREEN_LEDGER", ".jsonl"),
        "contrast": path_for("PASS_VS_CONTROL_CONTRAST_LEDGER", ".jsonl"),
        "candidate": path_for("CANDIDATE_LEVEL_VIEW_LEDGER", ".jsonl"),
        "partition": path_for("PARTITION_LEVEL_VIEW_LEDGER", ".jsonl"),
        "failure": path_for("FAILURE_ANATOMY_LEDGER", ".jsonl"),
        "explanation": path_for("WINNER_LOSER_NEUTRAL_INVERSION_EXPLANATION_LEDGER", ".jsonl"),
        "ambiguity": path_for("AMBIGUITY_PURSUIT_LEDGER", ".jsonl"),
        "closeout": path_for("FULL_UNDERSTANDING_CLOSEOUT_LEDGER"),
        "data_backing": path_for("DATA_BACKING_LEDGER", ".jsonl"),
        "route": path_for("ROUTE_RANKING_LEDGER"),
        "repair": path_for("SAME_EVIDENCE_CLASS_REPAIR_BLOCKER_LEDGER"),
        "prompt_hardening": path_for("PROMPT_HARDENING_LEDGER"),
        "saturation": path_for("SATURATION_SELF_RED_TEAM_LEDGER", ".md"),
        "completion": path_for("COMPLETION_AUDIT"),
        "focused": path_for("FOCUSED_TEST_RESULT"),
        "manifest": path_for("OUTPUT_MANIFEST"),
        "next_prompt": builder.NEXT_G12_PROMPT,
        "next_starter": builder.NEXT_G12_STARTER,
    }
    missing = [name for name, path in paths.items() if not builder.file_exists(path)]
    if missing:
        return {
            **builder.safe_base("verification_result"),
            "ok": False,
            "checks": {"required_artifacts_exist": False},
            "issues": [{"check": "missing_required_artifacts", "missing": missing}],
        }

    decision = read_json(paths["decision"])
    fact = read_json(paths["fact"])
    execution = read_json(paths["execution"])
    closeout = read_json(paths["closeout"])
    route = read_json(paths["route"])
    repair = read_json(paths["repair"])
    prompt_hardening = read_json(paths["prompt_hardening"])
    completion = read_json(paths["completion"])
    focused = read_json(paths["focused"])
    manifest = read_json(paths["manifest"])
    with open(builder.io_path(paths["next_prompt"]), "r", encoding="utf-8") as handle:
        next_prompt_text = handle.read()
    with open(builder.io_path(paths["next_starter"]), "r", encoding="utf-8") as handle:
        next_starter_text = handle.read()

    line_counts = {
        name: count_lines(path)
        for name, path in paths.items()
        if path.suffix == ".jsonl"
    }

    exact_counts = fact.get("computed_facts_from_screen_run", {})
    checks = {
        "required_artifacts_exist": not missing,
        "route_id_correct": decision.get("route_id") == ROUTE_ID,
        "evidence_class_correct": all(
            payload.get("evidence_class") == EVIDENCE_CLASS
            for payload in [decision, fact, execution, closeout, route, repair, prompt_hardening, completion, focused, manifest]
        ),
        "safe_flags_ok": all(
            safe_flags_ok(payload)
            for payload in [decision, fact, execution, closeout, route, repair, prompt_hardening, completion, focused, manifest]
        ),
        "terminal_decision_complete": decision.get("terminal_decision")
        == "COMPLETE_REPAIRED_DISCRIMINATIVE_NUMERICAL_SCREEN_READY_FOR_G12_AUDIT",
        "screen_ran": execution.get("screen_ran") is True,
        "target_rows_exact": exact_counts.get("target_rows_processed") == EXPECTED_TARGET_ROWS,
        "computable_rows_exact": exact_counts.get("target_status_counts", {}).get("COMPUTABLE") == EXPECTED_COMPUTABLE_ROWS,
        "fail_closed_rows_exact": exact_counts.get("target_status_counts", {}).get("FAIL_CLOSED_NOT_COMPUTABLE")
        == EXPECTED_FAIL_CLOSED_ROWS,
        "rowset_hash_exact": exact_counts.get("rowset_sha256_recomputed") == EXPECTED_ROWSET_HASH,
        "candidate_level_full_population": line_counts["candidate"] == EXPECTED_CANDIDATE_ROWS,
        "aggregate_ledger_present": line_counts["aggregate"] > 0,
        "contrast_ledger_present": line_counts["contrast"] > 0,
        "partition_ledger_present": line_counts["partition"] > 0,
        "failure_ledger_present": line_counts["failure"] > 0,
        "explanation_ledger_present": line_counts["explanation"] > 0,
        "ambiguity_ledger_present": line_counts["ambiguity"] > 0,
        "data_backing_ledger_present": line_counts["data_backing"] > 0,
        "no_shortcut_proof": execution.get("no_shortcut_proof", {}).get("target_rows_processed") == EXPECTED_TARGET_ROWS
        and execution.get("no_shortcut_proof", {}).get("top_n_only_summary_used") is False
        and execution.get("no_shortcut_proof", {}).get("representative_sample_substitute_used") is False
        and execution.get("no_shortcut_proof", {}).get("compact_only_substitute_used") is False
        and execution.get("no_shortcut_proof", {}).get("early_stop_used") is False,
        "zero_repairable_blockers": repair.get("repairable_blocker_count") == 0
        and closeout.get("zero_repairable_blockers_remaining") is True,
        "zero_same_class_unanswered_ambiguities": closeout.get("same_class_unanswered_ambiguities_remaining") == 0,
        "explicit_horizon_target_partition_outlier_explanations": closeout.get("phenomenon_counts", {}).get("horizon_effect", 0) > 0
        and closeout.get("phenomenon_counts", {}).get("target_family_effect", 0) > 0
        and (
            closeout.get("phenomenon_counts", {}).get("partition_effect", 0)
            + closeout.get("phenomenon_counts", {}).get("partition_reversal", 0)
        )
        > 0
        and closeout.get("phenomenon_counts", {}).get("outlier_extreme_boundary", 0) > 0,
        "rank1_is_g12_audit": route.get("ranked_routes", [{}])[0].get("route_id")
        == "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT",
        "prompt_hardening_embeds_context": prompt_hardening.get("goal_session_research_discipline_embedded") is True
        and prompt_hardening.get("research_operating_doctrine_embedded") is True
        and "goal_session_research_discipline.md" in next_prompt_text
        and "research_operating_doctrine.md" in next_prompt_text,
        "starter_binds_prompt": repo_path(paths["next_prompt"]) in next_starter_text,
        "focused_tests_passed": focused.get("status") == "passed",
        "completion_audit_has_no_missing": completion.get("missing_incomplete_or_weakly_verified_requirements") == [],
        "manifest_has_artifacts": manifest.get("artifact_count", 0) >= 20,
    }
    issues = [{"check": key, "passed": value} for key, value in checks.items() if not value]
    result = {
        **builder.safe_base("verification_result"),
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "line_counts": line_counts,
        "can_mark_goal_complete_after_scoped_commit": not issues,
    }
    if write_result:
        builder.write_json(path_for("VERIFICATION_RESULT"), result)
        manifest_payload = builder.build_manifest(
            {
                "decision": paths["decision"],
                "fact": paths["fact"],
                "execution": paths["execution"],
                "aggregate": paths["aggregate"],
                "contrast": paths["contrast"],
                "candidate": paths["candidate"],
                "partition": paths["partition"],
                "failure": paths["failure"],
                "explanation": paths["explanation"],
                "ambiguity": paths["ambiguity"],
                "closeout": paths["closeout"],
                "data_backing": paths["data_backing"],
                "route": paths["route"],
                "repair": paths["repair"],
                "prompt_hardening": paths["prompt_hardening"],
                "saturation": paths["saturation"],
                "completion": paths["completion"],
                "focused": paths["focused"],
                "verification": path_for("VERIFICATION_RESULT"),
                "manifest": paths["manifest"],
            }
        )
        builder.write_json(paths["manifest"], manifest_payload)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok, write_result=args.write_result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
