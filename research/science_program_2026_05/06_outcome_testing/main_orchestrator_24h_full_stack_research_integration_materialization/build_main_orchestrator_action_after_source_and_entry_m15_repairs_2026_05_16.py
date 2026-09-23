"""Build implementation action queue after SOURCE and entry M15 repairs."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
BASE_BUILDER = ROUTE_DIR / "build_main_orchestrator_implementation_action_after_source_m15_repair_2026_05_16.py"
ENTRY_M15_REPAIR_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_LEDGER_{DATE}.jsonl"
ENTRY_M15_REPAIR_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_SUMMARY_{DATE}.json"
PREVIOUS_ACTION_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_OUTPUT_MANIFEST_{DATE}.json"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("impl_action_source_m15_builder", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base builder from {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base()


def build_entry_m15_rows(start_seq: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seq = start_seq
    for source_row in base.read_jsonl(ENTRY_M15_REPAIR_LEDGER):
        seq += 1
        after_proxy = source_row.get("after_entry_proxy_r")
        action_row = base.make_action_row(
            row_id=f"MAIN-ORCH24-ACTION-SRC-ENTRY-M15-{seq:05d}",
            source_plate="entry_offset_m15_hard_no_fill_repair",
            source_artifact=ENTRY_M15_REPAIR_LEDGER,
            source_row=source_row,
            action_class=str(source_row.get("after_entry_action_class") or "REVIEW_REQUIRED"),
            branch_decision=str(source_row.get("after_entry_branch_decision") or ""),
            implementation_decision=str(source_row.get("after_entry_scorer_status") or ""),
            current_action=str(source_row.get("after_entry_branch_decision") or ""),
            exact_r=source_row.get("exact_r"),
            before_proxy_r=source_row.get("before_entry_proxy_r"),
            after_proxy_r=after_proxy,
            proxy_r_delta=after_proxy,
            data_requirement_state=source_row.get("tick_source_status"),
            source_capture_surface="entry_offset_m15_hard_no_fill_repair",
            extra_fields={
                "entry_retest_redesign_bucket": source_row.get("entry_retest_redesign_bucket"),
                "m15_hard_no_fill_repaired": source_row.get("m15_hard_no_fill_repaired"),
                "m15_hard_no_fill_proof_status": source_row.get("m15_hard_no_fill_proof_status"),
                "m15_nearest_distance_to_entry_r": source_row.get("m15_nearest_distance_to_entry_r"),
                "after_entry_score_status": source_row.get("after_entry_score_status"),
                "after_entry_scorer_status": source_row.get("after_entry_scorer_status"),
                "before_entry_scorer_status": source_row.get("before_entry_scorer_status"),
            },
        )
        action_row["primitive_family"] = "entry_geometry_fillability_tick_path_ordering"
        rows.append(action_row)
    return rows


def build_rows() -> list[dict[str, Any]]:
    previous_rows = base.build_rows()
    fvg_rows = [row for row in previous_rows if row.get("source_plate") == "fvg_structural_scorer_candidate_recompute"]
    pending_rows = [row for row in previous_rows if row.get("source_plate") == "pending_lifecycle_source_derivation_recompute"]
    source_rows = [row for row in previous_rows if row.get("source_plate") == "source_m15_ordering_repair"]
    entry_rows = build_entry_m15_rows(len(fvg_rows))
    return fvg_rows + entry_rows + pending_rows + source_rows


def entry_m15_bounds(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_rows = [row for row in rows if row.get("source_plate") == "entry_offset_m15_hard_no_fill_repair"]
    proxy_values = [base.safe_float(row.get("after_proxy_r")) for row in entry_rows if base.safe_float(row.get("after_proxy_r")) is not None]
    repaired = [row for row in entry_rows if row.get("m15_hard_no_fill_repaired") is True]
    return {
        "rows": len(entry_rows),
        "proxy_rows": len(proxy_values),
        "proxy_sum": round(sum(proxy_values), 8),
        "m15_hard_no_fill_repaired_rows": len(repaired),
        "m15_hard_no_fill_proxy_sum": round(sum(base.safe_float(row.get("after_proxy_r")) or 0.0 for row in repaired), 8),
    }


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    inputs = [
        base.FVG_STRUCT_LEDGER,
        ENTRY_M15_REPAIR_LEDGER,
        base.PENDING_DERIVATION_LEDGER,
        base.SOURCE_M15_REPAIR_LEDGER,
        PREVIOUS_ACTION_SUMMARY,
        ENTRY_M15_REPAIR_SUMMARY,
        base.SOURCE_M15_REPAIR_SUMMARY,
    ]
    return {
        "route_id": base.ROUTE_ID,
        "generated_utc": base.utc_now(),
        "input_artifacts": {
            path.name: {"sha256": base.sha256_file(path), "size_bytes": path.stat().st_size}
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": base.sha256_file(path), "size_bytes": path.stat().st_size}
            for path in paths
        },
        "safe_flags": base.SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    previous_summary = base.read_json(PREVIOUS_ACTION_SUMMARY)
    entry_summary = base.read_json(ENTRY_M15_REPAIR_SUMMARY)
    source_summary = base.read_json(base.SOURCE_M15_REPAIR_SUMMARY)
    action_counts = base.counter(rows, "action_class")
    coverage_counts = base.counter(rows, "coverage_status")
    proxy_summary = base.proxy_delta_summary(rows)
    entry_bounds = entry_m15_bounds(rows)

    base.write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": base.ROUTE_ID,
        "generated_utc": base.utc_now(),
        "evidence_class": "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_AND_ENTRY_M15_REPAIRS",
        "claim_boundary": (
            "Versioned implementation/action queue after SOURCE M15-ordering and entry-offset "
            "M15 hard no-fill repairs. It closes stale action rows only; no live behavior, "
            "broker R, promotion, validation-safe, or execution change."
        ),
        "action_rows": len(rows),
        "source_plate_counts": base.counter(rows, "source_plate"),
        "action_class_counts": action_counts,
        "coverage_status_counts": coverage_counts,
        "primitive_family_counts": base.counter(rows, "primitive_family"),
        "branch_decision_counts": base.counter(rows, "branch_decision"),
        "implementation_decision_counts": base.counter(rows, "implementation_decision"),
        "proxy_delta_summary_by_plate": proxy_summary,
        "before_action_class_counts": previous_summary.get("action_class_counts"),
        "action_class_delta_vs_previous": base.action_count_delta(previous_summary.get("action_class_counts", {}), action_counts),
        "before_coverage_status_counts": previous_summary.get("coverage_status_counts"),
        "coverage_status_delta_vs_previous": base.action_count_delta(previous_summary.get("coverage_status_counts", {}), coverage_counts),
        "entry_offset_source_repair_actions_before": previous_summary.get("action_class_counts", {}).get("SOURCE_REPAIR", 0),
        "entry_offset_m15_repair_rows": entry_summary.get("m15_ordering_repaired_rows") or entry_summary.get("m15_hard_no_fill_repaired_rows"),
        "entry_offset_m15_action_bounds": entry_bounds,
        "entry_offset_proxy_rows_after": entry_bounds["proxy_rows"],
        "entry_offset_proxy_sum_after": entry_bounds["proxy_sum"],
        "entry_offset_proxy_row_delta_vs_previous_action": entry_bounds["proxy_rows"] - previous_summary.get("proxy_delta_summary_by_plate", {}).get("entry_redesign_tick_offset_recompute", {}).get("numeric_proxy_delta_rows", 0),
        "entry_offset_proxy_sum_delta_vs_previous_action": round(entry_bounds["proxy_sum"] - previous_summary.get("proxy_delta_summary_by_plate", {}).get("entry_redesign_tick_offset_recompute", {}).get("proxy_r_delta_sum", 0.0), 8),
        "source_m15_ordering_proxy_bounds": previous_summary.get("source_m15_ordering_proxy_bounds"),
        "source_m15_after_branch_decision_counts": source_summary.get("after_branch_decision_counts"),
        "m15_ordering_repair_actions_after": action_counts.get("M15_ORDERING_REPAIR", 0),
        "plate_decision": "IMPLEMENTATION_ACTION_QUEUE_CONSUMES_SOURCE_AND_ENTRY_M15_REPAIRS",
        "safe_flags": base.SAFE_FLAGS,
    }
    base.write_json(OUTPUT_SUMMARY, summary)
    base.write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(json.dumps({"rows_written": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
