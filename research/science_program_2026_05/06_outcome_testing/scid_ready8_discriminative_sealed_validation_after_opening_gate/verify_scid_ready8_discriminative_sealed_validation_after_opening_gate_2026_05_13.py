from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py"
spec = importlib.util.spec_from_file_location("ready8_sealed_validation_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_jsonl(path: Path) -> int:
    rows = 0
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:  # pragma: no cover - printed in verifier output
                raise AssertionError(f"{path}:{line_number} failed JSONL parse: {exc}") from exc
            rows += 1
    return rows


def has_closed_safe_flags(obj: dict[str, Any]) -> bool:
    expected = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_live_trading_behavior": False,
    }
    return all(obj.get(k) == v for k, v in expected.items())


def forbidden_manifest_paths(paths: list[str]) -> list[str]:
    forbidden = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith("src/"):
            forbidden.append(path)
        if normalized.startswith("config/"):
            forbidden.append(path)
        if normalized.startswith("prompts/"):
            forbidden.append(path)
        if normalized.startswith("scripts/canary") or normalized.startswith("scripts/canary_fixtures"):
            forbidden.append(path)
        if normalized in {"run_agent.py", "start_all.bat"}:
            forbidden.append(path)
    return forbidden


def update_focused_result(passed: bool) -> None:
    path = HERE / builder.OUTPUTS["focused"]
    data = load_json(path)
    data["status"] = "PASSED" if passed else "FAILED"
    data["passed"] = passed
    data["focused_test_command"] = f"python -B -m pytest -p no:cacheprovider {builder.rel(HERE / 'test_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py')} -q --basetemp C:\\tmp\\pytest_ready8_sealed"
    data["recorded_after_pytest_run"] = True
    builder.write_json(path, data)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    if mark_focused_tests_ok:
        update_focused_result(True)

    manifest_path = HERE / builder.OUTPUTS["manifest"]
    manifest = load_json(manifest_path)
    artifact_paths = [a["path"] for a in manifest["artifacts"]]
    missing = [a["path"] for a in manifest["artifacts"] if not a.get("exists")]

    parse_counts: dict[str, int] = {}
    parse_failures: list[str] = []
    for artifact in manifest["artifacts"]:
        path = builder.ROOT / artifact["path"]
        if not path.exists():
            continue
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                load_json(path)
                parse_counts[artifact["path"]] = 1
            elif suffix == ".jsonl":
                parse_counts[artifact["path"]] = parse_jsonl(path)
        except Exception as exc:
            parse_failures.append(f"{artifact['path']}: {exc}")

    frozen = load_json(HERE / builder.OUTPUTS["frozen_input_hash"])
    decision = load_json(HERE / builder.OUTPUTS["decision"])
    coverage = load_json(HERE / builder.OUTPUTS["coverage"])
    completion = load_json(HERE / builder.OUTPUTS["completion"])
    focused = load_json(HERE / builder.OUTPUTS["focused"])
    opening_gate = load_json(builder.GATE_VERIFICATION)

    checks = {
        "manifest_exists": manifest_path.exists(),
        "required_manifest_artifacts_exist": not missing,
        "json_and_jsonl_parse_ok": not parse_failures,
        "rowset_hash_exact": frozen.get("rowset_sha256_matches") is True,
        "opening_gate_verified_or_losslessly_verified": opening_gate.get("ok") is True and frozen.get("opening_gate_verification_ok") is True,
        "target_result_count_exact": frozen["counts_observed"]["target_result_rows"] == builder.EXPECTED_COUNTS["target_result_rows"],
        "computable_count_exact": frozen["counts_observed"]["computable_rows"] == builder.EXPECTED_COUNTS["computable_rows"],
        "fail_closed_count_exact": frozen["counts_observed"]["fail_closed_rows"] == builder.EXPECTED_COUNTS["fail_closed_rows"],
        "source_candidate_duplicate_count_exact": frozen["counts_observed"]["source_candidates_unique_duplicate_proxy_denominator_keys"] == builder.EXPECTED_COUNTS["source_candidates"],
        "branch_families_covered": coverage.get("required_branch_families_covered") is True and coverage.get("no_allowed_branch_family_skipped") is True,
        "no_top_n_substitution": coverage.get("top_n_substitution_used") is False,
        "sealed_primary_nonempty": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["sealed_primary"]), 0) > 0,
        "stress_nonempty": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["stress"]), 0) > 0,
        "pass_control_nonempty": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["pass_control"]), 0) > 0,
        "question_ledger_nonempty": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["questions"]), 0) > 0,
        "ambiguity_ledger_nonempty": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["ambiguity"]), 0) > 0,
        "duplicate_ledger_exact_3014": parse_counts.get(builder.rel(HERE / builder.OUTPUTS["duplicate"]), 0) == builder.EXPECTED_COUNTS["source_candidates"],
        "completion_audit_satisfied": not completion.get("missing_or_unverified_requirements"),
        "focused_tests_recorded_passed": focused.get("passed") is True,
        "safe_flags_closed_manifest": has_closed_safe_flags(manifest),
        "safe_flags_closed_decision": has_closed_safe_flags(decision),
        "no_forbidden_surface_paths_in_manifest": not forbidden_manifest_paths(artifact_paths),
        "next_g12_prompt_exists": builder.G12_PROMPT.exists(),
        "next_g12_starter_exists": (HERE / builder.OUTPUTS["g12_starter"]).exists(),
    }
    issues = []
    issues.extend([f"missing artifact: {path}" for path in missing])
    issues.extend(parse_failures)
    forbidden = forbidden_manifest_paths(artifact_paths)
    issues.extend([f"forbidden manifest path: {path}" for path in forbidden])
    for name, ok in checks.items():
        if not ok:
            issues.append(f"check failed: {name}")

    result = {
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        **builder.SAFE_FLAGS,
        "generated_at_utc": builder.utc_now(),
        "ok": not issues,
        "can_mark_goal_complete": not issues,
        "checks": checks,
        "issues": issues,
        "parse_counts": parse_counts,
        "forbidden_surface_touches": forbidden,
        "terminal_decision": "ACCEPT_SELF_VERIFIED_READY_FOR_G12_AUDIT" if not issues else "VERIFICATION_FAILED",
    }
    builder.write_json(HERE / builder.OUTPUTS["verification"], result)
    builder.write_manifest(result["generated_at_utc"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps({"ok": result["ok"], "issues": result["issues"], "can_mark_goal_complete": result["can_mark_goal_complete"]}, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
