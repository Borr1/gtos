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
    NumericRouterImplementationCatalog,
    numeric_router_source_repair_selector_event_from_surface,
    numeric_router_source_repair_selector_route_for_event,
    summarize_numeric_router_source_repair_selector_events,
    summarize_numeric_router_source_repair_selector_routes,
)


SELECTOR_SURFACE_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_LEDGER_{DATE}.jsonl"
)
SOURCE_REPAIR_QUEUE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE_LEDGER_{DATE}.jsonl"
OUTPUT_EVENT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_EVENT_LEDGER_{DATE}.jsonl"
OUTPUT_ROUTE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_numeric_router_system_recommendations.py"),
    Path("tests/research_infra/test_moonshot_numeric_router_system_recommendations.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orchestrator_numeric_router_source_repair_selector_router_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orchestrator_numeric_router_source_repair_selector_router_2026_05_18.py"
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
    selector_sha = sha256_path(SELECTOR_SURFACE_LEDGER)
    catalog_sha = sha256_path(SOURCE_REPAIR_QUEUE_LEDGER)
    catalog_entries = read_jsonl(SOURCE_REPAIR_QUEUE_LEDGER)
    catalog_by_id = {
        row.get("numeric_router_catalog_entry_id"): row
        for row in catalog_entries
        if row.get("numeric_router_catalog_entry_id")
    }
    catalog = NumericRouterImplementationCatalog(catalog_entries)

    events: list[dict[str, Any]] = []
    for source_line_no, selector_surface in read_jsonl_with_line_no(SELECTOR_SURFACE_LEDGER):
        catalog_entry = catalog_by_id.get(selector_surface.get("input_numeric_router_catalog_entry_id"))
        events.append(
            numeric_router_source_repair_selector_event_from_surface(
                selector_surface,
                catalog_entry,
                event_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SELECTOR-EVENT-{len(events) + 1:08d}",
                source_artifact=display_path(SELECTOR_SURFACE_LEDGER),
                source_line_no=source_line_no,
                source_sha256=selector_sha,
            )
        )
    write_jsonl(OUTPUT_EVENT_LEDGER, events)
    event_sha = sha256_path(OUTPUT_EVENT_LEDGER)

    routes: list[dict[str, Any]] = []
    for event_line_no, event in enumerate(events, start=1):
        matches = catalog.evaluate_event(event, include_source_repair=True)
        routes.append(
            numeric_router_source_repair_selector_route_for_event(
                event,
                matches,
                route_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SELECTOR-ROUTE-{len(routes) + 1:08d}",
                source_artifact=display_path(OUTPUT_EVENT_LEDGER),
                source_line_no=event_line_no,
                source_sha256=event_sha,
            )
        )
    write_jsonl(OUTPUT_ROUTE_LEDGER, routes)

    event_summary = summarize_numeric_router_source_repair_selector_events(events)
    route_summary = summarize_numeric_router_source_repair_selector_routes(routes)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER",
        "schema_version": "main_orch48_numeric_router_source_repair_selector_router_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_selector_surface_ledger": {
            "path": display_path(SELECTOR_SURFACE_LEDGER),
            "rows": count_lines(SELECTOR_SURFACE_LEDGER),
            "sha256": selector_sha,
        },
        "input_source_repair_queue_ledger": {
            "path": display_path(SOURCE_REPAIR_QUEUE_LEDGER),
            "rows": count_lines(SOURCE_REPAIR_QUEUE_LEDGER),
            "sha256": catalog_sha,
        },
        "code_surfaces": code_surface_summary(),
        "selector_event_rows": event_summary["rows"],
        "selector_route_rows": route_summary["rows"],
        "input_action_rows": route_summary["input_action_rows"],
        "source_repair_selector_event_status_counts": event_summary[
            "source_repair_selector_event_status_counts"
        ],
        "source_repair_selector_event_status_input_action_counts": event_summary[
            "source_repair_selector_event_status_input_action_counts"
        ],
        "source_repair_selector_route_status_counts": route_summary[
            "source_repair_selector_route_status_counts"
        ],
        "source_repair_selector_route_status_input_action_counts": route_summary[
            "source_repair_selector_route_status_input_action_counts"
        ],
        "catalog_entry_found_rows": event_summary["catalog_entry_found_rows"],
        "catalog_entry_id_match_rows": event_summary["catalog_entry_id_match_rows"],
        "catalog_family_spec_id_match_rows": event_summary["catalog_family_spec_id_match_rows"],
        "event_routable_rows": event_summary["event_routable_rows"],
        "event_routable_input_action_rows": event_summary["event_routable_input_action_rows"],
        "router_path_ready_default_off_rows": route_summary["router_path_ready_default_off_rows"],
        "router_path_ready_default_off_input_action_rows": route_summary[
            "router_path_ready_default_off_input_action_rows"
        ],
        "catalog_matched_rows": route_summary["catalog_matched_rows"],
        "source_repair_queue_matched_rows": route_summary["source_repair_queue_matched_rows"],
        "expected_catalog_entry_matched_rows": route_summary["expected_catalog_entry_matched_rows"],
        "trade_params_source_repair_identity_patch_rows": route_summary[
            "trade_params_source_repair_identity_patch_rows"
        ],
        "trade_params_source_repair_identity_patch_input_action_rows": route_summary[
            "trade_params_source_repair_identity_patch_input_action_rows"
        ],
        "source_packet_context_payload_rows": route_summary["source_packet_context_payload_rows"],
        "source_packet_context_payload_input_action_rows": route_summary[
            "source_packet_context_payload_input_action_rows"
        ],
        "requires_prospective_execution_identity_capture_rows": route_summary[
            "requires_prospective_execution_identity_capture_rows"
        ],
        "requires_prospective_execution_identity_capture_input_action_rows": route_summary[
            "requires_prospective_execution_identity_capture_input_action_rows"
        ],
        "exact_r_repaired_by_this_event_rows": event_summary["exact_r_repaired_by_this_event_rows"],
        "slippage_join_repaired_by_this_event_rows": event_summary[
            "slippage_join_repaired_by_this_event_rows"
        ],
        "exact_r_repaired_by_this_route_rows": route_summary["exact_r_repaired_by_this_route_rows"],
        "slippage_join_repaired_by_this_route_rows": route_summary[
            "slippage_join_repaired_by_this_route_rows"
        ],
        "runtime_score_allowed_rows": route_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": route_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": route_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": route_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": route_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "default_off_selector_event_router_available": True,
            "catalog_evaluation_include_source_repair_required": True,
            "source_repair_identity_selector_rows_routed": route_summary[
                "trade_params_source_repair_identity_patch_rows"
            ],
            "source_packet_context_rows_routed_to_prospective_capture": route_summary[
                "source_packet_context_payload_rows"
            ],
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_EVENT_LEDGER, OUTPUT_ROUTE_LEDGER, OUTPUT_SUMMARY]
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
        "selector_event_rows": summary["selector_event_rows"],
        "selector_route_rows": summary["selector_route_rows"],
        "input_action_rows": summary["input_action_rows"],
        "source_repair_selector_route_status_counts": summary["source_repair_selector_route_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
