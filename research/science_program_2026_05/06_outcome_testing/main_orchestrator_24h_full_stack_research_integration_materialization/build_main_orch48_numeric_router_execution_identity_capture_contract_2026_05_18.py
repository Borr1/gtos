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
    numeric_router_source_repair_execution_identity_capture_contract_for_route,
    summarize_numeric_router_source_repair_execution_identity_capture_contracts,
)


ROUTER_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_LEDGER_{DATE}.jsonl"
SLIPPAGE_CAPTURE_PATCH_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl"
)
SOURCE_REPAIR_QUEUE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_numeric_router_execution_identity_capture_contract_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_numeric_router_execution_identity_capture_contract_2026_05_18.py"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [row for _, row in read_jsonl_with_line_no(path)]


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
    router_sha = sha256_path(ROUTER_LEDGER)
    slippage_capture_sha = sha256_path(SLIPPAGE_CAPTURE_PATCH_LEDGER)
    source_repair_queue_sha = sha256_path(SOURCE_REPAIR_QUEUE_LEDGER)
    capture_patch_rows = read_jsonl(SLIPPAGE_CAPTURE_PATCH_LEDGER)
    source_repair_queue_by_id = {
        row.get("numeric_router_catalog_entry_id"): row
        for row in read_jsonl(SOURCE_REPAIR_QUEUE_LEDGER)
        if row.get("numeric_router_catalog_entry_id")
    }

    contracts: list[dict[str, Any]] = []
    for source_line_no, selector_route in read_jsonl_with_line_no(ROUTER_LEDGER):
        contracts.append(
            numeric_router_source_repair_execution_identity_capture_contract_for_route(
                selector_route,
                capture_patch_rows,
                contract_row_id=(
                    "MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-EXECUTION-IDENTITY-"
                    f"CAPTURE-CONTRACT-{len(contracts) + 1:08d}"
                ),
                source_artifact=display_path(ROUTER_LEDGER),
                source_line_no=source_line_no,
                source_sha256=router_sha,
                source_repair_queue_entry=source_repair_queue_by_id.get(
                    selector_route.get("input_numeric_router_catalog_entry_id")
                ),
            )
        )
    write_jsonl(OUTPUT_LEDGER, contracts)

    contract_summary = summarize_numeric_router_source_repair_execution_identity_capture_contracts(contracts)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_IDENTITY_CAPTURE_CONTRACT",
        "schema_version": "main_orch48_numeric_router_source_repair_execution_identity_capture_contract_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_selector_router_ledger": {
            "path": display_path(ROUTER_LEDGER),
            "rows": count_lines(ROUTER_LEDGER),
            "sha256": router_sha,
        },
        "input_slippage_capture_patch_ledger": {
            "path": display_path(SLIPPAGE_CAPTURE_PATCH_LEDGER),
            "rows": count_lines(SLIPPAGE_CAPTURE_PATCH_LEDGER),
            "sha256": slippage_capture_sha,
        },
        "input_source_repair_queue_ledger": {
            "path": display_path(SOURCE_REPAIR_QUEUE_LEDGER),
            "rows": count_lines(SOURCE_REPAIR_QUEUE_LEDGER),
            "sha256": source_repair_queue_sha,
        },
        "code_surfaces": code_surface_summary(),
        **contract_summary,
        "implementation_effect": {
            "default_off_execution_identity_capture_contract_available": True,
            "selector_route_rows_bound_to_slippage_capture_schema": contract_summary[
                "capture_patch_fields_bound_to_route_rows"
            ],
            "source_repair_queue_route_bound_rows": contract_summary["source_repair_queue_route_bound_rows"],
            "trade_params_identity_contract_rows": contract_summary[
                "trade_params_source_repair_identity_patch_rows"
            ],
            "packet_context_capture_contract_rows": contract_summary["source_packet_context_payload_rows"],
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
        "contract_rows": summary["rows"],
        "input_action_rows": summary["input_action_rows"],
        "execution_identity_capture_contract_status_counts": summary[
            "execution_identity_capture_contract_status_counts"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
