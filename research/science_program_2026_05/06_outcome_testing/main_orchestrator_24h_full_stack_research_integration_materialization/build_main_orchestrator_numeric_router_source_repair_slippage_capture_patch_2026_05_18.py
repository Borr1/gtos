from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/components/slippage_shadow_logger.py"),
    Path("src/components/execution.py"),
    Path("tests/test_slippage_shadow_logger.py"),
]
NUMERIC_ROUTER_REPAIR_FIELDS = [
    "broker_fill_time_utc",
    "commission",
    "deal_ticket",
    "executed_entry_price",
    "executed_exit_price",
    "executed_lot_size",
    "executed_stop_price",
    "executed_target_price",
    "order_ticket",
    "partial_exit_lifecycle",
    "slippage_price",
    "swap",
]
FIELD_CAPTURE_SURFACES = {
    "broker_fill_time_utc": ["entry_slippage_optional_status_guard", "close_slippage_close_time_status_guard"],
    "commission": ["entry_slippage_account_history_required_status", "close_slippage_optional_account_history"],
    "deal_ticket": ["entry_slippage_order_result_deal_optional", "close_slippage_mt5_deal_id_alias"],
    "executed_entry_price": ["entry_slippage_filled_price_alias", "close_slippage_trade_entry_alias"],
    "executed_exit_price": ["entry_slippage_not_applicable_status", "close_slippage_fill_price_alias"],
    "executed_lot_size": ["entry_slippage_lots_alias", "close_slippage_volume_closed_alias"],
    "executed_stop_price": ["entry_slippage_stop_loss_alias", "close_slippage_stop_loss_alias"],
    "executed_target_price": ["entry_slippage_broker_target_alias", "close_slippage_not_captured_status"],
    "order_ticket": ["entry_slippage_order_ticket_alias", "close_slippage_order_ticket_alias"],
    "partial_exit_lifecycle": ["entry_slippage_full_position_opened", "close_slippage_partial_or_full_exit"],
    "slippage_price": ["existing_entry_slippage_price", "existing_close_slippage_price"],
    "swap": ["entry_slippage_account_history_required_status", "close_slippage_optional_account_history"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def code_hits_for_field(field: str, source_text_by_path: dict[str, str]) -> list[str]:
    return sorted(path for path, text in source_text_by_path.items() if f'"{field}"' in text or f"{field}=" in text)


def build() -> dict[str, Any]:
    source_text_by_path = {
        str(path).replace("\\", "/"): (REPO / path).read_text(encoding="utf-8")
        for path in CODE_SURFACES
    }
    code_surface_summary = [
        {
            "path": str(path).replace("\\", "/"),
            "bytes": (REPO / path).stat().st_size,
            "lines": count_lines(REPO / path),
            "sha256": sha256_path(REPO / path),
        }
        for path in CODE_SURFACES
    ]
    output_rows = []
    for index, field in enumerate(NUMERIC_ROUTER_REPAIR_FIELDS, start=1):
        hits = code_hits_for_field(field, source_text_by_path)
        status = (
            "PROSPECTIVE_SLIPPAGE_CAPTURE_SCHEMA_PRESENT_WITH_STATUS_GUARDS"
            if "src/components/slippage_shadow_logger.py" in hits
            else "PROSPECTIVE_SLIPPAGE_CAPTURE_SCHEMA_MISSING"
        )
        output_rows.append(
            {
                "slippage_capture_patch_row_id": (
                    f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SLIPPAGE-CAPTURE-{index:04d}"
                ),
                "schema_version": "main_orch48_numeric_router_source_repair_slippage_capture_patch_v1",
                "missing_field": field,
                "prospective_capture_status": status,
                "capture_surfaces": FIELD_CAPTURE_SURFACES[field],
                "source_code_hits": hits,
                "existing_local_field_availability_input": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY",
                "row_identity_bound_to_numeric_router_source_repair_queue": False,
                "exact_r_repaired_by_this_patch": False,
                "source_operation": "prospective_fail_open_slippage_schema_extension",
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "implementation_effect": {
                    "prospective_observability_schema_effect": True,
                    "runtime_logging_schema_effect_if_runtime_reenabled": True,
                    "runtime_trading_or_live_broker_effect": False,
                    "broker_operation": False,
                    "paid_api_or_vendor_call": False,
                },
            }
        )
    write_jsonl(OUTPUT_LEDGER, output_rows)

    status_counts = Counter(row["prospective_capture_status"] for row in output_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH",
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_capture_patch_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_local_field_availability_route": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY",
        "code_surfaces": code_surface_summary,
        "rows": len(output_rows),
        "prospective_capture_status_counts": dict(sorted(status_counts.items())),
        "numeric_router_repair_fields": NUMERIC_ROUTER_REPAIR_FIELDS,
        "all_repair_fields_have_slippage_schema_rows": all(
            row["prospective_capture_status"] == "PROSPECTIVE_SLIPPAGE_CAPTURE_SCHEMA_PRESENT_WITH_STATUS_GUARDS"
            for row in output_rows
        ),
        "row_identity_bound_to_numeric_router_source_repair_queue_rows": sum(
            bool(row["row_identity_bound_to_numeric_router_source_repair_queue"]) for row in output_rows
        ),
        "exact_r_repaired_by_this_patch_rows": sum(bool(row["exact_r_repaired_by_this_patch"]) for row in output_rows),
        "runtime_score_allowed_rows": sum(bool(row["runtime_score_allowed"]) for row in output_rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row["runtime_candidate_use_permitted"]) for row in output_rows),
        "candidate_use_allowed_now_rows": sum(bool(row["candidate_use_allowed_now"]) for row in output_rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row["unconditional_scalar_use_allowed"]) for row in output_rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row["replay_r_reference_counted_as_new_main_result"]) for row in output_rows
        ),
        "implementation_effect": {
            "prospective_observability_schema_effect": True,
            "runtime_logging_schema_effect_if_runtime_reenabled": True,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": summary["route_id"],
        "rows": summary["rows"],
        "prospective_capture_status_counts": summary["prospective_capture_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
