from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair,
    numeric_router_source_repair_slippage_lifecycle_pairs,
    summarize_numeric_router_source_repair_slippage_lifecycle_join_events,
)


CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
CLOSE_CAPTURE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_SUMMARY_{DATE}.json"
SLIPPAGE_LOG = REPO / "shadow_logs/slippage.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_SLIP_LIFECYCLE_JOIN_AUDIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_SLIP_LIFECYCLE_JOIN_AUDIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_SLIP_LIFECYCLE_JOIN_AUDIT_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
    Path("src/components/slippage_shadow_logger.py"),
    Path("src/components/execution.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_numeric_router_slippage_lifecycle_join_audit_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_numeric_router_slippage_lifecycle_join_audit_2026_05_18.py"
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_with_line_no(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                rows.append((line_no, json.loads(line)))
    return rows


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


def slippage_rows_with_source_lines() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, row in read_jsonl_with_line_no(SLIPPAGE_LOG):
        row_copy = dict(row)
        row_copy["_source_line_no"] = line_no
        rows.append(row_copy)
    return rows


def build() -> dict[str, Any]:
    contract_sha = sha256_path(CONTRACT_LEDGER)
    slippage_sha = sha256_path(SLIPPAGE_LOG)
    close_capture_sha = sha256_path(CLOSE_CAPTURE_SUMMARY)
    close_capture_summary = read_json(CLOSE_CAPTURE_SUMMARY)
    contracts = read_jsonl_with_line_no(CONTRACT_LEDGER)
    slippage_rows = slippage_rows_with_source_lines()
    lifecycle_pairs = numeric_router_source_repair_slippage_lifecycle_pairs(slippage_rows)

    events: list[dict[str, Any]] = []
    for contract_line_no, contract in contracts:
        for pair in lifecycle_pairs:
            events.append(
                numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair(
                    contract,
                    pair,
                    event_row_id=f"MAIN-ORCH48-NR-SRC-REPAIR-SLIP-LIFECYCLE-JOIN-AUDIT-{len(events) + 1:08d}",
                    source_artifact=display_path(CONTRACT_LEDGER),
                    source_line_no=contract_line_no,
                    source_sha256=contract_sha,
                    slippage_source_artifact=display_path(SLIPPAGE_LOG),
                    slippage_source_sha256=slippage_sha,
                )
            )
    write_jsonl(OUTPUT_LEDGER, events)

    join_summary = summarize_numeric_router_source_repair_slippage_lifecycle_join_events(events)
    pair_tickets = [pair.get("ticket") for pair in lifecycle_pairs]
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_LIFECYCLE_JOIN_AUDIT",
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_lifecycle_join_audit_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_execution_identity_capture_contract_ledger": {
            "path": display_path(CONTRACT_LEDGER),
            "rows": count_lines(CONTRACT_LEDGER),
            "sha256": contract_sha,
        },
        "input_slippage_shadow_log": {
            "path": display_path(SLIPPAGE_LOG),
            "rows": count_lines(SLIPPAGE_LOG),
            "sha256": slippage_sha,
            "entry_close_lifecycle_pairs_found": len(lifecycle_pairs),
            "entry_close_lifecycle_pair_tickets": pair_tickets,
        },
        "input_close_source_capture_patch_summary": {
            "path": display_path(CLOSE_CAPTURE_SUMMARY),
            "sha256": close_capture_sha,
            "patched_source_capture_ready_rows": close_capture_summary.get("patched_source_capture_ready_rows"),
            "future_contract_complete_if_emitted_rows_inherited": close_capture_summary.get(
                "future_contract_complete_if_emitted_rows_inherited"
            ),
        },
        "code_surfaces": code_surface_summary(),
        "source_writer_surfaces": {
            "entry_identity_writer": "src/components/slippage_shadow_logger.py::record_slippage",
            "execution_trade_params_forwarder": "src/components/execution.py::ExecutionEngine.open_trade",
            "close_lifecycle_geometry_writer": "src/components/slippage_shadow_logger.py::record_close_slippage",
            "lifecycle_join_auditor": (
                "src/research_infra/moonshot_numeric_router_system_recommendations.py::"
                "numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair"
            ),
        },
        **join_summary,
        "implementation_effect": {
            "default_off_slippage_lifecycle_join_audit_available": True,
            "current_slippage_lifecycle_pairs_checked": len(lifecycle_pairs),
            "current_lifecycle_pairs_bound_to_contract": join_summary[
                "slippage_lifecycle_pair_bound_to_contract_rows"
            ],
            "historical_slippage_rows_repaired": 0,
            "historical_exact_r_repaired_rows": 0,
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
        "ok": True,
        "route_id": summary["route_id"],
        "join_audit_rows": summary["rows"],
        "current_slippage_lifecycle_pairs_checked": len(lifecycle_pairs),
        "status_counts": summary["slippage_lifecycle_join_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
