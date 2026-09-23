from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
MOONSHOT_ROOT = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    numeric_router_source_repair_source_packet_trace_for_proof_row,
    summarize_numeric_router_source_repair_source_packet_traces,
)


PLAN_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_LEDGER_{DATE}.jsonl"
PROOF_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_LEDGER_{DATE}.jsonl"
OUTPUT_PLAN_SUMMARY_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_PLAN_SUMMARY_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_MANIFEST_{DATE}.json"

SOURCE_JOIN_REQUIRED_DECISION = "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF"
TRACE_COMPLETE_STATUS = "SOURCE_PACKET_TRACE_COMPLETE_PACKET_FOUND_EXECUTION_IDENTITY_ABSENT"

SOURCE_PACKET_CONFIGS = {
    "nofill_far_miss_retest": {
        "id_field": "retest_redesign_branch_id",
        "original_packet": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl",
        "source_join_packet": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_RETEST_REDESIGN_JOIN_LEDGER_2026-05-16.jsonl",
    },
    "nofill_far_miss_source_confidence": {
        "id_field": "source_confidence_branch_id",
        "original_packet": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl",
        "source_join_packet": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_SOURCE_CONFIDENCE_JOIN_LEDGER_2026-05-16.jsonl",
    },
    "nofill_far_miss_avoid": {
        "id_field": "avoid_filter_branch_id",
        "original_packet": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl",
        "source_join_packet": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_AVOID_JOIN_LEDGER_2026-05-16.jsonl",
    },
    "nofill_near_miss_offset": {
        "id_field": "near_miss_entry_control_offset_branch_id",
        "original_packet": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl",
        "source_join_packet": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_OFFSET_JOIN_LEDGER_2026-05-16.jsonl",
    },
    "nofill_near_miss_market_entry": {
        "id_field": "near_miss_entry_control_market_branch_id",
        "original_packet": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl",
        "source_join_packet": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_MARKET_ENTRY_JOIN_LEDGER_2026-05-16.jsonl",
    },
}

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


def index_packet_file(path: Path, id_field: str) -> dict[str, dict[str, Any]]:
    sha = sha256_path(path)
    index: dict[str, dict[str, Any]] = {}
    for line_no, row in read_jsonl_with_line_no(path):
        row_id = row.get(id_field)
        if row_id:
            index[str(row_id)] = {
                "row": row,
                "line_no": line_no,
                "source_artifact": display_path(path),
                "source_sha256": sha,
            }
    return index


def load_packet_indexes() -> dict[str, dict[str, Any]]:
    packet_indexes: dict[str, dict[str, Any]] = {}
    for source_component, config in SOURCE_PACKET_CONFIGS.items():
        id_field = config["id_field"]
        original_path = MOONSHOT_ROOT / config["original_packet"]
        join_path = MOONSHOT_ROOT / config["source_join_packet"]
        packet_indexes[source_component] = {
            "id_field": id_field,
            "original_path": original_path,
            "source_join_path": join_path,
            "original_index": index_packet_file(original_path, id_field) if original_path.exists() else {},
            "source_join_index": index_packet_file(join_path, id_field) if join_path.exists() else {},
            "original_sha256": sha256_path(original_path) if original_path.exists() else None,
            "source_join_sha256": sha256_path(join_path) if join_path.exists() else None,
            "original_rows": count_lines(original_path) if original_path.exists() else 0,
            "source_join_rows": count_lines(join_path) if join_path.exists() else 0,
        }
    return packet_indexes


def plan_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("source_component") or ""),
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
    )


def load_source_join_required_plans() -> dict[tuple[str, str, str], dict[str, Any]]:
    plans: dict[tuple[str, str, str], dict[str, Any]] = {}
    for _, row in read_jsonl_with_line_no(PLAN_LEDGER):
        if row.get("required_source_class") == "source_join_keys_or_original_packet_rows":
            plans[plan_key(row)] = row
    return plans


def source_row_for_proof(row: dict[str, Any]) -> dict[str, Any]:
    source_row = row.get("source_row")
    return source_row if isinstance(source_row, dict) else {}


def build_trace_rows(
    plans_by_key: dict[tuple[str, str, str], dict[str, Any]],
    packet_indexes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    proof_sha = sha256_path(PROOF_LEDGER)
    trace_rows: list[dict[str, Any]] = []
    for source_line_no, proof_row in read_jsonl_with_line_no(PROOF_LEDGER):
        proof_source_row = source_row_for_proof(proof_row)
        plan = plans_by_key.get(plan_key(proof_source_row))
        if not plan:
            continue
        if proof_source_row.get("source_repair_system_decision") != SOURCE_JOIN_REQUIRED_DECISION:
            continue
        source_component = str(proof_source_row.get("source_component") or "")
        packet_index = packet_indexes[source_component]
        source_row_id = str(proof_source_row.get("source_row_id") or "")
        original_match = packet_index["original_index"].get(source_row_id)
        join_match = packet_index["source_join_index"].get(source_row_id)
        trace = numeric_router_source_repair_source_packet_trace_for_proof_row(
            plan,
            proof_source_row,
            trace_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SOURCE-PACKET-TRACE-{len(trace_rows) + 1:08d}",
            source_artifact=display_path(PROOF_LEDGER),
            source_line_no=source_line_no,
            source_sha256=proof_sha,
            source_packet_id_field=packet_index["id_field"],
            original_packet_row=original_match["row"] if original_match else None,
            original_packet_source_artifact=original_match["source_artifact"] if original_match else None,
            original_packet_source_line_no=original_match["line_no"] if original_match else None,
            original_packet_source_sha256=original_match["source_sha256"] if original_match else None,
            source_join_packet_row=join_match["row"] if join_match else None,
            source_join_source_artifact=join_match["source_artifact"] if join_match else None,
            source_join_source_line_no=join_match["line_no"] if join_match else None,
            source_join_source_sha256=join_match["source_sha256"] if join_match else None,
        )
        trace |= {
            "upstream_source_repair_proof_source_artifact": proof_row.get("source_artifact"),
            "upstream_source_repair_proof_source_line_no": proof_row.get("source_line_no"),
            "upstream_source_repair_proof_source_sha256": proof_row.get("source_sha256"),
        }
        trace_rows.append(trace)
    return trace_rows


def build_plan_summary_rows(
    plans_by_key: dict[tuple[str, str, str], dict[str, Any]],
    packet_indexes: dict[str, dict[str, Any]],
    trace_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trace_rows:
        rows_by_plan[str(row.get("input_source_repair_plan_row_id") or "")].append(row)

    summaries: list[dict[str, Any]] = []
    for index, plan in enumerate(plans_by_key.values(), start=1):
        plan_rows = rows_by_plan[str(plan.get("source_repair_plan_row_id") or "")]
        status_counts = Counter(str(row.get("source_packet_trace_status") or "") for row in plan_rows)
        all_packets_found = (
            len(plan_rows) == int(plan.get("input_action_rows") or 0)
            and all(row.get("original_source_packet_found") for row in plan_rows)
            and all(row.get("source_join_packet_found") for row in plan_rows)
        )
        identity_rows = sum(bool(row.get("direct_execution_identity_fields_present")) for row in plan_rows)
        if all_packets_found and identity_rows == 0:
            plan_status = "SOURCE_PACKET_TRACE_PLAN_COMPLETE_EXECUTION_IDENTITY_ABSENT"
        elif all_packets_found:
            plan_status = "SOURCE_PACKET_TRACE_PLAN_COMPLETE_DIRECT_EXECUTION_IDENTITY_PRESENT"
        else:
            plan_status = "SOURCE_PACKET_TRACE_PLAN_INCOMPLETE_PACKET_MATCHES"
        source_component = str(plan.get("source_component") or "")
        packet_index = packet_indexes[source_component]
        summaries.append(
            {
                "source_packet_trace_plan_summary_row_id": (
                    f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-SOURCE-PACKET-PLAN-{index:08d}"
                ),
                "schema_version": "main_orch48_numeric_router_source_repair_source_packet_trace_plan_summary_v1",
                "input_source_repair_plan_row_id": plan.get("source_repair_plan_row_id"),
                "input_numeric_router_catalog_entry_id": plan.get("input_numeric_router_catalog_entry_id"),
                "input_numeric_router_family_spec_id": plan.get("input_numeric_router_family_spec_id"),
                "source_component": source_component,
                "symbol": plan.get("symbol"),
                "route_session": plan.get("route_session"),
                "input_action_rows": int(plan.get("input_action_rows") or 0),
                "trace_rows": len(plan_rows),
                "source_packet_trace_status_counts": dict(sorted(status_counts.items())),
                "original_source_packet_found_rows": sum(
                    bool(row.get("original_source_packet_found")) for row in plan_rows
                ),
                "source_join_packet_found_rows": sum(bool(row.get("source_join_packet_found")) for row in plan_rows),
                "direct_execution_identity_found_rows": identity_rows,
                "exact_r_repaired_by_this_trace_rows": sum(
                    bool(row.get("exact_r_repaired_by_this_trace")) for row in plan_rows
                ),
                "slippage_join_repaired_by_this_trace_rows": sum(
                    bool(row.get("slippage_join_repaired_by_this_trace")) for row in plan_rows
                ),
                "requires_prospective_execution_identity_capture_rows": sum(
                    bool(row.get("requires_prospective_execution_identity_capture")) for row in plan_rows
                ),
                "source_packet_trace_plan_status": plan_status,
                "source_packet_id_field": packet_index["id_field"],
                "original_source_packet_artifact": display_path(packet_index["original_path"]),
                "original_source_packet_sha256": packet_index["original_sha256"],
                "original_source_packet_total_rows": packet_index["original_rows"],
                "source_join_packet_artifact": display_path(packet_index["source_join_path"]),
                "source_join_packet_sha256": packet_index["source_join_sha256"],
                "source_join_packet_total_rows": packet_index["source_join_rows"],
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    return summaries


def build() -> dict[str, Any]:
    packet_indexes = load_packet_indexes()
    plans_by_key = load_source_join_required_plans()
    trace_rows = build_trace_rows(plans_by_key, packet_indexes)
    plan_summary_rows = build_plan_summary_rows(plans_by_key, packet_indexes, trace_rows)
    write_jsonl(OUTPUT_LEDGER, trace_rows)
    write_jsonl(OUTPUT_PLAN_SUMMARY_LEDGER, plan_summary_rows)

    trace_summary = summarize_numeric_router_source_repair_source_packet_traces(trace_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE",
        "schema_version": "main_orch48_numeric_router_source_repair_source_packet_trace_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "moonshot_root": display_path(MOONSHOT_ROOT),
        "input_plan_ledger": {
            "path": display_path(PLAN_LEDGER),
            "rows": count_lines(PLAN_LEDGER),
            "sha256": sha256_path(PLAN_LEDGER),
            "source_join_required_plan_rows": len(plans_by_key),
        },
        "input_proof_ledger": {
            "path": display_path(PROOF_LEDGER),
            "rows": count_lines(PROOF_LEDGER),
            "sha256": sha256_path(PROOF_LEDGER),
        },
        "source_packet_inputs": [
            {
                "source_component": source_component,
                "id_field": packet_index["id_field"],
                "original_source_packet_artifact": display_path(packet_index["original_path"]),
                "original_source_packet_rows": packet_index["original_rows"],
                "original_source_packet_sha256": packet_index["original_sha256"],
                "source_join_packet_artifact": display_path(packet_index["source_join_path"]),
                "source_join_packet_rows": packet_index["source_join_rows"],
                "source_join_packet_sha256": packet_index["source_join_sha256"],
            }
            for source_component, packet_index in sorted(packet_indexes.items())
        ],
        "code_surfaces": code_surface_summary(),
        "trace_rows": trace_summary["rows"],
        "plan_summary_rows": len(plan_summary_rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in plan_summary_rows),
        "source_packet_trace_status_counts": trace_summary["source_packet_trace_status_counts"],
        "source_component_counts": trace_summary["source_component_counts"],
        "symbol_counts": trace_summary["symbol_counts"],
        "route_session_counts": trace_summary["route_session_counts"],
        "original_source_packet_found_rows": trace_summary["original_source_packet_found_rows"],
        "source_join_packet_found_rows": trace_summary["source_join_packet_found_rows"],
        "direct_execution_identity_found_rows": trace_summary["direct_execution_identity_found_rows"],
        "source_absence_proof_repaired_rows": trace_summary["source_absence_proof_repaired_rows"],
        "exact_r_repaired_by_this_trace_rows": trace_summary["exact_r_repaired_by_this_trace_rows"],
        "slippage_join_repaired_by_this_trace_rows": trace_summary["slippage_join_repaired_by_this_trace_rows"],
        "requires_prospective_execution_identity_capture_rows": trace_summary[
            "requires_prospective_execution_identity_capture_rows"
        ],
        "runtime_score_allowed_rows": trace_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": trace_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": trace_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": trace_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": trace_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "source_packet_absence_proof_repaired_from_original_packets": True,
            "exact_r_or_slippage_join_repaired": False,
            "prospective_execution_identity_capture_still_required": True,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_PLAN_SUMMARY_LEDGER, OUTPUT_SUMMARY]
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
        "trace_rows": summary["trace_rows"],
        "plan_summary_rows": summary["plan_summary_rows"],
        "source_packet_trace_status_counts": summary["source_packet_trace_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
