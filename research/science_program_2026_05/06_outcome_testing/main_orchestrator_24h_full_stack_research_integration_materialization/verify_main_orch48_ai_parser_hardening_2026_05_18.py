from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_PARSER_HARDENING"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.utils.validation import strip_json_fences


LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 5
EXPECTED_MALFORMED_ROWS = 39
EXPECTED_PARSER_SCOPE_ROWS = 2
EXPECTED_TEST_COVERAGE_ROWS = 4
EXPECTED_MANIFEST_OUTPUT_COUNT = 2


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def resolve_display_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO / path


def parser_smoke_issues() -> list[str]:
    issues: list[str] = []
    extra_object = '{"decision": "NO_TRADE"}\n{"note": "extra"}'
    if json.loads(strip_json_fences(extra_object)) != {"decision": "NO_TRADE"}:
        issues.append("parser_smoke_extra_object_not_recovered")

    brace_preamble = 'analysis {not json}\n{"decision": "NO_TRADE", "reason": "literal } brace"}\n{"note": true}'
    parsed = json.loads(strip_json_fences(brace_preamble))
    if parsed.get("reason") != "literal } brace":
        issues.append("parser_smoke_brace_preamble_or_string_brace_failed")

    flat_refusal = "Sorry, I can't produce JSON right now."
    if strip_json_fences(flat_refusal) != flat_refusal:
        issues.append("parser_smoke_flat_refusal_changed")
    return issues


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('rows')}:{len(rows)}")
    if summary.get("malformed_response_rows") != EXPECTED_MALFORMED_ROWS:
        issues.append(f"malformed_response_rows_unexpected:{summary.get('malformed_response_rows')}")
    if summary.get("parser_hardening_scope_rows") != EXPECTED_PARSER_SCOPE_ROWS:
        issues.append(f"parser_hardening_scope_rows_unexpected:{summary.get('parser_hardening_scope_rows')}")
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_COVERAGE_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")

    expected_surfaces = {
        "ai_architecture_audit_inheritance",
        "focused_parser_test_coverage",
        "malformed_response_parser_hardening_trigger",
        "primary_analyzer_parser_path",
        "shared_strip_json_fences_patch",
    }
    if set(summary.get("audit_surface_counts") or {}) != expected_surfaces:
        issues.append(f"audit_surface_counts_unexpected:{summary.get('audit_surface_counts')}")

    if summary.get("repo_runtime_parser_code_changed_rows") != 1:
        issues.append(f"repo_runtime_parser_code_changed_rows_unexpected:{summary.get('repo_runtime_parser_code_changed_rows')}")
    if summary.get("runtime_parser_behavior_effect_if_runtime_reenabled_rows") != 2:
        issues.append(
            "runtime_parser_behavior_effect_if_runtime_reenabled_rows_unexpected:"
            f"{summary.get('runtime_parser_behavior_effect_if_runtime_reenabled_rows')}"
        )
    for key in ("paid_api_or_vendor_call_rows", "broker_operation_rows", "runtime_candidate_use_permitted_rows"):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("shared_parser_hardened") is not True:
        issues.append("effect_shared_parser_not_hardened")
    if effect.get("primary_analyzer_uses_hardened_shared_parser") is not True:
        issues.append("effect_primary_analyzer_not_using_hardened_parser")
    if effect.get("runtime_parser_behavior_effect_if_runtime_reenabled") is not True:
        issues.append("effect_runtime_parser_behavior_not_recorded")
    for key in ("paid_api_or_vendor_call", "broker_operation", "runtime_trading_or_live_broker_effect", "runtime_candidate_use_permitted"):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    for row in rows:
        boundary = row.get("research_boundary") or {}
        row_id = row.get("ai_parser_hardening_row_id")
        for key in ("paid_api_or_vendor_call", "broker_operation", "runtime_trading_or_live_broker_effect", "runtime_candidate_use_permitted"):
            if boundary.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUT_COUNT:
        issues.append(f"manifest_output_count_unexpected:{len(output_by_name)}")

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    issues.extend(parser_smoke_issues())

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "malformed_response_rows": summary.get("malformed_response_rows"),
        "parser_hardening_scope_rows": summary.get("parser_hardening_scope_rows"),
        "expected_test_names_covered_rows": summary.get("expected_test_names_covered_rows"),
        "repo_runtime_parser_code_changed_rows": summary.get("repo_runtime_parser_code_changed_rows"),
        "paid_api_or_vendor_call_rows": summary.get("paid_api_or_vendor_call_rows"),
        "broker_operation_rows": summary.get("broker_operation_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
