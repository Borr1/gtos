from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

LIFECYCLE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/components/slippage_shadow_logger.py"),
    Path("src/components/execution.py"),
    Path("tests/test_slippage_shadow_logger.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_numeric_router_close_source_capture_patch_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_numeric_router_close_source_capture_patch_2026_05_18.py"
    ),
]


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


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def code_surface_summary() -> list[dict[str, Any]]:
    return [
        {
            "path": str(path).replace("\\", "/"),
            "bytes": (REPO / path).stat().st_size,
            "lines": count_lines(REPO / path),
            "sha256": sha256_path(REPO / path),
        }
        for path in CODE_SURFACES
    ]


def source_has(path: Path, needle: str) -> bool:
    return needle in (REPO / path).read_text(encoding="utf-8")


def build_rows(lifecycle_summary: dict[str, Any]) -> list[dict[str, Any]]:
    execution_path = Path("src/components/execution.py")
    slippage_path = Path("src/components/slippage_shadow_logger.py")
    tests_path = Path("tests/test_slippage_shadow_logger.py")
    inherited_contract_rows = int(lifecycle_summary.get("future_contract_complete_if_emitted_rows") or 0)
    inherited_input_action_rows = int(
        (lifecycle_summary.get("future_slippage_lifecycle_emitter_status_input_action_counts") or {}).get(
            "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE",
            0,
        )
    )
    return [
        {
            "close_source_capture_patch_row_id": "MAIN-ORCH48-NR-CLOSE-SOURCE-CAPTURE-PATCH-00000001",
            "capture_surface": "trade_state_source_repair_identity_retention",
            "source_artifact": display_path(execution_path),
            "source_file_sha256": sha256_path(REPO / execution_path),
            "patch_status": (
                "PATCHED_SOURCE_CAPTURE_READY"
                if source_has(execution_path, "source_repair_identity: Optional[dict] = None")
                and source_has(execution_path, "source_repair_identity=trade_params.get(\"source_repair_identity\")")
                else "PATCH_NOT_FOUND"
            ),
            "future_contract_complete_if_emitted_rows_inherited": inherited_contract_rows,
            "input_action_rows_inherited": inherited_input_action_rows,
            "runtime_trading_or_live_broker_effect": False,
        },
        {
            "close_source_capture_patch_row_id": "MAIN-ORCH48-NR-CLOSE-SOURCE-CAPTURE-PATCH-00000002",
            "capture_surface": "close_slippage_source_repair_identity_writer",
            "source_artifact": display_path(slippage_path),
            "source_file_sha256": sha256_path(REPO / slippage_path),
            "patch_status": (
                "PATCHED_SOURCE_CAPTURE_READY"
                if source_has(slippage_path, "source_repair_identity: Optional[dict[str, Any]] = None")
                and source_has(slippage_path, "\"source_repair_identity_key_status\": (")
                and source_has(slippage_path, "\"BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE\"")
                else "PATCH_NOT_FOUND"
            ),
            "future_contract_complete_if_emitted_rows_inherited": inherited_contract_rows,
            "input_action_rows_inherited": inherited_input_action_rows,
            "runtime_trading_or_live_broker_effect": False,
        },
        {
            "close_source_capture_patch_row_id": "MAIN-ORCH48-NR-CLOSE-SOURCE-CAPTURE-PATCH-00000003",
            "capture_surface": "close_slippage_target_geometry_writer",
            "source_artifact": display_path(slippage_path),
            "source_file_sha256": sha256_path(REPO / slippage_path),
            "patch_status": (
                "PATCHED_SOURCE_CAPTURE_READY"
                if source_has(slippage_path, "executed_target_price: Optional[float] = None")
                and source_has(slippage_path, "\"executed_target_price_status\": (")
                else "PATCH_NOT_FOUND"
            ),
            "future_contract_complete_if_emitted_rows_inherited": inherited_contract_rows,
            "input_action_rows_inherited": inherited_input_action_rows,
            "runtime_trading_or_live_broker_effect": False,
        },
        {
            "close_source_capture_patch_row_id": "MAIN-ORCH48-NR-CLOSE-SOURCE-CAPTURE-PATCH-00000004",
            "capture_surface": "execution_close_slippage_forwarder",
            "source_artifact": display_path(execution_path),
            "source_file_sha256": sha256_path(REPO / execution_path),
            "patch_status": (
                "PATCHED_SOURCE_CAPTURE_READY"
                if source_has(execution_path, "executed_target_price=trade.take_profit_1")
                and source_has(execution_path, "source_repair_identity=getattr(trade, \"source_repair_identity\", None)")
                else "PATCH_NOT_FOUND"
            ),
            "future_contract_complete_if_emitted_rows_inherited": inherited_contract_rows,
            "input_action_rows_inherited": inherited_input_action_rows,
            "runtime_trading_or_live_broker_effect": False,
        },
        {
            "close_source_capture_patch_row_id": "MAIN-ORCH48-NR-CLOSE-SOURCE-CAPTURE-PATCH-00000005",
            "capture_surface": "focused_tests_cover_entry_and_close_identity",
            "source_artifact": display_path(tests_path),
            "source_file_sha256": sha256_path(REPO / tests_path),
            "patch_status": (
                "PATCHED_SOURCE_CAPTURE_READY"
                if source_has(tests_path, "test_close_source_repair_identity_can_be_bound_prospectively")
                and source_has(tests_path, "test_close_slippage_wire_carries_source_repair_identity")
                else "PATCH_NOT_FOUND"
            ),
            "future_contract_complete_if_emitted_rows_inherited": inherited_contract_rows,
            "input_action_rows_inherited": inherited_input_action_rows,
            "runtime_trading_or_live_broker_effect": False,
        },
    ]


def build() -> dict[str, Any]:
    lifecycle_summary = read_json(LIFECYCLE_SUMMARY)
    rows = build_rows(lifecycle_summary)
    write_jsonl(OUTPUT_LEDGER, rows)
    patched_rows = sum(row.get("patch_status") == "PATCHED_SOURCE_CAPTURE_READY" for row in rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH",
        "schema_version": "main_orch48_numeric_router_source_repair_close_source_capture_patch_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_future_slippage_lifecycle_emitter_summary": {
            "path": display_path(LIFECYCLE_SUMMARY),
            "sha256": sha256_path(LIFECYCLE_SUMMARY),
            "future_contract_complete_if_emitted_rows": lifecycle_summary.get(
                "future_contract_complete_if_emitted_rows"
            ),
            "source_repair_identity_written_to_future_entry_payload_rows": lifecycle_summary.get(
                "source_repair_identity_written_to_future_entry_payload_rows"
            ),
        },
        "code_surfaces": code_surface_summary(),
        "rows": len(rows),
        "patched_source_capture_ready_rows": patched_rows,
        "patch_not_found_rows": len(rows) - patched_rows,
        "future_contract_complete_if_emitted_rows_inherited": lifecycle_summary.get(
            "future_contract_complete_if_emitted_rows"
        ),
        "future_identity_payload_rows_inherited": lifecycle_summary.get(
            "source_repair_identity_written_to_future_entry_payload_rows"
        ),
        "historical_slippage_rows_repaired": 0,
        "historical_exact_r_repaired_rows": 0,
        "runtime_score_allowed_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "unconditional_scalar_use_allowed_rows": 0,
        "replay_r_reference_counted_as_new_main_result_rows": 0,
        "implementation_effect": {
            "close_source_repair_identity_capture_patched": patched_rows == len(rows),
            "close_target_context_capture_patched": patched_rows == len(rows),
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": patched_rows == len(rows),
    }
    write_json(OUTPUT_SUMMARY, summary)
    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": summary["can_continue_to_next_system_conversion_plate"],
        "route_id": summary["route_id"],
        "rows": summary["rows"],
        "patched_source_capture_ready_rows": patched_rows,
        "future_contract_complete_if_emitted_rows_inherited": summary[
            "future_contract_complete_if_emitted_rows_inherited"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
