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
    numeric_router_source_repair_execution_identity_capture_event_from_slippage_row,
    summarize_numeric_router_source_repair_execution_identity_capture_events,
)


CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
SLIPPAGE_LOG = REPO / "shadow_logs/slippage.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_numeric_router_exec_id_slip_join_check_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_numeric_router_exec_id_slip_join_check_2026_05_18.py"
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


def build() -> dict[str, Any]:
    contract_sha = sha256_path(CONTRACT_LEDGER)
    slippage_sha = sha256_path(SLIPPAGE_LOG)
    contracts = read_jsonl_with_line_no(CONTRACT_LEDGER)
    slippage_rows = read_jsonl_with_line_no(SLIPPAGE_LOG)

    events: list[dict[str, Any]] = []
    for contract_line_no, contract in contracts:
        for slippage_line_no, slippage_row in slippage_rows:
            events.append(
                numeric_router_source_repair_execution_identity_capture_event_from_slippage_row(
                    contract,
                    slippage_row,
                    event_row_id=(
                        "MAIN-ORCH48-NR-SRC-REPAIR-EXEC-ID-SLIP-JOIN-CHECK-"
                        f"{len(events) + 1:08d}"
                    ),
                    source_artifact=display_path(CONTRACT_LEDGER),
                    source_line_no=contract_line_no,
                    source_sha256=contract_sha,
                    slippage_source_artifact=display_path(SLIPPAGE_LOG),
                    slippage_source_line_no=slippage_line_no,
                    slippage_source_sha256=slippage_sha,
                )
            )
    write_jsonl(OUTPUT_LEDGER, events)

    event_summary = summarize_numeric_router_source_repair_execution_identity_capture_events(events)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_IDENTITY_CURRENT_SLIPPAGE_JOIN_CHECK",
        "schema_version": "main_orch48_numeric_router_source_repair_execution_identity_current_slippage_join_check_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_execution_identity_capture_contract_ledger": {
            "path": display_path(CONTRACT_LEDGER),
            "rows": count_lines(CONTRACT_LEDGER),
            "sha256": contract_sha,
        },
        "input_slippage_log": {
            "path": display_path(SLIPPAGE_LOG),
            "rows": count_lines(SLIPPAGE_LOG),
            "sha256": slippage_sha,
        },
        "code_surfaces": code_surface_summary(),
        **event_summary,
        "implementation_effect": {
            "default_off_current_slippage_join_check_available": True,
            "existing_slippage_rows_bound_to_contract": event_summary["slippage_row_bound_to_contract_rows"],
            "historical_exact_r_repaired_rows": event_summary["exact_r_repaired_by_this_event_rows"],
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
        "event_rows": summary["rows"],
        "unique_contract_rows_checked": summary["unique_contract_rows_checked"],
        "unique_slippage_rows_checked": summary["unique_slippage_rows_checked"],
        "execution_identity_capture_event_status_counts": summary[
            "execution_identity_capture_event_status_counts"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
