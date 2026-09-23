from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 231
EXPECTED_STATUS_COUNTS = {
    "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY": 199,
    "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST": 22,
    "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED": 10,
}
EXPECTED_MECHANICAL_SCOPE_ROWS = 221
EXPECTED_BLOCKLIST_ROWS = 32
EXPECTED_EVENT_ROWS = 9266
EXPECTED_REGISTRY_MATCH_ROWS = 55646
EXPECTED_IMPLEMENT_READY_CANDIDATES = 1597
EXPECTED_CAPACITY_BLOCKED_CANDIDATES = 151
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
    if summary.get("production_change_dossier_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(
            "production_change_dossier_status_counts_unexpected:"
            f"{summary.get('production_change_dossier_status_counts')}"
        )
    if summary.get("mechanical_selector_scope_draft_ready_for_separate_review_rows") != EXPECTED_MECHANICAL_SCOPE_ROWS:
        issues.append(
            "mechanical_selector_scope_draft_ready_for_separate_review_rows_unexpected:"
            f"{summary.get('mechanical_selector_scope_draft_ready_for_separate_review_rows')}"
        )
    if summary.get("capacity_blocked_selector_blocklist_required_rows") != EXPECTED_BLOCKLIST_ROWS:
        issues.append(
            "capacity_blocked_selector_blocklist_required_rows_unexpected:"
            f"{summary.get('capacity_blocked_selector_blocklist_required_rows')}"
        )
    if summary.get("event_rows") != EXPECTED_EVENT_ROWS:
        issues.append(f"event_rows_unexpected:{summary.get('event_rows')}")
    if summary.get("registry_match_rows") != EXPECTED_REGISTRY_MATCH_ROWS:
        issues.append(f"registry_match_rows_unexpected:{summary.get('registry_match_rows')}")
    if summary.get("implementation_ready_candidate_rows") != EXPECTED_IMPLEMENT_READY_CANDIDATES:
        issues.append(f"implementation_ready_candidate_rows_unexpected:{summary.get('implementation_ready_candidate_rows')}")
    if summary.get("capacity_blocked_candidate_rows") != EXPECTED_CAPACITY_BLOCKED_CANDIDATES:
        issues.append(f"capacity_blocked_candidate_rows_unexpected:{summary.get('capacity_blocked_candidate_rows')}")

    for key in (
        "binding_repair_candidate_rows",
        "binding_repair_registry_match_rows",
        "production_change_opened_now_rows",
        "live_selector_change_now_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    if summary.get("separate_production_change_review_required_rows") != EXPECTED_ROWS:
        issues.append(
            "separate_production_change_review_required_rows_unexpected:"
            f"{summary.get('separate_production_change_review_required_rows')}"
        )
    if summary.get("owner_approval_required_before_runtime_enablement_rows") != EXPECTED_ROWS:
        issues.append(
            "owner_approval_required_before_runtime_enablement_rows_unexpected:"
            f"{summary.get('owner_approval_required_before_runtime_enablement_rows')}"
        )

    for row in rows:
        row_id = row.get("production_change_dossier_row_id")
        if row.get("production_change_opened_now"):
            issues.append(f"production_change_opened_now:{row_id}")
            break
        if row.get("live_selector_change_now"):
            issues.append(f"live_selector_change_now:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted"):
            issues.append(f"runtime_candidate_use_permitted:{row_id}")
            break
        if row.get("candidate_use_allowed_now"):
            issues.append(f"candidate_use_allowed_now:{row_id}")
            break
        if not row.get("separate_production_change_review_required"):
            issues.append(f"separate_review_not_required:{row_id}")
            break
        if not row.get("owner_approval_required_before_runtime_enablement"):
            issues.append(f"owner_approval_not_required:{row_id}")
            break
        if row.get("production_change_dossier_status") not in EXPECTED_STATUS_COUNTS:
            issues.append(f"unexpected_dossier_status:{row_id}:{row.get('production_change_dossier_status')}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("production_change_dossier_draft_available") is not True:
        issues.append("production_change_dossier_draft_not_available")
    if effect.get("default_off_mechanical_selector_scope_rows_for_review") != EXPECTED_MECHANICAL_SCOPE_ROWS:
        issues.append(
            "effect_default_off_mechanical_selector_scope_rows_for_review_unexpected:"
            f"{effect.get('default_off_mechanical_selector_scope_rows_for_review')}"
        )
    if effect.get("production_change_opened_now") is not False:
        issues.append("effect_production_change_opened")
    if effect.get("runtime_trading_or_live_broker_effect") is not False:
        issues.append("runtime_trading_or_live_broker_effect_claimed")

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
        "route_id": "MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PRODUCTION_CHANGE_DOSSIER",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "dossier_rows": len(rows),
        "production_change_dossier_status_counts": summary.get("production_change_dossier_status_counts"),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": summary.get(
            "mechanical_selector_scope_draft_ready_for_separate_review_rows"
        ),
        "capacity_blocked_selector_blocklist_required_rows": summary.get(
            "capacity_blocked_selector_blocklist_required_rows"
        ),
        "production_change_opened_now_rows": summary.get("production_change_opened_now_rows"),
        "live_selector_change_now_rows": summary.get("live_selector_change_now_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
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
