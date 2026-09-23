#!/usr/bin/env python3
"""Verify the SCID as-of quarantined neutral-target execution packet."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_ASOF_NEUTRAL_TARGET"
ROUTE_ID = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET"
EVIDENCE_CLASS = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_ONLY"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
FORBIDDEN_RAW_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
HORIZONS = [1, 4, 16, 32]
EXPECTED_COUNTS = {
    "candidate_rows": 3014,
    "bar_rows": 7567,
    "sealed_rows": 2432,
    "stress_rows": 582,
    "discovery_exclusions": 365,
    "denominator_groups": 7,
}

REQUIRED_JSON = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
    f"{PREFIX}_PREREQUISITE_ACCEPTANCE_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_PRE_TARGET_FREEZE_PACKET_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_HASH_BINDING_{DATE_TAG}.json",
    f"{PREFIX}_DESCRIPTOR_FREEZE_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_AGGREGATE_DISTRIBUTION_MATRIX_{DATE_TAG}.json",
    f"{PREFIX}_PARTITION_SYMBOL_SESSION_MATRIX_{DATE_TAG}.json",
    f"{PREFIX}_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_BASELINE_CONTROL_READINESS_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_FAILURE_ANATOMY_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
]
REQUIRED_OTHER = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
    f"{PREFIX}_ROW_RESULTS_{DATE_TAG}.jsonl",
    f"{PREFIX}_NOT_COMPUTABLE_LEDGER_{DATE_TAG}.jsonl",
    f"{PREFIX}_INTERPRETATION_LIMITS_{DATE_TAG}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
    "build_scid_asof_neutral_target_execution_packet_2026_05_12.py",
    "verify_scid_asof_neutral_target_execution_packet_2026_05_12.py",
    "test_scid_asof_neutral_target_execution_packet_2026_05_12.py",
]
NEXT_G12_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
)


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                yield line_number, json.loads(line)


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def refresh_manifest_with_verification_result() -> None:
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    if not manifest_path.exists() or not RESULT_PATH.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = [
        item for item in manifest.get("artifacts", []) if item.get("path") != rel(RESULT_PATH)
    ]
    artifacts.append(
        {
            "path": rel(RESULT_PATH),
            "sha256": sha256_file(RESULT_PATH),
            "size_bytes": RESULT_PATH.stat().st_size,
        }
    )
    artifacts.sort(key=lambda item: item["path"])
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    false_keys = [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "strategy_result_scoring_opened",
        "changes_live_trading_behavior",
        "credentials_touched",
        "opens_ai_api",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_live_restart",
        "opens_paid_or_vendor_access",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
    ]
    return (
        payload.get("route_id") == ROUTE_ID
        and payload.get("evidence_class") == EVIDENCE_CLASS
        and payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and payload.get("neutral_target_behavior_opened") is True
        and all(payload.get(key) is False for key in false_keys)
    )


def forbidden_matrix_labels(payload: Any) -> list[str]:
    forbidden = {"win_rate", "expectancy", "pnl", "profit_factor", "strategy_edge", "edge", "alpha", "pass_rate"}
    allowed_exact = {"positive_return_fraction_not_win_rate"}
    issues: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).lower()
                if lowered not in allowed_exact and lowered in forbidden:
                    issues.append(f"{path}.{key}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "matrix")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true", help="do not rewrite the verification result")
    args = parser.parse_args()

    issues: list[str] = []
    checks: dict[str, bool] = {}
    required_paths = [ROUTE_DIR / name for name in REQUIRED_JSON + REQUIRED_OTHER] + [NEXT_G12_PROMPT]
    checks["required_files_exist"] = all(path.exists() for path in required_paths)
    if not checks["required_files_exist"]:
        issues.append(f"missing required files: {[rel(path) for path in required_paths if not path.exists()]}")

    parsed: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_JSON:
        path = ROUTE_DIR / name
        if path.exists():
            try:
                parsed[name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(f"json parse failed for {rel(path)}: {exc}")
    checks["json_parse_ok"] = not any(issue.startswith("json parse failed") for issue in issues)

    row_results_path = ROUTE_DIR / f"{PREFIX}_ROW_RESULTS_{DATE_TAG}.jsonl"
    not_path = ROUTE_DIR / f"{PREFIX}_NOT_COMPUTABLE_LEDGER_{DATE_TAG}.jsonl"
    terminal_keys: Counter[tuple[str, str, int]] = Counter()
    row_result_count = 0
    not_count = 0
    target_hash_missing = 0
    safe_flag_bad = 0
    families_seen: set[str] = set()
    horizons_seen: set[int] = set()
    for path, kind in [(row_results_path, "row"), (not_path, "not")]:
        if not path.exists():
            continue
        try:
            for _, row in iter_jsonl(path):
                key = (row["candidate_input_row_id"], row["target_family_id"], int(row["horizon_m15_bars"]))
                terminal_keys[key] += 1
                families_seen.add(row["target_family_id"])
                horizons_seen.add(int(row["horizon_m15_bars"]))
                if "target_row_hash" not in row:
                    target_hash_missing += 1
                if not safe_flags_closed(row):
                    safe_flag_bad += 1
                if kind == "row":
                    row_result_count += 1
                else:
                    not_count += 1
        except Exception as exc:  # noqa: BLE001 - verifier reports exact parse failure
            issues.append(f"jsonl parse failed for {rel(path)}: {exc}")
    checks["jsonl_parse_ok"] = not any(issue.startswith("jsonl parse failed") for issue in issues)

    source = parsed.get(f"{PREFIX}_SOURCE_HASH_BINDING_{DATE_TAG}.json", {})
    freeze = parsed.get(f"{PREFIX}_PRE_TARGET_FREEZE_PACKET_{DATE_TAG}.json", {})
    desc = parsed.get(f"{PREFIX}_DESCRIPTOR_FREEZE_LEDGER_{DATE_TAG}.json", {})
    aggregate = parsed.get(f"{PREFIX}_AGGREGATE_DISTRIBUTION_MATRIX_{DATE_TAG}.json", {})
    concentration = parsed.get(f"{PREFIX}_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json", {})
    completion = parsed.get(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", {})
    manifest = parsed.get(f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", {})
    prerequisite = parsed.get(f"{PREFIX}_PREREQUISITE_ACCEPTANCE_LEDGER_{DATE_TAG}.json", {})

    checks["safe_flags_closed"] = all(safe_flags_closed(payload) for payload in parsed.values()) and safe_flag_bad == 0
    checks["source_hashes_match"] = all(
        item.get("sha256") == sha256_file(ROOT / item["path"])
        for item in source.get("source_artifacts", [])
        if item.get("exists")
    )
    checks["manifest_input_hashes_match"] = all(source.get("manifest_hash_reconciliation", {}).values())
    checks["prerequisites_accepted"] = all(prerequisite.get("acceptance_checks", {}).values())
    checks["pre_target_freeze_complete"] = (
        freeze.get("candidate_row_count") == EXPECTED_COUNTS["candidate_rows"]
        and freeze.get("bar_row_count") == EXPECTED_COUNTS["bar_rows"]
        and freeze.get("partition_counts", {}).get("SEALED_VALIDATION_CANDIDATE_DESIGN") == EXPECTED_COUNTS["sealed_rows"]
        and freeze.get("partition_counts", {}).get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN") == EXPECTED_COUNTS["stress_rows"]
        and freeze.get("denominator_group_count") == EXPECTED_COUNTS["denominator_groups"]
        and freeze.get("discovery_exclusion_count") == EXPECTED_COUNTS["discovery_exclusions"]
        and freeze.get("target_families") == TARGET_FAMILIES
        and freeze.get("horizons_m15_bars") == HORIZONS
        and freeze.get("pre_target_freeze_emitted_before_target_computation") is True
    )
    checks["descriptor_rows_complete"] = desc.get("descriptor_freeze_status") == "FROZEN_BEFORE_TARGET_COMPUTATION" and desc.get(
        "descriptor_row_count"
    ) == EXPECTED_COUNTS["candidate_rows"]
    expected_terminal = EXPECTED_COUNTS["candidate_rows"] * len(TARGET_FAMILIES) * len(HORIZONS)
    checks["terminal_grid_complete"] = (
        len(terminal_keys) == expected_terminal
        and all(count == 1 for count in terminal_keys.values())
        and row_result_count + not_count == expected_terminal
        and families_seen == set(TARGET_FAMILIES)
        and horizons_seen == set(HORIZONS)
        and target_hash_missing == 0
    )
    checks["partition_counts_exact"] = concentration.get("partition_counts") == {
        "SEALED_VALIDATION_CANDIDATE_DESIGN": EXPECTED_COUNTS["sealed_rows"],
        "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": EXPECTED_COUNTS["stress_rows"],
    }
    checks["denominator_groups_exact"] = concentration.get("denominator_group_count") == EXPECTED_COUNTS["denominator_groups"]
    checks["no_forbidden_secondary_denominator_candidates"] = (
        concentration.get("forbidden_secondary_denominator_candidate_count") == 0
    )
    checks["aggregate_matrices_present"] = bool(aggregate.get("matrices")) and bool(aggregate.get("availability_summary"))
    checks["aggregate_matrix_forbidden_labels_absent"] = not forbidden_matrix_labels(aggregate)
    checks["completion_passes"] = completion.get("can_mark_goal_complete") is True
    checks["manifest_has_required_artifacts"] = manifest.get("artifact_count", 0) >= 20
    checks["next_g12_prompt_exists"] = NEXT_G12_PROMPT.exists()
    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    checks["route_has_no_raw_blobs"] = not any(path.suffix.lower() in FORBIDDEN_RAW_EXTENSIONS for path in route_files)
    checks["forbidden_live_surface_files_not_in_route"] = not any(
        rel(path).startswith(("src/", "prompts/", "config/", "scripts/canary")) for path in route_files
    )

    for key, value in checks.items():
        if not value:
            issues.append(f"check failed: {key}")

    output = {
        "route_id": ROUTE_ID,
        "schema_version": "scid_asof_quarantined_neutral_target_execution_packet_verifier_v1",
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "neutral_target_behavior_opened": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "strategy_result_scoring_opened": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "row_result_count": row_result_count,
        "not_computable_count": not_count,
        "terminal_combination_count": row_result_count + not_count,
        "expected_terminal_combination_count": expected_terminal,
        "git_status_short_informational": git_status_short(),
        "can_mark_goal_complete_after_commit_and_closeout": not issues,
    }
    if not args.no_write:
        RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refresh_manifest_with_verification_result()
    print(json.dumps({"ok": output["ok"], "issues": issues}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
