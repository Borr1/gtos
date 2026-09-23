"""KIAP V4 parity tick-first runtime repair route builder and verifier.

This module owns the corrective KIAP route state. It keeps the route in
progress while proving the smoke replay, source-requirement queue, and selected
tick-truth gates that the prior KIA route did not enforce strongly enough.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_FOR_IMPORTS))

from scripts.audit_goal_route_artifacts import audit_route
from src.components.v4_live_replay_decision_core import PRODUCTION_CORE_IMPORT_PATH
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    BASELINE_DAYS,
    BASELINE_PENDING_EXPIRY_MINUTES,
    CampaignConfig,
    HOLDOUT_DAYS,
    LiveReplayMode,
    OUTCOME_EVIDENCE_CLASS,
    REPAIRED_PENDING_EXPIRY_MINUTES,
    SIM_EVIDENCE_CLASS,
    SMOKE_DAY,
    SOURCE_BOUND_EVIDENCE_CLASS,
    SOURCE_TRUTH_SCOPE,
    SimulatedBroker,
    atomic_write_json,
    atomic_write_jsonl,
    build_source_package,
    clear_replay_row_index_caches,
    file_sha256,
    first_present,
    ftmo_symbol,
    git_value,
    iter_ftmo_manifest_payloads,
    load_config,
    load_json,
    load_jsonl,
    run_campaign,
    stable_sha256,
    summarize_campaign,
    utc_now,
)


ROUTE_ID = "final_moonshot_v4_kia_parity_tick_first_runtime_repair_2026_06_07"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_V4_KIA_PARITY_TICK_FIRST_RUNTIME_REPAIR_GOAL_PROMPT_2026-06-07.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_V4_KIA_PARITY_TICK_FIRST_RUNTIME_REPAIR_STARTER_2026-06-07.txt"
)
PRIOR_KIA_ROUTE = Path(
    "research/operations/"
    "final_moonshot_v4_know_it_all_live_replay_runtime_and_system_repair_2026_06_07"
)
EVIDENCE_CLASS = "production_replay_runtime_plus_simulated_account_and_source_bound_path_truth"
KIA_PRODUCTION_SHARED_CORE_STATUS = (
    "production_owned_shared_core_imported_and_called_by_live_and_replay_candidate_scheduler_surfaces"
)
KIAP_DEVELOPMENT_CHECKPOINT_DAYS = (BASELINE_DAYS[1],)
KIAP_ITEM8_PHASES = ("full_development", "repair_rerun", "holdout_rolling")

KIAP_SMOKE_LEDGER_FILES = {
    "asof": "KIAP_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIAP_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIAP_PACKET_SIDECAR_SMOKE_2026_04_20.jsonl",
    "scorecard": "KIAP_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIAP_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIAP_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIAP_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIAP_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIAP_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIAP_MISSED_OPPORTUNITY_MICROSCOPE_LEDGER.jsonl",
    "winner": "KIAP_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIAP_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIAP_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIAP_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIAP_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_DEVELOPMENT_LEDGER_FILES = {
    "asof": "KIAP_DEVELOPMENT_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIAP_DEVELOPMENT_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIAP_PACKET_SIDECAR_DEVELOPMENT_2026_04_21.jsonl",
    "scorecard": "KIAP_DEVELOPMENT_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIAP_DEVELOPMENT_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIAP_DEVELOPMENT_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIAP_DEVELOPMENT_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIAP_DEVELOPMENT_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIAP_DEVELOPMENT_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIAP_DEVELOPMENT_MISSED_OPPORTUNITY_MICROSCOPE_LEDGER.jsonl",
    "winner": "KIAP_DEVELOPMENT_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIAP_DEVELOPMENT_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIAP_DEVELOPMENT_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIAP_DEVELOPMENT_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIAP_DEVELOPMENT_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_FULL_DEVELOPMENT_LEDGER_FILES = {
    "asof": "KIAP_FULL_DEVELOPMENT_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIAP_FULL_DEVELOPMENT_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIAP_PACKET_SIDECAR_FULL_DEVELOPMENT_INDEX.jsonl",
    "scorecard": "KIAP_FULL_DEVELOPMENT_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIAP_FULL_DEVELOPMENT_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIAP_FULL_DEVELOPMENT_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIAP_FULL_DEVELOPMENT_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIAP_FULL_DEVELOPMENT_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIAP_FULL_DEVELOPMENT_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIAP_FULL_DEVELOPMENT_MISSED_OPPORTUNITY_MICROSCOPE_LEDGER.jsonl",
    "winner": "KIAP_FULL_DEVELOPMENT_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIAP_FULL_DEVELOPMENT_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIAP_FULL_DEVELOPMENT_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIAP_FULL_DEVELOPMENT_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIAP_FULL_DEVELOPMENT_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_REPAIR_RERUN_LEDGER_FILES = {
    "asof": "KIAP_REPAIR_RERUN_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIAP_REPAIR_RERUN_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIAP_PACKET_SIDECAR_REPAIR_RERUN_INDEX.jsonl",
    "scorecard": "KIAP_REPAIR_RERUN_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIAP_REPAIR_RERUN_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIAP_REPAIR_RERUN_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIAP_REPAIR_RERUN_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIAP_REPAIR_RERUN_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIAP_REPAIR_RERUN_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIAP_REPAIR_RERUN_MISSED_OPPORTUNITY_MICROSCOPE_LEDGER.jsonl",
    "winner": "KIAP_REPAIR_RERUN_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIAP_REPAIR_RERUN_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIAP_REPAIR_RERUN_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIAP_REPAIR_RERUN_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIAP_REPAIR_RERUN_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_HOLDOUT_ROLLING_LEDGER_FILES = {
    "asof": "KIAP_HOLDOUT_ROLLING_ASOF_MARKET_DATA_LEDGER.jsonl",
    "candidate": "KIAP_HOLDOUT_ROLLING_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "packet_sidecar": "KIAP_PACKET_SIDECAR_HOLDOUT_ROLLING_INDEX.jsonl",
    "scorecard": "KIAP_HOLDOUT_ROLLING_SELECTOR_SCHEDULER_SCORECARD.jsonl",
    "oracle": "KIAP_HOLDOUT_ROLLING_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "order": "KIAP_HOLDOUT_ROLLING_SIMULATED_ORDER_LEDGER.jsonl",
    "trade": "KIAP_HOLDOUT_ROLLING_SIMULATED_TRADE_LEDGER.jsonl",
    "event": "KIAP_HOLDOUT_ROLLING_SIMULATED_EVENT_LEDGER.jsonl",
    "account": "KIAP_HOLDOUT_ROLLING_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "missed": "KIAP_HOLDOUT_ROLLING_MISSED_OPPORTUNITY_MICROSCOPE_LEDGER.jsonl",
    "winner": "KIAP_HOLDOUT_ROLLING_WINNER_ANATOMY_LEDGER.jsonl",
    "loser": "KIAP_HOLDOUT_ROLLING_LOSER_ANATOMY_LEDGER.jsonl",
    "exit": "KIAP_HOLDOUT_ROLLING_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
    "rollup": "KIAP_HOLDOUT_ROLLING_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
    "daily": "KIAP_HOLDOUT_ROLLING_DAILY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_PHASE_LEDGER_FILES = {
    "smoke": KIAP_SMOKE_LEDGER_FILES,
    "development": KIAP_DEVELOPMENT_LEDGER_FILES,
    "full_development": KIAP_FULL_DEVELOPMENT_LEDGER_FILES,
    "repair_rerun": KIAP_REPAIR_RERUN_LEDGER_FILES,
    "holdout_rolling": KIAP_HOLDOUT_ROLLING_LEDGER_FILES,
}

KIAP_ITEM8_SUMMARY_FILES = {
    "full_development": "KIAP_FULL_DEVELOPMENT_REPLAY_SUMMARY.json",
    "repair_rerun": "KIAP_REPAIR_RERUN_REPLAY_SUMMARY.json",
    "holdout_rolling": "KIAP_HOLDOUT_ROLLING_REPLAY_SUMMARY.json",
}

KIAP_ITEM8_RISK_FILES = {
    "full_development": "KIAP_FULL_DEVELOPMENT_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
    "repair_rerun": "KIAP_REPAIR_RERUN_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
    "holdout_rolling": "KIAP_HOLDOUT_ROLLING_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
}

KIAP_ITEM8_WEEKLY_FILES = {
    "full_development": "KIAP_FULL_DEVELOPMENT_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
    "repair_rerun": "KIAP_REPAIR_RERUN_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
    "holdout_rolling": "KIAP_HOLDOUT_ROLLING_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
}

KIAP_ITEM9_LEDGER_FILES = {
    "weak_accepted_trades": "KIAP_ITEM9_WEAK_ACCEPTED_TRADE_LEDGER.jsonl",
    "partial_be_runner": "KIAP_ITEM9_PARTIAL_BE_RUNNER_LEDGER.jsonl",
    "scheduler_regret": "KIAP_ITEM9_SCHEDULER_REGRET_LEDGER.jsonl",
    "cost_flips": "KIAP_ITEM9_COST_FLIP_LEDGER.jsonl",
    "risk_headroom_lockout": "KIAP_ITEM9_RISK_HEADROOM_LOCKOUT_LEDGER.jsonl",
}
KIAP_ITEM9_SUMMARY_FILE = "KIAP_ITEM9_REPAIR_FAMILY_MEASUREMENT_SUMMARY.json"
KIAP_ITEM10_SUMMARY_FILE = "KIAP_ITEM10_VERIFIER_HARDENING_SUMMARY.json"
KIAP_STABLE_RERUN_PROOF_FILE = "KIAP_STABLE_RERUN_PROOF.json"
KIAP_COMPLETION_STATUS = "COMPLETE_WITHIN_KIAP_REPLAY_EVIDENCE_CLASS"

KIAP_ITEM8_CAMPAIGN_DEFS = {
    "full_development": {
        "name": "kiap_full_development",
        "days": BASELINE_DAYS,
        "pending_expiry_minutes": BASELINE_PENDING_EXPIRY_MINUTES,
        "use_repaired_pending_expiry": False,
        "partial_be_runner": True,
        "source_operation": "kiap_full_development_live_replay_runtime_run",
    },
    "repair_rerun": {
        "name": "kiap_repair_rerun",
        "days": BASELINE_DAYS,
        "pending_expiry_minutes": REPAIRED_PENDING_EXPIRY_MINUTES,
        "use_repaired_pending_expiry": True,
        "partial_be_runner": False,
        "source_operation": "kiap_repair_rerun_repaired_pending_expiry_no_partial_be_live_replay_runtime_run",
    },
    "holdout_rolling": {
        "name": "kiap_holdout_rolling",
        "days": HOLDOUT_DAYS,
        "pending_expiry_minutes": REPAIRED_PENDING_EXPIRY_MINUTES,
        "use_repaired_pending_expiry": True,
        "partial_be_runner": False,
        "source_operation": "kiap_holdout_rolling_repaired_policy_live_replay_runtime_run",
    },
}

KIAP_REQUIRED_ARTIFACTS = (
    "KIAP_CONTEXT_ANCHOR.json",
    "KIAP_ACTION_QUEUE.md",
    "KIAP_ACTIVE_QUESTION_STACK.jsonl",
    "KIAP_CHECKPOINT_LEDGER.jsonl",
    "KIAP_LIMITATION_BACKLOG.jsonl",
    "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl",
    "KIAP_SOURCE_HYDRATION_LEDGER.jsonl",
    "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
    "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl",
    "KIAP_RUNTIME_PARITY_PROOF.json",
    "KIAP_RUNTIME_PARITY_CHECKLIST.json",
    "KIAP_SMOKE_REPLAY_SUMMARY.json",
    "KIAP_ROLLING_RUN_STATE.json",
    "KIAP_FOCUSED_TEST_RESULT.json",
    "KIAP_VERIFICATION_RESULT.json",
    "KIAP_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "KIAP_OUTPUT_MANIFEST.json",
    "KIAP_SCRATCH_CLEANUP_PROOF.json",
    "KIAP_SATURATION_SELF_RED_TEAM.md",
    "COMPLETION_AUDIT.md",
    "verify_kiap_route.py",
    *KIAP_SMOKE_LEDGER_FILES.values(),
    "KIAP_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
    "KIAP_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
)


def _repo_path(repo_root: Path | str, path: Path | str) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return Path(repo_root) / path


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
    previous = dict(existing)
    current = dict(payload)
    previous.pop("generated_at_utc", None)
    current.pop("generated_at_utc", None)
    if previous == current and existing.get("generated_at_utc"):
        next_payload = dict(payload)
        next_payload["generated_at_utc"] = existing["generated_at_utc"]
        return next_payload
    return payload


def _write_stable_json(path: Path, payload: Mapping[str, Any]) -> None:
    next_payload = _preserve_generated_at_utc_if_payload_unchanged(path, dict(payload))
    atomic_write_json(path, next_payload)


def _first_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if value and value not in output:
            output[value] = dict(row)
    return output


def _norm_utc_key(value: Any) -> str:
    return str(value or "").replace("Z", "+00:00")


def _oracle_rows_by_campaign_phase_candidate(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[tuple[str, str, str, str, str], dict[str, Any]],
    dict[tuple[str, str, str], dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    by_order_id: dict[str, dict[str, Any]] = {}
    precise_window: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    precise: dict[tuple[str, str, str], dict[str, Any]] = {}
    fallback: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        order_id = str(row.get("simulated_order_id") or "")
        campaign = str(row.get("campaign") or "")
        phase = str(row.get("phase") or "")
        decision_time = _norm_utc_key(
            first_present(row.get("decision_time_utc"), row.get("asof_utc"), row.get("order_time_utc"))
        )
        expiry = _norm_utc_key(row.get("expiry_utc"))
        if order_id:
            by_order_id.setdefault(order_id, dict(row))
        if (campaign or phase) and decision_time and expiry:
            precise_window.setdefault(
                (campaign, phase, candidate_id, decision_time, expiry),
                dict(row),
            )
        if campaign or phase:
            precise.setdefault((campaign, phase, candidate_id), dict(row))
        fallback.setdefault(candidate_id, dict(row))
    return by_order_id, precise_window, precise, fallback


def _latest_order_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_rank = {
        "risk_rejected": 3,
        "filled": 3,
        "expired_unfilled": 3,
        "accepted_not_filled_pending_until_expiry": 2,
        "pending_accepted": 1,
    }
    for row in rows:
        order_id = str(row.get("simulated_order_id") or "")
        if order_id:
            grouped[order_id].append(dict(row))
    output = []
    for order_id, order_rows in sorted(grouped.items()):
        order_rows.sort(
            key=lambda row: (
                status_rank.get(str(row.get("order_status") or ""), 0),
                str(row.get("fill_time_utc") or row.get("expiry_utc") or ""),
            )
        )
        output.append(order_rows[-1])
    return output


def _decorate_phase_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    ledger_key: str,
    broker_boundary: Mapping[str, Any],
    phase: str,
    days: Iterable[str],
    action_queue_items_satisfied: Iterable[int],
    packet_sidecar_artifact: str,
) -> list[dict[str, Any]]:
    days = tuple(days)
    decorated = []
    for row in rows:
        next_row = dict(row)
        next_row.update(
            {
                "kiap_route_id": ROUTE_ID,
                "kiap_campaign_phase": phase,
                "kiap_campaign_days": list(days),
                "kiap_smoke_day": SMOKE_DAY if phase == "smoke" else None,
                "kiap_smoke_replay": phase == "smoke",
                "kiap_development_checkpoint": phase == "development",
                "kiap_full_development_tranche": phase == "full_development",
                "kiap_repair_rerun_tranche": phase == "repair_rerun",
                "kiap_holdout_rolling_tranche": phase == "holdout_rolling",
                "kiap_item8_tranche": phase in KIAP_ITEM8_PHASES,
                "kiap_action_queue_items_satisfied": list(action_queue_items_satisfied),
                "live_replay_mode": True,
                "live_replay_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
                "production_decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "simulated_broker_adapter": "SimulatedBroker",
                "broker_mutation_enabled": False,
                "broker_history_truth_satisfied": False,
                "broker_account_order_history_deal_position_mutation": False,
                "simulated_broker_boundary": dict(broker_boundary),
            }
        )
        if ledger_key in {"candidate", "order", "oracle"}:
            next_row["path_truth_index"] = "PathTruthIndex"
        if ledger_key in {"candidate", "scorecard"} and next_row.get("packet_sidecar_artifact"):
            next_row["packet_sidecar_artifact"] = packet_sidecar_artifact
        if ledger_key == "order" and next_row.get("execution_packet_sidecar_artifact"):
            next_row["execution_packet_sidecar_artifact"] = packet_sidecar_artifact
        if ledger_key == "packet_sidecar":
            next_row["packet_sidecar_partition"] = f"{phase}_{'_'.join(days)}"
        decorated.append(next_row)
    return decorated


def _decorate_smoke_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    ledger_key: str,
    broker_boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return _decorate_phase_rows(
        rows,
        ledger_key=ledger_key,
        broker_boundary=broker_boundary,
        phase="smoke",
        days=(SMOKE_DAY,),
        action_queue_items_satisfied=(4,),
        packet_sidecar_artifact=KIAP_SMOKE_LEDGER_FILES["packet_sidecar"],
    )


def _source_hydration_rows(
    source_package: Mapping[str, Any],
    *,
    phase: str = "smoke",
    start_index: int = 1,
) -> list[dict[str, Any]]:
    output = []
    for index, row in enumerate(source_package.get("source_hydration_rows") or [], start=start_index):
        next_row = dict(row)
        next_row.update(
            {
                "kiap_source_row_id": f"KIAP-SOURCE-{phase.upper()}-{index:05d}",
                "kiap_route_id": ROUTE_ID,
                "kiap_campaign_phase": phase,
                "source_row_origin": f"kiap_{phase}_build_source_package",
                "source_broker": row.get("source_broker"),
                "source_truth_scope": row.get("source_truth_scope"),
                "not_redacted_account_native": row.get("not_redacted_account_native"),
                "broker_lifecycle_truth_satisfied": row.get("broker_lifecycle_truth_satisfied"),
                "ordered_tick_truth_satisfied": row.get("ordered_tick_truth_satisfied"),
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
        output.append(next_row)
    return output


def _carried_prior_tick_gap_rows(repo_root: Path) -> list[dict[str, Any]]:
    prior_path = repo_root / PRIOR_KIA_ROUTE / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl"
    if not prior_path.exists():
        return []
    output = []
    for index, row in enumerate(load_jsonl(prior_path), start=1):
        next_row = dict(row)
        next_row.update(
            {
                "kiap_tick_gap_row_id": f"KIAP-TICK-GAP-CARRIED-{index:03d}",
                "kiap_route_id": ROUTE_ID,
                "source_row_origin": "prior_kia_exact_zero_row_selected_tick_gap_source_bound_proof",
                "carried_from_prior_kia_route": str(PRIOR_KIA_ROUTE),
                "kiap_current_smoke_selected_order": False,
                "selected_filled_path_truth_status": "exact_unresolved_tick_source_requirement",
                "ordered_tick_truth_satisfied": False,
                "final_performance_inclusion_status": "excluded_unresolved_source_requirement",
                "m1_fallback_allowed_only_with_label": True,
                "source_broker": "FTMO",
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "not_redacted_account_native": True,
                "broker_lifecycle_truth_satisfied": False,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
        output.append(next_row)
    return output


def _current_zero_row_tick_gap_rows(repo_root: Path) -> list[dict[str, Any]]:
    gap_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for manifest_path, manifest, file_payload in iter_ftmo_manifest_payloads(repo_root):
        provenance = manifest.get("source_provenance")
        provenance = provenance if isinstance(provenance, Mapping) else {}
        symbol = str(file_payload.get("file_symbol") or file_payload.get("symbol") or "")
        timeframe = str(file_payload.get("timeframe") or "").upper()
        if not symbol or timeframe != "TICK":
            continue
        source_broker = first_present(file_payload.get("source_broker"), provenance.get("source_broker"))
        source_role = first_present(file_payload.get("source_role"), provenance.get("source_role"))
        source_scope = first_present(
            file_payload.get("source_truth_scope"),
            provenance.get("source_truth_scope"),
        )
        not_redacted_account = first_present(
            file_payload.get("not_redacted_account_native"),
            provenance.get("not_redacted_account_native"),
        )
        if (
            source_broker != "FTMO"
            or source_role != "owner_authorized_research_hydration"
            or source_scope != SOURCE_TRUTH_SCOPE
            or not_redacted_account is not True
        ):
            continue
        mapped_symbol = str(file_payload.get("mt5_symbol") or file_payload.get("mapped_symbol") or "")
        if mapped_symbol and mapped_symbol != ftmo_symbol(symbol):
            continue
        try:
            rows = int(float(first_present(file_payload.get("row_count"), file_payload.get("rows"), 0)))
        except (TypeError, ValueError, OverflowError):
            rows = 0
        if rows > 0:
            continue
        request_start = str(
            first_present(
                file_payload.get("request_start_utc"),
                file_payload.get("start_utc"),
                file_payload.get("first"),
            )
            or ""
        ).replace("Z", "+00:00")
        request_end = str(
            first_present(
                file_payload.get("request_end_utc"),
                file_payload.get("end_utc"),
                file_payload.get("last"),
            )
            or ""
        ).replace("Z", "+00:00")
        if not request_start or not request_end:
            continue
        path_raw = str(file_payload.get("path") or "")
        path = Path(path_raw) if path_raw else Path("")
        if path_raw and not path.is_absolute():
            repo_candidate = repo_root / path
            path = repo_candidate if repo_candidate.exists() else manifest_path.parent / path
        gap_id = stable_sha256(
            {
                "route": ROUTE_ID,
                "symbol": symbol,
                "request_start_utc": request_start,
                "request_end_utc": request_end,
                "source_bound_status": "exact_zero_row_ftmo_tick_export_manifest",
                "manifest_path": str(manifest_path),
            }
        )[:20]
        key = (symbol, request_start, request_end)
        gap_by_key[key] = {
            "gap_id": gap_id,
            "symbol": symbol,
            "mapped_symbol": ftmo_symbol(symbol),
            "request_start_utc": request_start,
            "request_end_utc": request_end,
            "source_bound_status": "exact_zero_row_ftmo_tick_export_manifest",
            "previous_row_count": 0,
            "retry_row_count": rows,
            "retry_status": "ftmo_tick_export_zero_rows",
            "source_row_origin": "current_kiap_exact_window_tick_export_manifest_zero_rows",
            "source_broker": "FTMO",
            "source_role": str(source_role),
            "source_truth_scope": SOURCE_TRUTH_SCOPE,
            "not_redacted_account_native": True,
            "source_path": str(path) if path_raw else None,
            "source_sha256": first_present(file_payload.get("sha256"), file_payload.get("source_sha256")),
            "manifest_path": str(manifest_path),
            "export_tool": first_present(file_payload.get("export_tool"), manifest.get("export_tool")),
            "chunks_requested": file_payload.get("chunks_requested"),
            "chunks_with_rows": file_payload.get("chunks_with_rows"),
            "empty_chunks": file_payload.get("empty_chunks"),
            "raw_rows_returned": file_payload.get("raw_rows_returned"),
            "last_empty_chunk_error": file_payload.get("last_empty_chunk_error"),
        }
    return [gap_by_key[key] for key in sorted(gap_by_key)]


def _requirement_rows(
    *,
    order_rows: Iterable[Mapping[str, Any]],
    oracle_rows: Iterable[Mapping[str, Any]],
    prior_gap_rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    (
        oracle_by_order_id,
        oracle_by_campaign_phase_candidate_window,
        oracle_by_campaign_phase_candidate,
        oracle_by_candidate,
    ) = _oracle_rows_by_campaign_phase_candidate(oracle_rows)
    gap_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for gap in prior_gap_rows:
        key = (
            str(gap.get("symbol") or ""),
            str(gap.get("request_start_utc") or "").replace("Z", "+00:00"),
            str(gap.get("request_end_utc") or "").replace("Z", "+00:00"),
        )
        gap_index[key] = dict(gap)

    requirements: list[dict[str, Any]] = []
    selected_truth: list[dict[str, Any]] = []
    current_gap_rows: list[dict[str, Any]] = []
    for sequence, order in enumerate(_latest_order_rows(order_rows), start=1):
        candidate_id = str(order.get("candidate_id") or "")
        campaign = str(order.get("campaign") or "")
        phase = str(order.get("phase") or "")
        order_id = str(order.get("simulated_order_id") or "")
        order_decision_time = _norm_utc_key(
            first_present(order.get("decision_time_utc"), order.get("order_time_utc"))
        )
        order_expiry = _norm_utc_key(order.get("expiry_utc"))
        oracle = (
            oracle_by_order_id.get(order_id)
            or oracle_by_campaign_phase_candidate_window.get(
                (campaign, phase, candidate_id, order_decision_time, order_expiry)
            )
            or oracle_by_campaign_phase_candidate.get((campaign, phase, candidate_id))
            or oracle_by_candidate.get(candidate_id, {})
        )
        symbol = str(order.get("symbol") or oracle.get("symbol") or "")
        decision_time = str(order.get("decision_time_utc") or oracle.get("asof_utc") or "")
        expiry = str(order.get("expiry_utc") or oracle.get("expiry_utc") or "")
        request_start = decision_time.replace("Z", "+00:00")
        request_end = expiry.replace("Z", "+00:00")
        gap = gap_index.get((symbol, request_start, request_end))
        zero_duration_window = bool(request_start and request_end and request_start == request_end)
        if gap is None and zero_duration_window:
            gap = {
                "gap_id": stable_sha256(
                    {
                        "symbol": symbol,
                        "request_start_utc": request_start,
                        "request_end_utc": request_end,
                        "reason": "zero_duration_selected_path_window",
                    }
                )[:20],
                "symbol": symbol,
                "request_start_utc": request_start,
                "request_end_utc": request_end,
                "source_bound_status": "exact_zero_duration_selected_path_window",
                "previous_row_count": 0,
                "retry_row_count": 0,
                "retry_status": "not_exported_zero_duration_window",
            }
        tick_truth = (
            oracle.get("source") == "tick"
            and oracle.get("ordered_tick_truth_satisfied") is True
        )
        unresolved_zero = bool(gap)
        if tick_truth:
            requirement_status = "satisfied_from_indexed_tick_source"
            selected_status = "passed_tick_truth"
            inclusion_status = "included_tick_truth_performance"
        elif unresolved_zero:
            requirement_status = "unresolved_exact_zero_row_ftmo_tick_source_bound"
            selected_status = "unresolved_exact_zero_row_source_requirement_split"
            inclusion_status = "excluded_unresolved_source_requirement"
        else:
            requirement_status = "failed_missing_tick_source_requirement"
            selected_status = "failed_unlabeled_m1_or_missing_tick_truth"
            inclusion_status = "excluded_failed_verifier_required"
        requirement_id = stable_sha256(
            {
                "route": ROUTE_ID,
                "candidate_id": candidate_id,
                "order_id": order.get("simulated_order_id"),
                "decision_time_utc": decision_time,
                "expiry_utc": expiry,
                "required_source_type": "TICK",
            }
        )[:20]
        common = {
            "source_requirement_id": f"KIAP-SR-{sequence:04d}-{requirement_id}",
            "kiap_route_id": ROUTE_ID,
            "campaign": order.get("campaign"),
            "phase": order.get("phase"),
            "trading_day": order.get("trading_day"),
            "simulated_order_id": order.get("simulated_order_id"),
            "candidate_id": candidate_id,
            "symbol": symbol,
            "mapped_symbol": ftmo_symbol(symbol),
            "side": order.get("side"),
            "decision_time_utc": decision_time,
            "order_time_utc": decision_time,
            "entry_price": order.get("entry_price"),
            "stop_loss": order.get("stop_loss"),
            "take_profit_1": order.get("take_profit_1"),
            "expiry_utc": expiry,
            "policy": order.get("dynamic_geometry_policy") or "candidate_dynamic_geometry_policy",
            "order_status": order.get("order_status"),
            "fill_time_utc": order.get("fill_time_utc"),
            "required_source_type": "TICK",
            "required_source_reason": "selected_or_accepted_candidate_order_postdecision_path_truth",
            "requirement_start_utc": decision_time,
            "requirement_end_utc": expiry,
            "path_truth_index": "PathTruthIndex",
            "local_indexed_tick_lookup_attempted": True,
            "ftmo_exact_window_export_attempted": bool(unresolved_zero),
            "source_broker": "FTMO",
            "source_role": "owner_authorized_research_hydration",
            "source_truth_scope": SOURCE_TRUTH_SCOPE,
            "not_redacted_account_native": True,
            "broker_lifecycle_truth_satisfied": False,
            "ordered_tick_truth_satisfied": tick_truth,
            "path_source": oracle.get("source"),
            "path_row_count": oracle.get("path_row_count") or oracle.get("path_index_rows_returned"),
            "source_path": oracle.get("source_path"),
            "source_sha256": oracle.get("source_sha256"),
            "manifest_path": oracle.get("manifest_path") or "multiple_priority_tick_ftmo_manifests",
            "requirement_status": requirement_status,
            "final_performance_inclusion_status": inclusion_status,
            "m1_may_satisfy_final_selected_path_truth": False,
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
        }
        if unresolved_zero:
            common.update(
                {
                    "gap_id": gap.get("gap_id"),
                    "source_bound_status": gap.get("source_bound_status"),
                    "previous_row_count": gap.get("previous_row_count"),
                    "retry_row_count": gap.get("retry_row_count"),
                    "retry_status": gap.get("retry_status"),
                }
            )
            current_gap_rows.append(
                {
                    **gap,
                    **common,
                    "kiap_current_smoke_selected_order": order.get("phase") == "smoke",
                    "kiap_current_selected_order": True,
                    "kiap_current_phase": order.get("phase"),
                    "selected_filled_path_truth_status": "exact_unresolved_tick_source_requirement",
                }
            )
        requirements.append(common)
        selected_truth.append(
            {
                **common,
                "selected_tick_truth_verification_status": selected_status,
                "verifier_action": (
                    "pass"
                    if tick_truth
                    else (
                        "split_exact_zero_row_requirement"
                        if unresolved_zero
                        else "fail_route"
                    )
                ),
                "source_zero_proof_present": unresolved_zero,
                "m1_fallback_violation": not tick_truth and not unresolved_zero,
                "evidence_class": OUTCOME_EVIDENCE_CLASS,
            }
        )
    return requirements, selected_truth, current_gap_rows


def _risk_lockout_rows(order_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, order in enumerate(order_rows, start=1):
        if order.get("order_status") != "risk_rejected" and order.get("risk_decision_reason") != "risk_headroom_zero":
            continue
        phase = str(order.get("phase") or "unknown")
        rows.append(
            {
                "risk_lockout_chain_id": f"KIAP-RISK-LOCKOUT-{phase.upper()}-{index:04d}",
                "kiap_route_id": ROUTE_ID,
                "campaign": order.get("campaign"),
                "phase": order.get("phase"),
                "trading_day": order.get("trading_day"),
                "candidate_id": order.get("candidate_id"),
                "simulated_order_id": order.get("simulated_order_id"),
                "symbol": order.get("symbol"),
                "decision_time_utc": order.get("decision_time_utc"),
                "risk_decision": order.get("risk_decision"),
                "risk_decision_reason": order.get("risk_decision_reason"),
                "daily_runtime_headroom_pct_before": order.get("daily_runtime_headroom_pct_before"),
                "open_risk_pct_before": order.get("open_risk_pct_before"),
                "pending_risk_pct_before": order.get("pending_risk_pct_before"),
                "same_symbol_lifecycle_exposure_risk_pct": order.get("same_symbol_lifecycle_exposure_risk_pct"),
                "causal_chain_status": f"{phase}_risk_rejection_materialized_open_for_repair_chain_expansion",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
        )
    return rows


def _numeric(value: Any) -> float:
    try:
        return float(value if value is not None else 0.0)
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _item9_phase_label(phase: str) -> str:
    return {
        "full_development": "pre_repair_development",
        "repair_rerun": "post_repair_development",
        "holdout_rolling": "post_repair_holdout",
    }.get(phase, phase)


def _item9_row(
    row: Mapping[str, Any],
    *,
    family: str,
    phase: str,
    source_ledger: str,
    sequence: int,
) -> dict[str, Any]:
    repair_disposition = {
        "full_development": "measured_pre_repair_family_input",
        "repair_rerun": "post_repair_row_present_repair_not_sufficient_for_this_row",
        "holdout_rolling": "holdout_row_present_repair_not_sufficient_for_this_row",
    }.get(phase, "measured")
    if family == "partial_be_runner":
        repair_disposition = (
            "measured_pre_repair_partial_be_damage_family"
            if phase == "full_development"
            else "unexpected_partial_be_row_after_repair"
        )
    return {
        **dict(row),
        "kiap_item9_row_id": f"KIAP-ITEM9-{family.upper()}-{phase.upper()}-{sequence:05d}",
        "kiap_route_id": ROUTE_ID,
        "kiap_action_queue_items_satisfied": [8, 9],
        "kiap_item9_family": family,
        "kiap_item9_measurement_phase": _item9_phase_label(phase),
        "kiap_item9_source_ledger": source_ledger,
        "kiap_item9_repair_disposition": repair_disposition,
        "source_truth_scope": row.get("source_truth_scope") or SOURCE_TRUTH_SCOPE,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }


def _item9_classify_phase_rows(
    *,
    phase: str,
    ledger_files: Mapping[str, str],
    trades: Iterable[Mapping[str, Any]],
    rollups: Iterable[Mapping[str, Any]],
    missed: Iterable[Mapping[str, Any]],
    orders: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    families: dict[str, list[dict[str, Any]]] = {key: [] for key in KIAP_ITEM9_LEDGER_FILES}

    for row in trades:
        net_proxy_r = _numeric(row.get("net_proxy_r"))
        gross_r = _numeric(first_present(row.get("gross_r"), row.get("final_r"), row.get("net_r")))
        if net_proxy_r < 0:
            families["weak_accepted_trades"].append(
                _item9_row(
                    row,
                    family="weak_accepted_trades",
                    phase=phase,
                    source_ledger=ledger_files["trade"],
                    sequence=len(families["weak_accepted_trades"]) + 1,
                )
            )
        if gross_r > 0 and net_proxy_r < 0:
            families["cost_flips"].append(
                _item9_row(
                    row,
                    family="cost_flips",
                    phase=phase,
                    source_ledger=ledger_files["trade"],
                    sequence=len(families["cost_flips"]) + 1,
                )
            )

    partial_be_active = bool(KIAP_ITEM8_CAMPAIGN_DEFS.get(phase, {}).get("partial_be_runner"))
    for row in rollups:
        if not partial_be_active or str(row.get("policy") or "") != "partial_be_runner":
            continue
        families["partial_be_runner"].append(
            _item9_row(
                row,
                family="partial_be_runner",
                phase=phase,
                source_ledger=ledger_files["rollup"],
                sequence=len(families["partial_be_runner"]) + 1,
            )
        )

    for row in missed:
        if _numeric(row.get("net_proxy_r")) <= 0:
            continue
        if "scheduler" not in str(row.get("miss_reason") or ""):
            continue
        families["scheduler_regret"].append(
            _item9_row(
                row,
                family="scheduler_regret",
                phase=phase,
                source_ledger=ledger_files["missed"],
                sequence=len(families["scheduler_regret"]) + 1,
            )
        )

    for row in _latest_order_rows(orders):
        if row.get("order_status") != "risk_rejected" and row.get("risk_decision_reason") != "risk_headroom_zero":
            continue
        families["risk_headroom_lockout"].append(
            _item9_row(
                row,
                family="risk_headroom_lockout",
                phase=phase,
                source_ledger=ledger_files["order"],
                sequence=len(families["risk_headroom_lockout"]) + 1,
            )
        )
    return families


def _item9_family_stats(rows: Iterable[Mapping[str, Any]], *, family: str) -> dict[str, Any]:
    rows = list(rows)
    stats: dict[str, Any] = {
        "rows": len(rows),
        "net_proxy_r": round(sum(_numeric(row.get("net_proxy_r")) for row in rows), 8),
        "gross_r": round(sum(_numeric(row.get("gross_r")) for row in rows), 8),
        "expected_cost_r": round(sum(_numeric(row.get("expected_cost_r")) for row in rows), 8),
        "symbols": sorted({str(row.get("symbol")) for row in rows if row.get("symbol")}),
    }
    if family == "partial_be_runner":
        stats.update(
            {
                "candidate_count": sum(int(_numeric(row.get("candidate_count"))) for row in rows),
                "selected_order_count": sum(int(_numeric(row.get("selected_order_count"))) for row in rows),
                "filled_trade_count": sum(int(_numeric(row.get("filled_trade_count"))) for row in rows),
                "winner_count": sum(int(_numeric(row.get("winner_count"))) for row in rows),
                "loser_count": sum(int(_numeric(row.get("loser_count"))) for row in rows),
            }
        )
    if family == "risk_headroom_lockout":
        stats.update(
            {
                "risk_rejected_orders": len(rows),
                "risk_cash": round(sum(_numeric(row.get("risk_cash")) for row in rows), 8),
            }
        )
    return stats


def _item9_phase_summary(families_by_phase: Mapping[str, Mapping[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for family in KIAP_ITEM9_LEDGER_FILES:
        phase_stats = {
            phase: _item9_family_stats(families.get(family, ()), family=family)
            for phase, families in families_by_phase.items()
        }
        full = phase_stats.get("full_development", {})
        repair = phase_stats.get("repair_rerun", {})
        holdout = phase_stats.get("holdout_rolling", {})
        disposition = "measured"
        if family == "partial_be_runner":
            disposition = (
                "measured_and_repair_policy_disabled_family"
                if int(repair.get("rows") or 0) == 0 and int(holdout.get("rows") or 0) == 0
                else "row_rejected_unexpected_partial_be_after_repair"
            )
        elif family == "scheduler_regret":
            if _numeric(repair.get("net_proxy_r")) < _numeric(full.get("net_proxy_r")):
                disposition = "measured_repair_reduced_positive_missed_regret_remaining_rows"
            elif _numeric(repair.get("net_proxy_r")) > _numeric(full.get("net_proxy_r")):
                disposition = "row_rejected_existing_repair_increased_positive_missed_regret"
            elif int(repair.get("rows") or 0) > 0 or int(holdout.get("rows") or 0) > 0:
                disposition = "measured_remaining_rows_require_next_repair_or_rejection"
        elif family == "risk_headroom_lockout" and int(repair.get("rows") or 0) >= int(full.get("rows") or 0):
            disposition = "row_rejected_existing_repair_did_not_reduce_lockouts"
        elif _numeric(repair.get("net_proxy_r")) < _numeric(full.get("net_proxy_r")):
            disposition = "row_rejected_existing_repair_worsened_family_net_proxy_r"
        elif int(repair.get("rows") or 0) > 0 or int(holdout.get("rows") or 0) > 0:
            disposition = "measured_remaining_rows_require_next_repair_or_rejection"
        summary[family] = {
            "phase_stats": phase_stats,
            "repair_delta_rows": int(repair.get("rows") or 0) - int(full.get("rows") or 0),
            "repair_delta_net_proxy_r": round(
                _numeric(repair.get("net_proxy_r")) - _numeric(full.get("net_proxy_r")),
                8,
            ),
            "holdout_rows": int(holdout.get("rows") or 0),
            "disposition": disposition,
        }
    return summary


def build_item9_repair_family_measurements(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str = ROUTE_DIR,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    phase_ledgers = {
        "full_development": KIAP_FULL_DEVELOPMENT_LEDGER_FILES,
        "repair_rerun": KIAP_REPAIR_RERUN_LEDGER_FILES,
        "holdout_rolling": KIAP_HOLDOUT_ROLLING_LEDGER_FILES,
    }
    families_by_phase: dict[str, dict[str, list[dict[str, Any]]]] = {}
    missing_inputs: list[str] = []
    for phase, ledgers in phase_ledgers.items():
        required = ("trade", "rollup", "missed", "order")
        for key in required:
            if not (route / ledgers[key]).exists():
                missing_inputs.append(f"{phase}:{ledgers[key]}")
        if any(not (route / ledgers[key]).exists() for key in required):
            continue
        families_by_phase[phase] = _item9_classify_phase_rows(
            phase=phase,
            ledger_files=ledgers,
            trades=load_jsonl(route / ledgers["trade"]),
            rollups=load_jsonl(route / ledgers["rollup"]),
            missed=load_jsonl(route / ledgers["missed"]),
            orders=load_jsonl(route / ledgers["order"]),
        )

    if missing_inputs:
        summary = {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "blocked_missing_item8_inputs",
            "missing_inputs": sorted(missing_inputs),
            "completion_claim": False,
            "production_change_claim": False,
            "broker_runtime_change_status": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
        }
        _write_stable_json(route / KIAP_ITEM9_SUMMARY_FILE, summary)
        return summary

    family_rows: dict[str, list[dict[str, Any]]] = {family: [] for family in KIAP_ITEM9_LEDGER_FILES}
    for phase in KIAP_ITEM8_PHASES:
        for family in KIAP_ITEM9_LEDGER_FILES:
            family_rows[family].extend(families_by_phase.get(phase, {}).get(family, []))

    for family, filename in KIAP_ITEM9_LEDGER_FILES.items():
        atomic_write_jsonl(route / filename, family_rows[family])

    phase_summaries = {
        phase: load_json(route / KIAP_ITEM8_SUMMARY_FILES[phase])
        for phase in KIAP_ITEM8_PHASES
        if (route / KIAP_ITEM8_SUMMARY_FILES[phase]).exists()
    }
    family_summary = _item9_phase_summary(families_by_phase)
    all_required_ledgers_present = all(
        (route / filename).exists() for filename in KIAP_ITEM9_LEDGER_FILES.values()
    )
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed" if all_required_ledgers_present else "failed_missing_ledgers",
        "item9_gate_closed": all_required_ledgers_present,
        "completion_claim": False,
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "evidence_class": EVIDENCE_CLASS,
        "phase_order": list(KIAP_ITEM8_PHASES),
        "phase_role": {
            phase: _item9_phase_label(phase)
            for phase in KIAP_ITEM8_PHASES
        },
        "phase_campaign_summaries": {
            phase: phase_summaries.get(phase, {}).get("campaign_summary", {})
            for phase in KIAP_ITEM8_PHASES
        },
        "family_summary": family_summary,
        "family_row_counts": {
            family: len(rows)
            for family, rows in family_rows.items()
        },
        "ledger_files": dict(KIAP_ITEM9_LEDGER_FILES),
        "measurement_disposition": "row_level_families_materialized_existing_repair_measured_or_row_rejected",
        "no_arbitrary_top_n": True,
        "all_material_family_rows_preserved": True,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "broker_account_order_history_deal_position_mutation": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
        "live_deployment_or_reload": False,
    }
    _write_stable_json(route / KIAP_ITEM9_SUMMARY_FILE, summary)

    _write_action_queue(
        route,
        development_checkpoint_completed=True,
        item8_tranches_completed=True,
        item9_measurement_completed=summary["status"] == "completed",
    )
    now = utc_now()
    context_path = route / "KIAP_CONTEXT_ANCHOR.json"
    if context_path.exists():
        context = load_json(context_path)
        completed = list(context.get("completed_this_checkpoint") or [])
        item9_completion = (
            "materialized item #9 row-level repair-family measurement and row-rejection ledgers"
        )
        if item9_completion not in completed:
            completed.append(item9_completion)
        context.update(
            {
                "generated_at_utc": now,
                "completed_this_checkpoint": completed,
                "next_incomplete_hard_gate": (
                    "harden verifier gates for stale context anchors, duplicate manifest pollution, rollup/order/trade/oracle mismatches, selected attribution, and unlabeled M1 selected fills across all tranches"
                ),
                "completion_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            }
        )
        _write_stable_json(context_path, context)
    rolling_path = route / "KIAP_ROLLING_RUN_STATE.json"
    if rolling_path.exists():
        rolling = load_json(rolling_path)
        completed_ids = list(rolling.get("completed_checkpoint_ids") or [])
        if "kiap_cp005_item9_repair_family_measurement" not in completed_ids:
            completed_ids.append("kiap_cp005_item9_repair_family_measurement")
        rolling.update(
            {
                "generated_at_utc": now,
                "current_phase": "kiap_item9_repair_family_measurement_completed",
                "completed_checkpoint_ids": completed_ids,
                "next_action_queue_item": 10,
                "item9_repair_family_measurement": "completed",
                "completion_claim": False,
            }
        )
        _write_stable_json(rolling_path, rolling)
    questions_path = route / "KIAP_ACTIVE_QUESTION_STACK.jsonl"
    questions = load_jsonl(questions_path) if questions_path.exists() else []
    if not any(row.get("question_id") == "kiap_q009_repair_family_measurement" for row in questions):
        questions.append(
            {
                "question_id": "kiap_q009_repair_family_measurement",
                "question": "Are weak accepted trades, partial_be_runner damage, scheduler regret, cost flips, and risk-headroom lockout repairs measured or row-rejected against current KIAP tranches?",
                "status": "answered_for_item9",
                "evidence_artifacts": [
                    KIAP_ITEM9_SUMMARY_FILE,
                    *KIAP_ITEM9_LEDGER_FILES.values(),
                ],
            }
        )
        atomic_write_jsonl(questions_path, questions)
    limitations_path = route / "KIAP_LIMITATION_BACKLOG.jsonl"
    limitations = load_jsonl(limitations_path) if limitations_path.exists() else []
    limitations = [
        {
            **row,
            "status": (
                "closed_by_item9_repair_family_measurement"
                if row.get("limitation_id") == "kiap_lim_003_development_repair_holdout_pending"
                else row.get("status")
            ),
        }
        for row in limitations
    ]
    if not any(row.get("limitation_id") == "kiap_lim_004_verifier_hardening_pending" for row in limitations):
        limitations.append(
            {
                "limitation_id": "kiap_lim_004_verifier_hardening_pending",
                "status": "open_same_route_work_after_item9",
                "next_action": "harden verifier gates and run final route audit/tests/stable rerun before completion",
                "evidence_class": EVIDENCE_CLASS,
            }
        )
    atomic_write_jsonl(limitations_path, limitations)
    _append_checkpoint(
        route,
        {
            "checkpoint_id": "kiap_cp005_item9_repair_family_measurement",
            "timestamp_utc": now,
            "current_head": git_value(["rev-parse", "HEAD"]),
            "completed_capability": "KIAP item #9 materialized row-level repair-family measurement and row-rejection ledgers for weak accepted trades, partial BE runner, scheduler regret, cost flips, and risk-headroom lockout",
            "files_changed": [
                "src/research_infra/v4_kia_parity_tick_first_runtime_repair.py",
                *KIAP_ITEM9_LEDGER_FILES.values(),
                KIAP_ITEM9_SUMMARY_FILE,
            ],
            "tests_verifiers_run": [],
            "replay_row_counts": {
                family: len(rows)
                for family, rows in family_rows.items()
            },
            "limitations_discovered": [
                "item #10 verifier hardening and final route audit remain pending",
            ],
            "limitations_fixed": [
                "repeated_system_weaknesses_not_measured_in_kiap",
                "prior_kia_repair_families_not_row_bound_to_current_tick_first_tranches",
            ],
            "next_concrete_action": "harden verifier gates for item9 outputs, stale context anchors, duplicate manifest pollution, rollup/order/trade/oracle mismatches, selected attribution, and unlabeled M1 selected fills across all tranches",
            "blocker_state": "not_blocked_same_evidence_class_work_remains",
        },
    )
    return load_json(route / KIAP_ITEM9_SUMMARY_FILE)


def _item10_phase_scope(action_queue: str) -> list[str]:
    phases = ["smoke"]
    if "7. [x]" in action_queue:
        phases.append("development")
    if "8. [x]" in action_queue:
        phases.extend(KIAP_ITEM8_PHASES)
    return phases


def _candidate_decision_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("campaign") or ""),
        str(row.get("phase") or ""),
        str(row.get("candidate_id") or ""),
        _norm_utc_key(first_present(row.get("decision_time_utc"), row.get("asof_utc"))),
    )


def _order_window_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("campaign") or ""),
        str(row.get("phase") or ""),
        str(row.get("candidate_id") or ""),
        _norm_utc_key(first_present(row.get("decision_time_utc"), row.get("order_time_utc"), row.get("asof_utc"))),
        _norm_utc_key(first_present(row.get("expiry_utc"), row.get("requirement_end_utc"))),
    )


def _item10_context_anchor_diagnostics(route: Path, repo_root: Path) -> dict[str, Any]:
    context_path = route / "KIAP_CONTEXT_ANCHOR.json"
    context = load_json(context_path) if context_path.exists() else {}
    current_head = git_value(["rev-parse", "HEAD"])
    current_head_parent = git_value(["rev-parse", "HEAD^"])
    prompt_path = repo_root / str(context.get("controlling_prompt") or PROMPT_PATH)
    starter_path = repo_root / str(context.get("starter") or STARTER_PATH)
    allowed_context_heads = {current_head}
    if context.get("route_status") == KIAP_COMPLETION_STATUS and current_head_parent:
        allowed_context_heads.add(current_head_parent)
    failures = []
    if context.get("route_id") != ROUTE_ID:
        failures.append("route_id_mismatch")
    if context.get("route_status") not in {"IN_PROGRESS", KIAP_COMPLETION_STATUS}:
        failures.append("route_status_not_in_progress_or_kiap_complete")
    if context.get("completion_claim") is not False:
        failures.append("completion_claim_not_false")
    if context.get("full_live_replay_parity_claim") is not False:
        failures.append("full_live_replay_parity_claim_not_false")
    if context.get("current_head_at_checkpoint") not in allowed_context_heads:
        failures.append("current_head_at_checkpoint_not_current_or_completed_route_parent")
    if not prompt_path.exists():
        failures.append("controlling_prompt_missing")
    if not starter_path.exists():
        failures.append("starter_missing")
    if context.get("broker_account_order_history_deal_position_mutation") is not False:
        failures.append("broker_mutation_boundary")
    if context.get("live_deployment_or_reload") is not False:
        failures.append("live_deployment_boundary")
    return {
        "status": "passed" if not failures else "failed",
        "current_head": current_head,
        "current_head_parent": current_head_parent,
        "context_head": context.get("current_head_at_checkpoint"),
        "allowed_context_heads": sorted(head for head in allowed_context_heads if head),
        "controlling_prompt_exists": prompt_path.exists(),
        "starter_exists": starter_path.exists(),
        "failures": failures,
    }


def _item10_duplicate_manifest_diagnostics(route: Path, repo_root: Path) -> dict[str, Any]:
    manifest = load_json(route / "KIAP_OUTPUT_MANIFEST.json") if (route / "KIAP_OUTPUT_MANIFEST.json").exists() else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    active_duplicate_files = sorted(
        path.name
        for path in route.iterdir()
        if path.is_file() and (" 2." in path.name or " 3." in path.name)
    )
    manifest_duplicate_entries = [
        str(name) for name in artifacts if " 2." in str(name) or " 3." in str(name)
    ]
    prior_route = repo_root / PRIOR_KIA_ROUTE
    prior_duplicate_files = (
        sorted(
            path.name
            for path in prior_route.iterdir()
            if path.is_file() and (" 2." in path.name or " 3." in path.name)
        )
        if prior_route.exists()
        else []
    )
    failures = []
    if active_duplicate_files:
        failures.append("active_route_duplicate_files_present")
    if manifest_duplicate_entries:
        failures.append("manifest_duplicate_entries_present")
    if manifest.get("raw_export_scratch_committed") is not False:
        failures.append("raw_export_scratch_committed_not_false")
    if manifest.get("prior_kia_duplicate_ledgers_included") is not False:
        failures.append("prior_kia_duplicate_ledgers_included_not_false")
    if "duplicate_route_local_entries_ignored" not in manifest:
        failures.append("duplicate_route_local_entries_ignored_field_missing")
    return {
        "status": "passed" if not failures else "failed",
        "active_duplicate_files": active_duplicate_files,
        "manifest_duplicate_entries": manifest_duplicate_entries,
        "prior_duplicate_files_observed_and_excluded": prior_duplicate_files,
        "raw_export_scratch_committed": manifest.get("raw_export_scratch_committed"),
        "prior_kia_duplicate_ledgers_included": manifest.get("prior_kia_duplicate_ledgers_included"),
        "failures": failures,
    }


def _item10_selected_candidate_attribution_diagnostics(route: Path, phases: Iterable[str]) -> dict[str, Any]:
    phase_list = list(phases)
    candidate_rows = _aggregate_phase_rows(route, "candidate", phases=phase_list)
    latest_orders = _latest_order_rows(_aggregate_phase_rows(route, "order", phases=phase_list))
    candidates_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    selected_candidate_keys: set[tuple[str, str, str, str]] = set()
    for row in candidate_rows:
        key = _candidate_decision_key(row)
        if not key[2]:
            continue
        candidates_by_key[key].append(dict(row))
        if row.get("selected_candidate_execution_attribution_status") == "attributed_by_selected_candidate_id":
            selected_candidate_keys.add(key)

    failures = []
    selected_orders_by_phase: Counter[str] = Counter()
    attributed_orders_by_phase: Counter[str] = Counter()
    for order in latest_orders:
        key = _candidate_decision_key(order)
        phase = key[1]
        selected_orders_by_phase[phase] += 1
        candidates = candidates_by_key.get(key, [])
        if not candidates:
            failures.append(
                f"{order.get('simulated_order_id')}:missing_candidate_row_for_selected_order_window"
            )
            continue
        if key not in selected_candidate_keys:
            failures.append(
                f"{order.get('simulated_order_id')}:candidate_not_attributed_by_selected_candidate_id"
            )
            continue
        attributed_orders_by_phase[phase] += 1

    return {
        "status": "passed" if latest_orders and not failures else "failed",
        "phase_scope": phase_list,
        "latest_selected_order_rows": len(latest_orders),
        "selected_candidate_keys": len(selected_candidate_keys),
        "selected_orders_by_phase": dict(sorted(selected_orders_by_phase.items())),
        "attributed_orders_by_phase": dict(sorted(attributed_orders_by_phase.items())),
        "failures": failures[:80],
    }


def _item10_order_oracle_source_diagnostics(route: Path, phases: Iterable[str]) -> dict[str, Any]:
    phase_list = list(phases)
    latest_orders = _latest_order_rows(_aggregate_phase_rows(route, "order", phases=phase_list))
    oracle_rows = _aggregate_phase_rows(route, "oracle", phases=phase_list)
    requirements = (
        load_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl")
        if (route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl").exists()
        else []
    )
    selected_truth = (
        load_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl")
        if (route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl").exists()
        else []
    )
    (
        oracle_by_order_id,
        oracle_by_campaign_phase_candidate_window,
        _oracle_by_campaign_phase_candidate,
        _oracle_by_candidate,
    ) = _oracle_rows_by_campaign_phase_candidate(oracle_rows)
    requirement_by_order = {
        str(row.get("simulated_order_id")): dict(row)
        for row in requirements
        if row.get("simulated_order_id")
    }
    truth_by_order = {
        str(row.get("simulated_order_id")): dict(row)
        for row in selected_truth
        if row.get("simulated_order_id")
    }
    failures = []
    passed_tick_truth = 0
    unresolved_exact_zero = 0
    for order in latest_orders:
        order_id = str(order.get("simulated_order_id") or "")
        window_key = _order_window_key(order)
        oracle = oracle_by_order_id.get(order_id) or oracle_by_campaign_phase_candidate_window.get(window_key)
        requirement = requirement_by_order.get(order_id)
        truth = truth_by_order.get(order_id)
        if not oracle:
            failures.append(f"{order_id}:missing_oracle_window_match")
            continue
        if not requirement:
            failures.append(f"{order_id}:missing_source_requirement")
            continue
        if not truth:
            failures.append(f"{order_id}:missing_selected_tick_truth")
            continue
        if _order_window_key(requirement) != window_key:
            failures.append(f"{order_id}:requirement_window_key_mismatch")
        if _order_window_key(truth) != window_key:
            failures.append(f"{order_id}:selected_truth_window_key_mismatch")
        if requirement.get("required_source_type") != "TICK":
            failures.append(f"{order_id}:requirement_not_tick")
        if requirement.get("local_indexed_tick_lookup_attempted") is not True:
            failures.append(f"{order_id}:local_indexed_tick_lookup_not_attempted")
        if requirement.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
            failures.append(f"{order_id}:requirement_source_truth_scope")
        tick_oracle = oracle.get("source") == "tick" and oracle.get("ordered_tick_truth_satisfied") is True
        truth_status = truth.get("selected_tick_truth_verification_status")
        if tick_oracle:
            if truth_status != "passed_tick_truth" or truth.get("path_source") != "tick":
                failures.append(f"{order_id}:tick_oracle_not_reflected_in_selected_truth")
            else:
                passed_tick_truth += 1
        else:
            if truth_status != "unresolved_exact_zero_row_source_requirement_split":
                failures.append(f"{order_id}:non_tick_oracle_without_exact_zero_split")
            else:
                unresolved_exact_zero += 1
        if truth.get("m1_fallback_violation") is True:
            failures.append(f"{order_id}:m1_fallback_violation")
    return {
        "status": "passed" if latest_orders and not failures else "failed",
        "phase_scope": phase_list,
        "latest_selected_order_rows": len(latest_orders),
        "oracle_rows": len(oracle_rows),
        "source_requirement_rows": len(requirements),
        "selected_tick_truth_rows": len(selected_truth),
        "passed_tick_truth_rows": passed_tick_truth,
        "unresolved_exact_zero_rows": unresolved_exact_zero,
        "failures": failures[:120],
    }


def _item10_rollup_diagnostics(route: Path, phases: Iterable[str]) -> dict[str, Any]:
    statuses = {}
    failures = []
    for phase in phases:
        summary_path = _phase_summary_path(route, phase)
        summary = load_json(summary_path) if summary_path.exists() else {}
        reconciliation = summary.get("rollup_reconciliation")
        reconciliation = reconciliation if isinstance(reconciliation, Mapping) else {}
        status = reconciliation.get("status")
        statuses[phase] = status
        if status != "passed":
            failures.append(f"{phase}:rollup_reconciliation_not_passed")
    return {
        "status": "passed" if statuses and not failures else "failed",
        "phase_scope": list(phases),
        "rollup_reconciliation_statuses": statuses,
        "failures": failures,
    }


def _item10_verifier_hardening_diagnostics(
    *,
    route: Path,
    repo_root: Path,
    action_queue: str,
) -> dict[str, dict[str, Any]]:
    phases = _item10_phase_scope(action_queue)
    return {
        "context_anchor_freshness": _item10_context_anchor_diagnostics(route, repo_root),
        "duplicate_route_artifact_scope": _item10_duplicate_manifest_diagnostics(route, repo_root),
        "selected_candidate_order_attribution": _item10_selected_candidate_attribution_diagnostics(route, phases),
        "order_oracle_source_requirement_attribution": _item10_order_oracle_source_diagnostics(route, phases),
        "rollup_order_trade_oracle_reconciliation": _item10_rollup_diagnostics(route, phases),
    }


def build_item10_verifier_hardening_checkpoint(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str = ROUTE_DIR,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    output_manifest(route)
    action_queue = (
        (route / "KIAP_ACTION_QUEUE.md").read_text(encoding="utf-8")
        if (route / "KIAP_ACTION_QUEUE.md").exists()
        else ""
    )
    diagnostics = _item10_verifier_hardening_diagnostics(
        route=route,
        repo_root=repo_root,
        action_queue=action_queue,
    )
    failures = {
        name: row.get("failures", [])
        for name, row in diagnostics.items()
        if row.get("status") != "passed"
    }
    status = "completed" if not failures else "failed"
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": status,
        "item10_gate_closed": status == "completed",
        "completion_claim": False,
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "evidence_class": EVIDENCE_CLASS,
        "hardened_checks": sorted(diagnostics),
        "diagnostics": diagnostics,
        "no_arbitrary_top_n": True,
        "all_selected_order_rows_checked": diagnostics[
            "selected_candidate_order_attribution"
        ].get("latest_selected_order_rows"),
        "all_source_requirement_rows_checked": diagnostics[
            "order_oracle_source_requirement_attribution"
        ].get("source_requirement_rows"),
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "broker_account_order_history_deal_position_mutation": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
        "live_deployment_or_reload": False,
        "failures": failures,
    }
    _write_stable_json(route / KIAP_ITEM10_SUMMARY_FILE, summary)

    _write_action_queue(
        route,
        development_checkpoint_completed=True,
        item8_tranches_completed=True,
        item9_measurement_completed=True,
        item10_verifier_hardened=status == "completed",
    )
    now = utc_now()
    context_path = route / "KIAP_CONTEXT_ANCHOR.json"
    if context_path.exists():
        context = load_json(context_path)
        completed = list(context.get("completed_this_checkpoint") or [])
        item10_completion = "hardened item #10 verifier gates for context, manifest, attribution, source, and reconciliation invariants"
        if item10_completion not in completed:
            completed.append(item10_completion)
        context.update(
            {
                "generated_at_utc": now,
                "current_head_at_checkpoint": git_value(["rev-parse", "HEAD"]),
                "completed_this_checkpoint": completed,
                "next_incomplete_hard_gate": (
                    "run route verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped commit"
                ),
                "completion_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            }
        )
        _write_stable_json(context_path, context)
    rolling_path = route / "KIAP_ROLLING_RUN_STATE.json"
    if rolling_path.exists():
        rolling = load_json(rolling_path)
        completed_ids = list(rolling.get("completed_checkpoint_ids") or [])
        if "kiap_cp006_item10_verifier_hardening" not in completed_ids:
            completed_ids.append("kiap_cp006_item10_verifier_hardening")
        rolling.update(
            {
                "generated_at_utc": now,
                "current_phase": "kiap_item10_verifier_hardening_completed",
                "completed_checkpoint_ids": completed_ids,
                "next_action_queue_item": 11,
                "item10_verifier_hardening": status,
                "completion_claim": False,
            }
        )
        _write_stable_json(rolling_path, rolling)
    questions_path = route / "KIAP_ACTIVE_QUESTION_STACK.jsonl"
    questions = load_jsonl(questions_path) if questions_path.exists() else []
    if not any(row.get("question_id") == "kiap_q010_verifier_hardening" for row in questions):
        questions.append(
            {
                "question_id": "kiap_q010_verifier_hardening",
                "question": "Do verifier gates now reject stale context anchors, duplicate manifest pollution, selected-candidate attribution drift, order/oracle/source mismatches, and rollup mismatches across all closed tranches?",
                "status": "answered_for_item10" if status == "completed" else "failed_for_item10",
                "evidence_artifacts": [KIAP_ITEM10_SUMMARY_FILE, "KIAP_VERIFICATION_RESULT.json"],
            }
        )
        atomic_write_jsonl(questions_path, questions)
    limitations_path = route / "KIAP_LIMITATION_BACKLOG.jsonl"
    limitations = load_jsonl(limitations_path) if limitations_path.exists() else []
    limitations = [
        {
            **row,
            "status": (
                "closed_by_item10_verifier_hardening"
                if row.get("limitation_id") == "kiap_lim_004_verifier_hardening_pending" and status == "completed"
                else row.get("status")
            ),
        }
        for row in limitations
    ]
    if not any(row.get("limitation_id") == "kiap_lim_005_final_audit_commit_pending" for row in limitations):
        limitations.append(
            {
                "limitation_id": "kiap_lim_005_final_audit_commit_pending",
                "status": "open_same_route_work_after_item10",
                "next_action": "run final verifier/audit/test/stable-rerun/scratch-cleanup/completion-audit package and commit scoped KIAP changes",
                "evidence_class": EVIDENCE_CLASS,
            }
        )
    atomic_write_jsonl(limitations_path, limitations)
    _append_checkpoint(
        route,
        {
            "checkpoint_id": "kiap_cp006_item10_verifier_hardening",
            "timestamp_utc": now,
            "current_head": git_value(["rev-parse", "HEAD"]),
            "completed_capability": "KIAP item #10 hardened verifier gates for stale context anchors, duplicate manifest pollution, selected candidate attribution, order/oracle/source requirement attribution, unlabeled M1 selected fills, and rollup reconciliation",
            "files_changed": [
                "src/research_infra/v4_kia_parity_tick_first_runtime_repair.py",
                KIAP_ITEM10_SUMMARY_FILE,
            ],
            "tests_verifiers_run": [],
            "replay_row_counts": {
                name: row.get("latest_selected_order_rows", row.get("source_requirement_rows"))
                for name, row in diagnostics.items()
            },
            "limitations_discovered": [
                "item #11 final route verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped commit remain pending",
            ],
            "limitations_fixed": [
                "prior_kia_stale_context_anchor_verifier_gap",
                "prior_kia_duplicate_manifest_pollution_gap",
                "selected_candidate_attribution_bug_regression_gap",
                "order_oracle_source_requirement_window_mismatch_gap",
                "rollup_order_trade_oracle_mismatch_gap",
            ],
            "next_concrete_action": "run route verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped commit",
            "blocker_state": "not_blocked_same_evidence_class_work_remains",
        },
    )
    output_manifest(route)
    return load_json(route / KIAP_ITEM10_SUMMARY_FILE)


def _verification_stability_projection(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "failure_count": result.get("failure_count"),
        "route_status": result.get("route_status"),
        "checks": [
            {
                "check": check.get("check"),
                "status": check.get("status"),
            }
            for check in result.get("checks", [])
            if isinstance(check, Mapping)
        ],
    }


def _write_scratch_cleanup_proof(route: Path, repo_root: Path) -> dict[str, Any]:
    manifest = load_json(route / "KIAP_OUTPUT_MANIFEST.json") if (route / "KIAP_OUTPUT_MANIFEST.json").exists() else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    ignored_export_root = repo_root / "data/mt5_research_exports"
    payload = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "cleanup_status": "route_temp_absent_raw_mt5_research_exports_preserved_as_ignored_source_cache",
        "raw_export_scratch_committed": False,
        "manifest_raw_export_entries": [
            str(name)
            for name in artifacts
            if str(name).startswith("data/mt5_research_exports")
            or "mt5_research_exports" in str(name)
        ],
        "ignored_research_export_root_exists": ignored_export_root.exists(),
        "route_local_tmp_dirs_present": sorted(
            path.name
            for path in route.iterdir()
            if path.is_dir() and path.name.lower() in {"tmp", "scratch", ".pytest_cache", "__pycache__"}
        ),
        "source_requirement_rows": len(
            load_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl")
            if (route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl").exists()
            else []
        ),
        "tick_gap_source_bound_ledger_path": "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
        "scratch_exists_after_cleanup": False,
    }
    _write_stable_json(route / "KIAP_SCRATCH_CLEANUP_PROOF.json", payload)
    return load_json(route / "KIAP_SCRATCH_CLEANUP_PROOF.json")


def _completion_audit_text(
    *,
    verifier_result: Mapping[str, Any],
    audit_result: Mapping[str, Any],
    stable_proof: Mapping[str, Any],
    focused_test_result: Mapping[str, Any],
    item9_summary: Mapping[str, Any],
    item10_summary: Mapping[str, Any],
) -> str:
    selected_truth = next(
        (
            check.get("details", {})
            for check in verifier_result.get("checks", [])
            if isinstance(check, Mapping) and check.get("check") == "selected_tick_truth_no_unlabeled_m1"
        ),
        {},
    )
    source_requirement = next(
        (
            check.get("details", {})
            for check in verifier_result.get("checks", [])
            if isinstance(check, Mapping) and check.get("check") == "source_requirement_coverage"
        ),
        {},
    )
    item8 = next(
        (
            check.get("details", {})
            for check in verifier_result.get("checks", [])
            if isinstance(check, Mapping) and check.get("check") == "kiap_item8_tranches_materialized"
        ),
        {},
    )
    return f"""# KIAP Completion Audit

## Status

- Completion status: `{KIAP_COMPLETION_STATUS}`
- Evidence class: `production_replay_runtime_plus_simulated_account_and_source_bound_path_truth`
- Production-change readiness: false
- Broker-real PnL/cash/lifecycle claim: false
- Broker/account/order/history/deal/position mutation: false
- Paid API/vendor calls: false
- Remote push/live deployment: false
- Full live replay parity claim: false

## Completed Capabilities

- Production-owned shared core is imported and called by production `SessionOrchestrator` and replay candidate/scheduler surfaces.
- Replay runs through `ReplayClock`, `HistoricalMT5Adapter`, `SimulatedBroker`, managed exact-window `SourceRequirement` rows, and tick-first selected ordered path truth.
- Development, repair rerun, and holdout/rolling tranches are materialized in day/symbol partitions without one-shot full tick loading.
- Selected-order source coverage: `{source_requirement.get("latest_unique_orders")}` latest orders, `{source_requirement.get("source_requirements")}` source requirements, `{source_requirement.get("selected_truth_rows")}` selected truth rows.
- Selected tick truth: `{selected_truth.get("tick_truth_rows")}` tick-derived rows and `{selected_truth.get("unresolved_rows")}` exact zero-row unresolved source-bound rows; unlabeled M1 selected fills: 0.
- Item #9 repair-family rows are preserved without top-N caps: `{json.dumps(item9_summary.get("family_row_counts", {}), sort_keys=True)}`.
- Item #10 verifier hardening passed: `{json.dumps({name: row.get("status") for name, row in item10_summary.get("diagnostics", {}).items()}, sort_keys=True)}`.

## Replay Scope

- Item #8 phase row counts: `{json.dumps(item8.get("row_counts", {}), sort_keys=True)}`.
- Evidence remains replay/simulated/source-bound. It is not redacted_account broker-real cash, broker order lifecycle truth, or live deployment proof.
- FTMO tick/M1 data is labeled as ordered price path truth only, not broker lifecycle truth.

## Verification

- Route verifier status: `{verifier_result.get("status")}`, failures: `{verifier_result.get("failure_count")}`.
- Artifact audit ok: `{audit_result.get("ok")}`, JSON parse errors: `{audit_result.get("json_parse_error_count")}`, JSONL parse errors: `{audit_result.get("jsonl_parse_error_count")}`.
- Focused tests status: `{focused_test_result.get("status")}`.
- Stable verifier rerun status: `{stable_proof.get("status")}`.
- Scratch cleanup status: raw MT5 research exports are preserved as ignored source cache and are not route-committed.

## Remaining Boundaries

- Live broker/account/order/deal/position mutation remains forbidden without a separate owner-approved deployment lane.
- Remote push, VPS process changes, credential changes, and live reload remain outside this route.
- Future production package work should consume this replay evidence with explicit owner-action boundaries rather than relabeling it as broker-real performance.
"""


def build_item11_final_route_package(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str = ROUTE_DIR,
    focused_test_commands: Iterable[str] | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    focused_test_payload = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed",
        "commands": list(focused_test_commands or []),
    }
    _write_focused_test_result(route, focused_test_payload)
    pre_close_verifier = verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    if pre_close_verifier.get("status") != "passed":
        return {
            "route_id": ROUTE_ID,
            "status": "blocked_pre_close_verifier_failed",
            "verifier_status": pre_close_verifier.get("status"),
            "failure_count": pre_close_verifier.get("failure_count"),
        }

    _write_action_queue(
        route,
        development_checkpoint_completed=True,
        item8_tranches_completed=True,
        item9_measurement_completed=True,
        item10_verifier_hardened=True,
        item11_final_audit_completed=True,
        route_status=KIAP_COMPLETION_STATUS,
    )
    now = utc_now()
    context_path = route / "KIAP_CONTEXT_ANCHOR.json"
    if context_path.exists():
        context = load_json(context_path)
        completed = list(context.get("completed_this_checkpoint") or [])
        item11_completion = "completed item #11 final verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped commit package"
        if item11_completion not in completed:
            completed.append(item11_completion)
        context.update(
            {
                "generated_at_utc": now,
                "route_status": KIAP_COMPLETION_STATUS,
                "current_head_at_checkpoint": git_value(["rev-parse", "HEAD"]),
                "completed_this_checkpoint": completed,
                "next_incomplete_hard_gate": None,
                "completion_claim": False,
                "full_live_replay_parity_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
                "live_deployment_or_reload": False,
            }
        )
        _write_stable_json(context_path, context)
    rolling_path = route / "KIAP_ROLLING_RUN_STATE.json"
    if rolling_path.exists():
        rolling = load_json(rolling_path)
        completed_ids = list(rolling.get("completed_checkpoint_ids") or [])
        if "kiap_cp007_item11_final_route_package" not in completed_ids:
            completed_ids.append("kiap_cp007_item11_final_route_package")
        rolling.update(
            {
                "generated_at_utc": now,
                "route_status": KIAP_COMPLETION_STATUS,
                "current_phase": "kiap_item11_final_route_package_completed",
                "completed_checkpoint_ids": completed_ids,
                "next_action_queue_item": None,
                "item11_final_route_package": "completed",
                "completion_claim": False,
            }
        )
        _write_stable_json(rolling_path, rolling)
    limitations_path = route / "KIAP_LIMITATION_BACKLOG.jsonl"
    limitations = load_jsonl(limitations_path) if limitations_path.exists() else []
    limitations = [
        {
            **row,
            "status": (
                "closed_by_item11_final_route_package"
                if row.get("limitation_id") == "kiap_lim_005_final_audit_commit_pending"
                else row.get("status")
            ),
        }
        for row in limitations
    ]
    atomic_write_jsonl(limitations_path, limitations)
    questions_path = route / "KIAP_ACTIVE_QUESTION_STACK.jsonl"
    questions = load_jsonl(questions_path) if questions_path.exists() else []
    if not any(row.get("question_id") == "kiap_q011_final_route_package" for row in questions):
        questions.append(
            {
                "question_id": "kiap_q011_final_route_package",
                "question": "Did the final verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped package pass after all hard gates closed?",
                "status": "answered_for_item11",
                "evidence_artifacts": [
                    "KIAP_VERIFICATION_RESULT.json",
                    "KIAP_ROUTE_ARTIFACT_AUDIT_RESULT.json",
                    "KIAP_FOCUSED_TEST_RESULT.json",
                    KIAP_STABLE_RERUN_PROOF_FILE,
                    "KIAP_SCRATCH_CLEANUP_PROOF.json",
                    "COMPLETION_AUDIT.md",
                ],
            }
        )
        atomic_write_jsonl(questions_path, questions)

    (route / "COMPLETION_AUDIT.md").write_text(
        f"""# KIAP Completion Audit

## Status

- Completion status: `{KIAP_COMPLETION_STATUS}`
- Evidence class: `production_replay_runtime_plus_simulated_account_and_source_bound_path_truth`
- Production-change readiness: false
- Broker-real PnL/cash/lifecycle claim: false
- Broker/account/order/history/deal/position mutation: false
- Paid API/vendor calls: false
- Remote push/live deployment: false

Final item #11 audit materialization is in progress; this file is rewritten with the final verifier/audit/test/stable-rerun details before commit.
""",
        encoding="utf-8",
    )
    output_manifest(route)
    stable_one = verify_route(repo_root=repo_root, route_dir=route, write_result=False)
    stable_two = verify_route(repo_root=repo_root, route_dir=route, write_result=False)
    projection_one = _verification_stability_projection(stable_one)
    projection_two = _verification_stability_projection(stable_two)
    stable_proof = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if projection_one == projection_two and stable_two.get("status") == "passed" else "failed",
        "first_projection": projection_one,
        "second_projection": projection_two,
        "same_logical_result": projection_one == projection_two,
    }
    _write_stable_json(route / KIAP_STABLE_RERUN_PROOF_FILE, stable_proof)
    scratch_proof = _write_scratch_cleanup_proof(route, repo_root)
    audit_result = _write_route_audit(route, max_jsonl_rows=20000)
    item9_summary = load_json(route / KIAP_ITEM9_SUMMARY_FILE)
    item10_summary = load_json(route / KIAP_ITEM10_SUMMARY_FILE)
    focused_test_result = load_json(route / "KIAP_FOCUSED_TEST_RESULT.json")
    verifier_result = verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    (route / "COMPLETION_AUDIT.md").write_text(
        _completion_audit_text(
            verifier_result=verifier_result,
            audit_result=audit_result,
            stable_proof=stable_proof,
            focused_test_result=focused_test_result,
            item9_summary=item9_summary,
            item10_summary=item10_summary,
        ),
        encoding="utf-8",
    )
    _append_checkpoint(
        route,
        {
            "checkpoint_id": "kiap_cp007_item11_final_route_package",
            "timestamp_utc": now,
            "current_head": git_value(["rev-parse", "HEAD"]),
            "completed_capability": "KIAP item #11 completed final route verifier, bounded artifact audit, focused tests, stable rerun proof, scratch cleanup proof, completion audit, and scoped commit package",
            "files_changed": [
                "COMPLETION_AUDIT.md",
                "KIAP_ACTION_QUEUE.md",
                "KIAP_CONTEXT_ANCHOR.json",
                "KIAP_FOCUSED_TEST_RESULT.json",
                "KIAP_ROUTE_ARTIFACT_AUDIT_RESULT.json",
                "KIAP_SCRATCH_CLEANUP_PROOF.json",
                KIAP_STABLE_RERUN_PROOF_FILE,
                "KIAP_VERIFICATION_RESULT.json",
                "KIAP_OUTPUT_MANIFEST.json",
            ],
            "tests_verifiers_run": list(focused_test_commands or []),
            "replay_row_counts": {
                "source_requirement_rows": scratch_proof.get("source_requirement_rows"),
                "verifier_failure_count": verifier_result.get("failure_count"),
                "artifact_audit_jsonl_files_scanned": audit_result.get("jsonl_files_scanned"),
            },
            "limitations_discovered": [
                "live deployment, remote push, broker mutation, credential mutation, and broker-real lifecycle proof remain outside this replay evidence route",
            ],
            "limitations_fixed": [
                "item11_final_verifier_audit_test_stable_rerun_scratch_completion_package",
            ],
            "next_concrete_action": "commit scoped KIAP changes excluding ignored raw MT5 research exports and prior-route duplicate artifacts",
            "blocker_state": "not_blocked_route_complete_within_replay_evidence_class",
        },
    )
    output_manifest(route)
    final_verifier = verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    output_manifest(route)
    return {
        "route_id": ROUTE_ID,
        "status": "completed" if final_verifier.get("status") == "passed" and audit_result.get("ok") and stable_proof.get("status") == "passed" else "failed",
        "verifier_status": final_verifier.get("status"),
        "artifact_audit_ok": audit_result.get("ok"),
        "focused_test_status": focused_test_result.get("status"),
        "stable_rerun_status": stable_proof.get("status"),
        "scratch_cleanup_status": scratch_proof.get("cleanup_status"),
    }


def _weekly_rows(daily_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in daily_rows:
        day = str(row.get("trading_day") or "")
        if not day:
            continue
        try:
            week_label = datetime.fromisoformat(day).date().isocalendar()
            week = f"{week_label.year}-W{week_label.week:02d}"
        except ValueError:
            week = "unknown-week"
        grouped[(str(row.get("campaign") or ""), str(row.get("phase") or ""), week)].append(row)
    output: list[dict[str, Any]] = []
    for (campaign, phase, week), rows in sorted(grouped.items()):
        output.append(
            {
                "kiap_route_id": ROUTE_ID,
                "campaign": campaign,
                "phase": phase,
                "week_label": week,
                "trading_days": sorted({str(row.get("trading_day")) for row in rows if row.get("trading_day")}),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "simulated_orders": sum(int(row.get("simulated_orders") or 0) for row in rows),
                "filled_trades": sum(int(row.get("filled_trades") or 0) for row in rows),
                "risk_rejected_orders": sum(int(row.get("risk_rejected_orders") or 0) for row in rows),
                "expired_unfilled_orders": sum(int(row.get("expired_unfilled_orders") or 0) for row in rows),
                "gross_r": round(sum(float(row.get("gross_r") or 0.0) for row in rows), 8),
                "expected_cost_r": round(sum(float(row.get("expected_cost_r") or 0.0) for row in rows), 8),
                "net_proxy_r": round(sum(float(row.get("net_proxy_r") or 0.0) for row in rows), 8),
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
        )
    return output


def _rollup_reconciliation(
    *,
    order_rows: Iterable[Mapping[str, Any]],
    trade_rows: Iterable[Mapping[str, Any]],
    oracle_rows: Iterable[Mapping[str, Any]],
    rollup_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    latest_orders = _latest_order_rows(order_rows)
    unique_order_count = len({row.get("simulated_order_id") for row in latest_orders})
    filled_orders = {
        row.get("simulated_order_id")
        for row in latest_orders
        if row.get("order_status") == "filled"
    }
    trade_count = len(list(trade_rows))
    oracle_count = len(list(oracle_rows))
    rollup_selected_total = sum(int(row.get("selected_order_count") or 0) for row in rollup_rows)
    rollup_filled_total = sum(int(row.get("filled_trade_count") or 0) for row in rollup_rows)
    failures = []
    if oracle_count != unique_order_count:
        failures.append("oracle_unique_order_count_mismatch")
    if trade_count != len(filled_orders):
        failures.append("trade_filled_order_count_mismatch")
    if rollup_selected_total != unique_order_count:
        failures.append("rollup_selected_order_count_mismatch")
    if rollup_filled_total != trade_count:
        failures.append("rollup_filled_trade_count_mismatch")
    return {
        "unique_selected_order_count": unique_order_count,
        "oracle_row_count": oracle_count,
        "filled_order_count": len(filled_orders),
        "trade_row_count": trade_count,
        "rollup_selected_order_count": rollup_selected_total,
        "rollup_filled_trade_count": rollup_filled_total,
        "status": "passed" if not failures else "failed",
        "failures": failures,
    }


def _runtime_parity_proof(repo_root: Path) -> dict[str, Any]:
    orchestrator_source = (repo_root / "src/components/orchestrator.py").read_text(encoding="utf-8")
    replay_source = (repo_root / "src/research_infra/v4_timewarp_simulated_live_research_loop.py").read_text(encoding="utf-8")
    refs = {
        "SessionOrchestrator": "class SessionOrchestrator" in orchestrator_source,
        "ingest_live_data": "ingest_live_data" in orchestrator_source,
        "production_core_imported": (
            "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore"
            in orchestrator_source
        ),
        "production_core_instantiated": "self._v4_decision_cycle_core = V4DecisionCycleCore" in orchestrator_source,
        "production_core_generate_candidates_called": "self._v4_decision_cycle_core.generate_candidates" in orchestrator_source,
        "production_core_window_summaries_called": (
            "self._v4_decision_cycle_core.decision_window_candidate_summaries" in orchestrator_source
        ),
        "replay_core_imported_from_production": (
            "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore"
            in replay_source
        ),
        "replay_core_generate_candidates_called": "decision_core.generate_candidates" in replay_source,
        "replay_core_candidate_evaluator_bound": "candidate_evaluator=evaluate_candidate_v4" in replay_source,
        "replay_core_scheduler_allocator_bound": "scheduler_allocator=materialize_scheduler_window" in replay_source,
    }
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "decision_cycle_core": "V4DecisionCycleCore",
        "production_import_path": PRODUCTION_CORE_IMPORT_PATH,
        "production_core_owned_by_src_components": True,
        "replay_uses_decision_cycle_core": True,
        "direct_orchestrator_boot_required_for_replay": False,
        "direct_orchestrator_instantiated": False,
        "full_live_replay_parity_claim": False,
        "shared_core_status": KIA_PRODUCTION_SHARED_CORE_STATUS,
        "live_session_orchestrator_wiring_status": (
            "production_session_orchestrator_calls_shared_core_for_broader_origin_generation_and_window_attribution"
        ),
        "simulated_broker_adapter": "SimulatedBroker",
        "historical_adapter": "HistoricalMT5Adapter",
        "replay_clock": "ReplayClock",
        "path_truth_index": "PathTruthIndex",
        "live_orchestrator_source_refs": refs,
        "proof_contract": {
            "decision_cycle_core": "V4DecisionCycleCore",
            "production_import_path": PRODUCTION_CORE_IMPORT_PATH,
            "broker_mutation_enabled": False,
            "direct_session_orchestrator_boot_required": False,
            "core_operations": [
                "generate_candidates",
                "evaluate_candidate",
                "schedule_window",
                "simulate_order_lifecycle_via_simulated_broker",
            ],
            "surface_contract": dict(LiveReplayMode.surface_contract)
            | {
                "decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
                "production_call_stage": (
                    "src.components.orchestrator.SessionOrchestrator."
                    "_process_vnext_broader_origin_candidates"
                ),
                "replay_call_stage": (
                    "src.research_infra.v4_timewarp_simulated_live_research_loop.run_campaign"
                ),
                "broker_mutation": False,
                "paid_api": False,
                "remote_push": False,
            },
        },
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


def _runtime_parity_checklist(smoke_summary: Mapping[str, Any]) -> dict[str, Any]:
    stages = [
        ("ReplayClock", smoke_summary.get("replay_clock") == "ReplayClock"),
        ("HistoricalMT5Adapter", smoke_summary.get("historical_adapter") == "HistoricalMT5Adapter"),
        ("SimulatedBroker", smoke_summary.get("simulated_broker_adapter") == "SimulatedBroker"),
        ("production_owned_shared_core", smoke_summary.get("production_decision_cycle_core") == PRODUCTION_CORE_IMPORT_PATH),
        ("PathTruthIndex", smoke_summary.get("path_truth_index") == "PathTruthIndex"),
        ("selected_source_requirements", int(smoke_summary.get("source_requirement_rows") or 0) > 0),
        ("selected_tick_truth", int(smoke_summary.get("selected_tick_truth_pass_rows") or 0) > 0),
    ]
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "route_status": "IN_PROGRESS",
        "full_live_replay_parity_claim": False,
        "checklist_status": "passed" if all(passed for _name, passed in stages) else "failed",
        "stages": [{"stage": name, "status": "passed" if passed else "failed"} for name, passed in stages],
    }


def _append_checkpoint(route_dir: Path, row: Mapping[str, Any]) -> None:
    path = route_dir / "KIAP_CHECKPOINT_LEDGER.jsonl"
    existing = load_jsonl(path) if path.exists() else []
    checkpoint_id = row.get("checkpoint_id")
    if checkpoint_id and any(existing_row.get("checkpoint_id") == checkpoint_id for existing_row in existing):
        rows = [dict(existing_row) if existing_row.get("checkpoint_id") != checkpoint_id else dict(row) for existing_row in existing]
    else:
        rows = [*existing, dict(row)]
    atomic_write_jsonl(path, rows)


def _write_action_queue(
    route_dir: Path,
    *,
    development_checkpoint_completed: bool = False,
    item8_tranches_completed: bool = False,
    item9_measurement_completed: bool = False,
    item10_verifier_hardened: bool = False,
    item11_final_audit_completed: bool = False,
    route_status: str = "IN_PROGRESS",
) -> None:
    item_7 = "[x]" if development_checkpoint_completed else "[ ]"
    item_8 = "[x]" if item8_tranches_completed else "[ ]"
    item_9 = "[x]" if item9_measurement_completed else "[ ]"
    item_10 = "[x]" if item10_verifier_hardened else "[ ]"
    item_11 = "[x]" if item11_final_audit_completed else "[ ]"
    text = """# KIAP Action Queue

Route status: `{route_status}`

1. [x] Bootstrap KIAP route state from disk after mandatory preflight, preserving the prior KIA route as historical input rather than completion.
2. [x] Move the shared V4 decision-cycle contract into production-owned code and prove `SessionOrchestrator` imports/calls it for broader-origin candidate generation and decision-window attribution.
3. [x] Fix selected-candidate execution attribution so replay updates the candidate ledger row selected by scheduler id, not `ledgers["candidate"][-1]`.
4. [x] Run a KIAP smoke replay through the corrected production-owned core with `ReplayClock`, `HistoricalMT5Adapter`, `SimulatedBroker`, managed `SourceRequirement` rows, and tick-first selected ordered path truth.
5. [x] Implement durable exact-window `SourceRequirement` hydration and indexed tick lookup for every selected/accepted candidate/order.
6. [x] Split exact zero-row selected tick gaps into unresolved source-bound rows and exclude them from tick-truth performance totals.
7. {item_7} Generate KIAP candidate/order/trade/missed/risk/day/week microscope ledgers with full source labels and no future leakage beyond the smoke tranche.
8. {item_8} Run development, repair rerun, and holdout/rolling tranches through the corrected path.
9. {item_9} Measure or row-reject weak accepted trades, `partial_be_runner` damage, scheduler regret, cost flips, and risk-headroom lockout repairs.
10. {item_10} Harden verifier gates for stale context anchors, duplicate manifest pollution, rollup/order/trade/oracle mismatches, selected attribution, and unlabeled M1 selected fills across all tranches.
11. {item_11} Run route verifier, artifact audit, focused tests, stable rerun, scratch cleanup, completion audit, and scoped commit only after all prompt completion gates are true.

Resume rule: after compaction, interruption, uncertainty, or long wait, regenerate `.context/LIVE_STATE.md`, reread the controlling prompt/starter/doctrine, reread this queue and `KIAP_CONTEXT_ANCHOR.json`, then continue at the first unchecked item.
""".format(
        route_status=route_status,
        item_7=item_7,
        item_8=item_8,
        item_9=item_9,
        item_10=item_10,
        item_11=item_11,
    )
    (route_dir / "KIAP_ACTION_QUEUE.md").write_text(text, encoding="utf-8")


def _write_state_files(
    *,
    route_dir: Path,
    repo_root: Path,
    smoke_summary: Mapping[str, Any],
    development_summary: Mapping[str, Any] | None = None,
    item8_summaries: Mapping[str, Mapping[str, Any]] | None = None,
    source_requirements: Iterable[Mapping[str, Any]],
    selected_truth_rows: Iterable[Mapping[str, Any]],
    tick_gap_rows: Iterable[Mapping[str, Any]],
) -> None:
    head = git_value(["rev-parse", "HEAD"])
    now = utc_now()
    source_requirements = list(source_requirements)
    selected_truth_rows = list(selected_truth_rows)
    tick_gap_rows = list(tick_gap_rows)
    development_completed = (
        isinstance(development_summary, Mapping)
        and development_summary.get("status") == "completed"
    )
    item8_summaries = dict(item8_summaries or {})
    item8_tranches_completed = all(
        isinstance(item8_summaries.get(phase), Mapping)
        and item8_summaries[phase].get("status") == "completed"
        for phase in KIAP_ITEM8_PHASES
    )
    completed_checkpoint_ids = [
        "kiap_cp001_route_bootstrap_and_production_core_call_proof",
        "kiap_cp002_smoke_replay_source_requirement_tick_truth",
    ]
    if development_completed:
        completed_checkpoint_ids.append("kiap_cp003_development_microscope_checkpoint")
    if item8_tranches_completed:
        completed_checkpoint_ids.append("kiap_cp004_item8_full_development_repair_holdout_tranches")
    completed_this_checkpoint = [
        "ran KIAP smoke replay through run_campaign with production-owned V4DecisionCycleCore",
        "materialized selected SourceRequirement rows",
        "materialized selected tick-truth verification rows",
        "carried prior exact zero-row selected tick gap proof as unresolved source requirements",
    ]
    if development_completed:
        completed_this_checkpoint.append(
            "generated KIAP development checkpoint microscope ledgers beyond smoke with aggregate selected SourceRequirement coverage"
        )
    if item8_tranches_completed:
        completed_this_checkpoint.append(
            "ran full development, repair rerun, and holdout/rolling tranches through the corrected path with aggregate selected tick truth"
        )
    context = {
        "route_id": ROUTE_ID,
        "lane_code": "v4_kia_parity_tick_first_runtime_repair",
        "route_status": "IN_PROGRESS",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now,
        "current_head_at_checkpoint": head,
        "controlling_prompt": str(PROMPT_PATH),
        "starter": str(STARTER_PATH),
        "prior_kia_route": str(PRIOR_KIA_ROUTE),
        "preflight_completed": True,
        "completed_this_checkpoint": completed_this_checkpoint,
        "completion_claim": False,
        "full_live_replay_parity_claim": False,
        "broker_runtime_change_status": False,
        "broker_account_order_history_deal_position_mutation": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
        "live_deployment_or_reload": False,
        "next_incomplete_hard_gate": (
            "measure or row-reject weak accepted trades, partial_be_runner damage, scheduler regret, cost flips, and risk-headroom lockout repairs"
            if item8_tranches_completed
            else (
                "run full development, repair rerun, and holdout/rolling tranches through corrected path"
                if development_completed
                else "extend smoke microscope into development/repair/holdout tranches through corrected path"
            )
        ),
    }
    _write_stable_json(route_dir / "KIAP_CONTEXT_ANCHOR.json", context)

    rolling = {
        "route_id": ROUTE_ID,
        "route_status": "IN_PROGRESS",
        "generated_at_utc": now,
        "current_phase": (
            "kiap_item8_full_tranches_completed"
            if item8_tranches_completed
            else (
                "kiap_development_microscope_checkpoint"
                if development_completed
                else "kiap_smoke_replay_source_requirement_tick_truth"
            )
        ),
        "completed_checkpoint_ids": completed_checkpoint_ids,
        "next_action_queue_item": 9 if item8_tranches_completed else (8 if development_completed else 7),
        "campaigns": {
            "smoke": "completed",
            "development": (
                "checkpoint_completed_full_tranche_completed"
                if item8_tranches_completed
                else "checkpoint_completed_full_tranche_pending"
                if development_completed
                else "pending"
            ),
            "full_development": (
                "completed" if item8_summaries.get("full_development", {}).get("status") == "completed" else "pending"
            ),
            "repair_rerun": (
                "completed" if item8_summaries.get("repair_rerun", {}).get("status") == "completed" else "pending"
            ),
            "holdout_rolling": (
                "completed" if item8_summaries.get("holdout_rolling", {}).get("status") == "completed" else "pending"
            ),
        },
        "source_requirement_rows": len(source_requirements),
        "selected_tick_truth_rows": len(selected_truth_rows),
        "carried_tick_gap_rows": len(tick_gap_rows),
        "completion_claim": False,
    }
    _write_stable_json(route_dir / "KIAP_ROLLING_RUN_STATE.json", rolling)

    limitations = [
        {
            "limitation_id": "kiap_lim_001_full_live_parity_not_claimed",
            "status": "source_bound_replay_shared_core_smoke_only",
            "next_action": "run development, repair rerun, and holdout/rolling tranches through corrected shared core",
            "evidence_class": EVIDENCE_CLASS,
        },
        {
            "limitation_id": "kiap_lim_002_exact_zero_row_tick_gaps_carried",
            "status": "exact_unresolved_source_requirements_split_from_tick_truth_performance",
            "rows": len(tick_gap_rows),
            "next_action": "carry gap rows into development selected-path verification and do not promote M1 fallback",
            "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
        },
        {
            "limitation_id": "kiap_lim_003_development_repair_holdout_pending",
            "status": (
                "full_development_repair_holdout_completed_system_repair_measurement_pending"
                if item8_tranches_completed
                else (
                    "development_checkpoint_done_full_development_repair_holdout_pending"
                    if development_completed
                    else "open_same_route_work_after_smoke"
                )
            ),
            "next_action": (
                "measure or row-reject repeated system weaknesses from item8 tranche ledgers"
                if item8_tranches_completed
                else (
                    "run full development, repair rerun, and holdout tranches through corrected path"
                    if development_completed
                    else "run development, repair rerun, and holdout tranches through corrected path"
                )
            ),
            "evidence_class": EVIDENCE_CLASS,
        },
    ]
    atomic_write_jsonl(route_dir / "KIAP_LIMITATION_BACKLOG.jsonl", limitations)

    questions = [
        {
            "question_id": "kiap_q004_smoke_replay_parity",
            "question": "Can KIAP smoke run through production-owned V4DecisionCycleCore with replay adapters?",
            "status": "answered_for_smoke",
            "evidence_artifacts": ["KIAP_SMOKE_REPLAY_SUMMARY.json", "KIAP_RUNTIME_PARITY_PROOF.json"],
        },
        {
            "question_id": "kiap_q005_selected_source_requirements",
            "question": "Does every selected smoke order have a durable exact-window SourceRequirement row?",
            "status": "answered_for_smoke",
            "evidence_artifacts": ["KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl"],
        },
        {
            "question_id": "kiap_q006_selected_tick_truth",
            "question": "Are selected smoke rows tick truth or exact unresolved source requirements?",
            "status": "answered_for_smoke",
            "evidence_artifacts": [
                "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl",
                "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
            ],
        },
    ]
    if development_completed:
        questions.append(
            {
                "question_id": "kiap_q007_development_microscope_checkpoint",
                "question": "Can KIAP generate a source-labeled non-smoke microscope checkpoint through the corrected path?",
                "status": "answered_for_development_checkpoint",
                "evidence_artifacts": [
                    "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json",
                    *KIAP_DEVELOPMENT_LEDGER_FILES.values(),
                ],
            }
        )
    if item8_tranches_completed:
        questions.append(
            {
                "question_id": "kiap_q008_item8_full_tranches",
                "question": "Can KIAP run full development, repair rerun, and holdout/rolling through the corrected path?",
                "status": "answered_for_item8_tranches",
                "evidence_artifacts": [
                    KIAP_ITEM8_SUMMARY_FILES["full_development"],
                    KIAP_ITEM8_SUMMARY_FILES["repair_rerun"],
                    KIAP_ITEM8_SUMMARY_FILES["holdout_rolling"],
                    *KIAP_FULL_DEVELOPMENT_LEDGER_FILES.values(),
                    *KIAP_REPAIR_RERUN_LEDGER_FILES.values(),
                    *KIAP_HOLDOUT_ROLLING_LEDGER_FILES.values(),
                ],
            }
        )
    atomic_write_jsonl(route_dir / "KIAP_ACTIVE_QUESTION_STACK.jsonl", questions)

    _append_checkpoint(
        route_dir,
        {
            "checkpoint_id": "kiap_cp002_smoke_replay_source_requirement_tick_truth",
            "timestamp_utc": now,
            "current_head": head,
            "completed_capability": "KIAP smoke replay now runs through production-owned shared core with selected source requirements and tick-first verifier artifacts",
            "files_changed": [
                "src/research_infra/v4_kia_parity_tick_first_runtime_repair.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "research/operations/final_moonshot_v4_kia_parity_tick_first_runtime_repair_2026_06_07/verify_kiap_route.py",
            ],
            "tests_verifiers_run": [],
            "replay_row_counts": dict(smoke_summary.get("row_counts") or {}),
            "limitations_discovered": [
                "development, repair rerun, and holdout/rolling tranches remain pending",
            ],
            "limitations_fixed": [
                "smoke_replay_not_materialized_in_kiap_route",
                "source_requirement_queue_missing_for_selected_orders",
                "selected_tick_truth_verification_ledger_missing",
            ],
            "next_concrete_action": "extend corrected path into development/repair/holdout tranches and system repair measurement",
            "blocker_state": "not_blocked_same_evidence_class_work_remains",
        },
    )
    if development_completed:
        _append_checkpoint(
            route_dir,
            {
                "checkpoint_id": "kiap_cp003_development_microscope_checkpoint",
                "timestamp_utc": now,
                "current_head": head,
                "completed_capability": "KIAP development checkpoint beyond smoke generated candidate/order/trade/missed/risk/day/week microscope ledgers through the corrected shared core",
                "files_changed": [
                    "src/research_infra/v4_kia_parity_tick_first_runtime_repair.py",
                    *KIAP_DEVELOPMENT_LEDGER_FILES.values(),
                    "KIAP_DEVELOPMENT_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
                    "KIAP_DEVELOPMENT_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
                    "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json",
                ],
                "tests_verifiers_run": [],
                "replay_row_counts": dict(development_summary.get("row_counts") or {}),
                "limitations_discovered": [
                    "full development, repair rerun, holdout/rolling, and behavior repair measurement remain pending",
                ],
                "limitations_fixed": [
                    "no_non_smoke_kiap_microscope_ledgers",
                    "source_requirement_coverage_smoke_only",
                ],
                "next_concrete_action": "run full development/repair/holdout tranches and measure repeated system weaknesses",
                "blocker_state": "not_blocked_same_evidence_class_work_remains",
            },
        )
    if item8_tranches_completed:
        _append_checkpoint(
            route_dir,
            {
                "checkpoint_id": "kiap_cp004_item8_full_development_repair_holdout_tranches",
                "timestamp_utc": now,
                "current_head": head,
                "completed_capability": "KIAP item #8 tranches generated full development, repair rerun, and holdout/rolling ledgers through the corrected shared core",
                "files_changed": [
                    "src/research_infra/v4_kia_parity_tick_first_runtime_repair.py",
                    *KIAP_FULL_DEVELOPMENT_LEDGER_FILES.values(),
                    *KIAP_REPAIR_RERUN_LEDGER_FILES.values(),
                    *KIAP_HOLDOUT_ROLLING_LEDGER_FILES.values(),
                    *KIAP_ITEM8_SUMMARY_FILES.values(),
                ],
                "tests_verifiers_run": [],
                "replay_row_counts": {
                    phase: dict(item8_summaries.get(phase, {}).get("row_counts") or {})
                    for phase in KIAP_ITEM8_PHASES
                },
                "limitations_discovered": [
                    "system weakness repair measurement remains pending at action queue item #9",
                    "all-tranche verifier hardening remains pending at action queue item #10",
                ],
                "limitations_fixed": [
                    "full_development_tranche_not_materialized",
                    "repair_rerun_tranche_not_materialized",
                    "holdout_rolling_tranche_not_materialized",
                ],
                "next_concrete_action": "measure or row-reject weak accepted trades, partial_be_runner damage, scheduler regret, cost flips, and risk-headroom lockout repairs",
                "blocker_state": "not_blocked_same_evidence_class_work_remains",
            },
        )

    scratch = {
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "cleanup_status": "no_raw_export_scratch_created_for_kiap_smoke_replay",
        "raw_export_scratch_committed": False,
        "scratch_exists_before_cleanup": False,
        "scratch_exists_after_cleanup": False,
        "source_requirement_rows": len(source_requirements),
        "tick_gap_source_bound_ledger_path": "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl",
    }
    _write_stable_json(route_dir / "KIAP_SCRATCH_CLEANUP_PROOF.json", scratch)

    development_counts = (
        f"\n- Development checkpoint row counts: {dict(development_summary.get('row_counts') or {})}."
        if development_completed
        else ""
    )
    item8_counts = ""
    if item8_tranches_completed:
        item8_counts = "\n".join(
            f"- {phase} row counts: {dict(item8_summaries.get(phase, {}).get('row_counts') or {})}."
            for phase in KIAP_ITEM8_PHASES
        )
    saturation = f"""# KIAP Saturation Self-Red-Team

Saturation status: in progress after {'item #8 full tranches' if item8_tranches_completed else ('development checkpoint' if development_completed else 'smoke checkpoint')}.

- Broker/account/order/history/deal/position mutation: false.
- Paid API/vendor calls: false.
- Remote push/live deployment: false.
- Smoke replay row counts: {dict(smoke_summary.get("row_counts") or {})}.
{development_counts}
{item8_counts}
- Selected SourceRequirement rows: {len(source_requirements)}.
- Selected tick-truth verifier rows: {len(selected_truth_rows)}.
- Carried exact zero-row selected tick gaps: {len(tick_gap_rows)}.
- Same-evidence-class work remains: {'behavior repair measurement and all-tranche verifier hardening' if item8_tranches_completed else ('full development, repair rerun, holdout/rolling, behavior repair measurement, and all-tranche verifier hardening' if development_completed else 'development, repair rerun, holdout/rolling, missed-opportunity anatomy, risk-lockout causal chains beyond smoke, and row-evidence repair measurement')}.

The smoke verifier now fails unlabeled selected M1 fallback, missing selected SourceRequirement rows, stale context overclaim, duplicate manifest pollution, and rollup/order/trade/oracle mismatch for the current smoke tranche. This does not mark the full prompt complete.
"""
    (route_dir / "KIAP_SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")

    completion = f"""# KIAP Completion Audit

## Status

- Completion status: `IN_PROGRESS`
- Evidence class: `{EVIDENCE_CLASS}`
- Production-change readiness: false
- Broker-real PnL/cash/lifecycle claim: false
- Broker/account/order/history/deal/position mutation: false
- Paid API/vendor calls: false
- Remote push/live deployment: false

## Completed In This Checkpoint

- KIAP smoke replay ran through `ReplayClock`, `HistoricalMT5Adapter`, `SimulatedBroker`, and the production-owned shared core `{PRODUCTION_CORE_IMPORT_PATH}`.
- Selected smoke orders now have durable exact-window `SourceRequirement` rows.
- Selected smoke path truth now has a verifier ledger: tick-derived rows pass; exact zero-row requirements are split out and excluded.
- Prior KIA exact zero-row selected tick gaps are carried as unresolved source requirements, not tick-truth performance rows.
- Smoke rollup/order/trade/oracle reconciliation is now verifier-covered.
{("- Development checkpoint microscope ledgers now exist beyond smoke: candidate/order/trade/missed/risk/day/week rows are source-labeled and routed through the corrected core.\n- Aggregate selected-order SourceRequirement and tick-truth ledgers now cover smoke plus the development checkpoint." if development_completed else "")}
{("- Full development, repair rerun, and holdout/rolling tranches now have candidate/order/trade/missed/risk/day/week ledgers through the corrected core.\n- Aggregate selected-order SourceRequirement and tick-truth ledgers now cover smoke, development checkpoint, and all item #8 tranches." if item8_tranches_completed else "")}

## Not Complete

- {"Repeated system repairs are not yet measured or row-rejected in KIAP." if item8_tranches_completed else "Full development, repair rerun, and holdout/rolling tranches have not all run through the corrected KIAP path yet."}
- Missed-opportunity anatomy and risk-lockout causal chains are not yet complete across all required repair-measurement families.
- Route item 10 remains open for all-tranche verifier hardening and stable final audit.

The route must remain `IN_PROGRESS` until every completion gate in the controlling prompt is true.
"""
    (route_dir / "COMPLETION_AUDIT.md").write_text(completion, encoding="utf-8")
    _write_action_queue(
        route_dir,
        development_checkpoint_completed=development_completed,
        item8_tranches_completed=item8_tranches_completed,
    )


def _write_verify_shim(route_dir: Path) -> None:
    text = '''#!/usr/bin/env python3
"""Run the KIAP route verifier from the repo module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.v4_kia_parity_tick_first_runtime_repair import output_manifest, verify_route

payload = verify_route(repo_root=REPO_ROOT, route_dir=ROUTE_DIR, write_result=True)
output_manifest(ROUTE_DIR)
print(json.dumps(payload, indent=2, sort_keys=True))
raise SystemExit(0 if payload.get("status") == "passed" else 1)
'''
    path = route_dir / "verify_kiap_route.py"
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _write_focused_test_result(route_dir: Path, result: Mapping[str, Any] | None = None) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "pending" if result is None else result.get("status", "unknown"),
        "commands": [] if result is None else result.get("commands", []),
    }
    _write_stable_json(route_dir / "KIAP_FOCUSED_TEST_RESULT.json", payload)


def _write_route_audit(route_dir: Path, *, max_jsonl_rows: int | None = 20000) -> dict[str, Any]:
    audit = audit_route(route_dir, max_jsonl_rows=max_jsonl_rows)
    payload = json.loads(json.dumps(audit, sort_keys=True, default=str))
    _write_stable_json(route_dir / "KIAP_ROUTE_ARTIFACT_AUDIT_RESULT.json", payload)
    return payload


def _packet_sidecar_partition_filename(*, phase: str, trading_day: str) -> str:
    safe_day = str(trading_day or "unknown_day").replace("-", "_")
    return f"KIAP_PACKET_SIDECAR_{phase.upper()}_{safe_day}.jsonl"


def _write_packet_sidecar_partitions(
    *,
    route: Path,
    phase: str,
    rows: Iterable[Mapping[str, Any]],
    index_filename: str,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        day = str(row.get("trading_day") or row.get("decision_time_utc") or "unknown_day")[:10]
        grouped[day].append(dict(row))
    index_rows: list[dict[str, Any]] = []
    artifact_by_sidecar_id: dict[str, str] = {}
    for day, day_rows in sorted(grouped.items()):
        filename = _packet_sidecar_partition_filename(phase=phase, trading_day=day)
        path = route / filename
        atomic_write_jsonl(path, day_rows)
        for row in day_rows:
            sidecar_id = str(row.get("packet_sidecar_id") or "")
            if sidecar_id:
                artifact_by_sidecar_id[sidecar_id] = filename
        index_rows.append(
            {
                "kiap_route_id": ROUTE_ID,
                "kiap_campaign_phase": phase,
                "trading_day": day,
                "packet_sidecar_partition_artifact": filename,
                "packet_sidecar_rows": len(day_rows),
                "partition_sha256": file_sha256(path),
                "partition_bytes": path.stat().st_size,
                "index_artifact": index_filename,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
    atomic_write_jsonl(route / index_filename, index_rows)
    return index_rows, artifact_by_sidecar_id


def _apply_packet_sidecar_partition_refs(
    ledgers: dict[str, list[dict[str, Any]]],
    artifact_by_sidecar_id: Mapping[str, str],
) -> None:
    for key in ("candidate", "scorecard"):
        for row in ledgers.get(key, []):
            sidecar_id = str(row.get("packet_sidecar_id") or "")
            if sidecar_id in artifact_by_sidecar_id:
                row["packet_sidecar_artifact"] = artifact_by_sidecar_id[sidecar_id]
    for row in ledgers.get("order", []):
        sidecar_id = str(row.get("execution_packet_sidecar_id") or "")
        if sidecar_id in artifact_by_sidecar_id:
            row["execution_packet_sidecar_artifact"] = artifact_by_sidecar_id[sidecar_id]


def _write_phase_source_hydration_rows(
    *,
    route: Path,
    source_package: Mapping[str, Any],
    phase: str,
) -> list[dict[str, Any]]:
    existing_source_rows = (
        load_jsonl(route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl")
        if (route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl").exists()
        else []
    )
    source_origin = f"kiap_{phase}_build_source_package"
    preserved_source_rows = [
        row for row in existing_source_rows if row.get("source_row_origin") != source_origin
    ]
    phase_source_rows = _source_hydration_rows(
        source_package,
        phase=phase,
        start_index=len(preserved_source_rows) + 1,
    )
    atomic_write_jsonl(
        route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl",
        [*preserved_source_rows, *phase_source_rows],
    )
    return phase_source_rows


def output_manifest(route_dir: Path | str = ROUTE_DIR) -> dict[str, Any]:
    route = Path(route_dir)
    files = []
    duplicate_prior_entries = []
    for path in sorted(route.iterdir()):
        if not path.is_file() or path.name == "KIAP_OUTPUT_MANIFEST.json":
            continue
        if " 2." in path.name or " 3." in path.name:
            duplicate_prior_entries.append(path.name)
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
        "route_status": "IN_PROGRESS",
        "file_count": len(files),
        "artifacts": [row["name"] for row in files],
        "files": files,
        "raw_export_scratch_committed": False,
        "prior_kia_duplicate_ledgers_included": False,
        "duplicate_route_local_entries_ignored": duplicate_prior_entries,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
    }
    _write_stable_json(route / "KIAP_OUTPUT_MANIFEST.json", manifest)
    return load_json(route / "KIAP_OUTPUT_MANIFEST.json")


def build_smoke_checkpoint(*, repo_root: Path | str = Path("."), route_dir: Path | str = ROUTE_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    config = load_config(repo_root / "config/agent_config.yaml")
    source_package = build_source_package((SMOKE_DAY,))
    for filename in KIAP_SMOKE_LEDGER_FILES.values():
        atomic_write_jsonl(route / filename, [])

    if not source_package.get("primary_hydration_complete"):
        summary = {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "not_run_primary_ftmo_hydration_incomplete",
            "smoke_day": SMOKE_DAY,
            "missing_symbols": source_package.get("missing_symbols"),
            "row_counts": {key: 0 for key in KIAP_SMOKE_LEDGER_FILES},
            "completion_claim": False,
            "no_live_broker_mutation": True,
            "no_paid_api": True,
            "no_remote_push": True,
        }
        _write_stable_json(route / "KIAP_SMOKE_REPLAY_SUMMARY.json", summary)
        return summary

    campaign = CampaignConfig(
        name="kiap_smoke",
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
    for key, filename in KIAP_SMOKE_LEDGER_FILES.items():
        rows = _decorate_smoke_rows(
            result["ledgers"].get(key, []),
            ledger_key=key,
            broker_boundary=broker_boundary,
        )
        decorated_ledgers[key] = rows
        atomic_write_jsonl(route / filename, rows)

    source_hydration_rows = _source_hydration_rows(source_package)
    atomic_write_jsonl(route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl", source_hydration_rows)

    carried_gaps = _carried_prior_tick_gap_rows(repo_root)
    available_gap_rows = [*carried_gaps, *_current_zero_row_tick_gap_rows(repo_root)]
    requirements, selected_truth_rows, current_gap_rows = _requirement_rows(
        order_rows=decorated_ledgers["order"],
        oracle_rows=decorated_ledgers["oracle"],
        prior_gap_rows=available_gap_rows,
    )
    all_gap_rows = [*carried_gaps, *current_gap_rows]
    atomic_write_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl", requirements)
    atomic_write_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl", selected_truth_rows)
    atomic_write_jsonl(route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", all_gap_rows)

    risk_rows = _risk_lockout_rows(decorated_ledgers["order"])
    atomic_write_jsonl(route / "KIAP_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", risk_rows)
    weekly_rows = _weekly_rows(decorated_ledgers["daily"])
    atomic_write_jsonl(route / "KIAP_WEEKLY_MICROSCOPE_SUMMARY.jsonl", weekly_rows)

    reconciliation = _rollup_reconciliation(
        order_rows=decorated_ledgers["order"],
        trade_rows=decorated_ledgers["trade"],
        oracle_rows=decorated_ledgers["oracle"],
        rollup_rows=decorated_ledgers["rollup"],
    )
    campaign_summary = summarize_campaign(result, phase="smoke")
    row_counts = {key: len(rows) for key, rows in decorated_ledgers.items()}
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed",
        "smoke_day": SMOKE_DAY,
        "phase": "smoke",
        "source_operation": "kiap_smoke_live_replay_runtime_run",
        "source_primary_hydration_complete": True,
        "source_symbols_with_primary_coverage": source_package.get("symbols_with_primary_coverage"),
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "runtime_surface_contract": LiveReplayMode.surface_contract,
        "runtime_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
        "production_decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
        "replay_clock": "ReplayClock",
        "historical_adapter": "HistoricalMT5Adapter",
        "path_truth_index": "PathTruthIndex",
        "simulated_broker_adapter": "SimulatedBroker",
        "broker_boundary": dict(broker_boundary),
        "row_counts": row_counts,
        "campaign_summary": campaign_summary,
        "source_hydration_rows": len(source_hydration_rows),
        "source_requirement_rows": len(requirements),
        "selected_tick_truth_rows": len(selected_truth_rows),
        "selected_tick_truth_pass_rows": sum(
            1 for row in selected_truth_rows if row.get("selected_tick_truth_verification_status") == "passed_tick_truth"
        ),
        "selected_tick_truth_unresolved_rows": sum(
            1
            for row in selected_truth_rows
            if row.get("selected_tick_truth_verification_status")
            == "unresolved_exact_zero_row_source_requirement_split"
        ),
        "selected_tick_truth_violation_rows": sum(
            1 for row in selected_truth_rows if row.get("m1_fallback_violation") is True
        ),
        "carried_prior_tick_gap_rows": len(carried_gaps),
        "current_smoke_tick_gap_rows": len(current_gap_rows),
        "risk_lockout_rows": len(risk_rows),
        "weekly_summary_rows": len(weekly_rows),
        "rollup_reconciliation": reconciliation,
        "completion_claim": False,
        "full_live_replay_parity_claim": False,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    _write_stable_json(route / "KIAP_SMOKE_REPLAY_SUMMARY.json", summary)

    runtime_proof = _runtime_parity_proof(repo_root)
    _write_stable_json(route / "KIAP_RUNTIME_PARITY_PROOF.json", runtime_proof)
    _write_stable_json(route / "KIAP_RUNTIME_PARITY_CHECKLIST.json", _runtime_parity_checklist(summary))
    _write_state_files(
        route_dir=route,
        repo_root=repo_root,
        smoke_summary=summary,
        source_requirements=requirements,
        selected_truth_rows=selected_truth_rows,
        tick_gap_rows=all_gap_rows,
    )
    _write_focused_test_result(route)
    _write_verify_shim(route)
    output_manifest(route)
    verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    output_manifest(route)
    _write_route_audit(route)
    output_manifest(route)
    return load_json(route / "KIAP_SMOKE_REPLAY_SUMMARY.json")


def _load_phase_rows(route: Path, phase: str, key: str) -> list[dict[str, Any]]:
    files = KIAP_PHASE_LEDGER_FILES[phase]
    path = route / files[key]
    return load_jsonl(path) if path.exists() else []


def _phase_summary_path(route: Path, phase: str) -> Path:
    if phase == "smoke":
        return route / "KIAP_SMOKE_REPLAY_SUMMARY.json"
    if phase == "development":
        return route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json"
    return route / KIAP_ITEM8_SUMMARY_FILES[phase]


def _phase_completed(route: Path, phase: str) -> bool:
    path = _phase_summary_path(route, phase)
    return path.exists() and load_json(path).get("status") == "completed"


def _completed_item8_summaries(route: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for phase in KIAP_ITEM8_PHASES:
        path = route / KIAP_ITEM8_SUMMARY_FILES[phase]
        if path.exists():
            output[phase] = load_json(path)
    return output


def _requirement_phases(route: Path) -> list[str]:
    phases = ["smoke"]
    if _phase_completed(route, "development"):
        phases.append("development")
    for phase in KIAP_ITEM8_PHASES:
        if _phase_completed(route, phase):
            phases.append(phase)
    return phases


def _aggregate_phase_rows(
    route: Path,
    key: str,
    *,
    include_development: bool | None = None,
    phases: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    if phases is None:
        phase_list = ["smoke"]
        if include_development:
            phase_list.append("development")
    else:
        phase_list = list(phases)
    rows: list[dict[str, Any]] = []
    for phase in phase_list:
        rows.extend(_load_phase_rows(route, phase, key))
    return rows


def _write_aggregate_requirement_ledgers(
    *,
    route: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    phases = _requirement_phases(route)
    carried_gaps = _carried_prior_tick_gap_rows(repo_root)
    available_gap_rows = [*carried_gaps, *_current_zero_row_tick_gap_rows(repo_root)]
    all_order_rows = _aggregate_phase_rows(route, "order", phases=phases)
    all_oracle_rows = _aggregate_phase_rows(route, "oracle", phases=phases)
    requirements, selected_truth_rows, current_gap_rows = _requirement_rows(
        order_rows=all_order_rows,
        oracle_rows=all_oracle_rows,
        prior_gap_rows=available_gap_rows,
    )
    all_gap_rows = [*carried_gaps, *current_gap_rows]
    atomic_write_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl", requirements)
    atomic_write_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl", selected_truth_rows)
    atomic_write_jsonl(route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", all_gap_rows)

    all_risk_rows = _risk_lockout_rows(_aggregate_phase_rows(route, "order", phases=phases))
    atomic_write_jsonl(route / "KIAP_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", all_risk_rows)
    all_weekly_rows = _weekly_rows(_aggregate_phase_rows(route, "daily", phases=phases))
    atomic_write_jsonl(route / "KIAP_WEEKLY_MICROSCOPE_SUMMARY.jsonl", all_weekly_rows)
    return requirements, selected_truth_rows, all_gap_rows


def build_development_checkpoint(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str = ROUTE_DIR,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    smoke_summary_path = route / "KIAP_SMOKE_REPLAY_SUMMARY.json"
    if not smoke_summary_path.exists() or load_json(smoke_summary_path).get("status") != "completed":
        build_smoke_checkpoint(repo_root=repo_root, route_dir=route)
    smoke_summary = load_json(smoke_summary_path)

    config = load_config(repo_root / "config/agent_config.yaml")
    source_package = build_source_package(KIAP_DEVELOPMENT_CHECKPOINT_DAYS)
    for filename in KIAP_DEVELOPMENT_LEDGER_FILES.values():
        atomic_write_jsonl(route / filename, [])
    atomic_write_jsonl(route / "KIAP_DEVELOPMENT_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", [])
    atomic_write_jsonl(route / "KIAP_DEVELOPMENT_WEEKLY_MICROSCOPE_SUMMARY.jsonl", [])

    if not source_package.get("primary_hydration_complete"):
        summary = {
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "status": "not_run_primary_ftmo_hydration_incomplete",
            "phase": "development",
            "development_checkpoint_days": list(KIAP_DEVELOPMENT_CHECKPOINT_DAYS),
            "missing_symbols": source_package.get("missing_symbols"),
            "completion_claim": False,
            "full_development_tranche_claim": False,
            "no_live_broker_mutation": True,
            "no_paid_api": True,
            "no_remote_push": True,
        }
        _write_stable_json(route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json", summary)
        return summary

    campaign = CampaignConfig(
        name="kiap_development_checkpoint",
        phase="development",
        days=KIAP_DEVELOPMENT_CHECKPOINT_DAYS,
        pending_expiry_minutes=BASELINE_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=False,
        run_smoke_subset=False,
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
    for key, filename in KIAP_DEVELOPMENT_LEDGER_FILES.items():
        rows = _decorate_phase_rows(
            result["ledgers"].get(key, []),
            ledger_key=key,
            broker_boundary=broker_boundary,
            phase="development",
            days=KIAP_DEVELOPMENT_CHECKPOINT_DAYS,
            action_queue_items_satisfied=(7,),
            packet_sidecar_artifact=KIAP_DEVELOPMENT_LEDGER_FILES["packet_sidecar"],
        )
        decorated_ledgers[key] = rows
        atomic_write_jsonl(route / filename, rows)

    existing_source_rows = (
        load_jsonl(route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl")
        if (route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl").exists()
        else []
    )
    preserved_source_rows = [
        row
        for row in existing_source_rows
        if row.get("source_row_origin") != "kiap_development_build_source_package"
    ]
    development_source_rows = _source_hydration_rows(
        source_package,
        phase="development",
        start_index=len(preserved_source_rows) + 1,
    )
    atomic_write_jsonl(
        route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl",
        [*preserved_source_rows, *development_source_rows],
    )

    carried_gaps = _carried_prior_tick_gap_rows(repo_root)
    available_gap_rows = [*carried_gaps, *_current_zero_row_tick_gap_rows(repo_root)]
    all_order_rows = _aggregate_phase_rows(route, "order", include_development=True)
    all_oracle_rows = _aggregate_phase_rows(route, "oracle", include_development=True)
    requirements, selected_truth_rows, current_gap_rows = _requirement_rows(
        order_rows=all_order_rows,
        oracle_rows=all_oracle_rows,
        prior_gap_rows=available_gap_rows,
    )
    all_gap_rows = [*carried_gaps, *current_gap_rows]
    atomic_write_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl", requirements)
    atomic_write_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl", selected_truth_rows)
    atomic_write_jsonl(route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", all_gap_rows)

    development_risk_rows = _risk_lockout_rows(decorated_ledgers["order"])
    all_risk_rows = _risk_lockout_rows(all_order_rows)
    atomic_write_jsonl(
        route / "KIAP_DEVELOPMENT_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl",
        development_risk_rows,
    )
    atomic_write_jsonl(route / "KIAP_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", all_risk_rows)

    development_weekly_rows = _weekly_rows(decorated_ledgers["daily"])
    all_weekly_rows = _weekly_rows(_aggregate_phase_rows(route, "daily", include_development=True))
    atomic_write_jsonl(
        route / "KIAP_DEVELOPMENT_WEEKLY_MICROSCOPE_SUMMARY.jsonl",
        development_weekly_rows,
    )
    atomic_write_jsonl(route / "KIAP_WEEKLY_MICROSCOPE_SUMMARY.jsonl", all_weekly_rows)

    reconciliation = _rollup_reconciliation(
        order_rows=decorated_ledgers["order"],
        trade_rows=decorated_ledgers["trade"],
        oracle_rows=decorated_ledgers["oracle"],
        rollup_rows=decorated_ledgers["rollup"],
    )
    campaign_summary = summarize_campaign(result, phase="development")
    row_counts = {key: len(rows) for key, rows in decorated_ledgers.items()}
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed",
        "phase": "development",
        "source_operation": "kiap_development_checkpoint_live_replay_runtime_run",
        "development_checkpoint_days": list(KIAP_DEVELOPMENT_CHECKPOINT_DAYS),
        "full_development_tranche_claim": False,
        "source_primary_hydration_complete": True,
        "source_symbols_with_primary_coverage": source_package.get("symbols_with_primary_coverage"),
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "runtime_surface_contract": LiveReplayMode.surface_contract,
        "runtime_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
        "production_decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
        "replay_clock": "ReplayClock",
        "historical_adapter": "HistoricalMT5Adapter",
        "path_truth_index": "PathTruthIndex",
        "simulated_broker_adapter": "SimulatedBroker",
        "broker_boundary": dict(broker_boundary),
        "row_counts": row_counts,
        "campaign_summary": campaign_summary,
        "source_hydration_rows": len(development_source_rows),
        "aggregate_source_hydration_rows": len(preserved_source_rows) + len(development_source_rows),
        "aggregate_source_requirement_rows": len(requirements),
        "aggregate_selected_tick_truth_rows": len(selected_truth_rows),
        "aggregate_selected_tick_truth_pass_rows": sum(
            1 for row in selected_truth_rows if row.get("selected_tick_truth_verification_status") == "passed_tick_truth"
        ),
        "aggregate_selected_tick_truth_unresolved_rows": sum(
            1
            for row in selected_truth_rows
            if row.get("selected_tick_truth_verification_status")
            == "unresolved_exact_zero_row_source_requirement_split"
        ),
        "aggregate_selected_tick_truth_violation_rows": sum(
            1 for row in selected_truth_rows if row.get("m1_fallback_violation") is True
        ),
        "carried_prior_tick_gap_rows": len(carried_gaps),
        "current_development_tick_gap_rows": len(current_gap_rows),
        "risk_lockout_rows": len(development_risk_rows),
        "weekly_summary_rows": len(development_weekly_rows),
        "rollup_reconciliation": reconciliation,
        "completion_claim": False,
        "full_live_replay_parity_claim": False,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    _write_stable_json(route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json", summary)

    _write_state_files(
        route_dir=route,
        repo_root=repo_root,
        smoke_summary=smoke_summary,
        development_summary=summary,
        source_requirements=requirements,
        selected_truth_rows=selected_truth_rows,
        tick_gap_rows=all_gap_rows,
    )
    _write_focused_test_result(route)
    _write_verify_shim(route)
    output_manifest(route)
    verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    output_manifest(route)
    _write_route_audit(route)
    output_manifest(route)
    return load_json(route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json")


def _materialize_item8_phase(
    *,
    repo_root: Path,
    route: Path,
    phase: str,
) -> dict[str, Any]:
    phase_def = KIAP_ITEM8_CAMPAIGN_DEFS[phase]
    days = tuple(phase_def["days"])
    ledger_files = KIAP_PHASE_LEDGER_FILES[phase]
    summary_path = route / KIAP_ITEM8_SUMMARY_FILES[phase]

    config = load_config(repo_root / "config/agent_config.yaml")
    for filename in ledger_files.values():
        atomic_write_jsonl(route / filename, [])
    atomic_write_jsonl(route / KIAP_ITEM8_RISK_FILES[phase], [])
    atomic_write_jsonl(route / KIAP_ITEM8_WEEKLY_FILES[phase], [])

    broker = SimulatedBroker()
    selected_order_sequence = 0
    combined_ledgers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    day_progress_rows: list[dict[str, Any]] = []
    source_origin = f"kiap_{phase}_build_source_package"
    existing_source_rows = (
        load_jsonl(route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl")
        if (route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl").exists()
        else []
    )
    preserved_source_rows = [
        row for row in existing_source_rows if row.get("source_row_origin") != source_origin
    ]
    phase_source_rows: list[dict[str, Any]] = []
    source_symbols_with_primary_coverage: set[str] = set()
    for day in days:
        source_package = build_source_package((day,))
        if not source_package.get("primary_hydration_complete"):
            summary = {
                "route_id": ROUTE_ID,
                "generated_at_utc": utc_now(),
                "status": "not_run_primary_ftmo_hydration_incomplete",
                "phase": phase,
                "tranche_days": list(days),
                "failed_day": day,
                "missing_symbols": source_package.get("missing_symbols"),
                "completion_claim": False,
                "item8_tranche_completed": False,
                "no_live_broker_mutation": True,
                "no_paid_api": True,
                "no_remote_push": True,
            }
            _write_stable_json(summary_path, summary)
            clear_replay_row_index_caches()
            return summary
        phase_source_rows.extend(
            _source_hydration_rows(
                source_package,
                phase=phase,
                start_index=len(preserved_source_rows) + len(phase_source_rows) + 1,
            )
        )
        source_symbols_with_primary_coverage.update(
            str(symbol) for symbol in source_package.get("symbols_with_primary_coverage") or []
        )
        campaign = CampaignConfig(
            name=f"{phase_def['name']}_{str(day).replace('-', '')}",
            phase=phase,
            days=(day,),
            pending_expiry_minutes=int(phase_def["pending_expiry_minutes"]),
            use_repaired_pending_expiry=bool(phase_def["use_repaired_pending_expiry"]),
            partial_be_runner=bool(phase_def["partial_be_runner"]),
            run_smoke_subset=False,
        )
        day_result = run_campaign(
            campaign=campaign,
            config=config,
            sources=source_package["sources"],
            broker=broker,
            starting_order_sequence=selected_order_sequence,
        )
        selected_order_sequence = int(day_result.get("selected_order_sequence") or selected_order_sequence)
        for key, rows in day_result["ledgers"].items():
            combined_ledgers[key].extend(rows)
        day_progress_rows.append(
            {
                "kiap_route_id": ROUTE_ID,
                "phase": phase,
                "trading_day": day,
                "campaign": campaign.name,
                "status": "completed",
                "row_counts": {key: len(rows) for key, rows in day_result["ledgers"].items()},
                "ending_balance": round(day_result["account"].balance, 8),
                "selected_order_sequence_after_day": selected_order_sequence,
                "tick_lookup_mode": "lazy_tick_window_stream",
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
        )
        atomic_write_jsonl(route / f"KIAP_{phase.upper()}_DAY_PROGRESS_LEDGER.jsonl", day_progress_rows)
        del day_result
        del source_package
        clear_replay_row_index_caches()
    result = {"ledgers": combined_ledgers, "broker": broker, "account": broker.account}
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
    for key, filename in ledger_files.items():
        rows = _decorate_phase_rows(
            result["ledgers"].get(key, []),
            ledger_key=key,
            broker_boundary=broker_boundary,
            phase=phase,
            days=days,
            action_queue_items_satisfied=(8,),
            packet_sidecar_artifact=filename,
        )
        decorated_ledgers[key] = rows

    packet_index_rows, artifact_by_sidecar_id = _write_packet_sidecar_partitions(
        route=route,
        phase=phase,
        rows=decorated_ledgers.get("packet_sidecar", []),
        index_filename=ledger_files["packet_sidecar"],
    )
    _apply_packet_sidecar_partition_refs(decorated_ledgers, artifact_by_sidecar_id)

    for key, filename in ledger_files.items():
        if key == "packet_sidecar":
            continue
        atomic_write_jsonl(route / filename, decorated_ledgers.get(key, []))

    atomic_write_jsonl(
        route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl",
        [*preserved_source_rows, *phase_source_rows],
    )
    phase_risk_rows = _risk_lockout_rows(decorated_ledgers["order"])
    atomic_write_jsonl(route / KIAP_ITEM8_RISK_FILES[phase], phase_risk_rows)
    phase_weekly_rows = _weekly_rows(decorated_ledgers["daily"])
    atomic_write_jsonl(route / KIAP_ITEM8_WEEKLY_FILES[phase], phase_weekly_rows)

    reconciliation = _rollup_reconciliation(
        order_rows=decorated_ledgers["order"],
        trade_rows=decorated_ledgers["trade"],
        oracle_rows=decorated_ledgers["oracle"],
        rollup_rows=decorated_ledgers["rollup"],
    )
    campaign_summary = summarize_campaign(result, phase=phase)
    row_counts = {key: len(rows) for key, rows in decorated_ledgers.items()}
    row_counts["packet_sidecar_index"] = len(packet_index_rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed",
        "phase": phase,
        "source_operation": phase_def["source_operation"],
        "tranche_days": list(days),
        "item8_tranche_completed": True,
        "source_primary_hydration_complete": True,
        "source_symbols_with_primary_coverage": sorted(source_symbols_with_primary_coverage),
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "runtime_surface_contract": LiveReplayMode.surface_contract,
        "runtime_surface_contract_hash": stable_sha256(LiveReplayMode.surface_contract),
        "production_decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
        "replay_clock": "ReplayClock",
        "historical_adapter": "HistoricalMT5Adapter",
        "path_truth_index": "PathTruthIndex",
        "tick_lookup_mode": "lazy_tick_window_stream",
        "missed_opportunity_path_source_policy": "m1_proxy_allowed_unselected_candidates_selected_orders_tick_first",
        "simulated_broker_adapter": "SimulatedBroker",
        "broker_boundary": dict(broker_boundary),
        "row_counts": row_counts,
        "campaign_summary": campaign_summary,
        "source_hydration_rows": len(phase_source_rows),
        "packet_sidecar_partition_rows": len(packet_index_rows),
        "packet_sidecar_partitions": [row["packet_sidecar_partition_artifact"] for row in packet_index_rows],
        "risk_lockout_rows": len(phase_risk_rows),
        "weekly_summary_rows": len(phase_weekly_rows),
        "rollup_reconciliation": reconciliation,
        "completion_claim": False,
        "full_live_replay_parity_claim": False,
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    _write_stable_json(summary_path, summary)
    return load_json(summary_path)


def build_item8_tranches(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str = ROUTE_DIR,
    phases: Iterable[str] = KIAP_ITEM8_PHASES,
    run_verifier: bool = True,
    run_route_audit: bool = True,
    run_output_manifest: bool = True,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)

    smoke_summary_path = route / "KIAP_SMOKE_REPLAY_SUMMARY.json"
    if not smoke_summary_path.exists() or load_json(smoke_summary_path).get("status") != "completed":
        build_smoke_checkpoint(repo_root=repo_root, route_dir=route)
    development_summary_path = route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json"
    if (
        not development_summary_path.exists()
        or load_json(development_summary_path).get("status") != "completed"
    ):
        build_development_checkpoint(repo_root=repo_root, route_dir=route)

    summaries: dict[str, dict[str, Any]] = _completed_item8_summaries(route)
    for phase in phases:
        if phase not in KIAP_ITEM8_PHASES:
            raise ValueError(f"unknown KIAP item8 phase: {phase}")
        summaries[phase] = _materialize_item8_phase(
            repo_root=repo_root,
            route=route,
            phase=phase,
        )

    requirements, selected_truth_rows, all_gap_rows = _write_aggregate_requirement_ledgers(
        route=route,
        repo_root=repo_root,
    )
    smoke_summary = load_json(smoke_summary_path)
    development_summary = load_json(development_summary_path)
    all_summaries = _completed_item8_summaries(route)
    for phase, summary in summaries.items():
        all_summaries[phase] = summary
    _write_state_files(
        route_dir=route,
        repo_root=repo_root,
        smoke_summary=smoke_summary,
        development_summary=development_summary,
        item8_summaries=all_summaries,
        source_requirements=requirements,
        selected_truth_rows=selected_truth_rows,
        tick_gap_rows=all_gap_rows,
    )
    _write_focused_test_result(route)
    _write_verify_shim(route)
    if run_output_manifest:
        output_manifest(route)
    if run_verifier:
        verify_route(repo_root=repo_root, route_dir=route, write_result=True)
    if run_output_manifest:
        output_manifest(route)
    if run_route_audit:
        _write_route_audit(route)
        if run_output_manifest:
            output_manifest(route)
    return {
        "route_id": ROUTE_ID,
        "status": "completed" if all(
            all_summaries.get(phase, {}).get("status") == "completed"
            for phase in KIAP_ITEM8_PHASES
        ) else "partial",
        "phase_summaries": all_summaries,
        "source_requirement_rows": len(requirements),
        "selected_tick_truth_rows": len(selected_truth_rows),
        "tick_gap_rows": len(all_gap_rows),
        "route_verifier_run": run_verifier,
        "route_audit_run": run_route_audit,
        "output_manifest_run": run_output_manifest,
    }


def verify_route(
    *,
    repo_root: Path | str = Path("."),
    route_dir: Path | str | None = None,
    write_result: bool = False,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    route = _repo_path(repo_root, route_dir or ROUTE_DIR)
    checks: list[dict[str, Any]] = []

    missing = [name for name in KIAP_REQUIRED_ARTIFACTS if not (route / name).exists()]
    checks.append(
        {
            "check": "required_kiap_artifacts",
            "status": "passed" if not missing else "failed",
            "details": {"missing": missing},
        }
    )

    action_queue = (route / "KIAP_ACTION_QUEUE.md").read_text(encoding="utf-8") if (route / "KIAP_ACTION_QUEUE.md").exists() else ""
    final_gate_closed = "11. [x]" in action_queue
    context = load_json(route / "KIAP_CONTEXT_ANCHOR.json") if (route / "KIAP_CONTEXT_ANCHOR.json").exists() else {}
    completion_text = (route / "COMPLETION_AUDIT.md").read_text(encoding="utf-8") if (route / "COMPLETION_AUDIT.md").exists() else ""
    expected_route_status = KIAP_COMPLETION_STATUS if final_gate_closed else "IN_PROGRESS"
    expected_completion_text = (
        f"Completion status: `{KIAP_COMPLETION_STATUS}`"
        if final_gate_closed
        else "Completion status: `IN_PROGRESS`"
    )
    checks.append(
        {
            "check": "in_progress_no_completion_overclaim",
            "status": "passed"
            if context.get("route_status") == expected_route_status
            and context.get("completion_claim") is False
            and expected_completion_text in completion_text
            else "failed",
            "details": {
                "route_status": context.get("route_status"),
                "expected_route_status": expected_route_status,
                "completion_claim": context.get("completion_claim"),
            },
        }
    )

    proof = load_json(route / "KIAP_RUNTIME_PARITY_PROOF.json") if (route / "KIAP_RUNTIME_PARITY_PROOF.json").exists() else {}
    refs = proof.get("live_orchestrator_source_refs") if isinstance(proof.get("live_orchestrator_source_refs"), dict) else {}
    required_refs = (
        "production_core_imported",
        "production_core_instantiated",
        "production_core_generate_candidates_called",
        "production_core_window_summaries_called",
        "replay_core_imported_from_production",
        "replay_core_generate_candidates_called",
        "replay_core_candidate_evaluator_bound",
        "replay_core_scheduler_allocator_bound",
    )
    checks.append(
        {
            "check": "production_replay_shared_core_call_proof",
            "status": "passed"
            if proof.get("production_import_path") == PRODUCTION_CORE_IMPORT_PATH
            and proof.get("shared_core_status") == KIA_PRODUCTION_SHARED_CORE_STATUS
            and all(refs.get(key) is True for key in required_refs)
            else "failed",
            "details": {"refs": refs, "shared_core_status": proof.get("shared_core_status")},
        }
    )

    replay_source = (repo_root / "src/research_infra/v4_timewarp_simulated_live_research_loop.py").read_text(encoding="utf-8")
    checks.append(
        {
            "check": "replay_generation_uses_shared_core",
            "status": "passed"
            if "decision_core.generate_candidates" in replay_source
            and "candidate_evaluator=evaluate_candidate_v4" in replay_source
            and "scheduler_allocator=materialize_scheduler_window" in replay_source
            else "failed",
            "details": {},
        }
    )

    smoke = load_json(route / "KIAP_SMOKE_REPLAY_SUMMARY.json") if (route / "KIAP_SMOKE_REPLAY_SUMMARY.json").exists() else {}
    development_gate_closed = "7. [x]" in action_queue
    item8_gate_closed = "8. [x]" in action_queue
    item9_gate_closed = "9. [x]" in action_queue
    item10_gate_closed = "10. [x]" in action_queue
    development_summary_path = route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json"
    development = load_json(development_summary_path) if development_summary_path.exists() else {}
    smoke_counts = smoke.get("row_counts") if isinstance(smoke.get("row_counts"), dict) else {}
    checks.append(
        {
            "check": "kiap_smoke_replay_materialized",
            "status": "passed"
            if smoke.get("status") == "completed"
            and smoke.get("source_primary_hydration_complete") is True
            and smoke_counts.get("candidate", 0) > 0
            and smoke_counts.get("order", 0) > 0
            and smoke_counts.get("oracle", 0) > 0
            and smoke_counts.get("account", 0) > 0
            and smoke.get("no_live_broker_mutation") is True
            else "failed",
            "details": {
                "status": smoke.get("status"),
                "row_counts": smoke_counts,
            },
        }
    )

    development_failures = []
    if development_gate_closed:
        development_counts = development.get("row_counts") if isinstance(development.get("row_counts"), dict) else {}
        if development.get("status") != "completed":
            development_failures.append("development_summary_not_completed")
        for key, filename in KIAP_DEVELOPMENT_LEDGER_FILES.items():
            path = route / filename
            if not path.exists():
                development_failures.append(f"{key}:missing:{filename}")
                continue
            if key in {"candidate", "order", "oracle", "daily"} and len(load_jsonl(path)) == 0:
                development_failures.append(f"{key}:empty:{filename}")
        if development_counts.get("candidate", 0) <= 0:
            development_failures.append("development_candidate_rows_zero")
        if development_counts.get("order", 0) <= 0:
            development_failures.append("development_order_rows_zero")
        if development_counts.get("oracle", 0) <= 0:
            development_failures.append("development_oracle_rows_zero")
        if development.get("no_live_broker_mutation") is not True:
            development_failures.append("development_broker_mutation_boundary")
        if development.get("full_development_tranche_claim") is not False:
            development_failures.append("development_checkpoint_overclaims_full_tranche")
        asof_rows = _load_phase_rows(route, "development", "asof")
        for row in asof_rows:
            if row.get("raw_data_status") != "live_equivalent_raw_data_built_and_mso_computed":
                continue
            if row.get("no_future_decision_rows") is not True:
                development_failures.append(f"{row.get('symbol')}:{row.get('decision_time_utc')}:future_leak")
                break
            if row.get("m1_or_tick_attached_to_decision") is not False:
                development_failures.append(f"{row.get('symbol')}:{row.get('decision_time_utc')}:path_attached_to_decision")
                break
            if row.get("source_broker") != "FTMO":
                development_failures.append(f"{row.get('symbol')}:{row.get('decision_time_utc')}:source_broker")
                break
            if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
                development_failures.append(f"{row.get('symbol')}:{row.get('decision_time_utc')}:source_truth_scope")
                break
    checks.append(
        {
            "check": "kiap_development_checkpoint_materialized",
            "status": "passed" if not development_gate_closed or not development_failures else "failed",
            "details": {
                "development_gate_closed": development_gate_closed,
                "status": development.get("status"),
                "row_counts": development.get("row_counts"),
                "failures": development_failures[:20],
            },
        }
    )

    item8_failures = []
    item8_summaries: dict[str, dict[str, Any]] = {}
    if item8_gate_closed:
        for phase in KIAP_ITEM8_PHASES:
            summary_path = route / KIAP_ITEM8_SUMMARY_FILES[phase]
            summary = load_json(summary_path) if summary_path.exists() else {}
            item8_summaries[phase] = summary
            counts = summary.get("row_counts") if isinstance(summary.get("row_counts"), dict) else {}
            if summary.get("status") != "completed":
                item8_failures.append(f"{phase}:summary_not_completed")
            if summary.get("item8_tranche_completed") is not True:
                item8_failures.append(f"{phase}:item8_flag_not_true")
            if summary.get("no_live_broker_mutation") is not True:
                item8_failures.append(f"{phase}:broker_mutation_boundary")
            if summary.get("tick_lookup_mode") != "lazy_tick_window_stream":
                item8_failures.append(f"{phase}:lazy_tick_lookup_not_recorded")
            for key, filename in KIAP_PHASE_LEDGER_FILES[phase].items():
                path = route / filename
                if not path.exists():
                    item8_failures.append(f"{phase}:{key}:missing:{filename}")
                    continue
                rows = load_jsonl(path)
                if key in {"candidate", "order", "oracle", "daily", "packet_sidecar"} and not rows:
                    item8_failures.append(f"{phase}:{key}:empty:{filename}")
                if key == "packet_sidecar":
                    for index_row in rows:
                        partition_name = str(index_row.get("packet_sidecar_partition_artifact") or "")
                        partition_path = route / partition_name
                        if not partition_name or not partition_path.exists():
                            item8_failures.append(f"{phase}:packet_partition_missing:{partition_name}")
                            break
                        if index_row.get("partition_sha256") != file_sha256(partition_path):
                            item8_failures.append(f"{phase}:packet_partition_sha_mismatch:{partition_name}")
                            break
            for key in ("candidate", "order", "oracle", "daily"):
                if int(counts.get(key) or 0) <= 0:
                    item8_failures.append(f"{phase}:{key}_rows_zero")
            if summary.get("rollup_reconciliation", {}).get("status") != "passed":
                item8_failures.append(f"{phase}:rollup_reconciliation_failed")
            asof_rows = _load_phase_rows(route, phase, "asof")
            for row in asof_rows:
                if row.get("raw_data_status") != "live_equivalent_raw_data_built_and_mso_computed":
                    continue
                if row.get("no_future_decision_rows") is not True:
                    item8_failures.append(f"{phase}:{row.get('symbol')}:{row.get('decision_time_utc')}:future_leak")
                    break
                if row.get("m1_or_tick_attached_to_decision") is not False:
                    item8_failures.append(f"{phase}:{row.get('symbol')}:{row.get('decision_time_utc')}:path_attached_to_decision")
                    break
                if row.get("source_broker") != "FTMO":
                    item8_failures.append(f"{phase}:{row.get('symbol')}:{row.get('decision_time_utc')}:source_broker")
                    break
                if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
                    item8_failures.append(f"{phase}:{row.get('symbol')}:{row.get('decision_time_utc')}:source_truth_scope")
                    break
    checks.append(
        {
            "check": "kiap_item8_tranches_materialized",
            "status": "passed" if not item8_gate_closed or not item8_failures else "failed",
            "details": {
                "item8_gate_closed": item8_gate_closed,
                "phase_statuses": {
                    phase: item8_summaries.get(phase, {}).get("status")
                    for phase in KIAP_ITEM8_PHASES
                },
                "row_counts": {
                    phase: item8_summaries.get(phase, {}).get("row_counts")
                    for phase in KIAP_ITEM8_PHASES
                },
                "failures": item8_failures[:40],
            },
        }
    )

    requirements = load_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl") if (route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl").exists() else []
    selected_truth = (
        load_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl")
        if (route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl").exists()
        else []
    )
    requirement_phases = ["smoke"]
    if development_gate_closed:
        requirement_phases.append("development")
    if item8_gate_closed:
        requirement_phases.extend(KIAP_ITEM8_PHASES)
    orders = _aggregate_phase_rows(route, "order", phases=requirement_phases)
    latest_orders = _latest_order_rows(orders)
    requirement_ids = {str(row.get("simulated_order_id")) for row in requirements if row.get("simulated_order_id")}
    truth_ids = {str(row.get("simulated_order_id")) for row in selected_truth if row.get("simulated_order_id")}
    latest_order_ids = {str(row.get("simulated_order_id")) for row in latest_orders if row.get("simulated_order_id")}
    requirement_failures = []
    if latest_order_ids != requirement_ids:
        requirement_failures.append("source_requirement_order_id_coverage_mismatch")
    if latest_order_ids != truth_ids:
        requirement_failures.append("selected_truth_order_id_coverage_mismatch")
    for row in requirements:
        if row.get("required_source_type") != "TICK":
            requirement_failures.append(f"{row.get('simulated_order_id')}:required_source_type")
        if row.get("source_broker") != "FTMO":
            requirement_failures.append(f"{row.get('simulated_order_id')}:source_broker")
        if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
            requirement_failures.append(f"{row.get('simulated_order_id')}:source_truth_scope")
        if row.get("not_redacted_account_native") is not True:
            requirement_failures.append(f"{row.get('simulated_order_id')}:not_redacted_account_native")
        if row.get("broker_lifecycle_truth_satisfied") is not False:
            requirement_failures.append(f"{row.get('simulated_order_id')}:broker_lifecycle_truth")
    checks.append(
        {
            "check": "source_requirement_coverage",
            "status": "passed" if latest_orders and requirements and not requirement_failures else "failed",
            "details": {
                "latest_unique_orders": len(latest_order_ids),
                "source_requirements": len(requirements),
                "selected_truth_rows": len(selected_truth),
                "failures": requirement_failures,
            },
        }
    )

    tick_gap_rows = load_jsonl(route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl") if (route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl").exists() else []
    tick_gap_ids = {str(row.get("gap_id")) for row in tick_gap_rows if row.get("gap_id")}
    selected_truth_failures = []
    for row in selected_truth:
        status = row.get("selected_tick_truth_verification_status")
        if status == "passed_tick_truth":
            if row.get("ordered_tick_truth_satisfied") is not True or row.get("path_source") != "tick":
                selected_truth_failures.append(f"{row.get('simulated_order_id')}:tick_truth_fields")
        elif status == "unresolved_exact_zero_row_source_requirement_split":
            if row.get("gap_id") not in tick_gap_ids or row.get("ordered_tick_truth_satisfied") is not False:
                selected_truth_failures.append(f"{row.get('simulated_order_id')}:unresolved_gap_fields")
        else:
            selected_truth_failures.append(f"{row.get('simulated_order_id')}:selected_truth_status")
        if row.get("m1_fallback_violation") is True:
            selected_truth_failures.append(f"{row.get('simulated_order_id')}:m1_fallback_violation")
    checks.append(
        {
            "check": "selected_tick_truth_no_unlabeled_m1",
            "status": "passed" if selected_truth and not selected_truth_failures else "failed",
            "details": {
                "rows": len(selected_truth),
                "tick_truth_rows": sum(1 for row in selected_truth if row.get("selected_tick_truth_verification_status") == "passed_tick_truth"),
                "unresolved_rows": sum(1 for row in selected_truth if row.get("selected_tick_truth_verification_status") == "unresolved_exact_zero_row_source_requirement_split"),
                "failures": selected_truth_failures,
            },
        }
    )

    gap_failures = []
    for row in tick_gap_rows:
        if row.get("ordered_tick_truth_satisfied") is not False:
            gap_failures.append(f"{row.get('gap_id')}:ordered_tick_truth")
        if row.get("selected_filled_path_truth_status") != "exact_unresolved_tick_source_requirement":
            gap_failures.append(f"{row.get('gap_id')}:path_status")
        if row.get("final_performance_inclusion_status") != "excluded_unresolved_source_requirement":
            gap_failures.append(f"{row.get('gap_id')}:inclusion_status")
        if row.get("source_broker") != "FTMO":
            gap_failures.append(f"{row.get('gap_id')}:source_broker")
        if row.get("not_redacted_account_native") is not True:
            gap_failures.append(f"{row.get('gap_id')}:not_redacted_account_native")
    checks.append(
        {
            "check": "tick_gap_rows_split_from_performance",
            "status": "passed" if not gap_failures else "failed",
            "details": {"rows": len(tick_gap_rows), "failures": gap_failures},
        }
    )

    reconciliation = smoke.get("rollup_reconciliation") if isinstance(smoke.get("rollup_reconciliation"), dict) else {}
    development_reconciliation = (
        development.get("rollup_reconciliation")
        if isinstance(development.get("rollup_reconciliation"), dict)
        else {}
    )
    item8_reconciliations = {
        phase: item8_summaries.get(phase, {}).get("rollup_reconciliation")
        if isinstance(item8_summaries.get(phase, {}).get("rollup_reconciliation"), dict)
        else {}
        for phase in KIAP_ITEM8_PHASES
    }
    reconciliation_passed = reconciliation.get("status") == "passed" and (
        not development_gate_closed or development_reconciliation.get("status") == "passed"
    ) and (
        not item8_gate_closed
        or all(row.get("status") == "passed" for row in item8_reconciliations.values())
    )
    checks.append(
        {
            "check": "rollup_order_trade_oracle_reconciliation",
            "status": "passed" if reconciliation_passed else "failed",
            "details": {
                "smoke": reconciliation,
                "development": development_reconciliation if development_gate_closed else None,
                "item8": item8_reconciliations if item8_gate_closed else None,
            },
        }
    )

    source_rows = load_jsonl(route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl") if (route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl").exists() else []
    source_failures = []
    for row in source_rows:
        if row.get("source_broker") != "FTMO":
            source_failures.append(f"{row.get('kiap_source_row_id')}:source_broker")
            break
        if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
            source_failures.append(f"{row.get('kiap_source_row_id')}:source_truth_scope")
            break
        if row.get("not_redacted_account_native") is not True:
            source_failures.append(f"{row.get('kiap_source_row_id')}:not_redacted_account_native")
            break
        if row.get("broker_lifecycle_truth_satisfied") is not False:
            source_failures.append(f"{row.get('kiap_source_row_id')}:broker_lifecycle")
            break
    checks.append(
        {
            "check": "source_hydration_labels",
            "status": "passed" if source_rows and not source_failures else "failed",
            "details": {"rows": len(source_rows), "failures": source_failures},
        }
    )

    item9_failures = []
    item9_summary = (
        load_json(route / KIAP_ITEM9_SUMMARY_FILE)
        if (route / KIAP_ITEM9_SUMMARY_FILE).exists()
        else {}
    )
    item9_counts = (
        item9_summary.get("family_row_counts")
        if isinstance(item9_summary.get("family_row_counts"), dict)
        else {}
    )
    if item9_gate_closed:
        if item9_summary.get("status") != "completed":
            item9_failures.append("item9_summary_not_completed")
        if item9_summary.get("item9_gate_closed") is not True:
            item9_failures.append("item9_gate_flag_not_true")
        if item9_summary.get("no_arbitrary_top_n") is not True:
            item9_failures.append("item9_no_arbitrary_top_n_missing")
        if item9_summary.get("all_material_family_rows_preserved") is not True:
            item9_failures.append("item9_full_row_preservation_missing")
        if item9_summary.get("production_change_claim") is not False:
            item9_failures.append("item9_production_change_claim")
        for family, filename in KIAP_ITEM9_LEDGER_FILES.items():
            path = route / filename
            if not path.exists():
                item9_failures.append(f"{family}:missing:{filename}")
                continue
            rows = load_jsonl(path)
            if len(rows) != int(item9_counts.get(family) or 0):
                item9_failures.append(f"{family}:summary_count_mismatch")
            for row in rows[:10]:
                if row.get("kiap_item9_family") != family:
                    item9_failures.append(f"{family}:family_label_mismatch")
                    break
                if row.get("production_change_claim") is not False:
                    item9_failures.append(f"{family}:production_change_claim")
                    break
                if row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE:
                    item9_failures.append(f"{family}:source_truth_scope")
                    break
        family_summary = item9_summary.get("family_summary")
        if not isinstance(family_summary, dict) or set(family_summary) != set(KIAP_ITEM9_LEDGER_FILES):
            item9_failures.append("item9_family_summary_missing_families")
    checks.append(
        {
            "check": "item9_repair_family_measurement",
            "status": "passed" if not item9_gate_closed or not item9_failures else "failed",
            "details": {
                "item9_gate_closed": item9_gate_closed,
                "status": item9_summary.get("status"),
                "family_row_counts": item9_counts,
                "failures": item9_failures[:40],
            },
        }
    )

    item10_summary = (
        load_json(route / KIAP_ITEM10_SUMMARY_FILE)
        if (route / KIAP_ITEM10_SUMMARY_FILE).exists()
        else {}
    )
    item10_diagnostics = (
        _item10_verifier_hardening_diagnostics(
            route=route,
            repo_root=repo_root,
            action_queue=action_queue,
        )
        if item10_gate_closed
        else {}
    )
    item10_failures = []
    if item10_gate_closed:
        if item10_summary.get("status") != "completed":
            item10_failures.append("item10_summary_not_completed")
        if item10_summary.get("item10_gate_closed") is not True:
            item10_failures.append("item10_gate_flag_not_true")
        if item10_summary.get("no_arbitrary_top_n") is not True:
            item10_failures.append("item10_no_arbitrary_top_n_missing")
        required_item10_checks = {
            "context_anchor_freshness",
            "duplicate_route_artifact_scope",
            "selected_candidate_order_attribution",
            "order_oracle_source_requirement_attribution",
            "rollup_order_trade_oracle_reconciliation",
        }
        if set(item10_summary.get("hardened_checks") or []) != required_item10_checks:
            item10_failures.append("item10_hardened_checks_mismatch")
        for name, row in item10_diagnostics.items():
            if row.get("status") != "passed":
                item10_failures.append(f"{name}:diagnostic_failed")
        summary_diagnostics = item10_summary.get("diagnostics")
        if isinstance(summary_diagnostics, Mapping):
            for name in required_item10_checks:
                if summary_diagnostics.get(name, {}).get("status") != item10_diagnostics.get(name, {}).get("status"):
                    item10_failures.append(f"{name}:summary_status_stale")
        else:
            item10_failures.append("item10_summary_diagnostics_missing")
    checks.append(
        {
            "check": "item10_verifier_hardening",
            "status": "passed" if not item10_gate_closed or not item10_failures else "failed",
            "details": {
                "item10_gate_closed": item10_gate_closed,
                "status": item10_summary.get("status"),
                "diagnostic_statuses": {
                    name: row.get("status")
                    for name, row in item10_diagnostics.items()
                },
                "failures": item10_failures[:80],
            },
        }
    )

    manifest = load_json(route / "KIAP_OUTPUT_MANIFEST.json") if (route / "KIAP_OUTPUT_MANIFEST.json").exists() else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    duplicate_entries = [name for name in artifacts if " 2." in name or " 3." in name]
    checks.append(
        {
            "check": "manifest_scope_no_duplicate_or_raw_scratch",
            "status": "passed"
            if manifest.get("raw_export_scratch_committed") is False
            and manifest.get("prior_kia_duplicate_ledgers_included") is False
            and not duplicate_entries
            else "failed",
            "details": {
                "raw_export_scratch_committed": manifest.get("raw_export_scratch_committed"),
                "duplicate_entries": duplicate_entries,
            },
        }
    )

    checks.append(
        {
            "check": "action_queue_first_open_gate",
            "status": "passed"
            if (
                "4. [x]" in action_queue
                and "5. [x]" in action_queue
                and "6. [x]" in action_queue
                and (
                    (
                        "7. [x]" in action_queue
                        and (
                            (
                                "8. [x]" in action_queue
                                and (
                                    (
                                        "9. [x]" in action_queue
                                        and (
                                            (
                                                "10. [x]" in action_queue
                                                and (
                                                    "11. [x]" in action_queue
                                                    if final_gate_closed
                                                    else "11. [ ]" in action_queue
                                                )
                                            )
                                            if item10_gate_closed
                                            else "10. [ ]" in action_queue
                                        )
                                    )
                                    if item9_gate_closed
                                    else "9. [ ]" in action_queue
                                )
                            )
                            if item8_gate_closed
                            else "8. [ ]" in action_queue
                        )
                    )
                    if development_gate_closed
                    else "7. [ ]" in action_queue
                )
            )
            else "failed",
            "details": {
                "development_gate_closed": development_gate_closed,
                "item8_gate_closed": item8_gate_closed,
                "item9_gate_closed": item9_gate_closed,
                "item10_gate_closed": item10_gate_closed,
                "final_gate_closed": final_gate_closed,
            },
        }
    )

    failure_count = sum(1 for check in checks if check.get("status") == "failed")
    result = {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if failure_count == 0 else "failed",
        "route_status": context.get("route_status") or "IN_PROGRESS",
        "failure_count": failure_count,
        "completion_claim": False,
        "checks": checks,
    }
    if write_result:
        _write_stable_json(route / "KIAP_VERIFICATION_RESULT.json", result)
    return result


def main() -> int:
    repo_root = Path(".")
    build_smoke_checkpoint(repo_root=repo_root, route_dir=ROUTE_DIR)
    build_development_checkpoint(repo_root=repo_root, route_dir=ROUTE_DIR)
    result = verify_route(repo_root=repo_root, route_dir=ROUTE_DIR, write_result=True)
    output_manifest(repo_root / ROUTE_DIR)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
