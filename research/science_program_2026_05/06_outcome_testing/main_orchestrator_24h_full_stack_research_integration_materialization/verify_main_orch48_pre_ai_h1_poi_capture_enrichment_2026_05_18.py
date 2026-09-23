from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 5
EXPECTED_PRE_AI_SKIP_ROWS = 246
EXPECTED_SKIP_ROWS_MISSING_DIRECTIONAL_DETAIL = 246
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


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    effect = summary.get("implementation_effect") or {}
    source_gap = summary.get("source_gap_reference") or {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"rows_unexpected:{len(rows)}")
    if summary.get("status") != "OK_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_MATERIALIZED":
        issues.append(f"summary_status_unexpected:{summary.get('status')}")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_active_not_true:{summary.get('runtime_halt_active')}")
    if source_gap.get("pre_ai_skip_rows") != EXPECTED_PRE_AI_SKIP_ROWS:
        issues.append(f"pre_ai_skip_rows_unexpected:{source_gap.get('pre_ai_skip_rows')}")
    if source_gap.get("skip_rows_missing_directional_poi_detail") != EXPECTED_SKIP_ROWS_MISSING_DIRECTIONAL_DETAIL:
        issues.append(
            "skip_rows_missing_directional_poi_detail_unexpected:"
            f"{source_gap.get('skip_rows_missing_directional_poi_detail')}"
        )
    if summary.get("capture_enrichment_rows") != EXPECTED_ROWS:
        issues.append(f"capture_enrichment_rows_unexpected:{summary.get('capture_enrichment_rows')}")

    required_statuses = {
        "CAPTURE_GAP_IDENTIFIED_FROM_JOIN_ARTIFACT",
        "OBSERVATION_HELPER_WIRED",
        "LOGGER_CAPTURE_FIELDS_WIRED",
        "SKIP_CALLSITE_ENRICHED",
        "FOCUSED_TESTS_PASSED",
    }
    statuses = {str(row.get("status")) for row in rows}
    if statuses != required_statuses:
        issues.append(f"statuses_unexpected:{sorted(statuses)}")

    for row in rows:
        row_id = row.get("capture_enrichment_row_id")
        if row.get("runtime_decision_effect"):
            issues.append(f"runtime_decision_effect_claimed:{row_id}")
        for key, value in row.items():
            if key.endswith("_present") or key.endswith("_wired") or key.startswith("callsite_"):
                if value is not True:
                    issues.append(f"{key}_not_true:{row_id}:{value}")

    for key in (
        "gate_config_change_now",
        "runtime_decision_effect",
        "production_change_opened_now",
        "runtime_candidate_use_permitted",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")
    if effect.get("future_candidate_features_capture_enriched") is not True:
        issues.append(
            "effect_future_candidate_features_capture_enriched_not_true:"
            f"{effect.get('future_candidate_features_capture_enriched')}"
        )

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

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "pre_ai_skip_rows": source_gap.get("pre_ai_skip_rows"),
        "skip_rows_missing_directional_poi_detail": source_gap.get(
            "skip_rows_missing_directional_poi_detail"
        ),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
