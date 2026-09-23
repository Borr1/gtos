#!/usr/bin/env python3
"""Verify the FPB source-expansion packet without running validation."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
BUILDER_PATH = ROUTE_DIR / "build_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"
DATE_TAG = "2026-05-11"
VERIFY_BASE = f"FPB_SOURCE_EXPANSION_VERIFICATION_RESULT_{DATE_TAG}"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("fpb_source_expansion_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder at {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_condition(checks: list[dict[str, Any]], name: str, passed: bool, evidence: Any) -> None:
    checks.append({"check": name, "status": "PASS" if passed else "FAIL", "evidence": evidence})


def main() -> int:
    builder = load_builder()
    checks: list[dict[str, Any]] = []

    manifest_path = ROUTE_DIR / f"{builder.ARTIFACTS['manifest']}.json"
    completion_path = ROUTE_DIR / f"{builder.ARTIFACTS['completion']}.json"
    native_path = ROUTE_DIR / f"{builder.ARTIFACTS['native_scid_pool']}.json"
    csv_path = ROUTE_DIR / f"{builder.ARTIFACTS['local_csv_triage']}.json"
    selected_path = ROUTE_DIR / f"{builder.ARTIFACTS['selected_source_coverage']}.json"
    baseline_path = ROUTE_DIR / f"{builder.ARTIFACTS['baseline_preservation']}.json"
    source_contract_path = ROUTE_DIR / f"{builder.ARTIFACTS['source_contract']}.json"

    required_paths = [
        manifest_path,
        completion_path,
        native_path,
        csv_path,
        selected_path,
        baseline_path,
        source_contract_path,
        builder.NEXT_G12_PROMPT,
        BUILDER_PATH,
        Path(__file__).resolve(),
        ROUTE_DIR / "test_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py",
    ]
    for path in required_paths:
        assert_condition(checks, f"exists:{rel(path)}", path.exists(), rel(path))

    manifest = load_json(manifest_path)
    completion = load_json(completion_path)
    native = load_json(native_path)
    csv_ledger = load_json(csv_path)
    selected = load_json(selected_path)
    baseline = load_json(baseline_path)
    source_contract = load_json(source_contract_path)

    for key, expected in builder.SAFE_FLAGS.items():
        if isinstance(expected, bool):
            assert_condition(checks, f"safe_flag_{key}", manifest.get(key) is expected, manifest.get(key))
    assert_condition(
        checks,
        "no_validation_execution_prompt_emitted",
        manifest.get("validation_execution_prompt_emitted") is False,
        manifest.get("validation_execution_prompt_emitted"),
    )
    assert_condition(
        checks,
        "g12_source_pool_audit_prompt_emitted",
        manifest.get("g12_source_pool_audit_prompt_emitted") is True,
        manifest.get("next_g12_prompt"),
    )
    assert_condition(
        checks,
        "completion_standard_satisfied",
        completion.get("completion_standard_satisfied") is True,
        completion.get("missing_incomplete_or_weak_requirements"),
    )

    source_selection = load_json(builder.INPUTS["source_selection"])
    selected_hashes = {
        row.get("source_sha256")
        for row in source_selection.get("selected_sources", [])
        if row.get("source_sha256")
    }
    native_candidates = native.get("accepted_native_scid_candidates", [])
    csv_candidates = csv_ledger.get("accepted_csv_candidates", [])
    candidate_rows = native_candidates + csv_candidates
    candidate_hashes = {row.get("source_sha256") for row in candidate_rows if row.get("source_sha256")}
    assert_condition(
        checks,
        "selected_hashes_excluded_from_candidate_pool",
        selected_hashes.isdisjoint(candidate_hashes),
        {"selected_count": len(selected_hashes), "candidate_count": len(candidate_hashes)},
    )
    assert_condition(
        checks,
        "selected_source_count_preserved",
        source_selection.get("selected_source_count") == 365 and len(selected_hashes) == 365,
        {"source_selection_count": source_selection.get("selected_source_count"), "selected_hashes": len(selected_hashes)},
    )
    assert_condition(
        checks,
        "candidate_pool_materialized",
        len(candidate_rows) > 0,
        {"native": len(native_candidates), "csv": len(csv_candidates)},
    )

    required_candidate_fields = [
        "source_sha256",
        "coverage_start_utc",
        "coverage_end_utc",
        "parser_asof_status",
        "no_leak_status",
        "duplicate_source_decision",
        "partition_assignment",
    ]
    missing_by_candidate = []
    for row in candidate_rows:
        missing = [field for field in required_candidate_fields if not row.get(field)]
        if row.get("partition_assignment") != "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED":
            missing.append("expected_partition_assignment")
        if missing:
            missing_by_candidate.append({"source": row.get("file_name") or row.get("absolute_path"), "missing": missing})
    assert_condition(checks, "candidate_required_fields", not missing_by_candidate, missing_by_candidate)

    baseline_controls = baseline.get("baseline_controls", [])
    assert_condition(
        checks,
        "adversarial_baselines_preserved",
        baseline_controls == builder.BASELINE_CONTROLS,
        baseline_controls,
    )
    assert_condition(
        checks,
        "source_contract_candidate_count_matches",
        source_contract.get("candidate_count") == len(candidate_rows),
        {"source_contract": source_contract.get("candidate_count"), "ledger": len(candidate_rows)},
    )

    raw_market_files = [
        path
        for path in ROUTE_DIR.iterdir()
        if path.suffix.lower() in {".csv", ".parquet", ".scid", ".dly"}
    ]
    assert_condition(
        checks,
        "no_raw_market_data_written_to_route",
        not raw_market_files,
        [rel(path) for path in raw_market_files],
    )

    all_pass = all(check["status"] == "PASS" for check in checks)
    payload = {
        "schema_version": "fpb_source_expansion_verification_v1",
        "route_id": builder.ROUTE_ID,
        "artifact_family": "verification_result",
        "generated_at_utc": now_utc(),
        **builder.SAFE_FLAGS,
        "verification_passed": all_pass,
        "terminal_decision": builder.TERMINAL_DECISION if all_pass else "VERIFICATION_FAILED",
        "check_count": len(checks),
        "checks": checks,
        "accepted_native_scid_candidate_count": len(native_candidates),
        "accepted_csv_candidate_count": len(csv_candidates),
        "g12_source_pool_audit_prompt": rel(builder.NEXT_G12_PROMPT),
    }

    json_path = ROUTE_DIR / f"{VERIFY_BASE}.json"
    md_path = ROUTE_DIR / f"{VERIFY_BASE}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# FPB Source Expansion Verification Result",
                "",
                f"- Route: `{builder.ROUTE_ID}`",
                f"- verification_passed: `{str(all_pass).lower()}`",
                f"- accepted_native_scid_candidate_count: `{len(native_candidates)}`",
                f"- accepted_csv_candidate_count: `{len(csv_candidates)}`",
                f"- validation_safe: `{str(builder.SAFE_FLAGS['validation_safe']).lower()}`",
                f"- outcome_review_opened: `{str(builder.SAFE_FLAGS['outcome_review_opened']).lower()}`",
                f"- live_effect: `{str(builder.SAFE_FLAGS['live_effect']).lower()}`",
                "",
                "## Failed Checks",
                "",
                "```json",
                json.dumps([check for check in checks if check["status"] == "FAIL"], indent=2, sort_keys=True),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"verification_passed": all_pass, "check_count": len(checks)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
