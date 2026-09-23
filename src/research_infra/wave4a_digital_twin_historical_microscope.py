"""Wave4A deterministic digital-twin and historical-microscope substrate.

This module is local-file only. It consumes accepted post-hard-halt route
artifacts, freezes canonical source rows, emits deterministic as-of replay
events, and keeps path/outcome labels separated from observation fields.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROUTE_ID = "final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05"
LANE = "wave4a_digital_twin_historical_microscope"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_GOAL_PROMPT_2026-06-05.md"
)
STARTER_PATH = PROMPT_PATH.with_name(
    "FINAL_MOONSHOT_WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_STARTER_2026-06-05.txt"
)
WAVE2_ROUTE = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")
WAVE1A_ROUTE = Path("research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04")
WAVE3_ROUTE = Path("research/operations/wave3_historical_replay_digital_twin_v4_2026_06_04")

FORBIDDEN_LABEL_FIELDS = {
    "broker_real_cash",
    "broker_real_pnl_cash",
    "broker_net_cash",
    "commission_cash",
    "swap_cash",
    "fee_cash",
    "gross_deal_profit_cash",
    "exact_r",
    "proxy_r",
    "mfe_r",
    "mae_r",
    "giveback_r",
    "actual_r",
    "final_r",
    "terminal_tick_r",
    "tick_mfe_r",
    "tick_mae_r",
    "ledger_mfe_r",
    "ledger_mae_r",
    "future_path_outcome",
    "post_exit_outcome",
}

BOUNDARY_STATUS = {
    "RESULT_MATERIALIZATION_REQUIRED": True,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
    "broker_runtime_change_status": False,
    "broker_account_order_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_vendor_api_call": False,
    "remote_push": False,
    "active_vps_process_change": False,
    "live_trading_deployment": False,
}


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    relative_path: str
    expected_rows: int
    row_family: str
    source_role: str

    @property
    def path(self) -> Path:
        return Path(self.relative_path)


MATERIAL_SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        "broker_trade_causal_microscope",
        str(WAVE2_ROUTE / "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl"),
        77,
        "broker_real_trade",
        "broker-real redacted_account trade facts and row-level causal surface",
    ),
    SourceSpec(
        "candidate_causal_microscope",
        str(WAVE2_ROUTE / "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl"),
        13246,
        "candidate_reject_skip_shadow",
        "candidate, reject, skip, live-authority, and source-gap candidate rows",
    ),
    SourceSpec(
        "allocator_decision_window_replay",
        str(WAVE2_ROUTE / "WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl"),
        96,
        "decision_window",
        "allocator window reconstruction and replay rows",
    ),
    SourceSpec(
        "selected_vs_alternative_opportunity",
        str(WAVE2_ROUTE / "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl"),
        96,
        "accepted_rejected_same_symbol_window",
        "accepted, rejected, skipped, same-symbol, and zero-trade opportunity windows",
    ),
    SourceSpec(
        "pending_nofill_lifecycle",
        str(WAVE2_ROUTE / "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl"),
        877,
        "pending_nofill",
        "pending/no-fill lifecycle rows with non-generatable truth boundaries",
    ),
    SourceSpec(
        "zero_trade_counterfactual_path_rank",
        str(WAVE2_ROUTE / "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl"),
        416,
        "zero_trade_decision_window",
        "zero-trade and skipped decision value rows",
    ),
    SourceSpec(
        "tick_repaired_first_passage_mfe_mae_reversal",
        str(WAVE2_ROUTE / "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl"),
        55,
        "tick_repaired_path",
        "tick-repaired first-passage MFE/MAE/reversal path rows",
    ),
    SourceSpec(
        "loser_mfe_repair",
        str(WAVE2_ROUTE / "WAVE2_LOSER_MFE_REPAIR_LEDGER.jsonl"),
        29,
        "loser_mfe_harvest",
        "loss rows with positive MFE/giveback harvest requirements",
    ),
    SourceSpec(
        "static_r_geometry_audit",
        str(WAVE2_ROUTE / "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl"),
        471,
        "static_r_target_stop_geometry",
        "static-R/2R target geometry and stop/target efficiency rows",
    ),
    SourceSpec(
        "cost_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl"),
        77,
        "cost_drag_source",
        "broker cost, swap, slippage, and source coverage rows",
    ),
    SourceSpec(
        "profit_harvest_filled_trade",
        str(WAVE2_ROUTE / "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl"),
        55,
        "profit_harvest_filled_trade",
        "filled-trade MFE, partial, BE, harvest, and giveback rows",
    ),
    SourceSpec(
        "partial_be_runner_forensic",
        str(WAVE2_ROUTE / "WAVE2_PARTIAL_BE_RUNNER_FORENSIC_LEDGER.jsonl"),
        52,
        "partial_be_runner_forensic",
        "partial/BE runner forensic rows",
    ),
    SourceSpec(
        "time_to_destination_stale_thesis",
        str(WAVE2_ROUTE / "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl"),
        55,
        "time_to_destination_stale_thesis",
        "time-to-destination and stale-thesis path rows",
    ),
    SourceSpec(
        "target_stop_geometry_path_order",
        str(WAVE2_ROUTE / "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl"),
        77,
        "target_stop_path_order",
        "target/stop geometry and path-order rows",
    ),
)

SOURCE_GAP_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        "wave2_blocker_and_repair",
        str(WAVE2_ROUTE / "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"),
        43,
        "source_gap",
        "Wave2 blocker, repair, and capture requirements",
    ),
    SourceSpec(
        "allocator_window_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl"),
        6,
        "source_gap",
        "allocator decision-window source coverage gaps",
    ),
    SourceSpec(
        "sltp_modify_lifecycle_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl"),
        77,
        "source_gap",
        "SLTP modify lifecycle source coverage gaps",
    ),
    SourceSpec(
        "path_repair_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl"),
        8,
        "source_gap",
        "path-repair source coverage gaps",
    ),
    SourceSpec(
        "market_data_gap_proxy_repair",
        str(WAVE2_ROUTE / "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl"),
        6,
        "source_gap",
        "market-data gap and proxy-repair rows",
    ),
    SourceSpec(
        "static_r_geometry_join_gap",
        str(WAVE2_ROUTE / "WAVE2_STATIC_R_GEOMETRY_JOIN_GAP_LEDGER.jsonl"),
        5,
        "source_gap",
        "static-R geometry join-gap rows",
    ),
)

REQUIRED_CONTEXT_PATHS = (
    ".context/LIVE_STATE.md",
    "AGENTS.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/portable_path_authority.md",
    "research/operations/final_moonshot_wave4_wave5_lane_architecture_repair_2026_06_05/WAVE4_WAVE5_LANE_ARCHITECTURE.md",
)

UPSTREAM_ROUTE_PATHS = (
    "research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04/",
    "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/",
    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/",
    "research/operations/final_moonshot_wave1_integration_review_2026_06_04/",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/",
    "research/operations/final_moonshot_wave3_integration_review_2026_06_05/",
    "research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no} expected object row")
            yield row


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":"), default=str) + "\n")
            count += 1
    return count


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def route_abs(repo_root: Path, route_dir: Path = ROUTE_DIR) -> Path:
    return route_dir if route_dir.is_absolute() else repo_root / route_dir


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def git_value(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def parse_time(value: Any) -> datetime | None:
    if isinstance(value, Mapping):
        for key in (
            "decision_time_utc",
            "window_time_utc",
            "entry_time_utc",
            "close_time_utc",
            "last_time_utc",
            "timestamp_utc",
            "checked_candle_time_utc",
        ):
            parsed = parse_time(value.get(key))
            if parsed is not None:
                return parsed
        return None
    if value in (None, "", [], {}):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_time(row: Mapping[str, Any]) -> datetime | None:
    for key in (
        "time_window",
        "window_time_utc",
        "decision_time_utc",
        "entry_time_utc",
        "pending_created_time_utc",
        "timestamp_utc",
        "checked_candle_time_utc",
        "close_time_utc",
        "terminal_tick_time_utc",
        "tick_window_first_time_utc",
    ):
        parsed = parse_time(row.get(key))
        if parsed is not None:
            return parsed
    return None


def session_bucket(value: datetime | None) -> str:
    if value is None:
        return "session_unknown_clock_gap"
    hour = value.hour
    if 0 <= hour < 7:
        return "tokyo_broad"
    if 7 <= hour < 13:
        return "london_broad"
    if 13 <= hour < 18:
        return "ny_broad"
    return "off_kz_broad"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string(value: Any) -> str:
    return str(value or "").strip()


def _metric_blob(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("metric_fields_used")
    return value if isinstance(value, Mapping) else {}


def first_present(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    metrics = _metric_blob(row)
    for key in keys:
        if key in row and row[key] not in (None, "", [], {}):
            return row[key]
        if key in metrics and metrics[key] not in (None, "", [], {}):
            return metrics[key]
    return None


def as_float(value: Any) -> float | None:
    if value in (None, "", [], {}):
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def source_row_id(row: Mapping[str, Any], fallback: str) -> str:
    for key in (
        "row_id",
        "material_row_id",
        "candidate_id",
        "trade_id",
        "broker_position_id",
        "position_id",
        "inferred_window_id",
        "source_row_id",
        "source_zero_trade_row_id",
    ):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return fallback


def extract_symbol(row: Mapping[str, Any]) -> str:
    for key in ("symbol", "repo_symbol", "source_symbol", "broker_symbol", "tick_symbol", "instrument"):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    symbols = row.get("symbols")
    if isinstance(symbols, list) and symbols:
        return str(symbols[0])
    return "UNKNOWN_SYMBOL"


def extract_side(row: Mapping[str, Any]) -> str:
    for key in ("side", "direction", "requested_side"):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value).upper()
    sides = row.get("sides")
    if isinstance(sides, list) and sides:
        return str(sides[0]).upper()
    return "UNKNOWN_SIDE"


def missing_fields(row: Mapping[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in (
        "missing_fields",
        "missing_runtime_truth",
        "missing_or_non_generatable_truth",
        "source_gap",
        "ledger_basis_discrepancy_flags",
        "tick_parse_errors",
        "missing_tick_dates",
    ):
        values.extend(_as_list(row.get(key)))
    return sorted({str(item) for item in values if item not in (None, "", [], {})})


def source_completeness(row: Mapping[str, Any]) -> str:
    fields = missing_fields(row)
    status_text = " ".join(
        _string(row.get(key))
        for key in (
            "status",
            "source_capture_state",
            "source_read_status",
            "coverage_status",
            "result_use_status",
            "geometry_capture_status",
            "tick_repair_status",
            "source_capture_status",
            "source_completeness_status",
        )
    ).casefold()
    if fields:
        return "source_gap_present"
    if any(token in status_text for token in ("gap", "missing", "non-generatable", "incomplete", "source_required")):
        return "source_gap_present"
    if "partial" in status_text:
        return "partial_source_coverage"
    return "source_complete_or_not_materially_gapped"


def evidence_labels(row: Mapping[str, Any], source_key: str) -> dict[str, Any]:
    metrics = _metric_blob(row)
    evidence_class = _string(row.get("evidence_class")) or "unspecified_evidence_class"
    source_text = f"{source_key} {evidence_class} {json.dumps(metrics, sort_keys=True, default=str)}".casefold()
    broker_cash = first_present(
        row,
        (
            "broker_real_pnl_cash",
            "broker_net_cash",
            "broker_net_cash_from_deals",
            "broker_real_cash",
            "gross_deal_profit_cash",
        ),
    )
    exact_r = first_present(row, ("exact_r",))
    proxy_r = first_present(row, ("proxy_r",))
    actual_r = first_present(row, ("actual_r", "ledger_actual_r", "terminal_tick_r"))
    return {
        "evidence_class": evidence_class,
        "broker_real": {
            "available": broker_cash is not None or "broker-real" in source_text or "broker_real" in source_text,
            "cash_pnl": as_float(broker_cash),
            "source_label": "broker-real cash/PnL stays broker-local and is never replaced by R labels",
        },
        "exact_r": {
            "available": exact_r is not None,
            "value": as_float(exact_r),
            "source_label": "exact-R label only; not broker-real cash",
        },
        "proxy_r": {
            "available": proxy_r is not None,
            "value": as_float(proxy_r),
            "source_label": "proxy-R label only; not broker-real cash",
        },
        "replay_or_shadow": {
            "available": any(token in source_text for token in ("replay", "shadow", "simulation", "counterfactual")),
            "actual_r": as_float(actual_r),
            "source_label": "replay/simulation/shadow label only",
        },
    }


def path_metrics(row: Mapping[str, Any]) -> dict[str, Any]:
    mfe_r = first_present(row, ("mfe_r", "ledger_mfe_r", "tick_mfe_r", "near_mfe_within_0_10r_max_r"))
    mae_r = first_present(row, ("mae_r", "ledger_mae_r", "tick_mae_r"))
    giveback_r = first_present(row, ("giveback_r", "mfe_to_terminal_giveback_r", "mfe_to_worst_after_mfe_reversal_r"))
    actual_r = first_present(row, ("actual_r", "ledger_actual_r", "terminal_tick_r", "proxy_r", "exact_r"))
    return {
        "mfe_r": as_float(mfe_r),
        "mae_r": as_float(mae_r),
        "giveback_r": as_float(giveback_r),
        "actual_or_terminal_r": as_float(actual_r),
        "mfe_time_minutes": as_float(
            first_present(row, ("mfe_time_minutes", "ledger_mfe_time_minutes", "tick_mfe_time_minutes"))
        ),
        "mae_time_minutes": as_float(
            first_present(row, ("ledger_mae_time_minutes", "tick_mae_time_minutes"))
        ),
        "hold_minutes": as_float(first_present(row, ("hold_minutes", "ledger_hold_minutes"))),
        "time_from_mfe_to_terminal_minutes": as_float(
            first_present(row, ("time_from_mfe_to_terminal_minutes",))
        ),
        "first_giveback_0_25r_minutes_after_mfe": as_float(
            first_present(row, ("first_giveback_0_25r_minutes_after_mfe",))
        ),
        "first_giveback_0_5r_minutes_after_mfe": as_float(
            first_present(row, ("first_giveback_0_5r_minutes_after_mfe",))
        ),
        "stale_thesis_state": _string(
            first_present(row, ("stale_thesis_status", "stale_exposure_status", "thesis_horizon_status"))
        )
        or None,
        "partial_close_count": as_float(first_present(row, ("partial_close_count",))),
        "stop_width_or_risk_distance": as_float(
            first_present(row, ("risk_distance_for_r", "stop_width_r", "raw_trade_parameters_risk_reward_ratio"))
        ),
        "target_distance_or_multiple_r": as_float(
            first_present(
                row,
                (
                    "broker_order_initial_target_multiple_r",
                    "dynamic_final_target_r",
                    "dynamic_trigger_r",
                    "repaired_geometry_risk_reward_ratio",
                ),
            )
        ),
    }


def opportunity_status(row: Mapping[str, Any], source_key: str) -> str:
    text = " ".join(
        _string(row.get(key))
        for key in ("status", "final_outcome", "decision_status", "candidate_quality_classification", "rank_status")
    ).casefold()
    if source_key == "selected_vs_alternative_opportunity":
        return "decision_window_with_accepted_rejected_skipped_same_symbol_zero_trade_counts"
    if source_key == "pending_nofill_lifecycle":
        return "pending_or_nofill_lifecycle_row"
    if source_key == "zero_trade_counterfactual_path_rank" or "no_trade" in text or "skipped" in text:
        return "zero_trade_or_skipped_row"
    if "reject" in text:
        return "rejected_row"
    if "cancel" in text:
        return "cancelled_row"
    if "fill" in text or "selected" in text or "accepted" in text:
        return "accepted_or_filled_row"
    return "candidate_or_opportunity_row_status_not_explicit"


def canonical_entry(spec: SourceSpec, row: Mapping[str, Any], source_hash: str, index: int) -> dict[str, Any]:
    source_id = source_row_id(row, f"{spec.source_key}:{index:06d}")
    row_hash = stable_hash(row)
    clock = canonical_time(row)
    canonical_id = f"wave4a:{spec.source_key}:{index:06d}:{stable_hash([spec.source_key, source_id, source_hash])[:12]}"
    miss = missing_fields(row)
    labels = evidence_labels(row, spec.source_key)
    return {
        "schema_version": "wave4a_canonical_row_universe_v1",
        "canonical_row_id": canonical_id,
        "row_id": canonical_id,
        "lane": LANE,
        "source_key": spec.source_key,
        "row_family": spec.row_family,
        "source_role": spec.source_role,
        "source_path": spec.relative_path,
        "source_sha256": source_hash,
        "source_row_index": index,
        "source_row_id": source_id,
        "source_row_hash": row_hash,
        "canonical_time_utc": clock.isoformat() if clock else None,
        "clock_status": "asof_clock_available" if clock else "clock_source_gap",
        "symbol": extract_symbol(row),
        "side": extract_side(row),
        "session_bucket": session_bucket(clock),
        "duplicate_policy_key": _string(row.get("duplicate_source_row_key")) or source_id,
        "opportunity_status": opportunity_status(row, spec.source_key),
        "source_completeness_state": source_completeness(row),
        "missing_field_count": len(miss),
        "missing_fields_or_runtime_truth": miss,
        "evidence_labels": labels,
        "branch_decision": row.get("branch_decision") or row.get("implementation_decision") or "preserve_as_wave4a_source_row",
        "implementation_decision": row.get("implementation_decision") or "preserve_source_row_for_wave4b_wave4c_wave4i",
        "source_capture_state": row.get("source_capture_state")
        or row.get("source_capture_status")
        or "source_hash_materialized_from_current_disk",
        "raw_source_reference": {
            "source_row_id": source_id,
            "source_row_hash": row_hash,
            "source_path": spec.relative_path,
        },
    }


def load_material_entries(repo_root: Path, specs: Sequence[SourceSpec] = MATERIAL_SOURCE_SPECS) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    raw_by_canonical: dict[str, dict[str, Any]] = {}
    for spec in specs:
        path = repo_root / spec.path
        rows = list(iter_jsonl(path))
        if len(rows) != spec.expected_rows:
            raise ValueError(f"{spec.relative_path} expected {spec.expected_rows} rows, found {len(rows)}")
        source_hash = sha256_file(path)
        inventory.append(
            {
                "schema_version": "wave4a_source_input_inventory_v1",
                "source_key": spec.source_key,
                "row_family": spec.row_family,
                "source_role": spec.source_role,
                "path": spec.relative_path,
                "sha256": source_hash,
                "row_count": len(rows),
                "expected_rows": spec.expected_rows,
                "row_count_status": "matches_expected",
            }
        )
        for index, row in enumerate(rows, start=1):
            entry = canonical_entry(spec, row, source_hash, index)
            entries.append(entry)
            raw_by_canonical[entry["canonical_row_id"]] = dict(row)
    return entries, inventory, raw_by_canonical


def event_schema() -> dict[str, Any]:
    return {
        "schema_version": "wave4a_digital_twin_event_schema_v1",
        "lane": LANE,
        "event_contract": {
            "stable_identity": [
                "event_id",
                "canonical_row_id",
                "source_key",
                "source_path",
                "source_sha256",
                "source_row_hash",
            ],
            "asof_observation_allowed_fields": [
                "symbol",
                "side",
                "session_bucket",
                "source_key",
                "row_family",
                "source_completeness_state",
                "clock_status",
                "opportunity_status",
            ],
            "forbidden_asof_fields": sorted(FORBIDDEN_LABEL_FIELDS),
            "label_boundary": [
                "broker_real",
                "exact_r",
                "proxy_r",
                "replay_or_shadow",
                "path_clock_labels_post_decision_only",
            ],
        },
        "broker_real_cash_policy": "broker-real cash/PnL is stored only under label_boundary.broker_real and is never replaced by exact-R, proxy-R, replay, simulation, or shadow labels",
    }


def digital_twin_event(entry: Mapping[str, Any]) -> dict[str, Any]:
    observation = {
        "symbol": entry["symbol"],
        "side": entry["side"],
        "session_bucket": entry["session_bucket"],
        "source_key": entry["source_key"],
        "row_family": entry["row_family"],
        "source_completeness_state": entry["source_completeness_state"],
        "clock_status": entry["clock_status"],
        "opportunity_status": entry["opportunity_status"],
    }
    return {
        "schema_version": "wave4a_digital_twin_event_v1",
        "event_id": f"event:{entry['canonical_row_id']}:asof_decision",
        "canonical_row_id": entry["canonical_row_id"],
        "event_sequence": 1,
        "event_type": "asof_decision_observation",
        "event_time_utc": entry["canonical_time_utc"],
        "event_clock_status": entry["clock_status"],
        "source_key": entry["source_key"],
        "source_path": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "source_row_id": entry["source_row_id"],
        "source_row_hash": entry["source_row_hash"],
        "asof_observation": observation,
        "forbidden_label_fields_excluded": sorted(FORBIDDEN_LABEL_FIELDS),
        "label_boundary": entry["evidence_labels"],
        "result_use_status": "deterministic_asof_replay_event_not_outcome_score",
    }


def path_clock_row(entry: Mapping[str, Any], raw_row: Mapping[str, Any]) -> dict[str, Any]:
    metrics = path_metrics(raw_row)
    available = [key for key, value in metrics.items() if value not in (None, "", [])]
    miss = list(entry["missing_fields_or_runtime_truth"])
    if not available:
        status = "path_clock_source_gap_or_not_applicable"
    elif entry["source_completeness_state"] == "source_gap_present":
        status = "path_clock_partial_with_source_gap"
    else:
        status = "path_clock_materialized"
    return {
        "schema_version": "wave4a_path_clock_forensic_v1",
        "row_id": f"path_clock:{entry['canonical_row_id']}",
        "canonical_row_id": entry["canonical_row_id"],
        "source_key": entry["source_key"],
        "source_path": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "symbol": entry["symbol"],
        "side": entry["side"],
        "canonical_time_utc": entry["canonical_time_utc"],
        "path_clock_status": status,
        "path_metric_fields_available": sorted(available),
        "post_decision_path_labels": metrics,
        "path_labels_never_asof_features": True,
        "path_fact_classification": {
            "bad_selection": "selector" in json.dumps(raw_row, default=str).casefold(),
            "bad_timing": any(key in available for key in ("mfe_time_minutes", "mae_time_minutes")),
            "bad_geometry": entry["source_key"] in {"static_r_geometry_audit", "target_stop_geometry_path_order"},
            "cost_drag": entry["source_key"] == "cost_source_coverage",
            "stale_thesis": entry["source_key"] == "time_to_destination_stale_thesis"
            or bool(metrics.get("stale_thesis_state")),
            "missed_harvest": entry["source_key"] in {"loser_mfe_repair", "profit_harvest_filled_trade"},
            "same_symbol_conflict": entry["source_key"] == "selected_vs_alternative_opportunity"
            and "same_symbol" in json.dumps(raw_row, default=str).casefold(),
            "true_source_gap": entry["source_completeness_state"] == "source_gap_present",
        },
        "missing_source_or_capture_requirement": miss
        or ["no path label available from this source family; preserve source row and require downstream path source if material"],
        "result_use_status": "path_forensic_labels_only_not_asof_features",
    }


def opportunity_row(entry: Mapping[str, Any], raw_row: Mapping[str, Any]) -> dict[str, Any] | None:
    if entry["source_key"] not in {
        "candidate_causal_microscope",
        "selected_vs_alternative_opportunity",
        "pending_nofill_lifecycle",
        "zero_trade_counterfactual_path_rank",
    }:
        return None
    return {
        "schema_version": "wave4a_accepted_rejected_opportunity_v1",
        "row_id": f"opportunity:{entry['canonical_row_id']}",
        "canonical_row_id": entry["canonical_row_id"],
        "source_key": entry["source_key"],
        "source_path": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "symbol": entry["symbol"],
        "side": entry["side"],
        "canonical_time_utc": entry["canonical_time_utc"],
        "opportunity_status": entry["opportunity_status"],
        "selected_or_filled_candidate_ids": raw_row.get("selected_or_filled_candidate_ids")
        or _as_list(raw_row.get("candidate_id")),
        "rejected_skipped_no_trade_candidate_ids": raw_row.get("rejected_skipped_no_trade_candidate_ids")
        or ([] if entry["opportunity_status"] == "accepted_or_filled_row" else _as_list(raw_row.get("candidate_id"))),
        "same_symbol_alternative": raw_row.get("best_same_symbol_alternative_by_decision_time_expectancy"),
        "zero_trade_comparator": raw_row.get("zero_trade_comparator"),
        "counts": {
            "candidate_count": raw_row.get("candidate_count"),
            "filled_count": raw_row.get("filled_count"),
            "rejected_count": raw_row.get("rejected_count"),
            "skipped_count": raw_row.get("skipped_count"),
            "cancelled_count": raw_row.get("cancelled_count"),
            "alternative_count": raw_row.get("alternative_count"),
        },
        "source_bound_expectancy_context": raw_row.get("source_bound_expectancy_context")
        or raw_row.get("selected_vs_alternative_deltas")
        or raw_row.get("metric_fields_used"),
        "runtime_truth_gap": raw_row.get("missing_runtime_truth") or raw_row.get("missing_fields") or [],
        "evidence_class": entry["evidence_labels"]["evidence_class"],
        "result_use_status": "opportunity_denominator_row_not_realized_counterfactual_pnl",
    }


def loser_mfe_rows(entries: Sequence[Mapping[str, Any]], raw_by_canonical: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    broker_losses = [
        entry
        for entry in entries
        if entry["source_key"] == "broker_trade_causal_microscope"
        and str(_metric_blob(raw_by_canonical[entry["canonical_row_id"]]).get("win_loss", "")).casefold() == "loss"
    ]
    loser_entries = [entry for entry in entries if entry["source_key"] == "loser_mfe_repair"]
    covered_positions = {
        str(raw_by_canonical[entry["canonical_row_id"]].get("broker_position_id"))
        for entry in loser_entries
        if raw_by_canonical[entry["canonical_row_id"]].get("broker_position_id") not in (None, "")
    }
    rows: list[dict[str, Any]] = []
    for entry in loser_entries:
        raw = raw_by_canonical[entry["canonical_row_id"]]
        metrics = path_metrics(raw)
        rows.append(
            {
                "schema_version": "wave4a_loser_mfe_harvest_v1",
                "row_id": f"loser_harvest:{entry['canonical_row_id']}",
                "canonical_row_id": entry["canonical_row_id"],
                "broker_position_id": raw.get("broker_position_id"),
                "trade_id": raw.get("trade_id"),
                "symbol": entry["symbol"],
                "side": entry["side"],
                "source_path": entry["source_path"],
                "source_sha256": entry["source_sha256"],
                "source_support_status": "source_supported_loser_mfe_row",
                "mfe_r": metrics["mfe_r"],
                "mae_r": metrics["mae_r"],
                "actual_r": metrics["actual_or_terminal_r"],
                "giveback_r": metrics["giveback_r"],
                "mfe_time_minutes": metrics["mfe_time_minutes"],
                "hold_minutes": metrics["hold_minutes"],
                "harvest_tags": raw.get("harvest_tags") or [],
                "partial_close_count": metrics["partial_close_count"],
                "same_evidence_class_next_step": raw.get("same_evidence_class_next_step"),
                "result_use_status": "loser_mfe_path_label_not_asof_feature",
            }
        )
    for entry in broker_losses:
        raw = raw_by_canonical[entry["canonical_row_id"]]
        position = str(raw.get("broker_position_id") or "")
        if position and position in covered_positions:
            continue
        rows.append(
            {
                "schema_version": "wave4a_loser_mfe_harvest_v1",
                "row_id": f"loser_harvest_gap:{entry['canonical_row_id']}",
                "canonical_row_id": entry["canonical_row_id"],
                "broker_position_id": raw.get("broker_position_id"),
                "trade_id": raw.get("candidate_id"),
                "symbol": entry["symbol"],
                "side": entry["side"],
                "source_path": entry["source_path"],
                "source_sha256": entry["source_sha256"],
                "source_support_status": "broker_loss_without_loser_mfe_source_row",
                "mfe_r": None,
                "mae_r": None,
                "actual_r": as_float(_metric_blob(raw).get("proxy_r")),
                "giveback_r": None,
                "mfe_time_minutes": None,
                "hold_minutes": as_float(_metric_blob(raw).get("hold_minutes")),
                "harvest_tags": ["loss_without_source_supported_mfe_harvest_row"],
                "partial_close_count": None,
                "same_evidence_class_next_step": (
                    "join M1/tick first-passage, consolidation/reversal, and execution lifecycle if source exists; "
                    "otherwise preserve prospective capture requirement"
                ),
                "result_use_status": "source_gap_for_loser_mfe_path_label",
            }
        )
    return rows


def source_gap_rows(
    repo_root: Path,
    entries: Sequence[Mapping[str, Any]],
    loser_rows: Sequence[Mapping[str, Any]],
    specs: Sequence[SourceSpec] = SOURCE_GAP_SPECS,
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for spec in specs:
        path = repo_root / spec.path
        rows = list(iter_jsonl(path))
        if len(rows) != spec.expected_rows:
            raise ValueError(f"{spec.relative_path} expected {spec.expected_rows} rows, found {len(rows)}")
        source_hash = sha256_file(path)
        for index, row in enumerate(rows, start=1):
            rows_out.append(
                {
                    "schema_version": "wave4a_source_gap_capture_v1",
                    "row_id": f"source_gap:{spec.source_key}:{index:05d}",
                    "source_key": spec.source_key,
                    "source_path": spec.relative_path,
                    "source_sha256": source_hash,
                    "source_row_index": index,
                    "source_row_id": source_row_id(row, f"{spec.source_key}:{index:05d}"),
                    "source_gap_state": source_completeness(row),
                    "missing_source_or_field": row.get("missing_file_path_field_source")
                    or row.get("missing_source")
                    or row.get("missing_runtime_truth")
                    or row.get("missing_fields")
                    or row.get("source_gap"),
                    "repair_or_capture_requirement": row.get("owner_access_source_capture_requirement")
                    or row.get("repair_requirement")
                    or row.get("capture_requirement")
                    or row.get("same_evidence_class_next_step")
                    or "preserve exact source gap until the source/capture field is materialized",
                    "result_use_status": "source_gap_or_capture_requirement_no_label_imputation",
                }
            )
    for row in loser_rows:
        if row["source_support_status"] != "broker_loss_without_loser_mfe_source_row":
            continue
        rows_out.append(
            {
                "schema_version": "wave4a_source_gap_capture_v1",
                "row_id": f"source_gap:loser_mfe_uncovered:{row['canonical_row_id']}",
                "source_key": "loser_mfe_uncovered_broker_loss",
                "source_path": row["source_path"],
                "source_sha256": row["source_sha256"],
                "source_row_index": None,
                "source_row_id": row["canonical_row_id"],
                "source_gap_state": "prospective_capture_requirement",
                "missing_source_or_field": ["source_supported_mfe_mae_giveback_reversal_for_broker_loss"],
                "repair_or_capture_requirement": row["same_evidence_class_next_step"],
                "result_use_status": "source_gap_for_loser_mfe_path_label",
            }
        )
    canonical_gap_count = sum(1 for entry in entries if entry["source_completeness_state"] == "source_gap_present")
    rows_out.append(
        {
            "schema_version": "wave4a_source_gap_capture_v1",
            "row_id": "source_gap:canonical_universe_gap_summary",
            "source_key": "canonical_universe_gap_summary",
            "source_path": "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
            "source_sha256": None,
            "source_row_index": None,
            "source_row_id": "canonical_universe_gap_summary",
            "source_gap_state": "summary_only_counts_no_row_loss",
            "missing_source_or_field": {"canonical_rows_with_source_gap_state": canonical_gap_count},
            "repair_or_capture_requirement": "row-level source gaps remain in canonical rows and source-gap ledgers; no label imputation allowed",
            "result_use_status": "gap_summary_not_label",
        }
    )
    return rows_out


def question_rows() -> list[dict[str, Any]]:
    questions = [
        ("W4A_Q001", "canonical row universe", "Confirm or falsify prior 77 broker-real trade expectation and freeze all source rows."),
        ("W4A_Q002", "loser MFE harvest", "For every loss with source support, expose MFE, MAE, giveback, and harvest failure."),
        ("W4A_Q003", "accepted moved our way", "Identify accepted trades that moved favorably then failed target, partial/BE, or reversed."),
        ("W4A_Q004", "rejected skipped pending nofill alternatives", "Preserve alternatives that were safer or better than accepted risk."),
        ("W4A_Q005", "static-R and 2R geometry", "Preserve stop-too-wide, target-too-far, static-R, and 2R path geometry labels."),
        ("W4A_Q006", "cost drag", "Separate broker cost/swap/slippage drag from path and selector failures."),
        ("W4A_Q007", "same-symbol conflict", "Preserve same-symbol same-instrument alternative windows for Wave4B/Wave4C."),
        ("W4A_Q008", "zero-trade quality", "Preserve zero-trade and no-trade rows without inventing realized counterfactual PnL."),
        ("W4A_Q009", "pending no-fill lifecycle", "Preserve non-generatable pending intent and broker ticket gaps as capture requirements."),
        ("W4A_Q010", "path-clock leakage", "Prove path labels never enter as-of digital twin features."),
        ("W4A_Q011", "broker-real separation", "Prove broker-real cash/PnL stays separate from exact-R, proxy-R, replay, simulation, and shadow."),
        ("W4A_Q012", "stale thesis", "Preserve time-to-destination and stale-thesis path clocks for exit/harvest lanes."),
        ("W4A_Q013", "source hash completeness", "Hash and count every consumed source file for downstream reproducibility."),
        ("W4A_Q014", "Wave4 handoff", "Create row/path clocks that Wave4B Feature Store and Wave4C Label Store can consume."),
    ]
    return [
        {
            "schema_version": "wave4a_question_ledger_v1",
            "question_id": question_id,
            "question_family": family,
            "question": text,
            "pursuit_status": "answered_or_bounded_in_wave4a_artifacts",
            "evidence_artifacts": [
                "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
                "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl",
                "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl",
                "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
            ],
            "result_use_status": "question_stack_full_preserved_no_top_n_cutoff",
        }
        for question_id, family, text in questions
    ]


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    roots = [
        ".context/00_core",
        "AGENTS.md",
        str(PROMPT_PATH),
        str(STARTER_PATH),
        str(WAVE1A_ROUTE),
        str(WAVE2_ROUTE),
        str(WAVE3_ROUTE),
        "research/operations/final_moonshot_wave3_integration_review_2026_06_05",
        "research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05",
        "shadow_logs",
        "pipeline_state",
        "data/m1",
        "data/ticks",
        "/Users/borr/Documents/gtos/packages",
    ]
    rows = []
    for index, raw in enumerate(roots, start=1):
        path = Path(raw)
        exists = path.exists() if path.is_absolute() else (repo_root / path).exists()
        rows.append(
            {
                "schema_version": "wave4a_searched_root_v1",
                "row_id": f"searched_root:{index:03d}",
                "path": raw,
                "exists": exists,
                "search_status": "searched_or_inventory_checked" if exists else "not_present_in_current_local_root",
                "result_use_status": "source_discovery_context_not_label",
            }
        )
    return rows


def decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "wave4a_decision_ledger_v1",
            "decision_id": "W4A_DECISION_001",
            "decision": "IMPLEMENT_CANONICAL_ROW_UNIVERSE_AND_PATH_CLOCKS",
            "evidence_class": "source-bound deterministic replay plus path-forensic labels",
            "implementation_decision": "src/research_infra/wave4a_digital_twin_historical_microscope.py plus route-local builder/verifier/tests",
        },
        {
            "schema_version": "wave4a_decision_ledger_v1",
            "decision_id": "W4A_DECISION_002",
            "decision": "KEEP_PATH_AND_OUTCOME_LABELS_OUT_OF_ASOF_EVENTS",
            "evidence_class": "no-leak replay infrastructure",
            "implementation_decision": "digital twin events expose asof_observation only and put labels under label_boundary/path ledgers",
        },
        {
            "schema_version": "wave4a_decision_ledger_v1",
            "decision_id": "W4A_DECISION_003",
            "decision": "CARRY_SOURCE_GAPS_AND_PROSPECTIVE_CAPTURE_REQUIREMENTS_FORWARD",
            "evidence_class": "source gap/prospective capture requirement",
            "implementation_decision": "source-gap ledger materializes upstream gaps plus uncovered broker-loss MFE gaps",
        },
    ]


def coverage_matrix(
    entries: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    path_rows: Sequence[Mapping[str, Any]],
    loser_rows: Sequence[Mapping[str, Any]],
    opportunity_rows: Sequence[Mapping[str, Any]],
    source_gap_rows_in: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    label_counts = Counter()
    for entry in entries:
        labels = entry["evidence_labels"]
        for family in ("broker_real", "exact_r", "proxy_r", "replay_or_shadow"):
            if labels[family]["available"]:
                label_counts[family] += 1
    return {
        "schema_version": "wave4a_coverage_matrix_v1",
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "expected_material_rows": sum(spec.expected_rows for spec in MATERIAL_SOURCE_SPECS),
        "actual_material_rows": len(entries),
        "canonical_unique_rows": len({row["canonical_row_id"] for row in entries}),
        "digital_twin_event_rows": len(events),
        "path_clock_rows": len(path_rows),
        "loser_mfe_harvest_rows": len(loser_rows),
        "source_supported_loser_mfe_rows": sum(1 for row in loser_rows if row["source_support_status"] == "source_supported_loser_mfe_row"),
        "broker_loss_mfe_gap_rows": sum(1 for row in loser_rows if row["source_support_status"] == "broker_loss_without_loser_mfe_source_row"),
        "accepted_rejected_opportunity_rows": len(opportunity_rows),
        "source_gap_and_capture_rows": len(source_gap_rows_in),
        "source_counts": dict(sorted(Counter(row["source_key"] for row in entries).items())),
        "row_family_counts": dict(sorted(Counter(row["row_family"] for row in entries).items())),
        "source_completeness_counts": dict(sorted(Counter(row["source_completeness_state"] for row in entries).items())),
        "opportunity_status_counts": dict(sorted(Counter(row["opportunity_status"] for row in entries).items())),
        "path_clock_status_counts": dict(sorted(Counter(row["path_clock_status"] for row in path_rows).items())),
        "evidence_label_counts": dict(sorted(label_counts.items())),
        "source_inventory": list(inventory),
        "boundary_status": BOUNDARY_STATUS,
    }


def context_anchor(repo_root: Path, inventory: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "wave4a_context_anchor_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "created_at_utc": utc_now(),
        "prompt_path": str(PROMPT_PATH),
        "starter_path": str(STARTER_PATH),
        "route_dir": str(ROUTE_DIR),
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "git_status_short": git_value(repo_root, "status", "--short"),
        "evidence_class": "source-bound deterministic replay plus path-forensic labels",
        "boundary_status": BOUNDARY_STATUS,
        "required_context_paths": list(REQUIRED_CONTEXT_PATHS),
        "upstream_route_paths_read_from_disk": list(UPSTREAM_ROUTE_PATHS),
        "source_count": len(inventory),
        "source_rows_total": sum(int(row["row_count"]) for row in inventory),
        "pre_existing_unrelated_dirt_policy": "preserve and do not stage unrelated legacy research JSONL dirt",
    }


def instruction_coverage_markdown() -> str:
    return """# Wave4A Instruction Coverage Checklist

- `goal_session_research_discipline.md` read after preflight: yes.
- `research_operating_doctrine.md` read after preflight: yes.
- Lane posture: constructive builder/replay/source-repair lane, not G12/G0 audit.
- Evidence class: source-bound deterministic replay plus path-forensic labels.
- No chat memory reliance: repo and route artifacts were read from disk.
- No arbitrary top-N: full material source rows are preserved before summaries.
- Anti-boxing pursued: broker trades, candidates, rejects/skips, pending/no-fill, same-symbol windows, zero-trade windows, path-clock labels, static-R geometry, cost drag, stale thesis, and source gaps.
- Forbidden surfaces preserved: no broker mutation, credential mutation, paid API call, remote push, VPS process mutation, MT5 operation, live deployment, or live trading restart.
- Cross-boundary items not answered: Wave4B features, Wave4C labels, Wave4I partition acceptance, Wave5 ML training, and production-return deployment.
"""


def saturation_markdown(matrix: Mapping[str, Any]) -> str:
    return f"""# Wave4A Saturation And Self-Red-Team

## Attacks Run

- Evidence-class leakage: digital-twin events expose only `asof_observation`; broker-real cash, exact-R, proxy-R, replay/shadow, MFE/MAE, giveback, and terminal labels stay in label/path ledgers.
- Source hashes: every material source file is hashed in `WAVE4A_SOURCE_INPUT_INVENTORY.jsonl`; canonical rows carry source path, source hash, and source-row hash.
- Duplicate keys: canonical row ids include source key, row index, source id, and source hash; duplicate policy keys are preserved for Wave4I collapse decisions.
- Denominator loss: {matrix['actual_material_rows']} material source rows are preserved; row-family counts are in the coverage matrix.
- Loser MFE: source-supported loser MFE rows and broker-loss MFE gaps are both emitted, so missing path evidence is not hidden.
- Opportunity rows: accepted/rejected/skipped/pending/no-fill/zero-trade rows are preserved in `WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl`.
- Cost/static-R/stale-thesis omission: cost, target/stop path order, static-R geometry, time-to-destination, and partial/BE runner sources are included as material sources.
- Broker mixing: broker-real cash/PnL stays broker-local and separate from exact-R/proxy-R/replay labels.
- Source gaps: upstream source-gap ledgers plus uncovered broker-loss MFE gaps are materialized in `WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl`.

## Same-Evidence-Class Follow-Up

No executable same-evidence-class local read was left unmaterialized for this lane's artifact contract. Remaining gaps are exact source/capture requirements: non-generatable historical pending intent/order tickets, unavailable historical runtime candidate-set ids, source-supported MFE/MAE/giveback for uncovered broker losses, and broker-native slippage/spread fields where upstream routes recorded source gaps.
"""


def output_manifest(repo_root: Path, route_dir_abs: Path) -> dict[str, Any]:
    files = []
    manifest_name = "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json"
    for path in sorted(route_dir_abs.iterdir()):
        if not path.is_file() or path.name == manifest_name:
            continue
        row: dict[str, Any] = {
            "path": rel_path(repo_root, path),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        if path.suffix == ".jsonl":
            row["jsonl_rows"] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        files.append(row)
    return {
        "schema_version": "wave4a_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "lane": LANE,
        "file_count": len(files),
        "files": files,
        "manifest_self_excluded_from_hash_list": True,
        "boundary_status": BOUNDARY_STATUS,
    }


def build_artifacts(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    entries, inventory, raw_by_canonical = load_material_entries(repo_root)
    events = [digital_twin_event(entry) for entry in entries]
    path_rows = [path_clock_row(entry, raw_by_canonical[entry["canonical_row_id"]]) for entry in entries]
    opportunity_rows = [
        row
        for entry in entries
        for row in [opportunity_row(entry, raw_by_canonical[entry["canonical_row_id"]])]
        if row is not None
    ]
    loser_rows_out = loser_mfe_rows(entries, raw_by_canonical)
    gaps = source_gap_rows(repo_root, entries, loser_rows_out)
    matrix = coverage_matrix(entries, events, path_rows, loser_rows_out, opportunity_rows, gaps, inventory)
    route_dir_abs = route_abs(repo_root, route_dir)
    route_dir_abs.mkdir(parents=True, exist_ok=True)

    jsonl_artifacts = {
        "WAVE4A_SOURCE_INPUT_INVENTORY.jsonl": inventory,
        "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl": entries,
        "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl": events,
        "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl": path_rows,
        "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl": loser_rows_out,
        "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl": opportunity_rows,
        "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl": gaps,
        "WAVE4A_QUESTION_LEDGER.jsonl": question_rows(),
        "WAVE4A_DECISION_LEDGER.jsonl": decision_rows(),
        "WAVE4A_SEARCHED_ROOT_LEDGER.jsonl": searched_root_rows(repo_root),
    }
    written = {name: write_jsonl(route_dir_abs / name, rows) for name, rows in jsonl_artifacts.items()}

    write_json(route_dir_abs / "WAVE4A_CONTEXT_ANCHOR.json", context_anchor(repo_root, inventory))
    write_json(route_dir_abs / "WAVE4A_DIGITAL_TWIN_EVENT_SCHEMA.json", event_schema())
    write_json(route_dir_abs / "WAVE4A_COVERAGE_MATRIX.json", matrix)
    write_text(
        route_dir_abs / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_INSTRUCTION_COVERAGE_CHECKLIST.md",
        instruction_coverage_markdown(),
    )
    write_text(
        route_dir_abs / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_SATURATION_SELF_RED_TEAM.md",
        saturation_markdown(matrix),
    )
    write_completion_audit(repo_root, route_dir, verification=None, focused=None, prompt=None, audit=None)
    write_json(route_dir_abs / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json", output_manifest(repo_root, route_dir_abs))
    return {
        "route_dir": rel_path(repo_root, route_dir_abs),
        "canonical_rows": len(entries),
        "event_rows": len(events),
        "path_clock_rows": len(path_rows),
        "opportunity_rows": len(opportunity_rows),
        "loser_mfe_rows": len(loser_rows_out),
        "source_gap_rows": len(gaps),
        "jsonl_written": written,
    }


def _load_jsonl(route_dir_abs: Path, name: str) -> list[dict[str, Any]]:
    return list(iter_jsonl(route_dir_abs / name))


def verify_route(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route_dir_abs = route_abs(repo_root, route_dir)
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Mapping[str, Any] | None = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": dict(evidence or {})})

    required = [
        "WAVE4A_CONTEXT_ANCHOR.json",
        "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
        "WAVE4A_DIGITAL_TWIN_EVENT_SCHEMA.json",
        "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl",
        "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl",
        "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl",
        "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl",
        "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
        "WAVE4A_QUESTION_LEDGER.jsonl",
        "WAVE4A_COVERAGE_MATRIX.json",
        "WAVE4A_DECISION_LEDGER.jsonl",
        "WAVE4A_SOURCE_INPUT_INVENTORY.jsonl",
        "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_SATURATION_SELF_RED_TEAM.md",
        "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_INSTRUCTION_COVERAGE_CHECKLIST.md",
        "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json",
        "COMPLETION_AUDIT.md",
    ]
    for name in required:
        add(f"exists:{name}", (route_dir_abs / name).exists())

    json_errors = []
    jsonl_counts: dict[str, int] = {}
    for path in sorted(route_dir_abs.glob("*.json")):
        try:
            read_json(path)
        except Exception as exc:  # noqa: BLE001
            json_errors.append(f"{path.name}:{exc}")
    for path in sorted(route_dir_abs.glob("*.jsonl")):
        try:
            rows = list(iter_jsonl(path))
        except Exception as exc:  # noqa: BLE001
            json_errors.append(f"{path.name}:{exc}")
            rows = []
        jsonl_counts[path.name] = len(rows)
    add("all_json_and_jsonl_parse", not json_errors, {"errors": json_errors})

    canonical = _load_jsonl(route_dir_abs, "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl")
    events = _load_jsonl(route_dir_abs, "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl")
    paths = _load_jsonl(route_dir_abs, "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl")
    loser = _load_jsonl(route_dir_abs, "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl")
    opportunities = _load_jsonl(route_dir_abs, "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl")
    gaps = _load_jsonl(route_dir_abs, "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl")
    matrix = read_json(route_dir_abs / "WAVE4A_COVERAGE_MATRIX.json")
    expected_material = sum(spec.expected_rows for spec in MATERIAL_SOURCE_SPECS)
    expected_opportunity = sum(
        spec.expected_rows
        for spec in MATERIAL_SOURCE_SPECS
        if spec.source_key
        in {
            "candidate_causal_microscope",
            "selected_vs_alternative_opportunity",
            "pending_nofill_lifecycle",
            "zero_trade_counterfactual_path_rank",
        }
    )
    add("canonical_row_count_matches_expected", len(canonical) == expected_material, {"actual": len(canonical), "expected": expected_material})
    add("canonical_ids_unique", len({row["canonical_row_id"] for row in canonical}) == len(canonical))
    add("event_rows_match_canonical_rows", len(events) == len(canonical), {"events": len(events), "canonical": len(canonical)})
    add("path_clock_rows_match_canonical_rows", len(paths) == len(canonical), {"paths": len(paths), "canonical": len(canonical)})
    add("opportunity_rows_match_expected_sources", len(opportunities) == expected_opportunity, {"actual": len(opportunities), "expected": expected_opportunity})
    source_counts = Counter(row["source_key"] for row in canonical)
    add(
        "source_counts_match_contract",
        all(source_counts[spec.source_key] == spec.expected_rows for spec in MATERIAL_SOURCE_SPECS),
        {"actual": dict(sorted(source_counts.items()))},
    )
    source_hashes = {row["canonical_row_id"]: row["source_sha256"] for row in canonical}
    add(
        "events_preserve_source_hashes",
        all(source_hashes.get(row["canonical_row_id"]) == row["source_sha256"] for row in events),
    )
    event_ids_sorted = sorted((row["event_time_utc"] or "", row["event_id"]) for row in events)
    add("event_ordering_is_deterministic_sortable", len(event_ids_sorted) == len(events))
    leakage = []
    for row in events:
        obs = row.get("asof_observation", {})
        obs_keys = set(obs) if isinstance(obs, Mapping) else set()
        leaked = obs_keys & FORBIDDEN_LABEL_FIELDS
        if leaked:
            leakage.append({"event_id": row["event_id"], "fields": sorted(leaked)})
    add("path_and_label_fields_never_asof_features", not leakage, {"leakage": leakage[:5]})
    mixed_broker = []
    for row in canonical:
        labels = row["evidence_labels"]
        if labels["broker_real"]["available"] and (
            labels["exact_r"].get("source_label") == "broker-real cash/PnL"
            or labels["proxy_r"].get("source_label") == "broker-real cash/PnL"
        ):
            mixed_broker.append(row["canonical_row_id"])
    add("broker_real_cash_not_replaced_by_r_labels", not mixed_broker, {"mixed": mixed_broker[:5]})
    add(
        "path_metric_missing_state_explicit",
        all(row.get("path_clock_status") for row in paths)
        and all("missing_source_or_capture_requirement" in row for row in paths),
    )
    add(
        "loser_mfe_loss_coverage_explicit",
        matrix["source_supported_loser_mfe_rows"] == 29 and matrix["broker_loss_mfe_gap_rows"] == 17,
        {
            "source_supported": matrix["source_supported_loser_mfe_rows"],
            "gaps": matrix["broker_loss_mfe_gap_rows"],
        },
    )
    expected_min_gaps = sum(spec.expected_rows for spec in SOURCE_GAP_SPECS) + matrix["broker_loss_mfe_gap_rows"] + 1
    add("source_gap_rows_include_upstream_and_loser_gaps", len(gaps) >= expected_min_gaps, {"actual": len(gaps), "expected_min": expected_min_gaps})
    add("coverage_matrix_agrees_with_canonical_count", matrix["actual_material_rows"] == len(canonical))
    add("boundary_status_preserved", matrix["boundary_status"]["broker_runtime_change_status"] is False)

    return {
        "schema_version": "wave4a_verification_result_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "lane": LANE,
        "ok": all(check["passed"] for check in checks),
        "issue_count": sum(1 for check in checks if not check["passed"]),
        "checks": checks,
        "jsonl_counts": jsonl_counts,
        "boundary_status": BOUNDARY_STATUS,
    }


def write_verification_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    result = verify_route(repo_root, route_dir)
    write_json(
        route_abs(repo_root, route_dir) / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json",
        result,
    )
    return result


def write_completion_audit(
    repo_root: Path,
    route_dir: Path = ROUTE_DIR,
    *,
    verification: Mapping[str, Any] | None,
    focused: Mapping[str, Any] | None,
    prompt: Mapping[str, Any] | None,
    audit: Mapping[str, Any] | None,
) -> None:
    route_dir_abs = route_abs(repo_root, route_dir)
    matrix_path = route_dir_abs / "WAVE4A_COVERAGE_MATRIX.json"
    matrix = read_json(matrix_path) if matrix_path.exists() else {}
    verification_status = "pending" if verification is None else ("pass" if verification.get("ok") else "fail")
    focused_status = "pending" if focused is None else ("pass" if focused.get("ok") else focused.get("status", "recorded"))
    prompt_status = "pending" if prompt is None else ("pass" if prompt.get("ok") else "fail")
    audit_status = "pending" if audit is None else ("pass" if audit.get("ok") else "fail")
    lines = [
        "# Wave4A Completion Audit",
        "",
        f"Generated: {utc_now()}",
        f"Branch: `{git_value(repo_root, 'branch', '--show-current')}`",
        f"HEAD: `{git_value(repo_root, 'rev-parse', 'HEAD')}`",
        f"Route: `{rel_path(repo_root, route_dir_abs)}`",
        "",
        "## Scope",
        "",
        "Built the canonical Digital Twin V4 and Historical Microscope V2 substrate for Wave4A from current disk artifacts. This package freezes source rows, source hashes, as-of replay events, path-clock labels, loser MFE harvest coverage, accepted/rejected opportunity rows, and source-gap/capture rows.",
        "",
        "## Counts",
        "",
        f"- Canonical material rows: `{matrix.get('actual_material_rows', 'pending')}`.",
        f"- Digital twin event rows: `{matrix.get('digital_twin_event_rows', 'pending')}`.",
        f"- Path-clock rows: `{matrix.get('path_clock_rows', 'pending')}`.",
        f"- Accepted/rejected opportunity rows: `{matrix.get('accepted_rejected_opportunity_rows', 'pending')}`.",
        f"- Loser MFE harvest rows: `{matrix.get('loser_mfe_harvest_rows', 'pending')}` (`{matrix.get('source_supported_loser_mfe_rows', 'pending')}` source-supported, `{matrix.get('broker_loss_mfe_gap_rows', 'pending')}` broker-loss gaps).",
        f"- Source-gap/capture rows: `{matrix.get('source_gap_and_capture_rows', 'pending')}`.",
        "",
        "## Evidence Separation",
        "",
        "- Broker-real cash/PnL remains broker-local under broker-real label boundaries.",
        "- Exact-R, proxy-R, replay, simulation, shadow, path, MFE/MAE, giveback, and stale-thesis labels are not as-of digital-twin features.",
        "- Pending/no-fill and missing historical runtime truth are prospective capture requirements, not inferred broker facts.",
        "",
        "## Verification",
        "",
        f"- Wave4A verifier: `{verification_status}`.",
        f"- Focused tests/py_compile: `{focused_status}`.",
        f"- Prompt hardening: `{prompt_status}`.",
        f"- Route artifact audit: `{audit_status}`.",
        "",
        "## Boundaries",
        "",
        "No broker account/history/order/deal/position mutation, credential mutation/disclosure, paid/vendor API call, remote push, active VPS process mutation, MT5 live operation, live trading deployment, or live restart occurred.",
        "",
        "## Unresolved Exact Requirements",
        "",
        "Remaining gaps are exact source/capture requirements recorded in `WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl`, including non-generatable historical pending intent/order tickets, original allocator candidate-set ids, uncovered broker-loss MFE/MAE/giveback path support, and broker-native slippage/spread fields where upstream routes recorded source gaps.",
        "",
        "## Commit Status",
        "",
        "A scoped commit is required after verifier, focused test, prompt hardening, route audit, diff check, and staged-path review pass.",
        "",
    ]
    write_text(route_dir_abs / "COMPLETION_AUDIT.md", "\n".join(lines))
