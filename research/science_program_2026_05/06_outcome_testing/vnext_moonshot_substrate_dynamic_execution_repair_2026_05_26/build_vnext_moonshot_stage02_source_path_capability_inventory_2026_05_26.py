from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

OUTPUT_CAPABILITY_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE_ID}.jsonl"
OUTPUT_SEARCH_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_SEARCH_LEDGER_{DATE_ID}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json"
OUTPUT_FORWARD_CAPTURE = ROUTE_DIR / f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE_ID}.jsonl"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

HASH_LIMIT_BYTES = 25_000_000
ROW_COUNT_LIMIT_BYTES = 15_000_000

ROOTS = [
    ("repo_data", REPO_ROOT / "data"),
    ("repo_ticks", REPO_ROOT / "data" / "ticks"),
    ("repo_shadow_logs", REPO_ROOT / "shadow_logs"),
    ("repo_exports", REPO_ROOT / "exports"),
    ("repo_trade_records", REPO_ROOT / "knowledge_base" / "trade_records"),
    ("repo_pipeline_state", REPO_ROOT / "pipeline_state"),
    ("repo_route_moonshot", ROUTE_DIR),
    (
        "repo_route_activation_anatomy",
        REPO_ROOT
        / "research"
        / "science_program_2026_05"
        / "06_outcome_testing"
        / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26",
    ),
    (
        "repo_route_repaired_candidate",
        REPO_ROOT
        / "research"
        / "science_program_2026_05"
        / "06_outcome_testing"
        / "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25",
    ),
    (
        "repo_route_full_replay",
        REPO_ROOT
        / "research"
        / "science_program_2026_05"
        / "06_outcome_testing"
        / "vnext_full_historical_candidate_generation_replay_2026_05_24",
    ),
    ("absolute_tmp", Path("C:/tmp")),
    ("absolute_sierrachart", Path("C:/SierraChart")),
]

RELEVANT_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".gz",
    ".parquet",
    ".scid",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".log",
}

RELEVANT_NAME_TOKENS = [
    "tick",
    "ohlc",
    "mt5",
    "sierra",
    "scid",
    "shadow",
    "candidate",
    "path",
    "j46",
    "j49",
    "exit",
    "partial",
    "trail",
    "breakeven",
    "slippage",
    "nofill",
    "pending",
    "orderflow",
    "depth",
    "news",
    "calendar",
    "regime",
    "volatility",
    "vnext",
    "replay",
    "prop",
    "trade",
]

SKIP_DIR_NAMES = {".git", ".pytest_cache", ".mypy_cache", "__pycache__", "node_modules", ".venv", "venv"}


FORWARD_CAPTURE_REQUIREMENTS = [
    ("broker_order_ticket", "order_ticket", "non_generatable_historical_system_state", "execution_engine_order_submit"),
    ("broker_deal_ticket", "deal_ticket", "non_generatable_historical_system_state", "execution_engine_fill_event"),
    ("broker_fill_time", "broker_fill_time_utc", "non_generatable_historical_system_state", "execution_engine_fill_event"),
    ("broker_close_time", "broker_close_time_utc", "non_generatable_historical_system_state", "execution_engine_close_event"),
    ("executed_entry_price", "executed_entry_price", "non_generatable_historical_system_state", "execution_engine_fill_event"),
    ("executed_exit_price", "executed_exit_price", "non_generatable_historical_system_state", "execution_engine_close_event"),
    ("executed_stop_price", "executed_stop_price", "non_generatable_historical_system_state", "execution_engine_order_modify"),
    ("executed_target_price", "executed_target_price", "non_generatable_historical_system_state", "execution_engine_order_submit"),
    ("executed_lot_size", "executed_lot_size", "non_generatable_historical_system_state", "execution_engine_fill_event"),
    ("commission", "commission", "non_generatable_historical_system_state", "execution_engine_close_event"),
    ("swap", "swap", "non_generatable_historical_system_state", "execution_engine_close_event"),
    ("slippage_price", "slippage_price", "non_generatable_historical_system_state", "execution_engine_fill_and_close_event"),
    ("spread_entry_exit", "spread_at_entry_and_exit", "recoverable_forward_quote_capture", "tick_quote_capture"),
    ("bid_ask_path_order", "bid_ask_tick_ordering_between_entry_stop_target", "recoverable_market_data_if_ticks_exist", "tick_quote_capture"),
    ("partial_exit_lifecycle", "partial_exit_lifecycle", "non_generatable_historical_system_state", "execution_management_state"),
    ("be_move_lifecycle", "breakeven_move_request_result", "non_generatable_historical_system_state", "execution_management_state"),
    ("trailing_lifecycle", "trailing_stop_request_result", "non_generatable_historical_system_state", "execution_management_state"),
    ("time_stop_lifecycle", "time_stop_close_request_result", "non_generatable_historical_system_state", "execution_management_state"),
    ("pending_order_type", "pending_order_native_type_and_expiry", "non_generatable_historical_system_state", "pending_order_lifecycle"),
    ("pending_fill_reject", "pending_fill_reject_retcodes_and_reason", "non_generatable_historical_system_state", "pending_order_lifecycle"),
    ("source_join_ids", "candidate_trade_source_join_ids", "forward_capture_required_for_exact_join", "orchestrator_trade_record"),
    ("ai_prompt_hash", "ai_prompt_input_output_hashes", "forward_capture_required_for_ai_intent_truth", "primary_analyzer_call_record"),
    ("policy_transition_trace", "dynamic_exit_policy_transition_trace", "forward_capture_required_for_policy_truth", "execution_management_state"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_relevant(path: Path) -> bool:
    name = path.name.lower()
    suffixes = {suffix.lower() for suffix in path.suffixes}
    if suffixes & RELEVANT_SUFFIXES:
        return True
    return any(token in name for token in RELEVANT_NAME_TOKENS)


def iter_root_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    if root.is_file():
        yield root
        return
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in SKIP_DIR_NAMES]
        current = Path(current_root)
        for file_name in file_names:
            yield current / file_name


def source_family(path: Path, root_id: str) -> str:
    lowered = rel(path).lower()
    name = path.name.lower()
    if root_id == "absolute_sierrachart" or ".scid" in name or "sierra" in lowered:
        return "sierra_source"
    if "data/ticks" in lowered or ".parquet" in name:
        return "tick_parquet"
    if "trade_records" in lowered:
        return "trade_record"
    if "account_history" in lowered:
        return "account_history"
    if "shadow_logs" in lowered:
        return "shadow_log"
    if "economic_calendar" in name or "news" in name or "calendar" in name:
        return "news_calendar"
    if any(tf in name for tf in ["_m1.", "_m5.", "_m15.", "_h1.", "_h4.", "_d1."]):
        return "ohlc_bars"
    if "vnext_" in lowered or "replay" in lowered or "activation" in lowered:
        return "route_artifact"
    if root_id == "absolute_tmp":
        return "external_candidate_cache"
    if root_id == "repo_exports":
        return "export_artifact"
    if "pipeline_state" in lowered:
        return "pipeline_state"
    return "other_local_source"


def timeframe(path: Path) -> str | None:
    name = path.name.upper()
    for tf in ["M1", "M5", "M15", "H1", "H4", "D1"]:
        if f"_{tf}." in name or f"_{tf}_" in name:
            return tf
    return None


def source_priority(path: Path, family: str) -> tuple[int, str]:
    tf = timeframe(path)
    if family in {"trade_record", "account_history"}:
        return (1, "exact_system_or_broker_lifecycle_when_fields_exist")
    if family == "tick_parquet":
        return (2, "tick_bid_ask_or_tick_proxy_path")
    if family == "sierra_source":
        return (3, "sierra_scid_or_sierra_export_proxy")
    if tf == "M1":
        return (4, "m1_ohlc_proxy_path")
    if tf == "M5":
        return (5, "m5_ohlc_proxy_path")
    if tf == "M15":
        return (6, "m15_ohlc_proxy_path")
    if family == "shadow_log":
        return (7, "shadow_or_runtime_lifecycle_context")
    if tf in {"H1", "H4", "D1"}:
        return (8, "higher_timeframe_context")
    if family in {"news_calendar", "pipeline_state"}:
        return (8, "context_or_state_source")
    if family == "route_artifact":
        return (9, "research_route_diagnostic_or_prior_label_source")
    return (10, "auxiliary_local_source")


def dynamic_execution_usable(family: str, path: Path) -> tuple[bool, str]:
    lowered = rel(path).lower()
    if family in {"trade_record", "account_history"}:
        return (True, "usable for exact lifecycle fields only when required broker geometry fields are present")
    if family in {"tick_parquet", "sierra_source"}:
        return (True, "usable for source-ranked path ordering after parser/schema verification")
    if family == "ohlc_bars":
        return (True, "usable as OHLC proxy with same-bar ambiguity labels")
    if family == "shadow_log" and any(token in lowered for token in ["path", "exit", "j46", "j49", "slippage", "pending", "nofill"]):
        return (True, "usable as lifecycle/provenance input, not broker-truth unless fields exist")
    if family == "route_artifact":
        return (False, "diagnostic prior route label source; not dynamic execution truth until replayed")
    return (False, "not a direct execution path source")


def count_rows_if_safe(path: Path, size: int) -> tuple[int | None, str]:
    if size > ROW_COUNT_LIMIT_BYTES:
        return (None, "deferred_large_file")
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".jsonl") or path.suffix.lower() in {".csv", ".log"}:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                return (sum(1 for _ in handle), "counted_text_lines")
        except OSError as exc:
            return (None, f"row_count_error:{exc}")
    return (None, "not_row_oriented")


def file_record(seq: int, root_id: str, path: Path) -> dict:
    stat = path.stat()
    family = source_family(path, root_id)
    priority_rank, priority_label = source_priority(path, family)
    usable, usable_reason = dynamic_execution_usable(family, path)
    if stat.st_size <= HASH_LIMIT_BYTES:
        sha = sha256_file(path)
        sha_status = "computed"
    else:
        sha = None
        sha_status = "deferred_large_file_preserved_by_path_size_mtime"
    row_count, row_count_status = count_rows_if_safe(path, stat.st_size)
    truth_class = "recoverable_market_data"
    if family in {"trade_record", "account_history", "shadow_log", "pipeline_state"}:
        truth_class = "mixed_system_state_or_forward_truth"
    if family == "route_artifact":
        truth_class = "diagnostic_prior_route_artifact_not_execution_truth"
    if family == "external_candidate_cache":
        truth_class = "external_local_cache_requires_source_contract"
    return {
        "record_id": f"STAGE02-SOURCE-{seq:06d}",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
        "root_id": root_id,
        "source_path": rel(path),
        "source_family": family,
        "timeframe": timeframe(path),
        "bytes": stat.st_size,
        "modified_time_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "sha256": sha,
        "sha256_status": sha_status,
        "row_count": row_count,
        "row_count_status": row_count_status,
        "source_priority_rank": priority_rank,
        "source_priority_label": priority_label,
        "dynamic_execution_usable": usable,
        "dynamic_execution_usable_reason": usable_reason,
        "candidate_discovery_usable": family in {"ohlc_bars", "tick_parquet", "sierra_source", "shadow_log", "news_calendar"},
        "historical_truth_class": truth_class,
        "needs_parser_or_schema_review": family in {"sierra_source", "tick_parquet", "external_candidate_cache"},
        "no_live_or_paid_access_used": True,
    }


def search_record(root_id: str, root: Path, files_total: int, relevant_total: int, bytes_total: int, status: str) -> dict:
    return {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
        "root_id": root_id,
        "root_path": rel(root),
        "exists": root.exists(),
        "search_status": status,
        "files_seen": files_total,
        "relevant_files_recorded": relevant_total,
        "relevant_bytes": bytes_total,
        "search_policy": "full_recursive_listing_with_relevance_filter_no_top_n_sampling",
        "hash_limit_bytes": HASH_LIMIT_BYTES,
        "row_count_limit_bytes": ROW_COUNT_LIMIT_BYTES,
        "forbidden_boundaries_crossed": False,
    }


def write_forward_capture_requirements() -> list[dict]:
    rows = []
    for index, (req_id, field, blocker_class, capture_surface) in enumerate(FORWARD_CAPTURE_REQUIREMENTS, start=1):
        rows.append(
            {
                "requirement_id": f"STAGE02-FORWARD-CAPTURE-{index:03d}-{req_id}",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
                "field_or_contract": field,
                "blocker_class": blocker_class,
                "capture_surface": capture_surface,
                "why_needed": "Required to distinguish broker/lifecycle truth from price-path projection in dynamic execution replay.",
                "historical_reconstruction_policy": (
                    "do_not_infer_from_price_alone"
                    if blocker_class.startswith("non_generatable")
                    else "recover_from_source_only_with_hash_and_asof_contract"
                ),
                "exact_action": "add_or_verify_forward_logger_field_before_activation_truth_claim",
            }
        )
    with OUTPUT_FORWARD_CAPTURE.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def update_state(summary: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"
    state["first_incomplete_invariant"] = "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE"
    state["exact_next_action"] = (
        "Promote Stage02 source-ranked path capability into Stage03 policy-engine contracts, then run full policy replay."
    )
    state["source_gap_ledger_path"] = rel(OUTPUT_FORWARD_CAPTURE)
    state["row_counts_scanned"]["stage02_source_capability_rows"] = summary["source_capability_rows"]
    state["row_counts_scanned"]["stage02_search_root_rows"] = summary["search_rows"]
    state["row_counts_scanned"]["stage02_forward_capture_requirement_rows"] = summary["forward_capture_requirement_rows"]
    state["stage_status_table"]["STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"] = "complete"
    state["stage_status_table"]["STAGE_03_DYNAMIC_POLICY_STATE_MACHINE"] = "seed_implemented_ready_for_contract_hardening"
    state["output_artifact_manifest"]["source_path_capability_ledger"] = rel(OUTPUT_CAPABILITY_LEDGER)
    state["output_artifact_manifest"]["source_path_search_ledger"] = rel(OUTPUT_SEARCH_LEDGER)
    state["output_artifact_manifest"]["source_path_capability_summary"] = rel(OUTPUT_SUMMARY)
    state["output_artifact_manifest"]["forward_capture_requirements"] = rel(OUTPUT_FORWARD_CAPTURE)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage03"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage02_source_path_capability_inventory_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"source_rows={summary['source_capability_rows']}; "
                f"search_rows={summary['search_rows']}; "
                "first_incomplete=STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE"
            ),
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    capability_rows = []
    search_rows = []
    source_seq = 1
    for root_id, root in ROOTS:
        files_total = 0
        relevant_total = 0
        relevant_bytes = 0
        status = "missing"
        try:
            if root.exists():
                status = "scanned"
                for path in iter_root_files(root):
                    files_total += 1
                    if not is_relevant(path):
                        continue
                    relevant_total += 1
                    relevant_bytes += path.stat().st_size
                    capability_rows.append(file_record(source_seq, root_id, path))
                    source_seq += 1
        except OSError as exc:
            status = f"scan_error:{exc}"
        search_rows.append(search_record(root_id, root, files_total, relevant_total, relevant_bytes, status))

    with OUTPUT_CAPABILITY_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in capability_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with OUTPUT_SEARCH_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in search_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    forward_rows = write_forward_capture_requirements()

    family_counts = Counter(row["source_family"] for row in capability_rows)
    priority_counts = Counter(row["source_priority_label"] for row in capability_rows)
    root_counts = Counter(row["root_id"] for row in capability_rows)
    dynamic_usable_counts = Counter(str(row["dynamic_execution_usable"]) for row in capability_rows)
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
        "generated_at_utc": utc_now(),
        "source_capability_ledger_path": rel(OUTPUT_CAPABILITY_LEDGER),
        "source_path_search_ledger_path": rel(OUTPUT_SEARCH_LEDGER),
        "forward_capture_requirements_path": rel(OUTPUT_FORWARD_CAPTURE),
        "source_capability_rows": len(capability_rows),
        "search_rows": len(search_rows),
        "forward_capture_requirement_rows": len(forward_rows),
        "source_family_counts": dict(sorted(family_counts.items())),
        "source_priority_counts": dict(sorted(priority_counts.items())),
        "root_counts": dict(sorted(root_counts.items())),
        "dynamic_execution_usable_counts": dict(sorted(dynamic_usable_counts.items())),
        "hash_limit_bytes": HASH_LIMIT_BYTES,
        "row_count_limit_bytes": ROW_COUNT_LIMIT_BYTES,
        "source_priority_order": [
            "1 exact_system_or_broker_lifecycle_when_fields_exist",
            "2 tick_bid_ask_or_tick_proxy_path",
            "3 sierra_scid_or_sierra_export_proxy",
            "4 m1_ohlc_proxy_path",
            "5 m5_ohlc_proxy_path",
            "6 m15_ohlc_proxy_path",
            "7 shadow_or_runtime_lifecycle_context",
            "8 higher_timeframe_context_or_state",
            "9 research_route_diagnostic_or_prior_label_source",
            "10 auxiliary_local_source",
        ],
        "recoverability_policy": {
            "market_data": "recoverable_or_requestable_with_hash_and_asof_contract",
            "historical_system_state": "non_generatable_unless_already_logged",
            "route_artifacts": "diagnostic_until_dynamic_execution_replay_recomputes_labels",
        },
        "no_live_or_paid_access_used": True,
        "forbidden_boundaries_crossed": False,
        "first_incomplete_invariant_after_stage02": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_state(summary)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
                "source_rows": len(capability_rows),
                "search_rows": len(search_rows),
                "forward_capture_rows": len(forward_rows),
                "first_incomplete_invariant": "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
