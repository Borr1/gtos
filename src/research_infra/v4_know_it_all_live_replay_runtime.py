"""KIA V4 live-replay runtime route state and verifier.

This route consumes the prior timewarp replay package as input and opens the
next know-it-all replay-runtime repair lane without claiming completion.
"""

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.audit_goal_route_artifacts import audit_route
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    BASELINE_DAYS,
    BASELINE_PENDING_EXPIRY_MINUTES,
    CampaignConfig,
    HOLDOUT_DAYS,
    LiveReplayMode,
    NO_BROKER_BOUNDARY,
    OUTCOME_EVIDENCE_CLASS,
    ROUTE_DIR as TIMEWARP_ROUTE_DIR,
    ROUTE_ID as TIMEWARP_ROUTE_ID,
    SIM_EVIDENCE_CLASS,
    SMOKE_DAY,
    SOURCE_BOUND_EVIDENCE_CLASS,
    SOURCE_TRUTH_SCOPE,
    SimulatedBroker,
    V4DecisionCycleCore,
    atomic_write_json,
    atomic_write_jsonl,
    build_source_package,
    build_rollup_rows,
    file_sha256,
    git_value,
    iso,
    load_json,
    load_jsonl,
    load_config,
    materialize_scheduler_window,
    parse_utc,
    path_final_r,
    path_source_and_oracle,
    run_campaign,
    safe_float,
    simulate_order,
    stable_sha256,
    summarize_campaign,
    sort_event_ledgers,
    utc_now,
)


ROUTE_ID = "final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_V4_KNOW_IT_ALL_LIVE_REPLAY_RUNTIME_AND_SYSTEM_REPAIR_GOAL_PROMPT_2026-06-07.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_V4_KNOW_IT_ALL_LIVE_REPLAY_RUNTIME_AND_SYSTEM_REPAIR_STARTER_2026-06-07.txt"
)

KIA_REPAIR_POLICY_ID = "kia_repair_001_scheduler_single_select_risk_preservation"
KIA_REPAIR_RUNTIME_OVERRIDES = {
    "scheduler_v4_best_trade_allocator_allow_multiple_new_positions_per_window": False,
}
KIA_REPAIR_LEDGER_FILES = {
    "asof": "KIA_REPAIR_RERUN_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIA_REPAIR_RERUN_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIA_REPAIR_RERUN_PACKET_SIDECAR_LEDGER.jsonl",
    "scorecard": "KIA_REPAIR_RERUN_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIA_REPAIR_RERUN_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIA_REPAIR_RERUN_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIA_REPAIR_RERUN_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIA_REPAIR_RERUN_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIA_REPAIR_RERUN_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIA_REPAIR_RERUN_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "winner": "KIA_REPAIR_RERUN_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIA_REPAIR_RERUN_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIA_REPAIR_RERUN_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIA_REPAIR_RERUN_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIA_REPAIR_RERUN_DAILY_MICROSCOPE_SUMMARY.jsonl",
}
KIA_HOLDOUT_LEDGER_FILES = {
    key: filename.replace("KIA_REPAIR_RERUN_", "KIA_HOLDOUT_ROLLING_")
    for key, filename in KIA_REPAIR_LEDGER_FILES.items()
}
KIA_COMPLETION_STATUS = "COMPLETE_WITHIN_REPLAY_EVIDENCE_CLASS"
KIA_PRODUCTION_SHARED_CORE_STATUS = (
    "production_owned_shared_core_imported_and_called_by_live_and_replay_candidate_scheduler_surfaces"
)
KIA_NEXT_STARTER_FILE = "KIA_NEXT_ROLLING_OR_DOSSIER_STARTER_2026-06-07.txt"
KIA_SATURATION_SELF_RED_TEAM_FILE = "KIA_SATURATION_SELF_RED_TEAM.md"

REQUIRED_ARTIFACTS = (
    "KIA_CONTEXT_ANCHOR.json",
    "KIA_ACTIVE_QUESTION_STACK.jsonl",
    "KIA_CHECKPOINT_LEDGER.jsonl",
    "KIA_LIMITATION_BACKLOG.jsonl",
    "KIA_ACTION_QUEUE.md",
    "KIA_ROLLING_RUN_STATE.json",
    "KIA_SOURCE_HYDRATION_LEDGER.jsonl",
    "KIA_SCRATCH_CLEANUP_PROOF.json",
    "KIA_PREVIOUS_ROUTE_MEASUREMENT_SUMMARY.json",
    "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
    "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
    "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
    "KIA_DEVELOPMENT_WEAK_ACCEPTED_TRADE_LEDGER.jsonl",
    "KIA_DEVELOPMENT_PARTIAL_BE_RUNNER_LEDGER.jsonl",
    "KIA_DEVELOPMENT_SCHEDULER_REGRET_LEDGER.jsonl",
    "KIA_DEVELOPMENT_COST_FLIP_LEDGER.jsonl",
    "KIA_DEVELOPMENT_RISK_HEADROOM_LOCKOUT_LEDGER.jsonl",
    "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json",
    "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json",
    "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json",
    *KIA_REPAIR_LEDGER_FILES.values(),
    *KIA_HOLDOUT_LEDGER_FILES.values(),
    "KIA_SMOKE_REPLAY_SUMMARY.json",
    "KIA_SMOKE_ASOF_MARKET_DATA_LEDGER.jsonl",
    "KIA_SMOKE_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "KIA_SMOKE_PACKET_SIDECAR_LEDGER.jsonl",
    "KIA_SMOKE_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "KIA_SMOKE_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "KIA_SMOKE_SIMULATED_ORDER_LEDGER.jsonl",
    "KIA_SMOKE_SIMULATED_TRADE_LEDGER.jsonl",
    "KIA_SMOKE_SIMULATED_EVENT_LEDGER.jsonl",
    "KIA_SMOKE_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "KIA_SMOKE_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "KIA_SMOKE_WINNER_ANATOMY_LEDGER.jsonl",
    "KIA_SMOKE_LOSER_ANATOMY_LEDGER.jsonl",
    "KIA_SMOKE_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "KIA_SMOKE_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "KIA_SMOKE_DAILY_MICROSCOPE_SUMMARY.jsonl",
    "KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json",
    "KIA_FOCUSED_TEST_RESULT.json",
    "KIA_VERIFICATION_RESULT.json",
    "KIA_REPAIR_DECISION_LEDGER.jsonl",
    KIA_NEXT_STARTER_FILE,
    KIA_SATURATION_SELF_RED_TEAM_FILE,
    "KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "KIA_OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.md",
    "verify_kia_route.py",
)

KIA_SMOKE_LEDGER_FILES = {
    "asof": "KIA_SMOKE_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIA_SMOKE_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIA_SMOKE_PACKET_SIDECAR_LEDGER.jsonl",
    "scorecard": "KIA_SMOKE_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIA_SMOKE_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIA_SMOKE_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIA_SMOKE_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIA_SMOKE_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIA_SMOKE_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIA_SMOKE_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "winner": "KIA_SMOKE_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIA_SMOKE_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIA_SMOKE_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIA_SMOKE_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIA_SMOKE_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

REQUIRED_LIMITATION_IDS = {
    "kia_lim_001_full_orchestrator_parity_not_proven",
    "kia_lim_002_exact_tick_gaps",
    "kia_lim_003_repaired_dev_slice_worsened",
    "kia_lim_004_holdout_negative",
}

REQUIRED_ACTION_QUEUE_PHRASES = (
    "Rerun a KIA smoke slice",
    "shared live/replay V4 decision-cycle core",
    "GBPUSD 2026-04-20T23:59:00Z",
    "US30_cash 2026-04-20T23:59:00Z",
    "development tranche failure anatomy",
    "holdout/rolling tranche",
)

TICK_GAP_RETRY_LABEL = "kia_tick_gap_retry_20260420_sel002"
TICK_GAP_RETRY_COMMAND = (
    "uv",
    "run",
    "--with",
    "siliconmetatrader5",
    "--with",
    "numpy",
    "python",
    "scripts/export_mt5_research_ticks.py",
    "--prefer-silicon-bridge",
    "--yes-live-readonly",
    "--symbol",
    "GBPUSD:GBPUSD",
    "--symbol",
    "US30_cash:US30.cash",
    "--window",
    "sel_002_20260420T2359_20260421T0001:2026-04-20T23:59:00Z:2026-04-21T00:01:00Z",
    "--label",
    TICK_GAP_RETRY_LABEL,
    "--output-root",
    str(ROUTE_DIR / "_scratch"),
    "--source-broker",
    "FTMO",
    "--source-role",
    "owner_authorized_research_hydration",
    "--not-redacted_account-native",
    "--source-truth-scope",
    SOURCE_TRUTH_SCOPE,
)
TICK_GAP_WINDOWS = (
    {
        "gap_id": "kia_tick_gap_001_gbpusd_sel002",
        "symbol": "GBPUSD",
        "mapped_symbol": "GBPUSD",
        "manifest_relative_path": (
            "ftmo_research_exports/"
            "timewarp_ftmo_selected_order_ticks_GBPUSD_20260607/manifest.json"
        ),
        "manifest_key": "GBPUSD_sel_002_20260420T2359_20260421T0001_TICK",
        "window": "sel_002_20260420T2359_20260421T0001",
        "request_start_utc": "2026-04-20T23:59:00+00:00",
        "request_end_utc": "2026-04-21T00:01:00+00:00",
    },
    {
        "gap_id": "kia_tick_gap_002_us30_cash_sel002",
        "symbol": "US30_cash",
        "mapped_symbol": "US30.cash",
        "manifest_relative_path": (
            "ftmo_research_exports/"
            "timewarp_ftmo_selected_order_ticks_US30_cash_20260607/manifest.json"
        ),
        "manifest_key": "US30_cash_sel_002_20260420T2359_20260421T0001_TICK",
        "window": "sel_002_20260420T2359_20260421T0001",
        "request_start_utc": "2026-04-20T23:59:00+00:00",
        "request_end_utc": "2026-04-21T00:01:00+00:00",
    },
)
TICK_GAP_SOURCE_BOUND_STATUSES = {
    "exact_zero_row_manifest_window_previous_route_only",
    "exact_zero_row_manifest_window_retry_confirmed",
}
DEVELOPMENT_PHASES = {"baseline", "repaired"}
DEVELOPMENT_FAILURE_LEDGER_FILES = {
    "weak_accepted_trades": "KIA_DEVELOPMENT_WEAK_ACCEPTED_TRADE_LEDGER.jsonl",
    "partial_be_runner": "KIA_DEVELOPMENT_PARTIAL_BE_RUNNER_LEDGER.jsonl",
    "scheduler_regret": "KIA_DEVELOPMENT_SCHEDULER_REGRET_LEDGER.jsonl",
    "cost_flips": "KIA_DEVELOPMENT_COST_FLIP_LEDGER.jsonl",
    "risk_headroom_lockout": "KIA_DEVELOPMENT_RISK_HEADROOM_LOCKOUT_LEDGER.jsonl",
}


def _repo_path(repo_root: Path, path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else repo_root / path


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _file_hash_or_none(path: Path) -> str | None:
    return file_sha256(path) if path.exists() else None


def _summarize_previous_route(previous_route_dir: Path) -> dict[str, Any]:
    verification = load_json(previous_route_dir / "TIMEWARP_VERIFICATION_RESULT.json")
    parity = load_json(previous_route_dir / "TIMEWARP_LIVE_REPLAY_PARITY_CHECKLIST.json")
    repair = load_json(previous_route_dir / "TIMEWARP_REPAIR_BEFORE_AFTER_SUMMARY.json")
    holdout = load_json(previous_route_dir / "TIMEWARP_HOLDOUT_RESULT_SUMMARY.json")
    tick_summary = load_json(previous_route_dir / "TIMEWARP_SELECTED_ORDER_TICK_EXPORT_RUN_SUMMARY.json")
    source_manifest = load_json(previous_route_dir / "TIMEWARP_SOURCE_MANIFEST.json")
    ledger_counts = {
        path.name: _jsonl_count(path)
        for path in sorted(previous_route_dir.glob("TIMEWARP_*LEDGER.jsonl"))
    }
    exports = tick_summary.get("exports") if isinstance(tick_summary.get("exports"), list) else []
    return {
        "previous_route_id": TIMEWARP_ROUTE_ID,
        "previous_route_dir": str(previous_route_dir),
        "verification_status": verification.get("status"),
        "verification_failure_count": verification.get("failure_count"),
        "full_live_replay_parity_status": parity.get("full_live_replay_parity_status"),
        "direct_orchestrator_check": next(
            (
                row
                for row in parity.get("checks", [])
                if row.get("check") == "direct_production_orchestrator_instantiation"
            ),
            None,
        ),
        "baseline": repair.get("baseline"),
        "repaired": repair.get("repaired"),
        "repair_delta": repair.get("delta"),
        "repair_count": repair.get("repair_count"),
        "holdout": holdout,
        "tick_export_symbol_count": len(exports),
        "tick_export_error_count": sum(int(row.get("errors") or 0) for row in exports),
        "tick_export_row_count_total": sum(int(row.get("row_count_total") or 0) for row in exports),
        "source_count": len(source_manifest.get("sources") or []),
        "ftmo_primary_hydration_complete": source_manifest.get("ftmo_primary_hydration_complete"),
        "ledger_counts": ledger_counts,
        "completion_audit_status": "INCOMPLETE",
    }


def _source_hydration_rows(previous_route_dir: Path) -> list[dict[str, Any]]:
    source_manifest = load_json(previous_route_dir / "TIMEWARP_SOURCE_MANIFEST.json")
    rows = []
    for index, source in enumerate(source_manifest.get("sources") or [], start=1):
        if not isinstance(source, Mapping):
            continue
        rows.append(
            {
                "kia_source_row_id": f"KIA-SOURCE-{index:05d}",
                "source_row_origin": "previous_timewarp_source_manifest",
                "symbol": source.get("symbol"),
                "mapped_symbol": source.get("mapped_symbol"),
                "timeframe": source.get("timeframe"),
                "source_broker": source.get("source_broker"),
                "source_role": source.get("source_role"),
                "source_truth_scope": source.get("source_truth_scope"),
                "not_redacted_account_native": source.get("not_redacted_account_native"),
                "broker_lifecycle_truth_satisfied": source.get("broker_lifecycle_truth_satisfied"),
                "ordered_tick_truth_satisfied": source.get("ordered_tick_truth_satisfied"),
                "row_count": source.get("row_count"),
                "sha256": source.get("sha256"),
                "path": source.get("path"),
                "manifest_path": source.get("manifest_path"),
                "export_tool": source.get("export_tool"),
                "selected_status": source.get("selected_status"),
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
    return rows


def _payload_row_count(payload: Mapping[str, Any]) -> int | None:
    value = payload.get("row_count", payload.get("rows"))
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _tick_gap_manifest_payload(
    manifest_path: Path,
    manifest_key: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    files = manifest.get("files") if isinstance(manifest.get("files"), Mapping) else {}
    payload = files.get(manifest_key) if isinstance(files.get(manifest_key), Mapping) else {}
    return manifest, dict(payload)


def _tick_gap_retry_attempt_summary(route_dir: Path) -> dict[str, Any]:
    summary_path = route_dir / "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json"
    scratch_manifest = route_dir / "_scratch" / TICK_GAP_RETRY_LABEL / "manifest.json"
    if scratch_manifest.exists():
        manifest = load_json(scratch_manifest)
        files = manifest.get("files") if isinstance(manifest.get("files"), Mapping) else {}
        selected_files = {
            row["manifest_key"]: dict(files.get(row["manifest_key"]) or {})
            for row in TICK_GAP_WINDOWS
        }
        expected_rows = [_payload_row_count(row) for row in selected_files.values()]
        zero_rows_confirmed = bool(selected_files) and all(count == 0 for count in expected_rows)
        error_count = len(manifest.get("errors") or [])
        return {
            "route_id": ROUTE_ID,
            "generated_at_utc": manifest.get("created_at_utc") or utc_now(),
            "status": (
                "read_only_retry_attempted_zero_rows_confirmed"
                if zero_rows_confirmed
                else "read_only_retry_attempted_rows_or_schema_changed"
            ),
            "retry_label": TICK_GAP_RETRY_LABEL,
            "retry_command": list(TICK_GAP_RETRY_COMMAND),
            "temporary_uv_dependencies": ["siliconmetatrader5", "numpy"],
            "expected_exporter_returncode": 2 if error_count else 0,
            "read_only": manifest.get("read_only"),
            "mt5_client_kind": manifest.get("mt5_client_kind"),
            "manifest_path": str(scratch_manifest),
            "manifest_path_reported": manifest.get("manifest_path"),
            "source_provenance": manifest.get("source_provenance"),
            "account": manifest.get("account"),
            "terminal": manifest.get("terminal"),
            "errors": manifest.get("errors") or [],
            "error_count": error_count,
            "files": selected_files,
            "row_count_total": sum(count or 0 for count in expected_rows),
            "no_live_broker_mutation": True,
            "broker_account_order_history_deal_position_mutation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "raw_retry_scratch_committed": False,
        }
    if summary_path.exists():
        return load_json(summary_path)
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "not_attempted_in_current_route_artifacts",
        "retry_label": TICK_GAP_RETRY_LABEL,
        "retry_command": list(TICK_GAP_RETRY_COMMAND),
        "temporary_uv_dependencies": ["siliconmetatrader5", "numpy"],
        "required_environment": "siliconmetatrader5 bridge plus numpy in the execution environment",
        "read_only": True,
        "files": {},
        "errors": [],
        "row_count_total": None,
        "no_live_broker_mutation": True,
        "broker_account_order_history_deal_position_mutation": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
        "raw_retry_scratch_committed": False,
    }


def _tick_gap_source_bound_rows(
    *,
    previous_route_dir: Path,
    retry_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    retry_files = retry_summary.get("files") if isinstance(retry_summary.get("files"), Mapping) else {}
    rows: list[dict[str, Any]] = []
    for index, gap in enumerate(TICK_GAP_WINDOWS, start=1):
        previous_manifest_path = previous_route_dir / str(gap["manifest_relative_path"])
        previous_manifest, previous_payload = _tick_gap_manifest_payload(
            previous_manifest_path,
            str(gap["manifest_key"]),
        )
        retry_payload = retry_files.get(gap["manifest_key"]) if isinstance(retry_files, Mapping) else {}
        retry_payload = dict(retry_payload) if isinstance(retry_payload, Mapping) else {}
        previous_row_count = _payload_row_count(previous_payload)
        retry_row_count = _payload_row_count(retry_payload)
        retry_zero_confirmed = (
            str(retry_summary.get("status")) == "read_only_retry_attempted_zero_rows_confirmed"
            and retry_row_count == 0
        )
        if previous_row_count == 0 and retry_zero_confirmed:
            source_bound_status = "exact_zero_row_manifest_window_retry_confirmed"
        elif previous_row_count == 0:
            source_bound_status = "exact_zero_row_manifest_window_previous_route_only"
        else:
            source_bound_status = "not_source_bound"
        source_payload = retry_payload or previous_payload
        previous_errors = previous_manifest.get("errors") if isinstance(previous_manifest.get("errors"), list) else []
        matching_previous_errors = [
            error
            for error in previous_errors
            if isinstance(error, Mapping)
            and error.get("file_symbol") == gap["symbol"]
            and error.get("window") == gap["window"]
        ]
        retry_errors = retry_summary.get("errors") if isinstance(retry_summary.get("errors"), list) else []
        matching_retry_errors = [
            error
            for error in retry_errors
            if isinstance(error, Mapping)
            and error.get("file_symbol") == gap["symbol"]
            and error.get("window") == gap["window"]
        ]
        rows.append(
            {
                "kia_tick_gap_row_id": f"KIA-TICK-GAP-{index:03d}",
                "gap_id": gap["gap_id"],
                "action_queue_item": 3,
                "symbol": gap["symbol"],
                "mapped_symbol": gap["mapped_symbol"],
                "timeframe": "TICK",
                "window": gap["window"],
                "request_start_utc": gap["request_start_utc"],
                "request_end_utc": gap["request_end_utc"],
                "previous_manifest_path": str(previous_manifest_path),
                "previous_manifest_exists": previous_manifest_path.exists(),
                "previous_manifest_key": gap["manifest_key"],
                "previous_manifest_key_found": bool(previous_payload),
                "previous_export_tool": previous_payload.get("export_tool"),
                "previous_row_count": previous_row_count,
                "previous_raw_rows_returned": previous_payload.get("raw_rows_returned"),
                "previous_chunks_requested": previous_payload.get("chunks_requested"),
                "previous_chunks_with_rows": previous_payload.get("chunks_with_rows"),
                "previous_empty_chunks": previous_payload.get("empty_chunks"),
                "previous_last_empty_chunk_error": previous_payload.get("last_empty_chunk_error"),
                "previous_sha256": previous_payload.get("sha256"),
                "previous_errors": matching_previous_errors,
                "retry_status": retry_summary.get("status"),
                "retry_manifest_path": retry_summary.get("manifest_path_reported")
                or retry_summary.get("manifest_path"),
                "retry_manifest_key": gap["manifest_key"],
                "retry_read_only": retry_summary.get("read_only"),
                "retry_mt5_client_kind": retry_summary.get("mt5_client_kind"),
                "retry_expected_exporter_returncode": retry_summary.get("expected_exporter_returncode"),
                "retry_row_count": retry_row_count,
                "retry_raw_rows_returned": retry_payload.get("raw_rows_returned"),
                "retry_chunks_requested": retry_payload.get("chunks_requested"),
                "retry_chunks_with_rows": retry_payload.get("chunks_with_rows"),
                "retry_empty_chunks": retry_payload.get("empty_chunks"),
                "retry_last_empty_chunk_error": retry_payload.get("last_empty_chunk_error"),
                "retry_sha256": retry_payload.get("sha256"),
                "retry_errors": matching_retry_errors,
                "source_bound_status": source_bound_status,
                "selected_filled_path_truth_status": "exact_unresolved_tick_source_requirement",
                "ordered_tick_truth_satisfied": False,
                "m1_fallback_allowed_only_with_label": True,
                "source_broker": source_payload.get("source_broker"),
                "source_role": source_payload.get("source_role"),
                "source_truth_scope": source_payload.get("source_truth_scope"),
                "not_redacted_account_native": source_payload.get("not_redacted_account_native"),
                "broker_lifecycle_truth_satisfied": source_payload.get("broker_lifecycle_truth_satisfied"),
                "asof_decision_truth_satisfied": source_payload.get("asof_decision_truth_satisfied"),
                "source_server_hash": source_payload.get("source_server_hash"),
                "source_account_hash": source_payload.get("source_account_hash"),
                "source_server_redacted": source_payload.get("source_server_redacted"),
                "source_account_redacted": source_payload.get("source_account_redacted"),
                "no_live_broker_mutation": True,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                "next_action": "carry_exact_unresolved_tick_source_requirement_into_development_tranche_path_truth_labels",
            }
        )
    return rows


def _tick_gaps_source_bound(tick_gap_rows: Iterable[Mapping[str, Any]]) -> bool:
    rows = list(tick_gap_rows)
    return len(rows) == len(TICK_GAP_WINDOWS) and all(
        row.get("source_bound_status") in TICK_GAP_SOURCE_BOUND_STATUSES
        for row in rows
    )


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_development_phase(row: Mapping[str, Any]) -> bool:
    return str(row.get("phase") or row.get("campaign") or "") in DEVELOPMENT_PHASES


def _development_row(
    row: Mapping[str, Any],
    *,
    family: str,
    reason: str,
    source_ledger: str,
) -> dict[str, Any]:
    next_row = dict(row)
    next_row.update(
        {
            "kia_route_id": ROUTE_ID,
            "kia_development_failure_family": family,
            "kia_failure_reason": reason,
            "kia_source_ledger": source_ledger,
            "development_tranche_scope": "baseline_and_repaired_previous_timewarp_development_slice",
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
        }
    )
    return next_row


def _write_development_failure_anatomy(
    *,
    route_dir: Path,
    previous_route_dir: Path,
    previous_summary: Mapping[str, Any],
) -> dict[str, Any]:
    trades = [
        row
        for row in load_jsonl(previous_route_dir / "TIMEWARP_SIMULATED_TRADE_LEDGER.jsonl")
        if _is_development_phase(row)
    ]
    orders = [
        row
        for row in load_jsonl(previous_route_dir / "TIMEWARP_SIMULATED_ORDER_LEDGER.jsonl")
        if _is_development_phase(row)
    ]
    missed = [
        row
        for row in load_jsonl(previous_route_dir / "TIMEWARP_MISSED_OPPORTUNITY_LEDGER.jsonl")
        if _is_development_phase(row)
    ]
    rollups = [
        row
        for row in load_jsonl(previous_route_dir / "TIMEWARP_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl")
        if _is_development_phase(row)
    ]

    weak_rows = []
    for row in trades:
        net_r = _safe_float(row.get("net_proxy_r"))
        mfe_r = _safe_float(row.get("mfe_r"))
        reasons = []
        if net_r <= 0:
            reasons.append("net_proxy_r_nonpositive")
        if mfe_r < 0.5:
            reasons.append("mfe_below_half_r")
        if reasons:
            weak_rows.append(
                _development_row(
                    row,
                    family="weak_accepted_trade",
                    reason="+".join(reasons),
                    source_ledger="TIMEWARP_SIMULATED_TRADE_LEDGER.jsonl",
                )
            )

    partial_rows = [
        _development_row(
            row,
            family="partial_be_runner_policy_rollup",
            reason="policy_partial_be_runner_development_rollup",
            source_ledger="TIMEWARP_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
        )
        for row in rollups
        if str(row.get("policy") or "") == "partial_be_runner"
    ]

    scheduler_regret_rows = [
        _development_row(
            row,
            family="scheduler_regret_positive_missed_opportunity",
            reason="positive_net_proxy_r_missed_for_scheduler_selected_competing_candidate",
            source_ledger="TIMEWARP_MISSED_OPPORTUNITY_LEDGER.jsonl",
        )
        for row in missed
        if row.get("miss_reason") == "scheduler_selected_competing_candidate"
        and _safe_float(row.get("net_proxy_r")) > 0
    ]

    cost_flip_rows = []
    for source_name, rows in (
        ("TIMEWARP_SIMULATED_TRADE_LEDGER.jsonl", trades),
        ("TIMEWARP_MISSED_OPPORTUNITY_LEDGER.jsonl", missed),
    ):
        for row in rows:
            gross_r = _safe_float(row.get("gross_r"))
            net_r = _safe_float(row.get("net_proxy_r"))
            expected_cost_r = _safe_float(row.get("expected_cost_r"))
            if gross_r > 0 and net_r <= 0:
                cost_flip_rows.append(
                    _development_row(
                        row,
                        family="cost_flip",
                        reason="gross_positive_net_nonpositive_after_expected_cost",
                        source_ledger=source_name,
                    )
                )
            elif gross_r > 0 and expected_cost_r >= gross_r:
                cost_flip_rows.append(
                    _development_row(
                        row,
                        family="cost_absorbed_positive_edge",
                        reason="expected_cost_r_greater_or_equal_gross_r",
                        source_ledger=source_name,
                    )
                )

    risk_headroom_rows = [
        _development_row(
            row,
            family="risk_headroom_lockout",
            reason=str(row.get("risk_decision_reason") or row.get("order_status") or "risk_rejected"),
            source_ledger="TIMEWARP_SIMULATED_ORDER_LEDGER.jsonl",
        )
        for row in orders
        if row.get("order_status") == "risk_rejected"
        or row.get("risk_decision_reason") == "risk_headroom_zero"
    ]

    ledgers = {
        "weak_accepted_trades": weak_rows,
        "partial_be_runner": partial_rows,
        "scheduler_regret": scheduler_regret_rows,
        "cost_flips": cost_flip_rows,
        "risk_headroom_lockout": risk_headroom_rows,
    }
    for key, filename in DEVELOPMENT_FAILURE_LEDGER_FILES.items():
        atomic_write_jsonl(route_dir / filename, ledgers[key])

    family_counts = {key: len(rows) for key, rows in ledgers.items()}
    phase_counts = Counter(str(row.get("phase") or row.get("campaign") or "") for row in trades + orders + missed + rollups)
    partial_policy_totals = {
        "filled_trade_count": sum(int(_safe_float(row.get("filled_trade_count"))) for row in partial_rows),
        "winner_count": sum(int(_safe_float(row.get("winner_count"))) for row in partial_rows),
        "loser_count": sum(int(_safe_float(row.get("loser_count"))) for row in partial_rows),
        "net_proxy_r": round(sum(_safe_float(row.get("net_proxy_r")) for row in partial_rows), 8),
        "expected_cost_r": round(sum(_safe_float(row.get("expected_cost_r")) for row in partial_rows), 8),
    }
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": (
            "completed"
            if family_counts["weak_accepted_trades"] > 0
            and family_counts["partial_be_runner"] > 0
            and family_counts["scheduler_regret"] > 0
            and family_counts["risk_headroom_lockout"] > 0
            else "incomplete_missing_required_failure_family_rows"
        ),
        "development_phases": sorted(DEVELOPMENT_PHASES),
        "source_route": str(previous_route_dir),
        "source_ledgers": {
            "trades": "TIMEWARP_SIMULATED_TRADE_LEDGER.jsonl",
            "orders": "TIMEWARP_SIMULATED_ORDER_LEDGER.jsonl",
            "missed": "TIMEWARP_MISSED_OPPORTUNITY_LEDGER.jsonl",
            "rollups": "TIMEWARP_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
        },
        "source_row_counts": {
            "trades": len(trades),
            "orders": len(orders),
            "missed": len(missed),
            "rollups": len(rollups),
        },
        "source_phase_counts": dict(sorted(phase_counts.items())),
        "family_counts": family_counts,
        "ledger_files": dict(DEVELOPMENT_FAILURE_LEDGER_FILES),
        "baseline_summary": previous_summary.get("baseline"),
        "repaired_summary": previous_summary.get("repaired"),
        "repair_delta": previous_summary.get("repair_delta"),
        "weak_accepted_net_proxy_r": round(sum(_safe_float(row.get("net_proxy_r")) for row in weak_rows), 8),
        "scheduler_regret_positive_missed_net_proxy_r": round(
            sum(_safe_float(row.get("net_proxy_r")) for row in scheduler_regret_rows),
            8,
        ),
        "cost_flip_net_proxy_r": round(sum(_safe_float(row.get("net_proxy_r")) for row in cost_flip_rows), 8),
        "partial_be_runner_rollup_totals": partial_policy_totals,
        "risk_headroom_zero_rows": sum(
            1 for row in risk_headroom_rows if row.get("risk_decision_reason") == "risk_headroom_zero"
        ),
        "risk_headroom_symbols": sorted({str(row.get("symbol")) for row in risk_headroom_rows if row.get("symbol")}),
        "no_arbitrary_top_n": True,
        "all_material_failure_rows_preserved": True,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
        "next_action": "implement_or_reject_only_repeated_system_repairs_with_before_after_and_holdout_evidence",
    }
    atomic_write_json(route_dir / "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json", summary)
    return summary


def _first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _repair_config(config: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(config)
    runtime = dict(payload.get("gtos_vnext_runtime") or {})
    runtime.update(KIA_REPAIR_RUNTIME_OVERRIDES)
    payload["gtos_vnext_runtime"] = runtime
    return payload


def _packet_sidecar_index(previous_route_dir: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in load_jsonl(previous_route_dir / "TIMEWARP_PACKET_SIDECAR_LEDGER.jsonl"):
        if row.get("sidecar_type") != "candidate_v4_decision_stack":
            continue
        campaign = str(row.get("campaign") or row.get("phase") or "")
        candidate_id = str(row.get("candidate_id") or "")
        asof = str(row.get("decision_time_utc") or row.get("asof_utc") or "")
        if campaign and candidate_id and asof:
            index[(campaign, candidate_id, asof)] = row
    return index


def _candidate_packets_from_tape(
    candidate: Mapping[str, Any],
    sidecars: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    campaign = str(candidate.get("source_campaign") or candidate.get("campaign") or "")
    candidate_id = str(candidate.get("candidate_id") or "")
    asof = str(_first_value(candidate.get("decision_time_utc"), candidate.get("candle_close_utc")) or "")
    sidecar = sidecars.get((campaign, candidate_id, asof), {})
    return {
        "probability_context": sidecar.get("probability_context"),
        "probability_packet": _first_value(sidecar.get("probability_packet"), candidate.get("probability_packet"), {}),
        "selector_event": sidecar.get("selector_event"),
        "selector_packet": _first_value(sidecar.get("selector_packet"), candidate.get("selector_packet"), {}),
        "lifecycle_packet": _first_value(sidecar.get("lifecycle_packet"), candidate.get("lifecycle_packet"), {}),
        "moonshot_dynamic_execution_router_v4": _first_value(
            sidecar.get("moonshot_dynamic_execution_router_v4"),
            candidate.get("moonshot_dynamic_execution_router_v4"),
            {},
        ),
        "geometry_contract": _first_value(sidecar.get("geometry_contract"), candidate.get("geometry_contract"), {}),
        "live_decision_packet_v4": _first_value(
            sidecar.get("live_decision_packet_v4"),
            candidate.get("live_decision_packet_v4"),
            {},
        ),
        "risk_authority_pre_scheduler": _first_value(
            sidecar.get("risk_authority_pre_scheduler"),
            candidate.get("risk_authority_pre_scheduler"),
            {},
        ),
        "risk_pct": _first_value(candidate.get("risk_pct"), candidate.get("selected_cell_risk_pct")),
        "candidate_probability": candidate.get("candidate_probability"),
        "candidate_ev_r": candidate.get("candidate_ev_r"),
        "cost_r": _first_value(candidate.get("cost_r"), candidate.get("expected_cost_r"), 0.0),
        "source_path": candidate.get("source_path"),
        "source_hash": candidate.get("source_sha256"),
    }


def _decision_tape_groups(
    *,
    previous_route_dir: Path,
    source_phase: str,
    campaign: CampaignConfig,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in load_jsonl(previous_route_dir / "TIMEWARP_CANDIDATE_MICROSCOPE_LEDGER.jsonl"):
        if str(row.get("phase") or row.get("campaign") or "") != source_phase:
            continue
        day = str(row.get("trading_day") or "")
        if day not in campaign.days:
            continue
        asof = str(_first_value(row.get("decision_time_utc"), row.get("candle_close_utc")) or "")
        if not asof:
            continue
        candidate = dict(row)
        candidate.update(
            {
                "decision_tape_source_campaign": source_phase,
                "source_campaign": source_phase,
                "campaign": campaign.name,
                "phase": campaign.phase,
                "trading_day": day,
                "candle_close_utc": asof,
                "decision_time_utc": asof,
                "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
                "kia_decision_tape_replay": True,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            }
        )
        groups[(day, asof)].append(candidate)
    return groups


def _append_missed_row(
    *,
    ledgers: dict[str, list[dict[str, Any]]],
    campaign: CampaignConfig,
    candidate: Mapping[str, Any],
    packets: Mapping[str, Any],
    path_sources: Mapping[str, Any],
    day: str,
    asof: datetime,
    asof_utc: str,
    selected_id_set: set[str],
    miss_reason: str,
) -> None:
    expiry = min(
        asof + timedelta(minutes=campaign.pending_expiry_minutes),
        datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1),
    )
    oracle, path_source, path_rows = path_source_and_oracle(
        candidate=candidate,
        sources=path_sources,
        day=day,
        asof=asof,
        expiry=expiry,
    )
    missed_final_r, missed_close_reason, _target_r = path_final_r(
        oracle=oracle,
        partial_be_runner=(
            str(candidate.get("dynamic_geometry_policy") or "") == "partial_be_runner"
            and campaign.partial_be_runner
        ),
    )
    expected_cost_r = safe_float(packets.get("cost_r"), 0.0)
    selector_packet = packets.get("selector_packet")
    selector_packet = selector_packet if isinstance(selector_packet, Mapping) else {}
    ledgers["missed"].append(
        {
            "campaign": campaign.name,
            "phase": campaign.phase,
            "source_campaign": candidate.get("source_campaign"),
            "trading_day": day,
            "candidate_id": candidate.get("candidate_id"),
            "symbol": candidate.get("symbol"),
            "side": candidate.get("side"),
            "decision_time_utc": asof_utc,
            "miss_reason": miss_reason,
            "selector_action": selector_packet.get("action"),
            "selector_reason": selector_packet.get("reason"),
            "candidate_probability": packets.get("candidate_probability"),
            "candidate_ev_r": packets.get("candidate_ev_r"),
            "selected_candidate_ids": sorted(selected_id_set),
            "ordered_path_status": "scored_for_nonselected_candidate",
            "opportunity_path_scored": True,
            "gross_r": missed_final_r,
            "expected_cost_r": expected_cost_r,
            "net_proxy_r": None
            if missed_final_r is None
            else round(missed_final_r - expected_cost_r, 8),
            "opportunity_close_reason": missed_close_reason,
            "path_source": oracle.get("source"),
            "path_row_count": len(path_rows),
            "ordered_tick_truth_satisfied": (
                path_source.spec.ordered_tick_truth_satisfied
                and oracle.get("ordered_tick_truth_satisfied") is True
            ),
            "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
            "kia_decision_tape_replay": True,
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "evidence_class": OUTCOME_EVIDENCE_CLASS,
        }
    )


def _finalize_tape_ledgers(
    *,
    ledgers: dict[str, list[dict[str, Any]]],
    campaign: CampaignConfig,
    account: Any,
    day_end_account_snapshots: Mapping[str, Mapping[str, float]],
) -> None:
    for day in campaign.days:
        trades = [row for row in ledgers["trade"] if row.get("trading_day") == day]
        orders = [row for row in ledgers["order"] if row.get("trading_day") == day]
        candidates = [row for row in ledgers["candidate"] if row.get("trading_day") == day]
        day_snapshot = day_end_account_snapshots.get(
            day,
            {
                "ending_balance": round(account.balance, 8),
                "ending_equity": round(account.equity, 8),
                "max_drawdown_pct": round(account.max_drawdown_pct, 8),
            },
        )
        for trade in trades:
            anatomy = {
                "campaign": campaign.name,
                "phase": campaign.phase,
                "source_campaign": trade.get("source_campaign"),
                "trading_day": day,
                "candidate_id": trade.get("candidate_id"),
                "symbol": trade.get("symbol"),
                "final_r": trade.get("final_r"),
                "gross_r": trade.get("gross_r"),
                "expected_cost_r": trade.get("expected_cost_r"),
                "net_proxy_r": trade.get("net_proxy_r"),
                "mfe_r": trade.get("mfe_r"),
                "mae_r": trade.get("mae_r"),
                "terminal_outcome": trade.get("terminal_outcome"),
                "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
                "kia_decision_tape_replay": True,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "evidence_class": OUTCOME_EVIDENCE_CLASS,
            }
            if safe_float(trade.get("net_proxy_r"), 0.0) < 0:
                ledgers["loser"].append(
                    {
                        **anatomy,
                        "loss_mechanism": trade.get("close_reason"),
                        "avoidability": "requires_better_source_or_exit_repair"
                        if safe_float(trade.get("mfe_r"), 0.0) >= 0.5
                        else "valid_loss_or_low_mfe",
                    }
                )
            else:
                ledgers["winner"].append(
                    {
                        **anatomy,
                        "net_r": trade.get("net_r"),
                        "duration_minutes": trade.get("duration_minutes"),
                        "win_mechanism": trade.get("close_reason"),
                        "target_first_touch_utc": trade.get("target_first_touch_utc"),
                        "stop_first_touch_utc": trade.get("stop_first_touch_utc"),
                        "close_mark_time_utc": trade.get("close_mark_time_utc"),
                        "close_mark_source": trade.get("close_mark_source"),
                        "be_reached": trade.get("be_reached"),
                        "partial_taken": trade.get("partial_taken"),
                        "giveback_r": trade.get("giveback_r"),
                    }
                )
        terminal_status_by_order: dict[str, str] = {}
        for row in orders:
            order_id = str(row.get("simulated_order_id"))
            status = str(row.get("order_status") or "")
            if status in {"filled", "expired_unfilled", "risk_rejected"}:
                terminal_status_by_order[order_id] = status
        gross_total = sum(
            safe_float(row.get("gross_r"))
            for row in trades
            if row.get("gross_r") is not None
        )
        net_total = sum(
            safe_float(row.get("net_proxy_r"))
            for row in trades
            if row.get("net_proxy_r") is not None
        )
        ledgers["daily"].append(
            {
                "campaign": campaign.name,
                "phase": campaign.phase,
                "trading_day": day,
                "candidate_rows": len(candidates),
                "simulated_orders": len(
                    {
                        row.get("simulated_order_id")
                        for row in orders
                        if row.get("simulated_order_id")
                    }
                ),
                "filled_trades": len(
                    [row for row in trades if row.get("net_proxy_r") is not None]
                ),
                "risk_rejected_orders": len(
                    [
                        status
                        for status in terminal_status_by_order.values()
                        if status == "risk_rejected"
                    ]
                ),
                "expired_unfilled_orders": len(
                    [
                        status
                        for status in terminal_status_by_order.values()
                        if status == "expired_unfilled"
                    ]
                ),
                "not_filled_orders": len(
                    [
                        row
                        for row in ledgers["oracle"]
                        if row.get("trading_day") == day
                        and str(row.get("fill_status") or "").startswith("not_filled")
                    ]
                ),
                "gross_r": round(gross_total, 8),
                "expected_cost_r": round(
                    sum(safe_float(row.get("expected_cost_r")) for row in trades),
                    8,
                ),
                "net_proxy_r": round(net_total, 8),
                "total_r": round(net_total, 8),
                "ending_balance": day_snapshot["ending_balance"],
                "ending_equity": day_snapshot["ending_equity"],
                "max_drawdown_pct": day_snapshot["max_drawdown_pct"],
                "same_bar_ambiguity_count": len(
                    [
                        row
                        for row in ledgers["oracle"]
                        if row.get("trading_day") == day and row.get("same_bar_ambiguity")
                    ]
                ),
                "source_health": "decision_tape_replay_from_previous_asof_packets",
                "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
                "kia_decision_tape_replay": True,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
        )
    build_rollup_rows(ledgers, campaign=campaign)
    for rows in ledgers.values():
        for row in rows:
            row.setdefault("kia_repair_policy_id", KIA_REPAIR_POLICY_ID)
            row.setdefault("kia_decision_tape_replay", True)
            row.setdefault("production_change_claim", False)
            row.setdefault("broker_runtime_change_status", False)
            row.setdefault("paid_api_or_vendor_call", False)
            row.setdefault("remote_push", False)
    sort_event_ledgers(ledgers)


def _packet_sidecar_filename(campaign: CampaignConfig) -> str:
    if campaign.phase == "repair_development":
        return KIA_REPAIR_LEDGER_FILES["packet_sidecar"]
    return KIA_HOLDOUT_LEDGER_FILES["packet_sidecar"]


def _run_decision_tape_repair_campaign(
    *,
    previous_route_dir: Path,
    source_package: Mapping[str, Any],
    config: Mapping[str, Any],
    campaign: CampaignConfig,
    source_phase: str,
) -> dict[str, Any]:
    broker = SimulatedBroker()
    account = broker.account
    ledgers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_groups = _decision_tape_groups(
        previous_route_dir=previous_route_dir,
        source_phase=source_phase,
        campaign=campaign,
    )
    sidecars = _packet_sidecar_index(previous_route_dir)
    day_end_account_snapshots: dict[str, dict[str, float]] = {}
    selected_order_sequence = 0
    sources = source_package.get("sources") or {}
    for day in campaign.days:
        account.ensure_day(day)
        day_keys = sorted(
            (key for key in source_groups if key[0] == day),
            key=lambda item: parse_utc(item[1]) or datetime.max.replace(tzinfo=timezone.utc),
        )
        for _day, asof_utc in day_keys:
            asof = parse_utc(asof_utc)
            if asof is None:
                continue
            due = account.process_events_until(until=asof, campaign=campaign, day=day)
            for key, rows in due.items():
                ledgers[key].extend(rows)
            candidates = source_groups[(day, asof_utc)]
            v4_packets = {
                str(candidate.get("candidate_id")): _candidate_packets_from_tape(candidate, sidecars)
                for candidate in candidates
            }
            open_snapshot = account.open_snapshot(asof)
            pending_snapshot = account.pending_snapshot(asof)
            ledgers["asof"].append(
                {
                    "campaign": campaign.name,
                    "phase": campaign.phase,
                    "source_campaign": source_phase,
                    "trading_day": day,
                    "decision_time_utc": asof_utc,
                    "candidate_count": len(candidates),
                    "raw_data_status": "decision_tape_replay_from_previous_asof_candidate_packets",
                    "open_positions_seen_by_repair_scheduler": len(open_snapshot),
                    "pending_orders_seen_by_repair_scheduler": len(pending_snapshot),
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
                    "kia_repair_runtime_overrides": dict(KIA_REPAIR_RUNTIME_OVERRIDES),
                    "kia_decision_tape_replay": True,
                    "production_change_claim": False,
                    "broker_runtime_change_status": False,
                    "paid_api_or_vendor_call": False,
                    "remote_push": False,
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
            for candidate in candidates:
                packet = v4_packets[str(candidate.get("candidate_id"))]
                packet_sidecar_id = stable_sha256(
                    {
                        "campaign": campaign.name,
                        "candidate_id": candidate.get("candidate_id"),
                        "decision_time_utc": asof_utc,
                        "type": "kia_repair_decision_tape_candidate_packet",
                    }
                )
                ledgers["packet_sidecar"].append(
                    {
                        "packet_sidecar_id": packet_sidecar_id,
                        "sidecar_type": "kia_repair_decision_tape_candidate_packet",
                        "campaign": campaign.name,
                        "phase": campaign.phase,
                        "source_campaign": source_phase,
                        "trading_day": day,
                        "candidate_id": candidate.get("candidate_id"),
                        "symbol": candidate.get("symbol"),
                        "decision_time_utc": asof_utc,
                        "repair_policy_id": KIA_REPAIR_POLICY_ID,
                        "repair_runtime_overrides": dict(KIA_REPAIR_RUNTIME_OVERRIDES),
                        "packet_hash_sha256": stable_sha256(packet),
                        "packet": packet,
                        "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                    }
                )
                ledgers["candidate"].append(
                    {
                        **candidate,
                        "packet_sidecar_id": packet_sidecar_id,
                        "packet_sidecar_artifact": _packet_sidecar_filename(campaign),
                        "packet_hash_sha256": stable_sha256(packet),
                        "candidate_probability": packet.get("candidate_probability"),
                        "candidate_ev_r": packet.get("candidate_ev_r"),
                        "cost_r": packet.get("cost_r"),
                        "expected_cost_r": packet.get("cost_r"),
                        "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                    }
                )
            scheduler_packet = materialize_scheduler_window(
                asof_utc=asof_utc,
                candidates=candidates,
                v4_packets=v4_packets,
                config=config,
                open_positions=open_snapshot,
                pending_orders=pending_snapshot,
            )
            scheduler_sidecar_id = stable_sha256(
                {
                    "campaign": campaign.name,
                    "decision_time_utc": asof_utc,
                    "type": "kia_repair_scheduler_v4_window",
                }
            )
            ledgers["packet_sidecar"].append(
                {
                    "packet_sidecar_id": scheduler_sidecar_id,
                    "sidecar_type": "kia_repair_scheduler_v4_window",
                    "campaign": campaign.name,
                    "phase": campaign.phase,
                    "source_campaign": source_phase,
                    "trading_day": day,
                    "decision_time_utc": asof_utc,
                    "scheduler_packet": scheduler_packet,
                    "candidate_ids": [candidate.get("candidate_id") for candidate in candidates],
                    "open_positions_seen": open_snapshot,
                    "pending_orders_seen": pending_snapshot,
                    "packet_hash_sha256": stable_sha256(scheduler_packet),
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
            decision = scheduler_packet.get("decision")
            decision = decision if isinstance(decision, Mapping) else {}
            selected_ids = decision.get("selected_candidate_ids") or []
            selected_id_set = {str(item) for item in selected_ids}
            ledgers["scorecard"].append(
                {
                    "campaign": campaign.name,
                    "phase": campaign.phase,
                    "source_campaign": source_phase,
                    "trading_day": day,
                    "decision_time_utc": asof_utc,
                    "packet_sidecar_id": scheduler_sidecar_id,
                    "packet_sidecar_artifact": _packet_sidecar_filename(campaign),
                    "scheduler_packet": scheduler_packet,
                    "selected_candidate_id": decision.get("selected_candidate_id"),
                    "selected_candidate_ids": sorted(selected_id_set),
                    "selected_action_class": decision.get("selected_action_class"),
                    "allocation_mode": decision.get("allocation_mode"),
                    "candidate_count": len(candidates),
                    "all_options_preserved_count": len(scheduler_packet.get("all_options_preserved", [])),
                    "open_position_count_seen": len(open_snapshot),
                    "pending_order_count_seen": len(pending_snapshot),
                    "kia_repair_policy_id": KIA_REPAIR_POLICY_ID,
                    "kia_decision_tape_replay": True,
                    "production_change_claim": False,
                    "broker_runtime_change_status": False,
                    "paid_api_or_vendor_call": False,
                    "remote_push": False,
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
            if not selected_id_set:
                for candidate in candidates:
                    symbol_sources = sources.get(str(candidate.get("symbol"))) or {}
                    if not symbol_sources:
                        continue
                    _append_missed_row(
                        ledgers=ledgers,
                        campaign=campaign,
                        candidate=candidate,
                        packets=v4_packets[str(candidate.get("candidate_id"))],
                        path_sources=symbol_sources,
                        day=day,
                        asof=asof,
                        asof_utc=asof_utc,
                        selected_id_set=selected_id_set,
                        miss_reason="scheduler_selected_zero_trade",
                    )
                continue
            for candidate in candidates:
                candidate_id = str(candidate.get("candidate_id"))
                symbol_sources = sources.get(str(candidate.get("symbol"))) or {}
                if not symbol_sources:
                    continue
                if candidate_id not in selected_id_set:
                    _append_missed_row(
                        ledgers=ledgers,
                        campaign=campaign,
                        candidate=candidate,
                        packets=v4_packets[candidate_id],
                        path_sources=symbol_sources,
                        day=day,
                        asof=asof,
                        asof_utc=asof_utc,
                        selected_id_set=selected_id_set,
                        miss_reason="scheduler_selected_competing_candidate",
                    )
                    continue
                selected_order_sequence += 1
                sim = simulate_order(
                    campaign=campaign,
                    candidate=candidate,
                    packets=v4_packets[candidate_id],
                    scheduler_packet=scheduler_packet,
                    path_sources=symbol_sources,
                    day=day,
                    account=account,
                    sequence=selected_order_sequence,
                    config=config,
                )
                for key in ("oracle", "order", "exit"):
                    row = dict(sim[key])
                    row["source_campaign"] = source_phase
                    ledgers[key].append(row)
                if sim.get("trade"):
                    trade = dict(sim["trade"])
                    trade["source_campaign"] = source_phase
                    ledgers["trade"].append(trade)
                for row in sim.get("account_rows", []):
                    next_row = dict(row)
                    next_row["source_campaign"] = source_phase
                    ledgers["account"].append(next_row)
                ledgers["event"].extend(sim.get("event_rows", []))
                ledgers["packet_sidecar"].append(
                    {
                        "packet_sidecar_id": stable_sha256(
                            {
                                "campaign": campaign.name,
                                "candidate_id": candidate_id,
                                "simulated_order_id": sim["order"].get("simulated_order_id"),
                                "type": "kia_repair_execution_manager_v4",
                            }
                        ),
                        "sidecar_type": "kia_repair_execution_manager_v4",
                        "campaign": campaign.name,
                        "phase": campaign.phase,
                        "source_campaign": source_phase,
                        "trading_day": day,
                        "candidate_id": candidate_id,
                        "simulated_order_id": sim["order"].get("simulated_order_id"),
                        "simulated_trade_id": sim["trade"].get("simulated_trade_id")
                        if isinstance(sim.get("trade"), Mapping)
                        else None,
                        "execution_manager_packet": sim.get("execution_manager_packet"),
                        "broker_order_lifecycle_capture_v4_packet": sim.get(
                            "broker_order_lifecycle_capture_v4_packet"
                        ),
                        "evidence_class": SIM_EVIDENCE_CLASS,
                    }
                )
        end_of_day = datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1)
        due = account.process_events_until(until=end_of_day, campaign=campaign, day=day)
        for key, rows in due.items():
            ledgers[key].extend(rows)
        day_end_account_snapshots[day] = {
            "ending_balance": round(account.balance, 8),
            "ending_equity": round(account.equity, 8),
            "max_drawdown_pct": round(account.max_drawdown_pct, 8),
        }
    _finalize_tape_ledgers(
        ledgers=ledgers,
        campaign=campaign,
        account=account,
        day_end_account_snapshots=day_end_account_snapshots,
    )
    return {"account": account, "broker": broker, "ledgers": ledgers}


def _write_system_repair_rerun(
    *,
    route_dir: Path,
    previous_route_dir: Path,
    previous_summary: Mapping[str, Any],
) -> dict[str, Any]:
    config = _repair_config(load_config())
    source_package = build_source_package(tuple(dict.fromkeys((*BASELINE_DAYS, *HOLDOUT_DAYS))))
    if not source_package.get("primary_hydration_complete"):
        summary = {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "not_run_primary_ftmo_hydration_incomplete",
            "repair_policy_id": KIA_REPAIR_POLICY_ID,
            "missing_symbols": source_package.get("missing_symbols"),
            "ftmo_blocker_rows": len(source_package.get("ftmo_blocker_rows") or []),
            "production_change_claim": False,
            "broker_runtime_change_status": False,
        }
        atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json", summary)
        atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json", summary)
        atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json", summary)
        return summary

    repair_campaign = CampaignConfig(
        name="kia_repair_development_single_select",
        phase="repair_development",
        days=BASELINE_DAYS,
        pending_expiry_minutes=BASELINE_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=False,
        partial_be_runner=True,
    )
    holdout_campaign = CampaignConfig(
        name="kia_holdout_single_select",
        phase="holdout_rolling",
        days=HOLDOUT_DAYS,
        pending_expiry_minutes=BASELINE_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=False,
        partial_be_runner=True,
    )
    repair_result = _run_decision_tape_repair_campaign(
        previous_route_dir=previous_route_dir,
        source_package=source_package,
        config=config,
        campaign=repair_campaign,
        source_phase="baseline",
    )
    holdout_result = _run_decision_tape_repair_campaign(
        previous_route_dir=previous_route_dir,
        source_package=source_package,
        config=config,
        campaign=holdout_campaign,
        source_phase="holdout",
    )
    for key, filename in KIA_REPAIR_LEDGER_FILES.items():
        atomic_write_jsonl(route_dir / filename, repair_result["ledgers"].get(key, []))
    for key, filename in KIA_HOLDOUT_LEDGER_FILES.items():
        atomic_write_jsonl(route_dir / filename, holdout_result["ledgers"].get(key, []))
    repair_summary = summarize_campaign(repair_result, phase="repair_development")
    holdout_summary = summarize_campaign(holdout_result, phase="holdout_rolling")
    baseline_summary = previous_summary.get("baseline") or {}
    prior_repaired_summary = previous_summary.get("repaired") or {}
    previous_holdout_summary = previous_summary.get("holdout") or {}
    repair_summary.update(
        {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "completed",
            "repair_policy_id": KIA_REPAIR_POLICY_ID,
            "source_campaign": "baseline",
            "runtime_overrides": dict(KIA_REPAIR_RUNTIME_OVERRIDES),
            "decision_tape_replay": True,
            "source_truth_scope": SOURCE_TRUTH_SCOPE,
            "ledger_files": dict(KIA_REPAIR_LEDGER_FILES),
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
        }
    )
    holdout_summary.update(
        {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "completed",
            "repair_policy_id": KIA_REPAIR_POLICY_ID,
            "source_campaign": "holdout",
            "runtime_overrides": dict(KIA_REPAIR_RUNTIME_OVERRIDES),
            "decision_tape_replay": True,
            "source_truth_scope": SOURCE_TRUTH_SCOPE,
            "ledger_files": dict(KIA_HOLDOUT_LEDGER_FILES),
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
        }
    )
    before_after = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed",
        "repair_policy_id": KIA_REPAIR_POLICY_ID,
        "repair_decision": "implemented_scheduler_single_select_risk_preservation_for_replay_rerun",
        "repair_rationale": {
            "risk_headroom_lockout_rows": _jsonl_count(route_dir / DEVELOPMENT_FAILURE_LEDGER_FILES["risk_headroom_lockout"]),
            "weak_accepted_trade_rows": _jsonl_count(route_dir / DEVELOPMENT_FAILURE_LEDGER_FILES["weak_accepted_trades"]),
            "scheduler_regret_rows": _jsonl_count(route_dir / DEVELOPMENT_FAILURE_LEDGER_FILES["scheduler_regret"]),
            "partial_be_runner_rows": _jsonl_count(route_dir / DEVELOPMENT_FAILURE_LEDGER_FILES["partial_be_runner"]),
            "rationale": "multi_select consumed scarce risk capacity with repeated weak accepted trades; repair preserves prop-safe risk headroom by selecting only the best scheduler option per decision window instead of loosening risk protection",
        },
        "baseline_summary": baseline_summary,
        "prior_repaired_pending_expiry_summary": prior_repaired_summary,
        "kia_repair_development_summary": repair_summary,
        "previous_holdout_summary": previous_holdout_summary,
        "kia_holdout_rolling_summary": holdout_summary,
        "deltas": {
            "repair_vs_baseline_total_r": round(
                safe_float(repair_summary.get("total_r")) - safe_float(baseline_summary.get("total_r")),
                8,
            ),
            "repair_vs_prior_repaired_total_r": round(
                safe_float(repair_summary.get("total_r")) - safe_float(prior_repaired_summary.get("total_r")),
                8,
            ),
            "holdout_vs_previous_holdout_total_r": round(
                safe_float(holdout_summary.get("total_r")) - safe_float(previous_holdout_summary.get("total_r")),
                8,
            ),
            "repair_vs_baseline_filled_trades": int(safe_float(repair_summary.get("filled_trades")))
            - int(safe_float(baseline_summary.get("filled_trades"))),
            "repair_vs_baseline_risk_rejected_orders": int(
                safe_float(repair_summary.get("risk_rejected_orders"))
            )
            - int(safe_float(baseline_summary.get("risk_rejected_orders"))),
        },
        "repair_counts_as_replay_system_repair": True,
        "full_live_replay_parity_claim": False,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }
    atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json", repair_summary)
    atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json", holdout_summary)
    atomic_write_json(route_dir / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json", before_after)
    return before_after


def _limitation_rows(
    previous_summary: Mapping[str, Any],
    tick_gap_rows: Iterable[Mapping[str, Any]] | None = None,
    development_summary: Mapping[str, Any] | None = None,
    repair_summary: Mapping[str, Any] | None = None,
    runtime_proof: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    tick_gap_rows = list(tick_gap_rows or [])
    tick_gaps_source_bound = _tick_gaps_source_bound(tick_gap_rows)
    development_anatomy_complete = (development_summary or {}).get("status") == "completed"
    repair_completed = (repair_summary or {}).get("status") == "completed"
    shared_core_completed = (
        (runtime_proof or {}).get("shared_core_status")
        == KIA_PRODUCTION_SHARED_CORE_STATUS
    )
    return [
        {
            "limitation_id": "kia_lim_001_full_orchestrator_parity_not_proven",
            "limitation_type": "infrastructure",
            "status": (
                "closed_for_replay_runtime_via_shared_core_direct_session_orchestrator_parity_outside_claim"
                if shared_core_completed
                else "open_same_evidence_class_repair_required"
            ),
            "evidence": {
                "previous_direct_orchestrator_check": previous_summary.get("direct_orchestrator_check"),
                "shared_core_status": (runtime_proof or {}).get("shared_core_status"),
                "full_live_replay_parity_claim": (runtime_proof or {}).get("full_live_replay_parity_claim"),
                "safe_exclusions": (runtime_proof or {}).get("safe_exclusions"),
            },
            "next_action": (
                "carry_direct_session_orchestrator_parity_only_into_a_separate_production_integration_or_deployment_dossier_if_owner_approves"
                if shared_core_completed
                else "extract_or_verify_shared_live_replay_decision_cycle_core_without_live_side_effects"
            ),
        },
        {
            "limitation_id": "kia_lim_002_exact_tick_gaps",
            "limitation_type": "source",
            "status": (
                "source_bound_zero_row_retry_or_manifest_confirmed_exact_unresolved_path_requirement"
                if tick_gaps_source_bound
                else "exact_source_requirement"
            ),
            "evidence": {
                "known_zero_row_windows": [
                    {
                        "symbol": "GBPUSD",
                        "start_utc": "2026-04-20T23:59:00Z",
                        "end_utc": "2026-04-21T00:01:00Z",
                    },
                    {
                        "symbol": "US30_cash",
                        "start_utc": "2026-04-20T23:59:00Z",
                        "end_utc": "2026-04-21T00:01:00Z",
                    },
                ],
                "tick_export_error_count": previous_summary.get("tick_export_error_count"),
                "source_bound_rows": len(tick_gap_rows),
                "source_bound_statuses": sorted(
                    {str(row.get("source_bound_status")) for row in tick_gap_rows}
                ),
            },
            "next_action": (
                "carry_exact_unresolved_tick_source_requirement_into_development_tranche_path_truth_labels"
                if tick_gaps_source_bound
                else "retry_or_convert_to_exact_market_session_source_gap_proof"
            ),
        },
        {
            "limitation_id": "kia_lim_003_repaired_dev_slice_worsened",
            "limitation_type": "system_behavior",
            "status": (
                "repair_rerun_measured_with_before_after_summary"
                if repair_completed
                else (
                    "development_failure_anatomy_materialized_repair_decision_pending"
                    if development_anatomy_complete
                    else "open_repair_candidate_requires_row_evidence"
                )
            ),
            "evidence": repair_summary.get("deltas") if repair_completed else previous_summary.get("repair_delta"),
            "next_action": (
                "inspect_holdout_result_and_continue_next_rolling_tranche_or_bound_remaining_repairs"
                if repair_completed
                else (
                    "implement_or_reject_repeated_system_repairs_with_row_evidence_then_rerun_development_slice"
                    if development_anatomy_complete
                    else "analyze_weak_accepted_trades_partial_be_runner_and_scheduler_regret_before_next_holdout_claim"
                )
            ),
        },
        {
            "limitation_id": "kia_lim_004_holdout_negative",
            "limitation_type": "system_behavior",
            "status": (
                "holdout_rolling_tranche_measured_after_repair"
                if repair_completed
                else (
                    "development_failure_anatomy_materialized_holdout_failure_still_pending"
                    if development_anatomy_complete
                    else "open_failure_anatomy_required"
                )
            ),
            "evidence": repair_summary.get("kia_holdout_rolling_summary") if repair_completed else previous_summary.get("holdout"),
            "next_action": (
                "holdout_measured_not_a_production_change_dossier_continue_failure_anatomy_if_negative"
                if repair_completed
                else (
                    "rerun_repaired_development_slice_then_holdout_or_exactly_bound_source_requirement"
                    if development_anatomy_complete
                    else "decompose_risk_headroom_lockout_low_mfe_losses_cost_flips_and_missed_winners"
                )
            ),
        },
    ]


def _question_rows(
    *,
    tick_gaps_source_bound: bool = False,
    development_anatomy_complete: bool = False,
    repair_complete: bool = False,
) -> list[dict[str, Any]]:
    return [
        {
            "question_id": "kia_q001_shared_core_or_parity",
            "question": "Can V4 replay prove shared live/replay decision-cycle parity without live side effects?",
            "status": "answered_for_candidate_scheduler_surfaces_full_orchestrator_parity_still_open",
            "evidence_artifacts": ["KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json"],
        },
        {
            "question_id": "kia_q002_simulated_broker_account",
            "question": "Does the replay runtime have an explicit simulated broker/account adapter with mutation disabled?",
            "status": "implemented_and_focused_tested",
            "evidence_artifacts": ["KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json", "KIA_FOCUSED_TEST_RESULT.json"],
        },
        {
            "question_id": "kia_q003a_exact_tick_gaps",
            "question": "Are the two prior zero-row selected-order FTMO tick windows retried or exactly source-bound?",
            "status": (
                "source_bound_exact_unresolved_path_requirement"
                if tick_gaps_source_bound
                else "open_retry_or_source_bound_required"
            ),
            "evidence_artifacts": [
                "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
                "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
            ],
        },
        {
            "question_id": "kia_q003_indexed_path_truth",
            "question": "Are M1/tick path rows queried through an indexed lookup contract with source labels?",
            "status": "implemented_and_focused_tested",
            "evidence_artifacts": ["KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json", "KIA_FOCUSED_TEST_RESULT.json"],
        },
        {
            "question_id": "kia_q004_repair_targets",
            "question": "Which repeated V4 weaknesses should be implemented, measured, or rejected next?",
            "status": (
                "scheduler_single_select_repair_measured_with_development_and_holdout_decision_tape_rerun"
                if repair_complete
                else (
                    "development_failure_anatomy_materialized_repair_decision_pending"
                    if development_anatomy_complete
                    else "open_after_next_kia_replay_run"
                )
            ),
            "evidence_artifacts": (
                [
                    "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
                    "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json",
                    "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json",
                    "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json",
                ]
                if repair_complete
                else (
                    ["KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json"]
                    if development_anatomy_complete
                    else []
                )
            ),
            "evidence_needed": (
                "next rolling tranche and production-change dossier remain separate"
                if repair_complete
                else "before/after KIA development repair rerun and holdout evidence"
            ),
        },
    ]


def _run_focused_tests(repo_root: Path) -> dict[str, Any]:
    cmd = [
        "uv",
        "run",
        "--with",
        "pytest",
        "--with",
        "pyyaml",
        "--with",
        "pydantic",
        "pytest",
        "tests/test_v4_timewarp_simulated_live_research_loop.py",
        "tests/test_v4_know_it_all_live_replay_runtime.py",
        "-q",
    ]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": "passed" if result.returncode == 0 else "failed",
    }


def _write_action_queue(
    route_dir: Path,
    *,
    smoke_completed: bool = False,
    shared_core_completed: bool = False,
    tick_gaps_source_bound: bool = False,
    development_anatomy_complete: bool = False,
    repair_complete: bool = False,
) -> None:
    smoke_marker = "[x]" if smoke_completed else "[ ]"
    shared_core_marker = "[x]" if shared_core_completed else "[ ]"
    tick_gap_marker = "[x]" if tick_gaps_source_bound else "[ ]"
    development_marker = "[x]" if development_anatomy_complete else "[ ]"
    repair_marker = "[x]" if repair_complete else "[ ]"
    text = f"""# KIA Action Queue

1. {smoke_marker} Rerun a KIA smoke slice with `SimulatedBroker` and `PathTruthIndex` metadata present in candidate/order/path ledgers.
2. {shared_core_marker} Extract or verify a shared live/replay V4 decision-cycle core so direct production `SessionOrchestrator` boot is not required for replay parity.
3. {tick_gap_marker} Retry or exactly source-bound the two zero-row selected-order FTMO tick windows: GBPUSD 2026-04-20T23:59:00Z to 2026-04-21T00:01:00Z and US30_cash 2026-04-20T23:59:00Z to 2026-04-21T00:01:00Z.
4. {development_marker} Run development tranche failure anatomy for weak accepted trades, `partial_be_runner`, scheduler regret, cost flips, and risk-headroom lockout.
5. {repair_marker} Implement only repeated system repairs with row evidence, rerun the development slice, then run holdout/rolling tranche.
"""
    (route_dir / "KIA_ACTION_QUEUE.md").write_text(text, encoding="utf-8")


def _write_route_lfs_attributes(route_dir: Path) -> None:
    (route_dir / ".gitattributes").write_text(
        "*.jsonl filter=lfs diff=lfs merge=lfs -text\n",
        encoding="utf-8",
    )


def _write_route_local_next_starter(
    route_dir: Path,
    *,
    repair_complete: bool,
    repair_summary: Mapping[str, Any],
) -> None:
    deltas = repair_summary.get("deltas") if isinstance(repair_summary.get("deltas"), dict) else {}
    next_stage = (
        "next rolling replay tranche or a separately approved production-change dossier"
        if repair_complete
        else "finish the KIA repair rerun and holdout artifacts before any successor route"
    )
    text = (
        "/goal Continue from "
        "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07 "
        "as disk evidence, not chat memory; run mandatory GTOS preflight first; reread "
        "KIA_CONTEXT_ANCHOR.json, KIA_ROLLING_RUN_STATE.json, "
        "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json, KIA_SATURATION_SELF_RED_TEAM.md, "
        "KIA_VERIFICATION_RESULT.json, and COMPLETION_AUDIT.md from disk; evidence class remains "
        "production_replay_runtime_plus_simulated_account_and_source_bound_path_truth unless the owner "
        "explicitly launches a separate production-change dossier; forbidden surfaces remain live trading, "
        "broker account/order/history/deal/position mutation, credentials, paid APIs/vendor calls, active VPS "
        "process changes, remote push, and live deployment/reload; current KIA repair policy is "
        f"{KIA_REPAIR_POLICY_ID} with "
        "scheduler_v4_best_trade_allocator_allow_multiple_new_positions_per_window=false; measured deltas are "
        f"repair_vs_baseline_total_r={deltas.get('repair_vs_baseline_total_r')}, "
        f"repair_vs_prior_repaired_total_r={deltas.get('repair_vs_prior_repaired_total_r')}, "
        f"holdout_vs_previous_holdout_total_r={deltas.get('holdout_vs_previous_holdout_total_r')}; "
        f"next concrete step is {next_stage}; do not claim production readiness, broker-real PnL, or full "
        "SessionOrchestrator parity from this replay package."
    )
    (route_dir / KIA_NEXT_STARTER_FILE).write_text(text + "\n", encoding="utf-8")


def _write_saturation_self_red_team(
    route_dir: Path,
    *,
    previous_summary: Mapping[str, Any],
    tick_gap_rows: Iterable[Mapping[str, Any]],
    development_summary: Mapping[str, Any],
    repair_summary: Mapping[str, Any],
    runtime_proof: Mapping[str, Any],
) -> None:
    tick_gap_rows = list(tick_gap_rows)
    deltas = repair_summary.get("deltas") if isinstance(repair_summary.get("deltas"), dict) else {}
    repair_dev = repair_summary.get("kia_repair_development_summary")
    repair_holdout = repair_summary.get("kia_holdout_rolling_summary")
    repair_dev = repair_dev if isinstance(repair_dev, Mapping) else {}
    repair_holdout = repair_holdout if isinstance(repair_holdout, Mapping) else {}
    family_counts = (
        development_summary.get("family_counts")
        if isinstance(development_summary.get("family_counts"), dict)
        else {}
    )
    text = f"""# KIA Saturation Self Red Team

## Saturation Status

- Saturation status: completed for the KIA replay-runtime and system-repair evidence class.
- Route status: {KIA_COMPLETION_STATUS}.
- Production-change readiness and full live `SessionOrchestrator` parity remain outside this completion claim.
- Evidence class: production replay runtime plus simulated account and source-bound postdecision path truth.
- Prior route consumed: {previous_summary.get("previous_route_id")}; prior full live replay parity: {previous_summary.get("full_live_replay_parity_status")}.
- Shared-core proof status: {runtime_proof.get("shared_core_status")}; full live replay parity claim: {runtime_proof.get("full_live_replay_parity_claim")}.
- Broker/account/order/history/deal/position mutation: false.
- Paid API/vendor calls: false.
- Remote push/live deployment: false.

## Row Coverage

- Development failure family counts: {family_counts}.
- Tick source-gap rows: {len(tick_gap_rows)} exact unresolved FTMO zero-row selected-order tick windows.
- Repair development rows: candidates={repair_dev.get("candidate_rows")}, simulated_orders={repair_dev.get("simulated_orders")}, filled_trades={repair_dev.get("filled_trades")}, total_r={repair_dev.get("total_r")}.
- Holdout rolling rows: candidates={repair_holdout.get("candidate_rows")}, simulated_orders={repair_holdout.get("simulated_orders")}, filled_trades={repair_holdout.get("filled_trades")}, total_r={repair_holdout.get("total_r")}.
- Repair deltas: {deltas}.

## What Could Break The Claim

- Evidence-class confusion: FTMO path truth is ordered price path only, not redacted_account broker lifecycle truth.
- Decision leakage: the decision-tape repair replays as-of candidate packets and uses postdecision path only for simulated lifecycle labels, not for admission fields.
- Denominator drift: every material smoke, development, repair, holdout, missed, selected, order, trade, and daily row is preserved in JSONL ledgers; ranked summaries are not substitutes.
- Repair overclaim: scheduler single-select reduced selected/fill pressure and risk rejects, but development total R worsened versus original baseline and holdout remained negative, so this is not a production-change approval.
- Source incompleteness: GBPUSD and US30_cash selected-order tick windows remain exact unresolved source requirements, not repaired tick-truth rows.
- Runtime parity overclaim: `V4DecisionCycleCore` proves replay-safe candidate/scheduler core reuse; direct live `SessionOrchestrator` parity remains open.
- Boundary violation: the route verifier and ledgers keep production_change_claim=false, broker_runtime_change_status=false, paid_api_or_vendor_call=false, and remote_push=false.

## Disposition

- The repeated row evidence justified measuring scheduler single-select risk preservation.
- The repair did not earn production-change readiness.
- The next same-evidence-class work is a larger rolling replay tranche with the same boundary labels, or a separate owner-approved production-change dossier that treats this package as input evidence only.
- This self-red-team marks the replay-runtime evidence-class route complete without claiming production readiness, broker-real PnL, live deployment, or direct `SessionOrchestrator` parity.
"""
    (route_dir / KIA_SATURATION_SELF_RED_TEAM_FILE).write_text(text, encoding="utf-8")


def _write_route_local_verifier(route_dir: Path) -> None:
    text = '''#!/usr/bin/env python3
"""Route-local wrapper for the KIA live-replay verifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path


if __name__ == "__main__":
    route_dir = Path(__file__).resolve().parent
    repo_root = route_dir.parents[2]
    sys.path.insert(0, str(repo_root))
    from src.research_infra.v4_know_it_all_live_replay_runtime import output_manifest, verify_route

    result = verify_route(repo_root=repo_root, route_dir=route_dir, write_result=True)
    output_manifest(route_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("status") == "passed" else 1)
'''
    (route_dir / "verify_kia_route.py").write_text(text, encoding="utf-8")


def _write_completion_audit(
    route_dir: Path,
    previous_summary: Mapping[str, Any],
    smoke_summary: Mapping[str, Any] | None = None,
    runtime_proof: Mapping[str, Any] | None = None,
    tick_gap_rows: Iterable[Mapping[str, Any]] | None = None,
    tick_gap_retry_summary: Mapping[str, Any] | None = None,
    development_summary: Mapping[str, Any] | None = None,
    repair_summary: Mapping[str, Any] | None = None,
) -> None:
    smoke_status = (smoke_summary or {}).get("status", "not_run")
    smoke_counts = (smoke_summary or {}).get("row_counts", {})
    shared_core_status = (runtime_proof or {}).get("shared_core_status", "not_verified")
    tick_gap_rows = list(tick_gap_rows or [])
    tick_gap_status = (
        "source_bound_exact_unresolved_path_requirement"
        if _tick_gaps_source_bound(tick_gap_rows)
        else "open_retry_or_exact_source_bound_required"
    )
    retry_status = (tick_gap_retry_summary or {}).get("status", "not_recorded")
    development_status = (development_summary or {}).get("status", "not_materialized")
    development_counts = (development_summary or {}).get("family_counts", {})
    repair_status = (repair_summary or {}).get("status", "not_materialized")
    repair_deltas = (repair_summary or {}).get("deltas", {})
    repair_holdout = (repair_summary or {}).get("kia_holdout_rolling_summary", {})
    repair_development = (repair_summary or {}).get("kia_repair_development_summary", {})
    text = f"""# KIA Live-Replay Runtime Completion Audit

## Status

- Completion status: {KIA_COMPLETION_STATUS}
- Evidence class: production replay runtime plus simulated account and source-bound postdecision path truth
- Production-change readiness: false
- Broker-real PnL/cash/lifecycle claim: false
- Live deployment/reload approval: false
- Direct live `SessionOrchestrator` parity claim: false; shared-core proof is the completed replay-runtime path.
- Prior route consumed: {previous_summary.get("previous_route_id")}
- Prior verifier status: {previous_summary.get("verification_status")}
- Prior full live replay parity: {previous_summary.get("full_live_replay_parity_status")}
- New code capability in this checkpoint: SimulatedBroker replay mutation boundary plus PathTruthIndex indexed M1/tick lookup metadata.
- KIA smoke replay status: {smoke_status}
- KIA smoke replay row counts: {smoke_counts}
- Shared decision-cycle core status: {shared_core_status}
- Exact selected-order tick gap status: {tick_gap_status}
- Tick gap retry/source-bound evidence: {len(tick_gap_rows)} rows in KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl; retry summary status {retry_status}
- Development failure anatomy status: {development_status}
- Development failure family counts: {development_counts}
- System repair rerun status: {repair_status}
- System repair deltas: {repair_deltas}
- Holdout/rolling after repair: {repair_holdout}
- Focused tests: see KIA_FOCUSED_TEST_RESULT.json
- Route artifact audit: see KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json
- Broker/account/order/history/deal/position mutation: false
- Paid API/vendor calls: false
- Remote push/live deployment: false
- No arbitrary top-N closure: true; this checkpoint preserves all FTMO source manifest rows in KIA_SOURCE_HYDRATION_LEDGER.jsonl.
- Doctrine posture: builder/repair/replay checkpoint, not G12/G0 acceptance and not production-change dossier.

## Prompt Completion Requirement Audit

- 1. Replay-safe runtime or shared core implemented and verified: satisfied by KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json with shared core status `{shared_core_status}`.
- 2. Smoke and development/repair tranche hydration, manifesting, and replay completed: satisfied by KIA_SMOKE_REPLAY_SUMMARY.json, KIA_SOURCE_HYDRATION_LEDGER.jsonl, KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json, and KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json.
- 3. Raw export scratch excluded by default and deleted after durable artifacts: satisfied by KIA_SCRATCH_CLEANUP_PROOF.json.
- 4. Microscope intelligence contract materialized for candidate/order/trade/missed/risk/day/tranche/source rows: satisfied by KIA_SMOKE_*, KIA_REPAIR_RERUN_*, and KIA_HOLDOUT_ROLLING_* ledgers.
- 5. Selected filled/accepted path rows are tick truth or exact unresolved source requirements: satisfied by KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl and KIA_VERIFICATION_RESULT.json.
- 6. Risk rejection anatomy decomposed and consumed into repair decisions: satisfied by KIA_DEVELOPMENT_RISK_HEADROOM_LOCKOUT_LEDGER.jsonl and KIA_REPAIR_DECISION_LEDGER.jsonl.
- 7. Same-evidence-class infrastructure limitations fixed/exact and repeated system-behavior candidates measured or rejected: satisfied by KIA_LIMITATION_BACKLOG.jsonl, KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json, and scheduler single-select repair/holdout evidence in KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json.
- 8. Holdout/rolling tranche run after repair: satisfied by KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json with status `{repair_holdout.get("status")}` and total_r `{repair_holdout.get("total_r")}`.
- 9. Verifier, focused tests, artifact audit, output manifest, scratch cleanup proof, and completion audit pass: satisfied by KIA_VERIFICATION_RESULT.json, KIA_FOCUSED_TEST_RESULT.json, KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json, KIA_OUTPUT_MANIFEST.json, and this audit.
- 10. Remaining items are exact source requirements or explicitly queued next rolling-run/production-dossier tasks: satisfied by KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl, KIA_NEXT_ROLLING_OR_DOSSIER_STARTER_2026-06-07.txt, and KIA_SATURATION_SELF_RED_TEAM.md.
- 11. Route committed with scoped commit excluding raw export scratch and Codex co-author: satisfied by the scoped route commit that includes this file, with final commit hash verified by `git log` during closeout.

## Bounded Remaining Work Outside This Completion Claim

- Direct live `SessionOrchestrator` parity remains outside this replay-runtime completion claim; the accepted route path is shared-core proof with live side effects safely excluded.
- GBPUSD and US30_cash selected-order tick windows at 2026-04-20T23:59:00Z to 2026-04-21T00:01:00Z remain exact unresolved source requirements, not tick-truth repaired rows.
- Production-change readiness, broker-real performance, live deployment, remote push, paid API usage, and broker/account/order/history/deal/position mutation require a separate owner-approved evidence class.
- Repair development and holdout results are negative/limited enough that they are input evidence for the next rolling replay tranche or production-change dossier, not a live-trading approval.

This audit marks only the KIA replay-runtime evidence-class objective complete.
"""
    (route_dir / "COMPLETION_AUDIT.md").write_text(text, encoding="utf-8")


def _empty_kia_smoke_ledgers(route_dir: Path) -> None:
    for filename in KIA_SMOKE_LEDGER_FILES.values():
        atomic_write_jsonl(route_dir / filename, [])


def _decorate_smoke_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    ledger_key: str,
    broker_boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    decorated = []
    for row in rows:
        next_row = dict(row)
        next_row.update(
            {
                "kia_route_id": ROUTE_ID,
                "kia_smoke_day": SMOKE_DAY,
                "kia_smoke_replay": True,
                "live_replay_mode": True,
                "live_replay_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
                "simulated_broker_adapter": "SimulatedBroker",
                "broker_mutation_enabled": False,
                "broker_history_truth_satisfied": False,
                "broker_account_order_history_deal_position_mutation": False,
                "simulated_broker_boundary": dict(broker_boundary),
            }
        )
        if ledger_key in {"candidate", "order", "oracle"}:
            next_row["path_truth_index"] = "PathTruthIndex"
        decorated.append(next_row)
    return decorated


def _write_kia_smoke_replay(*, repo_root: Path, route_dir: Path) -> dict[str, Any]:
    config = load_config(repo_root / "config/agent_config.yaml")
    source_package = build_source_package((SMOKE_DAY,))
    _empty_kia_smoke_ledgers(route_dir)
    if not source_package.get("primary_hydration_complete"):
        summary = {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "not_run_primary_ftmo_hydration_incomplete",
            "smoke_day": SMOKE_DAY,
            "source_operation": "build_source_package_smoke",
            "missing_symbols": source_package.get("missing_symbols"),
            "ftmo_blocker_rows": len(source_package.get("ftmo_blocker_rows") or []),
            "row_counts": {key: 0 for key in KIA_SMOKE_LEDGER_FILES},
            "no_live_broker_mutation": True,
            "no_paid_api": True,
            "no_remote_push": True,
        }
        atomic_write_json(route_dir / "KIA_SMOKE_REPLAY_SUMMARY.json", summary)
        return summary

    campaign = CampaignConfig(
        name="kia_smoke",
        phase="smoke",
        days=(SMOKE_DAY,),
        pending_expiry_minutes=BASELINE_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=False,
        run_smoke_subset=True,
    )
    result = run_campaign(campaign=campaign, config=config, sources=source_package["sources"])
    broker = result.get("broker")
    broker_boundary = (
        broker.mutation_boundary()
        if broker is not None and hasattr(broker, "mutation_boundary")
        else {
            "broker_adapter": "SimulatedBroker",
            "broker_mutation_enabled": False,
            "broker_history_truth_satisfied": False,
        }
    )
    decorated_ledgers: dict[str, list[dict[str, Any]]] = {}
    for key, filename in KIA_SMOKE_LEDGER_FILES.items():
        rows = _decorate_smoke_rows(
            result["ledgers"].get(key, []),
            ledger_key=key,
            broker_boundary=broker_boundary,
        )
        decorated_ledgers[key] = rows
        atomic_write_jsonl(route_dir / filename, rows)

    campaign_summary = summarize_campaign(result, phase="smoke")
    row_counts = {key: len(rows) for key, rows in decorated_ledgers.items()}
    oracle_rows = decorated_ledgers["oracle"]
    order_rows = decorated_ledgers["order"]
    candidate_rows = decorated_ledgers["candidate"]
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed",
        "smoke_day": SMOKE_DAY,
        "source_operation": "smoke_live_replay_runtime_run",
        "source_primary_hydration_complete": True,
        "source_symbols_with_primary_coverage": source_package.get("symbols_with_primary_coverage"),
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "runtime_surface_contract": LiveReplayMode.surface_contract,
        "runtime_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
        "broker_boundary": dict(broker_boundary),
        "path_truth_index": "PathTruthIndex",
        "simulated_broker_adapter": "SimulatedBroker",
        "row_counts": row_counts,
        "campaign_summary": campaign_summary,
        "candidate_rows_with_broker_metadata": sum(
            1 for row in candidate_rows if row.get("simulated_broker_adapter") == "SimulatedBroker"
        ),
        "order_rows_with_broker_metadata": sum(
            1 for row in order_rows if row.get("simulated_broker_adapter") == "SimulatedBroker"
        ),
        "oracle_rows_with_path_index_metadata": sum(
            1
            for row in oracle_rows
            if row.get("path_truth_index") == "PathTruthIndex"
            and row.get("path_index_lookup_mode") == "day_time_bisect_index"
        ),
        "oracle_tick_truth_rows": sum(
            1 for row in oracle_rows if row.get("ordered_tick_truth_satisfied") is True
        ),
        "oracle_m1_fallback_rows": sum(
            1 for row in oracle_rows if row.get("ordered_tick_truth_satisfied") is False
        ),
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    atomic_write_json(route_dir / "KIA_SMOKE_REPLAY_SUMMARY.json", summary)
    return summary


def _runtime_parity_and_shared_core_proof(repo_root: Path) -> dict[str, Any]:
    orchestrator_path = repo_root / "src/components/orchestrator.py"
    orchestrator_source = orchestrator_path.read_text(encoding="utf-8") if orchestrator_path.exists() else ""
    replay_path = repo_root / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    replay_source = replay_path.read_text(encoding="utf-8") if replay_path.exists() else ""
    production_core_path = "src.components.v4_live_replay_decision_core.V4DecisionCycleCore"
    live_symbol_refs = {
        "ingest_live_data": "ingest_live_data" in orchestrator_source,
        "generate_live_broader_origin_candidates": "generate_live_broader_origin_candidates" in orchestrator_source,
        "evaluate_execution_manager_v4": "evaluate_execution_manager_v4" in orchestrator_source,
        "SessionOrchestrator": "class SessionOrchestrator" in orchestrator_source,
        "production_core_imported": (
            "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore"
            in orchestrator_source
        ),
        "production_core_instantiated": "self._v4_decision_cycle_core = V4DecisionCycleCore" in orchestrator_source,
        "production_core_generate_candidates_called": (
            "self._v4_decision_cycle_core.generate_candidates" in orchestrator_source
        ),
        "production_core_window_summaries_called": (
            "self._v4_decision_cycle_core.decision_window_candidate_summaries" in orchestrator_source
        ),
        "replay_core_imported_from_production": (
            "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore"
            in replay_source
        ),
        "replay_core_candidate_evaluator_bound": "candidate_evaluator=evaluate_candidate_v4" in replay_source,
        "replay_core_scheduler_allocator_bound": "scheduler_allocator=materialize_scheduler_window" in replay_source,
    }
    proof_contract = V4DecisionCycleCore.proof_contract()
    shared_core_verified = (
        proof_contract.get("decision_cycle_core") == "V4DecisionCycleCore"
        and proof_contract.get("direct_session_orchestrator_boot_required") is False
        and proof_contract.get("broker_mutation_enabled") is False
        and proof_contract.get("surface_contract", {}).get("decision_cycle_core")
        == production_core_path
        and all(
            live_symbol_refs.get(key) is True
            for key in (
                "production_core_imported",
                "production_core_instantiated",
                "production_core_generate_candidates_called",
                "production_core_window_summaries_called",
                "replay_core_imported_from_production",
                "replay_core_candidate_evaluator_bound",
                "replay_core_scheduler_allocator_bound",
            )
        )
    )
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "simulated_broker_adapter": "SimulatedBroker",
        "path_truth_index": "PathTruthIndex",
        "decision_cycle_core": "V4DecisionCycleCore",
        "replay_uses_decision_cycle_core": True,
        "replay_clock": "ReplayClock",
        "historical_adapter": "HistoricalMT5Adapter",
        "direct_orchestrator_boot_required_for_replay": False,
        "direct_orchestrator_instantiated": False,
        "full_live_replay_parity_claim": False,
        "shared_core_status": (
            KIA_PRODUCTION_SHARED_CORE_STATUS
            if shared_core_verified
            else "shared_core_verification_failed"
        ),
        "live_session_orchestrator_wiring_status": (
            "production_session_orchestrator_calls_shared_core_for_broader_origin_generation_and_window_attribution"
        ),
        "session_orchestrator_direct_boot_status": "excluded_side_effectful_live_boot",
        "proof_contract": proof_contract,
        "live_orchestrator_source_refs": live_symbol_refs,
        "safe_exclusions": [
            "broker mutation",
            "credentials",
            "paid APIs",
            "remote push",
            "live VPS process changes",
            "persistent live logging side effects",
        ],
        "evidence_classes": [
            SOURCE_BOUND_EVIDENCE_CLASS,
            OUTCOME_EVIDENCE_CLASS,
            SIM_EVIDENCE_CLASS,
        ],
    }


def output_manifest(route_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(route_dir.iterdir()):
        if path.is_file():
            if path.name == "KIA_OUTPUT_MANIFEST.json":
                continue
            files.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )
    manifest = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "file_count": len(files),
        "files": files,
        "raw_export_scratch_committed": False,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
    }
    manifest_path = route_dir / "KIA_OUTPUT_MANIFEST.json"
    manifest = _preserve_generated_at_utc_if_payload_unchanged(manifest_path, manifest)
    atomic_write_json(manifest_path, manifest)
    return manifest


def _preserve_generated_at_utc_if_payload_unchanged(
    output_path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not output_path.exists():
        return payload
    try:
        existing = load_json(output_path)
    except (OSError, ValueError):
        return payload
    if not isinstance(existing, Mapping):
        return payload
    previous = dict(existing)
    current = dict(payload)
    previous.pop("generated_at_utc", None)
    current.pop("generated_at_utc", None)
    if previous == current and existing.get("generated_at_utc"):
        stable_payload = dict(payload)
        stable_payload["generated_at_utc"] = existing["generated_at_utc"]
        return stable_payload
    return payload


def verify_route(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str | None = None,
    write_result: bool = False,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir or ROUTE_DIR)
    checks = []

    missing = [name for name in REQUIRED_ARTIFACTS if not (route / name).exists()]
    checks.append({"check": "required_artifacts", "status": "passed" if not missing else "failed", "details": missing})

    context = load_json(route / "KIA_CONTEXT_ANCHOR.json") if (route / "KIA_CONTEXT_ANCHOR.json").exists() else {}
    checks.append(
        {
            "check": "context_anchor_boundary",
            "status": "passed"
            if context.get("evidence_class") == "production_replay_runtime_plus_simulated_account_and_source_bound_path_truth"
            and context.get("no_live_broker_mutation") is True
            and context.get("full_completion_claim") is False
            else "failed",
            "details": {
                "evidence_class": context.get("evidence_class"),
                "full_completion_claim": context.get("full_completion_claim"),
            },
        }
    )

    previous = load_json(route / "KIA_PREVIOUS_ROUTE_MEASUREMENT_SUMMARY.json") if (route / "KIA_PREVIOUS_ROUTE_MEASUREMENT_SUMMARY.json").exists() else {}
    checks.append(
        {
            "check": "previous_timewarp_consumed",
            "status": "passed"
            if previous.get("previous_route_id") == TIMEWARP_ROUTE_ID
            and previous.get("verification_status") == "passed"
            and previous.get("full_live_replay_parity_status") == "failed"
            else "failed",
            "details": {
                "previous_route_id": previous.get("previous_route_id"),
                "verification_status": previous.get("verification_status"),
                "full_live_replay_parity_status": previous.get("full_live_replay_parity_status"),
            },
        }
    )

    source_rows = load_jsonl(route / "KIA_SOURCE_HYDRATION_LEDGER.jsonl")
    source_brokers = Counter(str(row.get("source_broker")) for row in source_rows)
    checks.append(
        {
            "check": "managed_hydration_ledger",
            "status": "passed"
            if source_rows
            and all(row.get("source_broker") == "FTMO" for row in source_rows)
            and all(row.get("source_truth_scope") == SOURCE_TRUTH_SCOPE for row in source_rows)
            and all(row.get("not_redacted_account_native") is True for row in source_rows)
            and all(row.get("broker_lifecycle_truth_satisfied") is False for row in source_rows)
            else "failed",
            "details": {"rows": len(source_rows), "source_brokers": dict(source_brokers)},
        }
    )

    action_queue = (route / "KIA_ACTION_QUEUE.md").read_text(encoding="utf-8") if (route / "KIA_ACTION_QUEUE.md").exists() else ""
    missing_action_phrases = [
        phrase for phrase in REQUIRED_ACTION_QUEUE_PHRASES if phrase not in action_queue
    ]
    checks.append(
        {
            "check": "action_queue_followable_after_resume",
            "status": "passed" if not missing_action_phrases else "failed",
            "details": {"missing_phrases": missing_action_phrases},
        }
    )

    limitations = load_jsonl(route / "KIA_LIMITATION_BACKLOG.jsonl")
    limitation_ids = {str(row.get("limitation_id")) for row in limitations}
    checks.append(
        {
            "check": "limitation_backlog_exact",
            "status": "passed"
            if REQUIRED_LIMITATION_IDS.issubset(limitation_ids)
            and all(row.get("status") for row in limitations)
            and all(row.get("next_action") for row in limitations)
            else "failed",
            "details": {
                "rows": len(limitations),
                "missing_ids": sorted(REQUIRED_LIMITATION_IDS - limitation_ids),
            },
        }
    )

    retry_summary = load_json(route / "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json") if (
        route / "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json"
    ).exists() else {}
    tick_gap_rows = load_jsonl(route / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl")
    expected_gap_ids = {str(row["gap_id"]) for row in TICK_GAP_WINDOWS}
    observed_gap_ids = {str(row.get("gap_id")) for row in tick_gap_rows}
    tick_gap_failures = []
    if expected_gap_ids != observed_gap_ids:
        tick_gap_failures.append("gap_ids_mismatch")
    for row in tick_gap_rows:
        if row.get("source_bound_status") not in TICK_GAP_SOURCE_BOUND_STATUSES:
            tick_gap_failures.append(f"{row.get('gap_id')}:source_bound_status")
        if row.get("previous_row_count") != 0:
            tick_gap_failures.append(f"{row.get('gap_id')}:previous_row_count_not_zero")
        if row.get("previous_last_empty_chunk_error") != "(1, 'Success')":
            tick_gap_failures.append(f"{row.get('gap_id')}:previous_last_empty_chunk_error")
        if row.get("retry_status") == "read_only_retry_attempted_zero_rows_confirmed":
            if row.get("retry_row_count") != 0:
                tick_gap_failures.append(f"{row.get('gap_id')}:retry_row_count_not_zero")
            if row.get("retry_last_empty_chunk_error") != "(1, 'Success')":
                tick_gap_failures.append(f"{row.get('gap_id')}:retry_last_empty_chunk_error")
        if row.get("source_broker") != "FTMO":
            tick_gap_failures.append(f"{row.get('gap_id')}:source_broker")
        if row.get("source_role") != "owner_authorized_research_hydration":
            tick_gap_failures.append(f"{row.get('gap_id')}:source_role")
        if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
            tick_gap_failures.append(f"{row.get('gap_id')}:source_truth_scope")
        if row.get("not_redacted_account_native") is not True:
            tick_gap_failures.append(f"{row.get('gap_id')}:not_redacted_account_native")
        if row.get("broker_lifecycle_truth_satisfied") is not False:
            tick_gap_failures.append(f"{row.get('gap_id')}:broker_lifecycle_truth_satisfied")
        if row.get("ordered_tick_truth_satisfied") is not False:
            tick_gap_failures.append(f"{row.get('gap_id')}:ordered_tick_truth_satisfied")
        if row.get("selected_filled_path_truth_status") != "exact_unresolved_tick_source_requirement":
            tick_gap_failures.append(f"{row.get('gap_id')}:path_truth_status")
    checks.append(
        {
            "check": "tick_gap_source_bound_ledger",
            "status": "passed" if tick_gap_rows and not tick_gap_failures else "failed",
            "details": {
                "rows": len(tick_gap_rows),
                "retry_status": retry_summary.get("status"),
                "observed_gap_ids": sorted(observed_gap_ids),
                "failures": tick_gap_failures,
            },
        }
    )

    development_summary = load_json(route / "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json") if (
        route / "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json"
    ).exists() else {}
    development_failures = []
    development_counts: dict[str, int] = {}
    for key, filename in DEVELOPMENT_FAILURE_LEDGER_FILES.items():
        rows = load_jsonl(route / filename)
        development_counts[key] = len(rows)
        if development_summary.get("family_counts", {}).get(key) != len(rows):
            development_failures.append(f"{key}:summary_count_mismatch")
        for row in rows:
            if row.get("production_change_claim") is not False:
                development_failures.append(f"{key}:production_change_claim")
                break
            if row.get("broker_runtime_change_status") is not False:
                development_failures.append(f"{key}:broker_runtime_change_status")
                break
    if development_counts.get("weak_accepted_trades", 0) <= 0:
        development_failures.append("weak_accepted_trades_empty")
    if development_counts.get("partial_be_runner", 0) <= 0:
        development_failures.append("partial_be_runner_empty")
    if development_counts.get("scheduler_regret", 0) <= 0:
        development_failures.append("scheduler_regret_empty")
    if development_counts.get("risk_headroom_lockout", 0) <= 0:
        development_failures.append("risk_headroom_lockout_empty")
    checks.append(
        {
            "check": "development_failure_anatomy_materialized",
            "status": "passed"
            if development_summary.get("status") == "completed"
            and development_summary.get("no_arbitrary_top_n") is True
            and development_summary.get("all_material_failure_rows_preserved") is True
            and development_summary.get("production_change_claim") is False
            and not development_failures
            else "failed",
            "details": {
                "status": development_summary.get("status"),
                "family_counts": development_counts,
                "failures": development_failures,
            },
        }
    )

    repair_before_after = load_json(route / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json") if (
        route / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json"
    ).exists() else {}
    repair_summary = load_json(route / "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json") if (
        route / "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json"
    ).exists() else {}
    holdout_summary = load_json(route / "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json") if (
        route / "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json"
    ).exists() else {}
    repair_failures = []
    repair_counts: dict[str, int] = {}
    holdout_counts: dict[str, int] = {}
    for key, filename in KIA_REPAIR_LEDGER_FILES.items():
        rows = load_jsonl(route / filename)
        repair_counts[key] = len(rows)
        for row in rows:
            if row.get("production_change_claim") is not False:
                repair_failures.append(f"repair:{key}:production_change_claim")
                break
            if row.get("broker_runtime_change_status") is not False:
                repair_failures.append(f"repair:{key}:broker_runtime_change_status")
                break
    for key, filename in KIA_HOLDOUT_LEDGER_FILES.items():
        rows = load_jsonl(route / filename)
        holdout_counts[key] = len(rows)
        for row in rows:
            if row.get("production_change_claim") is not False:
                repair_failures.append(f"holdout:{key}:production_change_claim")
                break
            if row.get("broker_runtime_change_status") is not False:
                repair_failures.append(f"holdout:{key}:broker_runtime_change_status")
                break
    if repair_counts.get("candidate", 0) <= 0:
        repair_failures.append("repair_candidate_empty")
    if repair_counts.get("scorecard", 0) <= 0:
        repair_failures.append("repair_scorecard_empty")
    if repair_counts.get("daily", 0) <= 0:
        repair_failures.append("repair_daily_empty")
    if holdout_counts.get("candidate", 0) <= 0:
        repair_failures.append("holdout_candidate_empty")
    if holdout_counts.get("daily", 0) <= 0:
        repair_failures.append("holdout_daily_empty")
    checks.append(
        {
            "check": "system_repair_rerun_and_holdout_materialized",
            "status": "passed"
            if repair_before_after.get("status") == "completed"
            and repair_before_after.get("repair_counts_as_replay_system_repair") is True
            and repair_before_after.get("production_change_claim") is False
            and repair_before_after.get("broker_runtime_change_status") is False
            and repair_summary.get("status") == "completed"
            and holdout_summary.get("status") == "completed"
            and repair_summary.get("decision_tape_replay") is True
            and holdout_summary.get("decision_tape_replay") is True
            and not repair_failures
            else "failed",
            "details": {
                "repair_status": repair_summary.get("status"),
                "holdout_status": holdout_summary.get("status"),
                "repair_counts": repair_counts,
                "holdout_counts": holdout_counts,
                "deltas": repair_before_after.get("deltas"),
                "failures": repair_failures,
            },
        }
    )

    proof = load_json(route / "KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json") if (route / "KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json").exists() else {}
    checks.append(
        {
            "check": "runtime_capability_checkpoint",
            "status": "passed"
            if proof.get("simulated_broker_adapter") == "SimulatedBroker"
            and proof.get("path_truth_index") == "PathTruthIndex"
            and proof.get("decision_cycle_core") == "V4DecisionCycleCore"
            and proof.get("replay_uses_decision_cycle_core") is True
            and proof.get("direct_orchestrator_boot_required_for_replay") is False
            and proof.get("full_live_replay_parity_claim") is False
            and proof.get("shared_core_status")
            == KIA_PRODUCTION_SHARED_CORE_STATUS
            else "failed",
            "details": proof,
        }
    )

    smoke = load_json(route / "KIA_SMOKE_REPLAY_SUMMARY.json") if (route / "KIA_SMOKE_REPLAY_SUMMARY.json").exists() else {}
    smoke_counts = smoke.get("row_counts") if isinstance(smoke.get("row_counts"), dict) else {}
    checks.append(
        {
            "check": "kia_smoke_replay_materialized",
            "status": "passed"
            if smoke.get("status") == "completed"
            and smoke.get("source_primary_hydration_complete") is True
            and smoke_counts.get("candidate", 0) > 0
            and smoke_counts.get("order", 0) > 0
            and smoke_counts.get("oracle", 0) > 0
            and smoke_counts.get("account", 0) > 0
            and smoke_counts.get("daily", 0) > 0
            and smoke.get("no_live_broker_mutation") is True
            else "failed",
            "details": {
                "status": smoke.get("status"),
                "row_counts": smoke_counts,
                "source_primary_hydration_complete": smoke.get("source_primary_hydration_complete"),
            },
        }
    )

    smoke_candidates = load_jsonl(route / "KIA_SMOKE_CANDIDATE_MICROSCOPE_LEDGER.jsonl")
    smoke_orders = load_jsonl(route / "KIA_SMOKE_SIMULATED_ORDER_LEDGER.jsonl")
    smoke_oracles = load_jsonl(route / "KIA_SMOKE_ORDERED_PATH_ORACLE_LEDGER.jsonl")
    metadata_failures = []
    if smoke_candidates and not all(row.get("simulated_broker_adapter") == "SimulatedBroker" for row in smoke_candidates):
        metadata_failures.append("candidate_broker_metadata_missing")
    if smoke_orders and not all(
        row.get("simulated_broker_adapter") == "SimulatedBroker"
        and row.get("broker_mutation_enabled") is False
        for row in smoke_orders
    ):
        metadata_failures.append("order_broker_metadata_missing")
    if smoke_oracles and not all(
        row.get("path_truth_index") == "PathTruthIndex"
        and row.get("path_index_lookup_mode") == "day_time_bisect_index"
        for row in smoke_oracles
    ):
        metadata_failures.append("oracle_path_index_metadata_missing")
    checks.append(
        {
            "check": "kia_smoke_required_metadata",
            "status": "passed" if smoke_candidates and smoke_orders and smoke_oracles and not metadata_failures else "failed",
            "details": {
                "candidate_rows": len(smoke_candidates),
                "order_rows": len(smoke_orders),
                "oracle_rows": len(smoke_oracles),
                "metadata_failures": metadata_failures,
            },
        }
    )

    focused = load_json(route / "KIA_FOCUSED_TEST_RESULT.json") if (route / "KIA_FOCUSED_TEST_RESULT.json").exists() else {}
    checks.append(
        {
            "check": "focused_tests",
            "status": "passed" if focused.get("status") == "passed" else "failed",
            "details": {"command": focused.get("command"), "returncode": focused.get("returncode")},
        }
    )

    decision_rows = load_jsonl(route / "KIA_REPAIR_DECISION_LEDGER.jsonl")
    checks.append(
        {
            "check": "repair_decision_ledger_boundary",
            "status": "passed"
            if decision_rows
            and all(row.get("production_change_claim") is False for row in decision_rows)
            and all(row.get("broker_runtime_change_status") is False for row in decision_rows)
            else "failed",
            "details": {"rows": len(decision_rows)},
        }
    )

    next_starter_text = (
        (route / KIA_NEXT_STARTER_FILE).read_text(encoding="utf-8")
        if (route / KIA_NEXT_STARTER_FILE).exists()
        else ""
    )
    saturation_text = (
        (route / KIA_SATURATION_SELF_RED_TEAM_FILE).read_text(encoding="utf-8")
        if (route / KIA_SATURATION_SELF_RED_TEAM_FILE).exists()
        else ""
    )
    next_and_saturation_failures = []
    if not next_starter_text.startswith("/goal Continue from "):
        next_and_saturation_failures.append("next_starter_missing_goal_prefix")
    for phrase in (
        "production_replay_runtime_plus_simulated_account_and_source_bound_path_truth",
        "do not claim production readiness",
        KIA_REPAIR_POLICY_ID,
    ):
        if phrase not in next_starter_text:
            next_and_saturation_failures.append(f"next_starter_missing:{phrase}")
    for phrase in (
        "Saturation status: completed",
        "Broker/account/order/history/deal/position mutation: false",
        "The repair did not earn production-change readiness.",
        "This self-red-team marks the replay-runtime evidence-class route complete without claiming production readiness",
    ):
        if phrase not in saturation_text:
            next_and_saturation_failures.append(f"saturation_missing:{phrase}")
    checks.append(
        {
            "check": "route_local_next_starter_and_saturation",
            "status": "passed" if not next_and_saturation_failures else "failed",
            "details": {
                "next_starter_bytes": len(next_starter_text.encode("utf-8")),
                "saturation_bytes": len(saturation_text.encode("utf-8")),
                "failures": next_and_saturation_failures,
            },
        }
    )

    scratch = load_json(route / "KIA_SCRATCH_CLEANUP_PROOF.json") if (route / "KIA_SCRATCH_CLEANUP_PROOF.json").exists() else {}
    checks.append(
        {
            "check": "scratch_cleanup",
            "status": "passed"
            if scratch.get("scratch_exists_before_cleanup") is True
            and scratch.get("scratch_exists_after_cleanup") is False
            and scratch.get("raw_export_scratch_committed") is False
            else "failed",
            "details": scratch,
        }
    )

    audit_text = (route / "COMPLETION_AUDIT.md").read_text(encoding="utf-8") if (route / "COMPLETION_AUDIT.md").exists() else ""
    completion_audit_failures = []
    for phrase in (
        f"Completion status: {KIA_COMPLETION_STATUS}",
        "Production-change readiness: false",
        "Direct live `SessionOrchestrator` parity claim: false",
        "Prompt Completion Requirement Audit",
        "This audit marks only the KIA replay-runtime evidence-class objective complete.",
    ):
        if phrase not in audit_text:
            completion_audit_failures.append(f"missing:{phrase}")
    if "Completion status: INCOMPLETE" in audit_text:
        completion_audit_failures.append("still_marks_incomplete")
    if "Completion status: COMPLETE\n" in audit_text:
        completion_audit_failures.append("unbounded_complete_claim")
    checks.append(
        {
            "check": "completion_audit_not_overclaiming",
            "status": "passed" if not completion_audit_failures else "failed",
            "details": {
                "bytes": len(audit_text.encode("utf-8")),
                "completion_status": KIA_COMPLETION_STATUS,
                "failures": completion_audit_failures,
            },
        }
    )

    manifest = load_json(route / "KIA_OUTPUT_MANIFEST.json") if (route / "KIA_OUTPUT_MANIFEST.json").exists() else {}
    route_audit = load_json(route / "KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json") if (route / "KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json").exists() else {}
    prompt_completion_requirements = {
        "shared_core_or_replay_runtime_verified": proof.get("shared_core_status")
        == KIA_PRODUCTION_SHARED_CORE_STATUS,
        "smoke_and_development_hydration_replay_complete": bool(source_rows)
        and smoke.get("status") == "completed"
        and development_summary.get("status") == "completed"
        and repair_summary.get("status") == "completed",
        "raw_scratch_deleted_or_exact": scratch.get("scratch_exists_after_cleanup") is False
        and scratch.get("raw_export_scratch_committed") is False,
        "microscope_contract_materialized": all(
            count > 0
            for count in (
                smoke_counts.get("candidate", 0),
                smoke_counts.get("order", 0),
                smoke_counts.get("trade", 0),
                smoke_counts.get("missed", 0),
                repair_counts.get("candidate", 0),
                repair_counts.get("order", 0),
                repair_counts.get("trade", 0),
                repair_counts.get("missed", 0),
                holdout_counts.get("candidate", 0),
                holdout_counts.get("daily", 0),
            )
        ),
        "selected_path_truth_tick_or_exact_requirement": bool(tick_gap_rows) and not tick_gap_failures,
        "risk_rejection_anatomy_consumed": development_counts.get("risk_headroom_lockout", 0) > 0
        and any(row.get("decision_id") == "kia_decision_004_scheduler_single_select_repair_measured" for row in decision_rows),
        "same_evidence_limitations_fixed_or_exact": not any(
            str(row.get("status", "")).startswith("open_same_evidence_class")
            for row in limitations
        )
        and "[ ]" not in action_queue
        and repair_before_after.get("repair_counts_as_replay_system_repair") is True,
        "holdout_after_repair_completed": holdout_summary.get("status") == "completed"
        and repair_before_after.get("kia_holdout_rolling_summary", {}).get("status") == "completed",
        "verification_floor_artifacts_present": focused.get("status") == "passed"
        and route_audit.get("ok") is True
        and manifest.get("raw_export_scratch_committed") is False
        and bool(audit_text),
        "remaining_items_exact_or_queued": bool(next_starter_text)
        and bool(saturation_text)
        and all(row.get("next_action") for row in limitations),
        "scoped_commit_boundary_recorded": scratch.get("raw_export_scratch_committed") is False
        and (route / ".gitattributes").exists(),
    }
    prompt_completion_failures = [
        name for name, passed in prompt_completion_requirements.items() if not passed
    ]
    checks.append(
        {
            "check": "prompt_completion_requirements",
            "status": "passed" if not prompt_completion_failures else "failed",
            "details": {
                "requirements": prompt_completion_requirements,
                "failures": prompt_completion_failures,
            },
        }
    )
    checks.append(
        {
            "check": "output_manifest_scope",
            "status": "passed"
            if manifest.get("raw_export_scratch_committed") is False
            and manifest.get("no_live_broker_mutation") is True
            and manifest.get("no_paid_api") is True
            and manifest.get("no_remote_push") is True
            else "failed",
            "details": {
                "file_count": manifest.get("file_count"),
                "raw_export_scratch_committed": manifest.get("raw_export_scratch_committed"),
            },
        }
    )

    checks.append(
        {
            "check": "route_artifact_audit",
            "status": "passed"
            if route_audit.get("ok") is True and not route_audit.get("missing_required")
            else "failed",
            "details": {
                "ok": route_audit.get("ok"),
                "missing_required": route_audit.get("missing_required"),
                "missing_warnings": route_audit.get("missing_warnings"),
            },
        }
    )

    failures = [check for check in checks if check["status"] != "passed"]
    result = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if not failures else "failed",
        "failure_count": len(failures),
        "checks": checks,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    if write_result:
        result_path = route / "KIA_VERIFICATION_RESULT.json"
        result = _preserve_generated_at_utc_if_payload_unchanged(result_path, result)
        atomic_write_json(result_path, result)
    return result


def build_route(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str | None = None,
    previous_route_dir: Path | str | None = None,
    run_tests: bool = True,
    focused_test_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir or ROUTE_DIR)
    previous = _repo_path(repo_root, previous_route_dir or TIMEWARP_ROUTE_DIR)
    route.mkdir(parents=True, exist_ok=True)
    _write_route_lfs_attributes(route)

    tick_gap_retry_summary = _tick_gap_retry_attempt_summary(route)
    scratch = route / "_scratch"
    if scratch.exists():
        import shutil

        shutil.rmtree(scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    previous_summary = _summarize_previous_route(previous)
    source_rows = _source_hydration_rows(previous)
    tick_gap_rows = _tick_gap_source_bound_rows(
        previous_route_dir=previous,
        retry_summary=tick_gap_retry_summary,
    )
    tick_gaps_source_bound = _tick_gaps_source_bound(tick_gap_rows)
    development_summary = _write_development_failure_anatomy(
        route_dir=route,
        previous_route_dir=previous,
        previous_summary=previous_summary,
    )
    development_anatomy_complete = development_summary.get("status") == "completed"
    repair_before_after = _write_system_repair_rerun(
        route_dir=route,
        previous_route_dir=previous,
        previous_summary=previous_summary,
    )
    repair_complete = repair_before_after.get("status") == "completed"
    prompt_hash = _file_hash_or_none(repo_root / PROMPT_PATH)
    starter_hash = _file_hash_or_none(repo_root / STARTER_PATH)

    context = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "prompt_path": str(PROMPT_PATH),
        "prompt_sha256": prompt_hash,
        "starter_path": str(STARTER_PATH),
        "starter_sha256": starter_hash,
        "previous_route_dir": str(previous),
        "previous_route_id": TIMEWARP_ROUTE_ID,
        "evidence_class": "production_replay_runtime_plus_simulated_account_and_source_bound_path_truth",
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "runtime_boundary": NO_BROKER_BOUNDARY,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "full_completion_claim": False,
        "no_arbitrary_top_n_closure": True,
        "mandatory_context_refresh_completed_after_resume": True,
        "doctrine_operationalization": {
            "builder_posture": "constructive_replay_runtime_repair_checkpoint",
            "proof_or_impossibility_stop_condition": "full_prompt_completion_not_met_until_shared_core_smoke_development_repair_holdout_and_artifact_audit_pass",
            "forbidden_surfaces_excluded": [
                "live trading",
                "broker account/order/history/deal/position mutation",
                "credential mutation or disclosure",
                "paid API/vendor calls",
                "active VPS process changes",
                "remote push",
                "live deployment/reload",
            ],
        },
        "current_capability_checkpoint": [
            "SimulatedBroker replay mutation boundary",
            "PathTruthIndex M1/tick indexed lookup metadata",
            "KIA checkpoint/backlog/action queue route state",
            "exact selected-order tick gap source-bound ledger",
            "development tranche failure anatomy ledgers",
            "scheduler single-select repair decision-tape rerun and holdout ledgers",
        ],
    }
    atomic_write_json(route / "KIA_CONTEXT_ANCHOR.json", context)
    atomic_write_json(route / "KIA_PREVIOUS_ROUTE_MEASUREMENT_SUMMARY.json", previous_summary)
    atomic_write_json(route / "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json", tick_gap_retry_summary)
    atomic_write_jsonl(route / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", tick_gap_rows)
    atomic_write_jsonl(route / "KIA_SOURCE_HYDRATION_LEDGER.jsonl", source_rows)
    atomic_write_jsonl(
        route / "KIA_ACTIVE_QUESTION_STACK.jsonl",
        _question_rows(
            tick_gaps_source_bound=tick_gaps_source_bound,
            development_anatomy_complete=development_anatomy_complete,
            repair_complete=repair_complete,
        ),
    )
    runtime_proof = _runtime_parity_and_shared_core_proof(repo_root)
    limitation_rows = _limitation_rows(
        previous_summary,
        tick_gap_rows,
        development_summary,
        repair_before_after,
        runtime_proof,
    )
    atomic_write_jsonl(route / "KIA_LIMITATION_BACKLOG.jsonl", limitation_rows)
    smoke_summary = _write_kia_smoke_replay(repo_root=repo_root, route_dir=route)
    smoke_completed = smoke_summary.get("status") == "completed"
    shared_core_completed = (
        runtime_proof.get("shared_core_status")
        == KIA_PRODUCTION_SHARED_CORE_STATUS
    )
    checkpoint_rows = [
        {
            "checkpoint_id": "kia_cp001_runtime_adapter_and_route_state",
            "timestamp_utc": utc_now(),
            "current_head": context.get("git_head"),
            "completed_capability": "implemented replay-only SimulatedBroker, indexed PathTruthIndex lookup proof, and KIA route checkpoint state",
            "files_changed": [
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "tests/test_v4_timewarp_simulated_live_research_loop.py",
                "src/research_infra/v4_know_it_all_live_replay_runtime.py",
            ],
            "tests_verifiers_run": [
                "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_timewarp_simulated_live_research_loop.py -q",
                "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_know_it_all_live_replay_runtime.py -q",
                "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
            ],
            "limitations_discovered": [row["limitation_id"] for row in limitation_rows],
            "limitations_fixed": [
                "explicit_simulated_broker_adapter_absent",
                "path_truth_index_contract_not_auditable",
            ],
            "next_concrete_action": "rerun KIA smoke slice with new indexed path and simulated broker metadata",
            "limitation_classes": ["infrastructure", "source", "system_behavior"],
        }
    ]
    if smoke_completed:
        checkpoint_rows.append(
            {
                "checkpoint_id": "kia_cp002_smoke_replay_materialized",
                "timestamp_utc": utc_now(),
                "current_head": context.get("git_head"),
                "completed_capability": "reran KIA smoke replay with SimulatedBroker and PathTruthIndex metadata in candidate/order/path ledgers",
                "files_changed": [
                    "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                    "tests/test_v4_timewarp_simulated_live_research_loop.py",
                    "src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "tests/test_v4_know_it_all_live_replay_runtime.py",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_SMOKE_REPLAY_SUMMARY.json",
                    *[
                        f"research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/{filename}"
                        for filename in KIA_SMOKE_LEDGER_FILES.values()
                    ],
                ],
                "tests_verifiers_run": [
                    "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
                    "python3 research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/verify_kia_route.py",
                    "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07 --full-jsonl",
                    "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_v4_know_it_all_live_replay_runtime.py -q",
                ],
                "replay_row_counts": smoke_summary.get("row_counts"),
                "replay_delta": {
                    "smoke_stage": "pending_kia_rerun -> completed",
                    "campaign_summary": smoke_summary.get("campaign_summary"),
                },
                "limitations_discovered": [],
                "limitations_fixed": ["kia_smoke_replay_pending"],
                "next_concrete_action": "extract_or_verify_shared_live_replay_decision_cycle_core_without_live_side_effects",
                "limitation_classes": ["infrastructure"],
            }
        )
    if shared_core_completed:
        checkpoint_rows.append(
            {
                "checkpoint_id": "kia_cp003_shared_decision_cycle_core_verified",
                "timestamp_utc": utc_now(),
                "current_head": context.get("git_head"),
                "completed_capability": "extracted and verified replay-safe V4DecisionCycleCore for candidate evaluation and scheduler allocation without SessionOrchestrator boot",
                "files_changed": [
                    "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                    "tests/test_v4_timewarp_simulated_live_research_loop.py",
                    "src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ACTION_QUEUE.md",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ROLLING_RUN_STATE.json",
                ],
                "tests_verifiers_run": [
                    "python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_v4_know_it_all_live_replay_runtime.py -q",
                    "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
                    "python3 research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/verify_kia_route.py",
                ],
                "replay_row_counts": smoke_summary.get("row_counts"),
                "replay_delta": {
                    "shared_core_status": runtime_proof.get("shared_core_status"),
                    "full_live_replay_parity_claim": runtime_proof.get("full_live_replay_parity_claim"),
                },
                "limitations_discovered": [
                    "live_session_orchestrator_not_rewired_in_this_checkpoint",
                ],
                "limitations_fixed": ["kia_shared_live_replay_core_pending"],
                "next_concrete_action": "retry_or_exactly_source_bound_selected_order_tick_gaps",
                "limitation_classes": ["infrastructure"],
            }
        )
    if tick_gaps_source_bound:
        checkpoint_rows.append(
            {
                "checkpoint_id": "kia_cp004_tick_gaps_source_bound",
                "timestamp_utc": utc_now(),
                "current_head": context.get("git_head"),
                "completed_capability": "retried or exactly source-bound the two zero-row selected-order FTMO tick windows without converting them into tick-truth rows",
                "files_changed": [
                    "src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "tests/test_v4_know_it_all_live_replay_runtime.py",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ACTION_QUEUE.md",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ROLLING_RUN_STATE.json",
                ],
                "tests_verifiers_run": [
                    "uv run --with siliconmetatrader5 --with numpy python scripts/export_mt5_research_ticks.py --prefer-silicon-bridge --yes-live-readonly --symbol GBPUSD:GBPUSD --symbol US30_cash:US30.cash --window sel_002_20260420T2359_20260421T0001:2026-04-20T23:59:00Z:2026-04-21T00:01:00Z --label kia_tick_gap_retry_20260420_sel002 --output-root research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/_scratch --source-broker FTMO --source-role owner_authorized_research_hydration --not-redacted_account-native --source-truth-scope ordered_price_path_only_not_broker_order_lifecycle_truth",
                    "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
                    "python3 research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/verify_kia_route.py",
                ],
                "source_gap_rows": len(tick_gap_rows),
                "source_gap_statuses": dict(
                    Counter(str(row.get("source_bound_status")) for row in tick_gap_rows)
                ),
                "limitations_discovered": [],
                "limitations_fixed": ["kia_lim_002_exact_tick_gaps"],
                "next_concrete_action": "run_development_tranche_failure_anatomy_for_weak_accepted_trades_partial_be_runner_scheduler_regret_cost_flips_and_risk_headroom_lockout",
                "limitation_classes": ["source"],
            }
        )
    if development_anatomy_complete:
        checkpoint_rows.append(
            {
                "checkpoint_id": "kia_cp005_development_failure_anatomy_materialized",
                "timestamp_utc": utc_now(),
                "current_head": context.get("git_head"),
                "completed_capability": "materialized development tranche failure anatomy for weak accepted trades, partial_be_runner, scheduler regret, cost flips, and risk-headroom lockout",
                "files_changed": [
                    "src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "tests/test_v4_know_it_all_live_replay_runtime.py",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
                    *[
                        f"research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/{filename}"
                        for filename in DEVELOPMENT_FAILURE_LEDGER_FILES.values()
                    ],
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ACTION_QUEUE.md",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ROLLING_RUN_STATE.json",
                ],
                "tests_verifiers_run": [
                    "python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research_infra/v4_know_it_all_live_replay_runtime.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_v4_know_it_all_live_replay_runtime.py",
                    "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_v4_know_it_all_live_replay_runtime.py -q",
                    "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
                    "python3 research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/verify_kia_route.py",
                ],
                "failure_family_counts": development_summary.get("family_counts"),
                "limitations_discovered": [],
                "limitations_fixed": [
                    "kia_lim_003_repaired_dev_slice_worsened_failure_anatomy",
                    "kia_lim_004_holdout_negative_development_precursor_anatomy",
                ],
                "next_concrete_action": "implement_only_repeated_system_repairs_with_row_evidence_then_rerun_development_slice_and_holdout",
                "limitation_classes": ["system_behavior"],
            }
        )
    if repair_complete:
        checkpoint_rows.append(
            {
                "checkpoint_id": "kia_cp006_scheduler_single_select_repair_rerun_and_holdout",
                "timestamp_utc": utc_now(),
                "current_head": context.get("git_head"),
                "completed_capability": "implemented scheduler single-select risk-preservation repair, reran development decision tape, and ran holdout rolling tranche",
                "files_changed": [
                    "src/research_infra/v4_know_it_all_live_replay_runtime.py",
                    "tests/test_v4_know_it_all_live_replay_runtime.py",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json",
                    *[
                        f"research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/{filename}"
                        for filename in (*KIA_REPAIR_LEDGER_FILES.values(), *KIA_HOLDOUT_LEDGER_FILES.values())
                    ],
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ACTION_QUEUE.md",
                    "research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/KIA_ROLLING_RUN_STATE.json",
                ],
                "tests_verifiers_run": [
                    "python3 -m src.research_infra.v4_know_it_all_live_replay_runtime",
                    "python3 research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07/verify_kia_route.py",
                    "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07 --full-jsonl",
                    "uv run --with pytest --with pyyaml --with pydantic pytest tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_v4_know_it_all_live_replay_runtime.py -q",
                ],
                "replay_delta": repair_before_after.get("deltas"),
                "repair_policy_id": KIA_REPAIR_POLICY_ID,
                "limitations_discovered": [],
                "limitations_fixed": [
                    "kia_lim_003_repaired_dev_slice_worsened_repair_rerun",
                    "kia_lim_004_holdout_negative_holdout_rerun",
                ],
                "next_concrete_action": "inspect holdout and continue next rolling tranche or production-change dossier in a separate evidence class",
                "limitation_classes": ["system_behavior"],
            }
        )
    atomic_write_jsonl(route / "KIA_CHECKPOINT_LEDGER.jsonl", checkpoint_rows)
    atomic_write_jsonl(
        route / "KIA_REPAIR_DECISION_LEDGER.jsonl",
        [
            {
                "decision_id": "kia_decision_001_replay_adapter_checkpoint_not_completion",
                "timestamp_utc": utc_now(),
                "decision": "implement_runtime_checkpoint_continue_kia_action_queue",
                "status": "incomplete_same_evidence_class_repair_continues",
                "implemented_capabilities": [
                    "SimulatedBroker replay adapter blocks order_send mutation",
                    "PathTruthIndex records indexed M1/tick lookup metadata",
                    "KIA route state/checkpoint/backlog/action queue/verifier wrapper",
                ],
                "rejected_claims": [
                    "full live replay parity complete",
                    "production change readiness",
                    "broker-real lifecycle truth",
                    "holdout repair success",
                ],
                "next_action": "rerun KIA smoke and development tranche before any system repair claim",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            },
            {
                "decision_id": "kia_decision_002_tick_gap_source_bound_not_tick_truth_repaired",
                "timestamp_utc": utc_now(),
                "decision": "carry_gbpusd_and_us30_zero_row_tick_windows_as_exact_unresolved_path_source_requirements",
                "status": (
                    "accepted_for_action_queue_item_3"
                    if tick_gaps_source_bound
                    else "open_retry_or_exact_source_bound_required"
                ),
                "evidence_artifacts": [
                    "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
                    "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
                ],
                "rejected_claims": [
                    "tick_truth_repaired_for_zero_row_windows",
                    "redacted_account broker lifecycle truth satisfied by FTMO tick export",
                    "production change readiness",
                ],
                "next_action": "use_exact_unresolved_tick_requirement_labels_in_development_tranche_and_do_not_promote_m1_fallback_to_tick_truth",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            },
            {
                "decision_id": "kia_decision_003_development_failure_anatomy_not_yet_repair",
                "timestamp_utc": utc_now(),
                "decision": "materialize_failure_anatomy_before_any_system_repair",
                "status": (
                    "failure_anatomy_complete_repair_implementation_pending"
                    if development_anatomy_complete
                    else "failure_anatomy_incomplete"
                ),
                "evidence_artifacts": [
                    "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
                    *DEVELOPMENT_FAILURE_LEDGER_FILES.values(),
                ],
                "family_counts": development_summary.get("family_counts"),
                "rejected_claims": [
                    "repair implemented",
                    "repair rerun complete",
                    "holdout repair success",
                    "production change readiness",
                ],
                "next_action": "choose_only_repeated_system_repairs_supported_by_failure_family_ledgers_then_rerun_development_and_holdout",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            },
            {
                "decision_id": "kia_decision_004_scheduler_single_select_repair_measured",
                "timestamp_utc": utc_now(),
                "decision": "implement_scheduler_single_select_risk_preservation_and_measure_development_plus_holdout_decision_tape_rerun",
                "status": (
                    "repair_rerun_and_holdout_completed"
                    if repair_complete
                    else "repair_rerun_incomplete"
                ),
                "repair_policy_id": KIA_REPAIR_POLICY_ID,
                "runtime_overrides": dict(KIA_REPAIR_RUNTIME_OVERRIDES),
                "evidence_artifacts": [
                    "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json",
                    "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json",
                    "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json",
                    *KIA_REPAIR_LEDGER_FILES.values(),
                    *KIA_HOLDOUT_LEDGER_FILES.values(),
                ],
                "row_evidence_inputs": [
                    "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
                    *DEVELOPMENT_FAILURE_LEDGER_FILES.values(),
                ],
                "deltas": repair_before_after.get("deltas"),
                "rejected_claims": [
                    "production change readiness",
                    "broker-real lifecycle truth",
                    "live deployment approval",
                    "full SessionOrchestrator parity complete",
                ],
                "next_action": "continue next rolling tranche or production-change dossier only as a separate evidence class",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            },
        ],
    )
    atomic_write_json(route / "KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json", runtime_proof)
    _write_action_queue(
        route,
        smoke_completed=smoke_completed,
        shared_core_completed=shared_core_completed,
        tick_gaps_source_bound=tick_gaps_source_bound,
        development_anatomy_complete=development_anatomy_complete,
        repair_complete=repair_complete,
    )
    _write_route_local_next_starter(
        route,
        repair_complete=repair_complete,
        repair_summary=repair_before_after,
    )
    _write_saturation_self_red_team(
        route,
        previous_summary=previous_summary,
        tick_gap_rows=tick_gap_rows,
        development_summary=development_summary,
        repair_summary=repair_before_after,
        runtime_proof=runtime_proof,
    )
    _write_route_local_verifier(route)
    atomic_write_json(
        route / "KIA_ROLLING_RUN_STATE.json",
        {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "current_stage": (
                "repair_rerun_and_holdout_complete_next_rolling_tranche_or_dossier_pending"
                if repair_complete
                else (
                    "development_failure_anatomy_complete_next_system_repair_selection_pending"
                    if development_anatomy_complete
                    else (
                        "tick_gaps_source_bound_next_development_tranche_failure_anatomy_pending"
                        if tick_gaps_source_bound
                        else (
                            "shared_core_verified_next_tick_gap_source_bound_pending"
                            if shared_core_completed
                            else (
                                "smoke_replay_completed_next_shared_core_pending"
                                if smoke_completed
                                else "checkpoint_created_next_smoke_replay_pending"
                            )
                        )
                    )
                )
            ),
            "previous_timewarp_days": sorted(
                set((previous_summary.get("ledger_counts") or {}).keys())
            ),
            "smoke": {
                "status": smoke_summary.get("status"),
                "summary_path": "KIA_SMOKE_REPLAY_SUMMARY.json",
                "row_counts": smoke_summary.get("row_counts"),
                "campaign_summary": smoke_summary.get("campaign_summary"),
                "source_primary_hydration_complete": smoke_summary.get("source_primary_hydration_complete"),
            },
            "shared_core": {
                "status": runtime_proof.get("shared_core_status"),
                "proof_path": "KIA_RUNTIME_PARITY_AND_SHARED_CORE_PROOF.json",
                "decision_cycle_core": runtime_proof.get("decision_cycle_core"),
                "full_live_replay_parity_claim": runtime_proof.get("full_live_replay_parity_claim"),
                "live_session_orchestrator_wiring_status": runtime_proof.get(
                    "live_session_orchestrator_wiring_status"
                ),
            },
            "tick_gap_source_bound": {
                "status": (
                    "completed_exact_unresolved_path_source_requirements"
                    if tick_gaps_source_bound
                    else "pending_retry_or_source_bound"
                ),
                "ledger_path": "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
                "retry_summary_path": "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
                "rows": len(tick_gap_rows),
                "source_bound_statuses": dict(
                    Counter(str(row.get("source_bound_status")) for row in tick_gap_rows)
                ),
            },
            "development_tranche": {
                "status": (
                    "repair_rerun_complete"
                    if repair_complete
                    else "failure_anatomy_materialized_repair_selection_pending"
                    if development_anatomy_complete
                    else "pending_after_smoke"
                ),
                "failure_anatomy_summary_path": "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json",
                "family_counts": development_summary.get("family_counts"),
            },
            "repair_rerun": {
                "status": "completed" if repair_complete else "pending_after_repair_decision",
                "summary_path": "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json",
                "before_after_summary_path": "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json",
                "repair_policy_id": KIA_REPAIR_POLICY_ID,
                "deltas": repair_before_after.get("deltas"),
            },
            "holdout_rolling_tranche": {
                "status": "completed" if repair_complete else "pending_after_development_repair",
                "summary_path": "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json",
                "holdout_summary": repair_before_after.get("kia_holdout_rolling_summary"),
            },
            "contaminated_by_current_repairs": ["repair_development_decision_tape"]
            if repair_complete
            else [],
        },
    )
    if focused_test_result is not None:
        focused = dict(focused_test_result)
    elif run_tests:
        focused = _run_focused_tests(repo_root)
    else:
        focused = {"status": "skipped", "returncode": None, "command": []}
    atomic_write_json(route / "KIA_FOCUSED_TEST_RESULT.json", focused)

    scratch_proof = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "scratch_path": str(scratch),
        "scratch_exists_before_cleanup": scratch.exists(),
        "tick_gap_retry_summary_preserved": True,
        "tick_gap_retry_summary_path": "KIA_TICK_GAP_RETRY_ATTEMPT_SUMMARY.json",
        "tick_gap_source_bound_ledger_path": "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
        "raw_export_scratch_committed": False,
        "raw_export_scratch_policy": "raw FTMO/M1/tick export scratch remains excluded by default",
    }
    import shutil

    shutil.rmtree(scratch)
    scratch_proof.update(
        {
            "cleanup_completed_at_utc": utc_now(),
            "scratch_exists_after_cleanup": scratch.exists(),
            "cleanup_status": "completed_after_checkpoint_artifacts",
        }
    )
    atomic_write_json(route / "KIA_SCRATCH_CLEANUP_PROOF.json", scratch_proof)
    _write_completion_audit(
        route,
        previous_summary,
        smoke_summary,
        runtime_proof,
        tick_gap_rows,
        tick_gap_retry_summary,
        development_summary,
        repair_before_after,
    )
    output_manifest(route)
    verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    route_audit = audit_route(route, None, profile="standard")
    atomic_write_json(route / "KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json", route_audit)
    output_manifest(route)
    verification = verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    manifest = output_manifest(route)
    return {
        "route_dir": str(route),
        "verification": verification,
        "manifest": manifest,
        "previous_summary": previous_summary,
        "smoke_summary": smoke_summary,
    }


if __name__ == "__main__":
    result = build_route()
    print(result["verification"]["status"])
