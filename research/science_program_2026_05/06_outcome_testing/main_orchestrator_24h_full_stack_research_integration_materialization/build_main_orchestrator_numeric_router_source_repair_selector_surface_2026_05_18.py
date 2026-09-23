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
    numeric_router_source_repair_selector_surface_for_selection_event,
    summarize_numeric_router_source_repair_selector_surfaces,
)


SELECTION_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_LEDGER_{DATE}.jsonl"
)
IDENTITY_ADAPTER_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_ADAPTER_LEDGER_{DATE}.jsonl"
)
SOURCE_PACKET_PLAN_SUMMARY_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_PLAN_SUMMARY_LEDGER_{DATE}.jsonl"
)
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
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


def build_adapter_lookup() -> dict[str, dict[str, Any]]:
    return {
        row.get("slippage_identity_adapter_row_id"): row
        for _, row in read_jsonl_with_line_no(IDENTITY_ADAPTER_LEDGER)
        if row.get("slippage_identity_adapter_row_id")
    }


def build_packet_plan_lookup() -> dict[str, dict[str, Any]]:
    return {
        row.get("input_source_repair_plan_row_id"): row
        for _, row in read_jsonl_with_line_no(SOURCE_PACKET_PLAN_SUMMARY_LEDGER)
        if row.get("input_source_repair_plan_row_id")
    }


def build() -> dict[str, Any]:
    selection_sha = sha256_path(SELECTION_LEDGER)
    adapter_lookup = build_adapter_lookup()
    packet_plan_lookup = build_packet_plan_lookup()
    surfaces: list[dict[str, Any]] = []
    for source_line_no, selection_event in read_jsonl_with_line_no(SELECTION_LEDGER):
        adapter = adapter_lookup.get(selection_event.get("input_slippage_identity_adapter_row_id"))
        packet_summary = packet_plan_lookup.get(selection_event.get("input_source_repair_plan_row_id"))
        surface = numeric_router_source_repair_selector_surface_for_selection_event(
            selection_event,
            adapter,
            packet_summary,
            selector_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SELECTOR-SURFACE-{len(surfaces) + 1:08d}",
            source_artifact=display_path(SELECTION_LEDGER),
            source_line_no=source_line_no,
            source_sha256=selection_sha,
        )
        surfaces.append(surface)

    write_jsonl(OUTPUT_LEDGER, surfaces)
    surface_summary = summarize_numeric_router_source_repair_selector_surfaces(surfaces)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE",
        "schema_version": "main_orch48_numeric_router_source_repair_selector_surface_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_slippage_selection_bridge_ledger": {
            "path": display_path(SELECTION_LEDGER),
            "rows": count_lines(SELECTION_LEDGER),
            "sha256": selection_sha,
        },
        "input_slippage_identity_adapter_ledger": {
            "path": display_path(IDENTITY_ADAPTER_LEDGER),
            "rows": count_lines(IDENTITY_ADAPTER_LEDGER),
            "sha256": sha256_path(IDENTITY_ADAPTER_LEDGER),
        },
        "input_source_packet_trace_plan_summary_ledger": {
            "path": display_path(SOURCE_PACKET_PLAN_SUMMARY_LEDGER),
            "rows": count_lines(SOURCE_PACKET_PLAN_SUMMARY_LEDGER),
            "sha256": sha256_path(SOURCE_PACKET_PLAN_SUMMARY_LEDGER),
        },
        "code_surfaces": code_surface_summary(),
        "selector_surface_rows": surface_summary["rows"],
        "input_action_rows": surface_summary["input_action_rows"],
        "source_repair_selector_surface_status_counts": surface_summary[
            "source_repair_selector_surface_status_counts"
        ],
        "source_repair_selector_surface_status_input_action_counts": surface_summary[
            "source_repair_selector_surface_status_input_action_counts"
        ],
        "trade_params_source_repair_identity_patch_rows": surface_summary[
            "trade_params_source_repair_identity_patch_rows"
        ],
        "trade_params_source_repair_identity_patch_input_action_rows": surface_summary[
            "trade_params_source_repair_identity_patch_input_action_rows"
        ],
        "source_packet_context_payload_rows": surface_summary["source_packet_context_payload_rows"],
        "source_packet_context_payload_input_action_rows": surface_summary[
            "source_packet_context_payload_input_action_rows"
        ],
        "requires_prospective_execution_identity_capture_rows": surface_summary[
            "requires_prospective_execution_identity_capture_rows"
        ],
        "requires_prospective_execution_identity_capture_input_action_rows": surface_summary[
            "requires_prospective_execution_identity_capture_input_action_rows"
        ],
        "exact_r_repaired_by_this_selector_rows": surface_summary["exact_r_repaired_by_this_selector_rows"],
        "slippage_join_repaired_by_this_selector_rows": surface_summary[
            "slippage_join_repaired_by_this_selector_rows"
        ],
        "runtime_score_allowed_rows": surface_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": surface_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": surface_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": surface_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": surface_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "default_off_source_repair_selector_surface_available": True,
            "trade_params_identity_selector_rows": surface_summary[
                "trade_params_source_repair_identity_patch_rows"
            ],
            "packet_context_selector_rows_without_execution_identity": surface_summary[
                "source_packet_context_payload_rows"
            ],
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
        "selector_surface_rows": summary["selector_surface_rows"],
        "input_action_rows": summary["input_action_rows"],
        "source_repair_selector_surface_status_counts": summary[
            "source_repair_selector_surface_status_counts"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
