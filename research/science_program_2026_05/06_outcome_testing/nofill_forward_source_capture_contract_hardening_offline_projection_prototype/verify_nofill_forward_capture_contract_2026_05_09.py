#!/usr/bin/env python3
"""Verify the NOFILL forward source-capture contract/prototype lane."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import build_nofill_forward_capture_contract_2026_05_09 as builder


DATE = builder.DATE
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
RESULT_JSON = OUT_DIR / builder.VERIFICATION_RESULT_NAME

REQUIRED_FILES = (
    builder.REQUIRED_MD
    + builder.REQUIRED_JSON
    + [
        builder.PROTOTYPE_ROWS_NAME,
        builder.VERIFICATION_RESULT_NAME,
        *builder.PARSER_FILES,
    ]
)

ALLOWED_DIR_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
)

TEXT_HASH_FALLBACK_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"}


def as_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def sha256_file(path: str | Path) -> str | None:
    full = as_path(path)
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_normalized_file(path: str | Path) -> str | None:
    full = as_path(path)
    if not full.exists() or not full.is_file():
        return None
    if full.suffix.lower() not in TEXT_HASH_FALLBACK_SUFFIXES:
        return None
    data = full.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def entry_allows_lf_normalized_fallback(entry: dict[str, Any]) -> bool:
    """Only explicit text artifacts may use LF-normalized hash portability."""
    path = as_path(entry.get("path", ""))
    return path.suffix.lower() in TEXT_HASH_FALLBACK_SUFFIXES


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{name}:{line_no}:{exc}") from exc
    return rows


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return sorted(paths)


def control_flags_ok(data: dict[str, Any], file_name: str, failures: list[dict[str, Any]]) -> None:
    if data.get("promotion_verdict") != builder.PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": file_name, "value": data.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if data.get(flag) is not False:
            failures.append({"check": "closed_flag", "file": file_name, "flag": flag, "value": data.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if flag in data and data.get(flag) is not False:
            failures.append({"check": "closed_route", "file": file_name, "flag": flag, "value": data.get(flag)})


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing_files = [name for name in REQUIRED_FILES if name == builder.VERIFICATION_RESULT_NAME or not (OUT_DIR / name).exists()]
    missing_files = [name for name in missing_files if name != builder.VERIFICATION_RESULT_NAME]
    if missing_files:
        failures.append({"check": "required_files", "missing": missing_files})

    parsed: dict[str, Any] = {}
    for name in builder.REQUIRED_JSON:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, data in parsed.items():
        if isinstance(data, dict):
            control_flags_ok(data, name, failures)

    for name in builder.REQUIRED_MD:
        path = OUT_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})
        for forbidden_literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if forbidden_literal in text:
                failures.append({"check": "forbidden_true_literal", "file": name, "literal": forbidden_literal})

    rows: list[dict[str, Any]] = []
    if (OUT_DIR / builder.PROTOTYPE_ROWS_NAME).exists():
        try:
            rows = load_jsonl(builder.PROTOTYPE_ROWS_NAME)
        except AssertionError as exc:
            failures.append({"check": "jsonl_parse", "error": str(exc)})

    if len(rows) != 298:
        failures.append({"check": "prototype_row_count", "expected": 298, "actual": len(rows)})
    family_counts = Counter(row.get("v3_terminal_family") for row in rows)
    if dict(family_counts) != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        failures.append({"check": "family_counts", "actual": dict(family_counts)})
    if sum(bool(row.get("row_level_denominator_member")) for row in rows) != 225:
        failures.append({"check": "row_level_denominator"})
    if sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows) != 182:
        failures.append({"check": "duplicate_key_denominator"})
    if sum(bool(row.get("duplicate_group_id_count_member")) for row in rows) != 139:
        failures.append({"check": "duplicate_group_denominator"})
    for row in rows:
        for forbidden_key in builder.FORBIDDEN_RAW_FIELD_NAMES:
            if forbidden_key in row:
                failures.append({"check": "forbidden_key_in_prototype", "packet_row_id": row.get("packet_row_id"), "key": forbidden_key})
                break
        for flag in ("validation_safe", "outcome_review_opened", "live_effect", "opens_result_scoring", "opens_live_wiring"):
            if row.get(flag) is not False:
                failures.append({"check": "prototype_row_open_flag", "packet_row_id": row.get("packet_row_id"), "flag": flag})
        if row.get("contract_acceptance_state") != "SOURCE_CONTROL_CONTRACT_FROZEN_G12_AUDIT_PENDING":
            failures.append({"check": "prototype_contract_gate", "packet_row_id": row.get("packet_row_id")})

    contract = parsed.get(f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.json", {})
    if contract.get("field_count", 0) < 55:
        failures.append({"check": "contract_field_count", "actual": contract.get("field_count")})
    contract_fields = {row.get("field_name") for row in contract.get("fields", [])}
    for required in (
        "capture_write_completed_at_utc",
        "capture_clock_skew_ms",
        "pending_order_mode_source_safe",
        "mt5_order_ticket_redaction_status",
        "entry_touch_spread_value_source_safe",
        "same_tick_same_bar_ambiguity_status",
        "nofill_duplicate_key_sha256",
        "forbidden_field_scan_status",
    ):
        if required not in contract_fields:
            failures.append({"check": "missing_contract_field", "field": required})
    if contract.get("future_live_logger_wiring_gate") != "YES_GATED_BEHIND_G12_ACCEPTANCE_AND_SEPARATE_OWNER_APPROVAL":
        failures.append({"check": "live_wiring_gate_not_explicit"})

    vocabulary = parsed.get(f"NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_{DATE}.json", {})
    expected_vocab = {
        "MISSING_SOURCE_FIELD",
        "NOT_APPLICABLE",
        "NOT_OBSERVED_SOURCE_SAFE",
        "SOURCE_IMPOSSIBLE",
        "REDACTED",
        "NOT_YET_CAPTURED",
        "FORBIDDEN_FAIL_CLOSED",
    }
    if set(vocabulary.get("canonical_groups", {})) != expected_vocab:
        failures.append({"check": "missing_status_vocab_groups", "actual": sorted(vocabulary.get("canonical_groups", {}))})

    fixture_manifest = parsed.get(f"NOFILL_FORWARD_FIXTURE_MANIFEST_{DATE}.json", {})
    categories = {item.get("category") for item in fixture_manifest.get("fixtures", [])}
    missing_categories = sorted(set(fixture_manifest.get("required_fixture_categories", [])) - categories)
    if missing_categories:
        failures.append({"check": "fixture_category_coverage", "missing": missing_categories})
    for item in fixture_manifest.get("fixtures", []):
        path = as_path(item.get("path", ""))
        if not path.exists():
            failures.append({"check": "fixture_missing", "path": item.get("path")})
            continue
        try:
            fixture = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append({"check": "fixture_json_parse", "path": item.get("path"), "error": str(exc)})
            continue
        if fixture.get("category") in {"redacted_ticket_row", "forbidden_field_examples"}:
            text = json.dumps(fixture, sort_keys=True)
            for forbidden_value in ("SECRET", "09", "ticket-"):
                if forbidden_value in text:
                    failures.append({"check": "raw_value_material_in_fixture", "path": item.get("path"), "value": forbidden_value})
            if "raw_value_material_included\": true" in text:
                failures.append({"check": "raw_value_marked_included", "path": item.get("path")})

    denom = parsed.get(f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{DATE}.json", {})
    if denom.get("status") != "PASS":
        failures.append({"check": "denominator_audit", "status": denom.get("status"), "issues": denom.get("issues")})
    no_leak = parsed.get(f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.json", {})
    if no_leak.get("status") != "PASS":
        failures.append({"check": "no_leak_audit", "status": no_leak.get("status"), "issues": no_leak.get("issues")})
    if no_leak.get("redaction_controls", {}).get("raw_ticket_values_emitted") is not False:
        failures.append({"check": "raw_ticket_values_emitted"})
    if no_leak.get("redaction_controls", {}).get("raw_ticket_values_hashed") is not False:
        failures.append({"check": "raw_ticket_values_hashed"})

    source_manifest = parsed.get(f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json", {})
    for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        entries = source_manifest.get(group)
        if not isinstance(entries, list) or not entries:
            failures.append({"check": "manifest_group_missing", "group": group})
            continue
        for entry in entries:
            if entry.get("exists") is not True:
                failures.append({"check": "manifest_entry_missing", "group": group, "path": entry.get("path")})
                continue
            recomputed = sha256_file(entry.get("path", ""))
            if entry.get("sha256") and recomputed != entry.get("sha256"):
                if entry.get("strict_hash_recompute") is False:
                    warnings.append(
                        {
                            "check": "mutable_context_hash_drift",
                            "group": group,
                            "path": entry.get("path"),
                            "expected": entry.get("sha256"),
                            "actual": recomputed,
                            "hash_policy": entry.get("hash_policy"),
                        }
                    )
                    continue
                lf_recomputed = sha256_lf_normalized_file(entry.get("path", ""))
                if (
                    entry_allows_lf_normalized_fallback(entry)
                    and entry.get("sha256_lf_normalized")
                    and lf_recomputed == entry.get("sha256_lf_normalized")
                ):
                    warnings.append(
                        {
                            "check": "text_lf_normalized_hash_match",
                            "group": group,
                            "path": entry.get("path"),
                            "expected_raw": entry.get("sha256"),
                            "actual_raw": recomputed,
                            "expected_lf_normalized": entry.get("sha256_lf_normalized"),
                            "actual_lf_normalized": lf_recomputed,
                            "hash_policy": "strict_lf_normalized_text_accepted",
                        }
                    )
                    continue
                failures.append({"check": "hash_recompute", "group": group, "path": entry.get("path"), "expected": entry.get("sha256"), "actual": recomputed})
                break

    completion = parsed.get(f"NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.json", {})
    if completion.get("future_live_logger_wiring_lane_still_gated") is not True:
        failures.append({"check": "completion_live_gate"})
    if completion.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "completion_status", "value": completion.get("can_mark_goal_complete_after_verification_and_commit")})
    weak = completion.get("missing_incomplete_or_weak_requirements", [])
    if weak:
        failures.append({"check": "completion_weak_requirements", "value": weak})

    dirty_paths = git_status_paths()
    forbidden_live_dirty = [path for path in dirty_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_scope_dirty = [path for path in dirty_paths if not path.startswith(ALLOWED_DIR_PREFIXES)]
    if forbidden_live_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_live_dirty})
    if outside_scope_dirty:
        warnings.append({"check": "outside_scope_dirty_informational", "paths": outside_scope_dirty})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.CONTROL_FLAGS,
        "failures": failures,
        "warnings": warnings,
        "required_file_count": len(REQUIRED_FILES),
        "json_files_parsed": sorted(parsed),
        "prototype_row_count": len(rows),
        "family_counts": dict(family_counts),
        "dirty_paths_reviewed": dirty_paths,
        "future_live_logger_wiring_lane_still_gated": True,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
