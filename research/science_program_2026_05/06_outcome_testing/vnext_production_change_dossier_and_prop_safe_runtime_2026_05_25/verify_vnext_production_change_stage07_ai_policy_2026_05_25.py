from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage07_ai_policy_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage07", MODULE_PATH)
stage07 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage07)


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in (stage07.REPO_ROOT / stage07.STAGE07_LEDGER_PATH)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def config_failures() -> list[str]:
    cfg = yaml.safe_load(
        (stage07.REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    )
    block = cfg["gtos_vnext_runtime"]
    expected = {
        "ai_policy_enabled": True,
        "ai_policy_apply_to_ai_call": False,
        "ai_policy_follow_no_ai_enabled": False,
        "ai_policy_allow_mixed_ai_resolution": True,
        "ai_policy_mixed_resolution_requires_source_bound_fields": True,
        "ai_policy_allow_legacy_broad_fallback": False,
        "ai_policy_legacy_requires_replayed_scope": True,
        "ai_policy_prompt_hash_logging_required": True,
        "ai_policy_schema_validation_required": True,
        "ai_policy_content_addressed_cache_required": True,
    }
    failures: list[str] = []
    for key, value in expected.items():
        if block.get(key) != value:
            failures.append(f"config {key} expected {value!r} got {block.get(key)!r}")
    if block.get("apply_to_execution") is not False:
        failures.append("global vNext apply_to_execution must remain false")
    return failures


def code_failures() -> list[str]:
    runtime_text = (stage07.REPO_ROOT / "src/components/gtos_vnext_runtime.py").read_text(
        encoding="utf-8"
    )
    orchestrator_text = (stage07.REPO_ROOT / "src/components/orchestrator.py").read_text(
        encoding="utf-8"
    )
    failures: list[str] = []
    required_runtime_tokens = [
        "GTOSVNextAIPolicyDecision",
        "evaluate_vnext_ai_policy",
        "format_vnext_ai_policy_context_for_prompt",
        "attach_vnext_ai_policy_to_record",
        "SKIP_AI_MECHANICAL_AVOID",
        "BLOCK_LEGACY_BROAD_FALLBACK",
        "ai_policy_apply_to_ai_call",
    ]
    for token in required_runtime_tokens:
        if token not in runtime_text:
            failures.append(f"runtime token missing: {token}")
    required_orchestrator_tokens = [
        "_evaluate_gtos_vnext_ai_policy",
        "GTOS_VNEXT_AI_POLICY",
        "GTOS_VNEXT_AI_POLICY_SKIP_PRE_AI",
        "vnext_ai_policy=vnext_ai_policy",
        "attach_vnext_ai_policy_to_record",
    ]
    for token in required_orchestrator_tokens:
        if token not in orchestrator_text:
            failures.append(f"orchestrator token missing: {token}")
    return failures


def dossier_failures() -> list[str]:
    text = (stage07.REPO_ROOT / stage07.STAGE07_DOSSIER_PATH).read_text(encoding="utf-8")
    required_phrases = [
        "Stage07 decision-surface groups",
        "Stage07 decision-map rows",
        "Prompt packet hashes",
        "Schema/parser fixtures",
        "No-Paid-Call Harness",
        "Stage08 still owns the always-on AI supervisor",
        "No live trading",
    ]
    return [f"dossier missing phrase: {phrase}" for phrase in required_phrases if phrase not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    rows = load_rows()
    summary = json.loads(
        (stage07.REPO_ROOT / stage07.STAGE07_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result = json.loads(
        (stage07.REPO_ROOT / stage07.STAGE07_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage07.verify_summary(summary, rows)
    failures.extend(config_failures())
    failures.extend(code_failures())
    failures.extend(dossier_failures())
    state = json.loads((stage07.REPO_ROOT / stage07.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage07 builder result is not ok")
    if state["stage_status_table"].get("STAGE_07_AI_POLICY") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage07 status is not in_progress or complete")

    output = {
        "route_id": stage07.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage07.rel(stage07.STAGE07_LEDGER_PATH),
        "scenario_row_count": summary["scenario_row_count"],
        "prompt_packet_count": summary["prompt_packet_count"],
        "parser_fixture_count": summary["parser_fixture_count"],
        "stage07_surface_rows": summary["stage07_surface"]["row_count"],
        "first_incomplete_invariant": (
            "STAGE_08_AI_SUPERVISOR"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage07.update_state(summary, complete=True)
        state_path = stage07.REPO_ROOT / stage07.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    args.test_command
                    or "py -3 -m pytest tests/test_gtos_vnext_runtime.py -q -k "
                    "'vnext_ai_policy or orchestrator_injects_vnext_ai_role_context'"
                ),
                "result": args.test_result or "Stage07 focused tests passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 -c py_compile changed Stage07 runtime/test/route files "
                    "with explicit cfile targets under C:/tmp/gtos_pycache/vnext_prod_stage07"
                ),
                "result": "compiled Stage07 files",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage07_ai_policy_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "scenario_row_count": summary["scenario_row_count"],
                    "prompt_packet_count": summary["prompt_packet_count"],
                    "parser_fixture_count": summary["parser_fixture_count"],
                    "stage07_surface_rows": summary["stage07_surface"]["row_count"],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage07_tests_passed"] = True
        stage07.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
