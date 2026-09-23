from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 5
EXPECTED_PATCHED_ROWS = 5
EXPECTED_FUTURE_CONTRACT_COMPLETE_ROWS = 1108
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
    if summary.get("patched_source_capture_ready_rows") != EXPECTED_PATCHED_ROWS:
        issues.append(f"patched_source_capture_ready_rows_unexpected:{summary.get('patched_source_capture_ready_rows')}")
    if summary.get("patch_not_found_rows") != 0:
        issues.append(f"patch_not_found_rows_nonzero:{summary.get('patch_not_found_rows')}")
    if summary.get("future_contract_complete_if_emitted_rows_inherited") != EXPECTED_FUTURE_CONTRACT_COMPLETE_ROWS:
        issues.append(
            "future_contract_complete_if_emitted_rows_inherited_unexpected:"
            f"{summary.get('future_contract_complete_if_emitted_rows_inherited')}"
        )

    for key in (
        "historical_slippage_rows_repaired",
        "historical_exact_r_repaired_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    expected_surfaces = {
        "trade_state_source_repair_identity_retention",
        "close_slippage_source_repair_identity_writer",
        "close_slippage_target_geometry_writer",
        "execution_close_slippage_forwarder",
        "focused_tests_cover_entry_and_close_identity",
    }
    seen_surfaces = {row.get("capture_surface") for row in rows}
    if seen_surfaces != expected_surfaces:
        issues.append(f"capture_surfaces_unexpected:{sorted(seen_surfaces)}")
    for row in rows:
        row_id = row.get("close_source_capture_patch_row_id")
        if row.get("patch_status") != "PATCHED_SOURCE_CAPTURE_READY":
            issues.append(f"patch_not_ready:{row_id}:{row.get('patch_status')}")
            break
        if row.get("runtime_trading_or_live_broker_effect"):
            issues.append(f"runtime_effect_claimed:{row_id}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("close_source_repair_identity_capture_patched") is not True:
        issues.append("close_source_repair_identity_capture_not_patched")
    if effect.get("close_target_context_capture_patched") is not True:
        issues.append("close_target_context_capture_not_patched")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "patched_source_capture_ready_rows": summary.get("patched_source_capture_ready_rows"),
        "future_contract_complete_if_emitted_rows_inherited": summary.get(
            "future_contract_complete_if_emitted_rows_inherited"
        ),
        "historical_slippage_rows_repaired": summary.get("historical_slippage_rows_repaired"),
        "historical_exact_r_repaired_rows": summary.get("historical_exact_r_repaired_rows"),
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
