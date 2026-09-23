from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 4
EXPECTED_MALFORMED_ROWS = 39
EXPECTED_SELECTOR_DOSSIER_ROWS = 231
EXPECTED_MECHANICAL_SELECTOR_SCOPE_ROWS = 221
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
        issues.append("summary_rows_mismatch")
    if summary.get("malformed_response_rows") != EXPECTED_MALFORMED_ROWS:
        issues.append(f"malformed_response_rows_unexpected:{summary.get('malformed_response_rows')}")
    if summary.get("selector_dossier_rows") != EXPECTED_SELECTOR_DOSSIER_ROWS:
        issues.append(f"selector_dossier_rows_unexpected:{summary.get('selector_dossier_rows')}")
    if summary.get("mechanical_selector_scope_draft_ready_for_separate_review_rows") != (
        EXPECTED_MECHANICAL_SELECTOR_SCOPE_ROWS
    ):
        issues.append(
            "mechanical_selector_scope_draft_ready_for_separate_review_rows_unexpected:"
            f"{summary.get('mechanical_selector_scope_draft_ready_for_separate_review_rows')}"
        )
    if summary.get("manual_canary_fixture_rows", 0) <= 0:
        issues.append(f"manual_canary_fixture_rows_not_positive:{summary.get('manual_canary_fixture_rows')}")

    for key in (
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "production_change_opened_now_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    expected_surfaces = {
        "ai_runtime_config",
        "malformed_response_monitoring",
        "manual_canary_fixture_guardrail",
        "mechanical_selector_ai_narrowing_dossier",
    }
    if set(summary.get("audit_surface_counts") or {}) != expected_surfaces:
        issues.append(f"audit_surface_counts_unexpected:{summary.get('audit_surface_counts')}")
    for row in rows:
        row_id = row.get("ai_architecture_audit_row_id")
        if row.get("paid_api_or_vendor_call"):
            issues.append(f"paid_api_or_vendor_call:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted"):
            issues.append(f"runtime_candidate_use_permitted:{row_id}")
            break
        if row.get("production_change_opened_now"):
            issues.append(f"production_change_opened_now:{row_id}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("ai_architecture_audit_available") is not True:
        issues.append("ai_architecture_audit_not_available")
    if effect.get("paid_api_or_vendor_call") is not False:
        issues.append("effect_paid_api_or_vendor_call_claimed")
    if effect.get("production_change_opened_now") is not False:
        issues.append("effect_production_change_opened")
    if effect.get("live_ai_runtime_change_now") is not False:
        issues.append("effect_live_ai_runtime_change_claimed")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    result = {
        "route_id": "MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "audit_rows": len(rows),
        "malformed_response_rows": summary.get("malformed_response_rows"),
        "manual_canary_fixture_rows": summary.get("manual_canary_fixture_rows"),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": summary.get(
            "mechanical_selector_scope_draft_ready_for_separate_review_rows"
        ),
        "paid_api_or_vendor_call_rows": summary.get("paid_api_or_vendor_call_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
        "production_change_opened_now_rows": summary.get("production_change_opened_now_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    if result["manifest_output_count"] != EXPECTED_MANIFEST_OUTPUT_COUNT:
        result["issues"].append(f"manifest_output_count_unexpected:{result['manifest_output_count']}")
        result["ok"] = False
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
