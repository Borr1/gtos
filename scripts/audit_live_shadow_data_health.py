"""Audit live-shadow data health across related logs.

This read-only verifier checks semantic data health that the schema verifier
does not fully cover: every live candidate should have dependent shadow rows,
latest-row semantics should line up, strategy rollups should match registered
candidate strategies, opportunity counting should not double-count duplicates,
and source-not-captured limitations should be explicit instead of hidden as
nulls.

It does not call AI, canary, Databento, MT5 orders, or live trading code.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.trade_record_candidate_backfill import (
    DEFAULT_TRADE_RECORD_ROOT,
    iter_trade_record_candidates,
)
from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DEFAULT_OUTPUT_JSON = Path("research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md")

POINT_IN_TIME_CANDIDATE_LOGS = (
    "v2b_forward_pairs.jsonl",
    "prefill_delivery_path.jsonl",
    "fvg_ob_confluence.jsonl",
    "context_control_ledger.jsonl",
    "live_structural_strategy_metadata.jsonl",
    "databento_live_trigger_decisions.jsonl",
    "sierra_confluence_source_status.jsonl",
    "sierra_depth_feature_snapshots.jsonl",
    "account_truth_reconciliation_status.jsonl",
)

PATH_ALIGNED_CANDIDATE_LOGS = (
    "candidate_path_follow.jsonl",
    "live_candidate_opportunity_clusters.jsonl",
    "live_candidate_strategy_rollups.jsonl",
    "v2b_forward_pair_resolutions.jsonl",
    "prefill_delivery_path_resolutions.jsonl",
    "fvg_ob_confluence_resolutions.jsonl",
    "missed_opportunity_shadow.jsonl",
    "candidate_ltf_path_order.jsonl",
)
EXTRA_SEMANTIC_LOGS = (
    "pending_limit_lifecycle_join_backfill.jsonl",
    "v2_structural_selector_readiness.jsonl",
    "xauusd_same_market_extension_status.jsonl",
    "es_mes_preregistration_status.jsonl",
    "shadow_observer_hardening_status.jsonl",
)

IDENTITY_FIELDS = ("symbol", "broker_symbol", "decision_time_utc", "side", "framework")
PATH_LABEL_TO_OUTCOME = {
    "entry_touched_then_reached_tp1": "ENTRY_TOUCHED_THEN_TP1",
    "went_through_entry_and_continued_to_sl": "ENTRY_TOUCHED_THEN_SL",
    "continued_without_entry_touch_to_tp_area": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
}
LANE_EXPECTATION_MODES = {
    **{name: "candidate_driven_point_in_time" for name in POINT_IN_TIME_CANDIDATE_LOGS},
    **{name: "candidate_driven_path_aligned" for name in PATH_ALIGNED_CANDIDATE_LOGS},
    "strategy_follow_candidates.jsonl": "candidate_registry",
    "live_mechanical_strategy_shadow_outcomes.jsonl": "candidate_path_aligned_strategy_rows",
    "pending_limit_lifecycle_join_backfill.jsonl": "source_driven_lifecycle_join",
    "be_shadow_log.jsonl": "event_waiting_exit_management",
    "partial_close_shadow_log.jsonl": "event_waiting_exit_management",
    "time_in_trade.jsonl": "event_waiting_exit_management",
    "databento_live_confluence.jsonl": "approval_blocked_event_triggered_paid_data",
    "ml_shadow_predictions.jsonl": "candidate_driven_point_in_time",
    "v2_structural_selector_readiness.jsonl": "source_driven_readiness_status",
    "xauusd_same_market_extension_status.jsonl": "source_driven_preregistration_status",
    "es_mes_preregistration_status.jsonl": "source_driven_preregistration_status",
    "shadow_observer_hardening_status.jsonl": "source_driven_observer_hardening_status",
}
KNOWN_OPPORTUNITY_COUNTING_STATUSES = {
    "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
    "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
    "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP",
}
COMMON_ALLOWED_NULL_FIELDS = {
    "_line_no",
    "regime",
    "source_hash",
    "source_symbol",
    "trade_id",
    "mt5_read_error",
}
ALLOWED_NULL_FIELDS_BY_LOG = {
    "account_truth_reconciliation_status.jsonl": {"asof_latest_candle_utc"},
    "candidate_ltf_path_order.jsonl": {"entry_first_touch_utc", "sl_first_touch_utc", "tp1_first_touch_utc"},
    "databento_live_trigger_decisions.jsonl": {"asof_latest_candle_utc"},
    "fvg_ob_confluence.jsonl": {"lower_timeframe_available", "touch_count"},
    "live_candidate_opportunity_clusters.jsonl": {
        "opportunity_entry_first_touch_utc",
        "opportunity_terminal_event_utc",
        "overlapping_active_symbol_opportunity_ids",
    },
    "live_candidate_strategy_rollups.jsonl": {
        "opportunity_entry_first_touch_utc",
        "overlapping_active_symbol_opportunity_ids",
    },
    "live_structural_strategy_metadata.jsonl": {"asof_latest_candle_utc"},
    "ml_shadow_predictions.jsonl": {"trade_id"},
    "prefill_delivery_path.jsonl": {
        "fill_delay_seconds",
        "fill_happened",
        "fvg_ob_swing_state_at_cancel",
        "fvg_ob_swing_state_at_fill",
        "pre_fill_candles",
        "pre_fill_ticks_summary",
        "reversal_leg_timing",
    },
    "sierra_confluence_source_status.jsonl": {"asof_latest_candle_utc"},
    "sierra_depth_feature_snapshots.jsonl": {"asof_latest_candle_utc"},
    "v2b_forward_pairs.jsonl": {"lower_timeframe_available"},
}
CRITICAL_NON_NULL_FIELDS_BY_LOG = {
    "strategy_follow_candidates.jsonl": {
        "candidate_id",
        "created_at_utc",
        "decision_time_utc",
        "symbol",
        "broker_symbol",
        "side",
        "framework",
        "final_outcome_at_log",
        "trade_parameters",
        "external_confluence",
        "strategy_snapshots",
    },
    "ml_shadow_predictions.jsonl": {
        "candidate_id",
        "created_at_utc",
        "decision_time_utc",
        "symbol",
        "broker_symbol",
        "side",
        "framework",
        "trade_parameters",
        "feature_bundle_version",
        "target_version",
        "prediction",
        "feature_vector",
    },
    "candidate_path_follow.jsonl": {
        "candidate_id",
        "created_at_utc",
        "decision_time_utc",
        "asof_latest_candle_utc",
        "symbol",
        "broker_symbol",
        "side",
        "framework",
        "path_label",
        "trade_parameters",
    },
    "live_candidate_opportunity_clusters.jsonl": {
        "candidate_id",
        "created_at_utc",
        "asof_latest_candle_utc",
        "opportunity_id",
        "opportunity_counting_status",
        "opportunity_assignment_algorithm_version",
    },
    "live_candidate_strategy_rollups.jsonl": {
        "candidate_id",
        "created_at_utc",
        "asof_latest_candle_utc",
        "strategy_statuses",
        "strategy_count",
    },
    "live_mechanical_strategy_shadow_outcomes.jsonl": {
        "candidate_id",
        "created_at_utc",
        "asof_latest_candle_utc",
        "strategy_id",
        "score_status",
        "outcome_status",
        "path_label",
    },
    "sierra_depth_feature_snapshots.jsonl": {
        "candidate_id",
        "created_at_utc",
        "decision_time_utc",
        "symbol",
        "depth_path",
        "feature_status",
        "features_present",
        "paid_fetch_attempted",
        "paid_data_calls",
        "no_leak_status",
        "promotion_verdict",
    },
}


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    if not path.exists():
        return rows, issues
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                issues.append(
                    issue(
                        "SERIOUS",
                        "INVALID_JSONL_ROW",
                        path.name,
                        f"line {line_no}: {exc}",
                        candidate_id=None,
                    )
                )
                continue
            if not isinstance(row, dict):
                issues.append(
                    issue(
                        "SERIOUS",
                        "NON_OBJECT_JSONL_ROW",
                        path.name,
                        f"line {line_no} is {type(row).__name__}, expected object",
                        candidate_id=None,
                    )
                )
                continue
            row["_line_no"] = line_no
            rows.append(row)
    return rows, issues


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def latest_by_candidate_asof(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_key = (
            parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            parse_utc(row.get("created_at_utc"))
            or parse_utc(row.get("backfilled_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc),
            int(row.get("_line_no") or 0),
        )
        previous = latest.get(cid) or {}
        previous_key = (
            parse_utc(previous.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            parse_utc(previous.get("created_at_utc"))
            or parse_utc(previous.get("backfilled_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc),
            int(previous.get("_line_no") or 0),
        )
        if current_key >= previous_key:
            latest[cid] = row
    return latest


def normalize_source_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").lstrip("./")


def latest_mechanical_by_key(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if not cid or not strategy_id or not asof:
            continue
        key = (cid, strategy_id, asof)
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc((latest.get(key) or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if (current_created, int(row.get("_line_no") or 0)) >= (
            previous_created,
            int((latest.get(key) or {}).get("_line_no") or 0),
        ):
            latest[key] = row
    return latest


def issue(
    severity: str,
    code: str,
    log: str,
    message: str,
    *,
    candidate_id: str | None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "log": log,
        "candidate_id": candidate_id,
        "message": message,
    }


def strategy_ids(candidate: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for snapshot in candidate.get("strategy_snapshots") or []:
        if isinstance(snapshot, dict) and snapshot.get("strategy_id"):
            ids.add(str(snapshot["strategy_id"]))
    return ids


def compare_identity(
    candidate: dict[str, Any],
    row: dict[str, Any],
    log_name: str,
    issues: list[dict[str, Any]],
) -> None:
    cid = str(candidate.get("candidate_id") or "")
    for field in IDENTITY_FIELDS:
        left = candidate.get(field)
        right = row.get(field)
        if left is None or right is None:
            continue
        if str(left) != str(right):
            issues.append(
                issue(
                    "SERIOUS",
                    "CANDIDATE_IDENTITY_CONFLICT",
                    log_name,
                    f"{field} mismatch: candidate={left!r}, row={right!r}",
                    candidate_id=cid,
                )
            )


def trade_params(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters")
    return params if isinstance(params, dict) else {}


def _m5_refinement_overrides(record: dict[str, Any]) -> dict[str, Any]:
    instrumentation = record.get("instrumentation")
    if not isinstance(instrumentation, dict):
        return {}
    details = instrumentation.get("m5_refinement_details")
    if not isinstance(details, dict) or details.get("applied") is not True:
        return {}
    overrides = details.get("overrides")
    return overrides if isinstance(overrides, dict) else {}


def effective_trade_record_params(trade_record: Any) -> dict[str, Any]:
    """Return the trade geometry that downstream shadow rows should mirror.

    NAS100 and other instruments can run a deterministic M5 entry refinement
    after the raw AI candidate response is saved. The trade record keeps both
    the original AI geometry and the applied override details; candidate shadow
    rows correctly use the effective/refined geometry, so audit comparisons
    need to do the same.
    """
    params = dict(trade_record.trade_parameters or {})
    overrides = _m5_refinement_overrides(trade_record.record)
    for field in ("entry_price", "stop_loss", "take_profit_1", "risk_reward_ratio"):
        if overrides.get(field) is not None:
            params[field] = overrides[field]
    return params


def values_match(expected: Any, observed: Any, *, tolerance: float = 1e-8) -> bool:
    try:
        return abs(float(expected) - float(observed)) <= tolerance
    except (TypeError, ValueError):
        return str(expected) == str(observed)


def compare_trade_geometry(
    candidate: dict[str, Any],
    row: dict[str, Any],
    log_name: str,
    issues: list[dict[str, Any]],
) -> None:
    cid = str(candidate.get("candidate_id") or "")
    candidate_params = trade_params(candidate)
    row_params = row.get("trade_parameters") if isinstance(row.get("trade_parameters"), dict) else {}
    row_metrics = row.get("path_metrics") if isinstance(row.get("path_metrics"), dict) else {}
    for field in ("entry_price", "stop_loss", "take_profit_1"):
        expected = candidate_params.get(field)
        observed = row_params.get(field, row_metrics.get(field))
        if expected is None or observed is None:
            continue
        if not values_match(expected, observed):
            issues.append(
                issue(
                    "SERIOUS",
                    "TRADE_GEOMETRY_CONFLICT",
                    log_name,
                    f"{field} mismatch: candidate={expected!r}, row={observed!r}",
                    candidate_id=cid,
                )
            )


def audit_candidate_coverage(
    candidates: dict[str, dict[str, Any]],
    latest_logs: dict[str, dict[str, dict[str, Any]]],
    asof_latest_logs: dict[str, dict[str, dict[str, Any]]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage: dict[str, Any] = {}
    latest_paths = latest_logs.get("candidate_path_follow.jsonl", {})
    for log_name in POINT_IN_TIME_CANDIDATE_LOGS + PATH_ALIGNED_CANDIDATE_LOGS:
        latest_rows = latest_logs.get(log_name, {})
        missing: list[str] = []
        asof_mismatch: list[str] = []
        covered = 0
        for cid, candidate in candidates.items():
            row = latest_rows.get(cid)
            if not row:
                missing.append(cid)
                issues.append(
                    issue(
                        "SERIOUS",
                        "MISSING_CANDIDATE_COVERAGE",
                        log_name,
                        "candidate has no latest row in dependent shadow log",
                        candidate_id=cid,
                    )
                )
                continue
            covered += 1
            compare_identity(candidate, row, log_name, issues)
            compare_trade_geometry(candidate, row, log_name, issues)
            if log_name in PATH_ALIGNED_CANDIDATE_LOGS and log_name != "candidate_path_follow.jsonl":
                path_asof = str((latest_paths.get(cid) or {}).get("asof_latest_candle_utc") or "")
                row_asof = str(row.get("asof_latest_candle_utc") or "")
                asof_row = (asof_latest_logs.get(log_name) or {}).get(cid) or {}
                coverage_asof = str(asof_row.get("asof_latest_candle_utc") or row_asof)
                if path_asof and row_asof and path_asof != row_asof and path_asof != coverage_asof:
                    asof_mismatch.append(cid)
                    issues.append(
                        issue(
                            "SERIOUS",
                            "LATEST_ASOF_MISMATCH",
                            log_name,
                            f"latest path asof {path_asof} != latest {log_name} asof {row_asof}",
                            candidate_id=cid,
                        )
                    )
        coverage[log_name] = {
            "covered_candidates": covered,
            "missing_candidates": missing,
            "asof_mismatch_candidates": asof_mismatch,
        }
    return coverage


def audit_all_row_candidate_identity(
    candidates: dict[str, dict[str, Any]],
    all_rows: dict[str, list[dict[str, Any]]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    rows_checked = 0
    orphan_by_log: dict[str, list[str]] = defaultdict(list)
    observed_identity_values: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for log_name, rows in all_rows.items():
        for row in rows:
            cid = str(row.get("candidate_id") or "")
            if not cid:
                continue
            rows_checked += 1
            candidate = candidates.get(cid)
            if not candidate:
                if len(orphan_by_log[log_name]) < 50:
                    orphan_by_log[log_name].append(cid)
                issues.append(
                    issue(
                        "SERIOUS",
                        "ORPHAN_DEPENDENT_CANDIDATE_ROW",
                        log_name,
                        "row has candidate_id that is absent from strategy_follow_candidates.jsonl",
                        candidate_id=cid,
                    )
                )
                continue
            for field in IDENTITY_FIELDS:
                if row.get(field) is not None:
                    observed_identity_values[cid][field].add(str(row[field]))
            compare_identity(candidate, row, log_name, issues)
            compare_trade_geometry(candidate, row, log_name, issues)

    variant_conflicts = {
        cid: {field: sorted(values) for field, values in fields.items() if len(values) > 1}
        for cid, fields in observed_identity_values.items()
        if any(len(values) > 1 for values in fields.values())
    }
    for cid, variants in variant_conflicts.items():
        issues.append(
            issue(
                "SERIOUS",
                "CANDIDATE_IDENTITY_VARIANTS_ACROSS_ROWS",
                "candidate_scoped_shadow_logs",
                f"candidate_id maps to multiple non-null identity variants across rows: {variants}",
                candidate_id=cid,
            )
        )

    return {
        "candidate_scoped_rows_checked": rows_checked,
        "orphan_dependent_rows_by_log": dict(orphan_by_log),
        "candidate_identity_variant_conflicts": variant_conflicts,
    }


def audit_external_confluence(candidates: dict[str, dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    sierra_statuses: Counter[str] = Counter()
    databento_statuses: Counter[str] = Counter()
    paid_fetch_attempted = 0
    paid_data_calls = 0
    missing_sierra: list[str] = []
    missing_databento: list[str] = []
    for cid, candidate in candidates.items():
        external = candidate.get("external_confluence") if isinstance(candidate.get("external_confluence"), dict) else {}
        sierra = external.get("sierra") if isinstance(external.get("sierra"), dict) else {}
        databento = external.get("databento") if isinstance(external.get("databento"), dict) else {}
        if not sierra:
            missing_sierra.append(cid)
            issues.append(issue("SERIOUS", "MISSING_SIERRA_CONFLUENCE_OBJECT", "strategy_follow_candidates.jsonl", "external_confluence.sierra is missing", candidate_id=cid))
        else:
            sierra_statuses[str(sierra.get("status") or "UNKNOWN")] += 1
            if sierra.get("paid_fetch_attempted") is True:
                paid_fetch_attempted += 1
        if not databento:
            missing_databento.append(cid)
            issues.append(issue("SERIOUS", "MISSING_DATABENTO_CONFLUENCE_OBJECT", "strategy_follow_candidates.jsonl", "external_confluence.databento is missing", candidate_id=cid))
        else:
            databento_statuses[str(databento.get("status") or "UNKNOWN")] += 1
            if databento.get("paid_fetch_attempted") is True:
                paid_fetch_attempted += 1
            calls = databento.get("paid_data_calls") or databento.get("cached_request_count") or 0
            try:
                paid_data_calls += int(calls) if databento.get("paid_fetch_attempted") is True else 0
            except (TypeError, ValueError):
                pass
    if paid_fetch_attempted:
        issues.append(
            issue(
                "SERIOUS",
                "PAID_FETCH_ATTEMPTED_IN_LIVE_SHADOW_CANDIDATE",
                "strategy_follow_candidates.jsonl",
                f"{paid_fetch_attempted} candidate confluence objects show paid fetch attempts",
                candidate_id=None,
            )
        )
    return {
        "sierra_statuses": dict(sierra_statuses),
        "databento_statuses": dict(databento_statuses),
        "missing_sierra_candidates": missing_sierra,
        "missing_databento_candidates": missing_databento,
        "paid_fetch_attempted_count": paid_fetch_attempted,
        "paid_data_calls_when_paid_fetch_attempted": paid_data_calls,
    }


def audit_trade_record_candidate_coverage(
    root: Path,
    candidates: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
    *,
    candidate_rows_all: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    include_dates = {
        dt.date()
        for row in candidates.values()
        if (dt := parse_utc(row.get("decision_time_utc"))) is not None
    }
    include_dates.add(datetime.now(timezone.utc).date())
    trade_records, skipped = iter_trade_record_candidates(
        root / DEFAULT_TRADE_RECORD_ROOT,
        include_dates=include_dates,
    )
    candidate_pool = candidate_rows_all or list(candidates.values())
    candidates_by_source_file = {
        normalize_source_path(row.get("source_file")): row
        for row in candidate_pool
        if row.get("source_file")
    }
    trade_records_by_candidate_id: dict[str, list[Any]] = {}
    for trade_record in trade_records:
        trade_records_by_candidate_id.setdefault(trade_record.candidate_id, []).append(trade_record)
    missing: list[str] = []
    mismatches: list[dict[str, Any]] = []
    documented_collisions: list[dict[str, Any]] = []
    matched = 0
    for trade_record in trade_records:
        source_key = normalize_source_path(trade_record.path)
        candidate = candidates_by_source_file.get(source_key)
        collision_rows = trade_records_by_candidate_id.get(trade_record.candidate_id, [])
        if candidate is None and len(collision_rows) > 1:
            if not any(item["candidate_id"] == trade_record.candidate_id for item in documented_collisions):
                documented_collisions.append(
                    {
                        "candidate_id": trade_record.candidate_id,
                        "source_files": [str(row.path) for row in collision_rows],
                        "reason": "multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison",
                    }
                )
            continue
        if candidate is None:
            candidate = candidates.get(trade_record.candidate_id)
        if not candidate:
            missing.append(trade_record.candidate_id)
            issues.append(
                issue(
                    "SERIOUS",
                    "MISSING_TRADE_RECORD_CANDIDATE_SHADOW",
                    "strategy_follow_candidates.jsonl",
                    f"trade record {trade_record.path} is AI CANDIDATE but has no candidate shadow row",
                    candidate_id=trade_record.candidate_id,
                )
            )
            continue
        matched += 1
        comparisons = {
            "symbol": (trade_record.symbol, candidate.get("symbol")),
            "decision_time_utc": (trade_record.decision_time_utc, candidate.get("decision_time_utc")),
            "side": (trade_record.side, candidate.get("side")),
            "framework": (trade_record.framework, candidate.get("framework")),
            "final_outcome_at_log": (trade_record.final_outcome, candidate.get("final_outcome_at_log")),
        }
        candidate_params = trade_params(candidate)
        trade_record_params = effective_trade_record_params(trade_record)
        for field in ("entry_price", "stop_loss", "take_profit_1"):
            expected = trade_record_params.get(field)
            observed = candidate_params.get(field)
            if expected is not None or observed is not None:
                comparisons[f"trade_parameters.{field}"] = (expected, observed)
        for field, (expected, observed) in comparisons.items():
            if expected is None or observed is None:
                continue
            matches = (
                values_match(expected, observed)
                if field.startswith("trade_parameters.")
                else str(expected) == str(observed)
            )
            if not matches:
                mismatch = {
                    "candidate_id": trade_record.candidate_id,
                    "field": field,
                    "trade_record": expected,
                    "candidate_shadow": observed,
                }
                mismatches.append(mismatch)
                issues.append(
                    issue(
                        "SERIOUS",
                        "TRADE_RECORD_CANDIDATE_VALUE_MISMATCH",
                        "strategy_follow_candidates.jsonl",
                        f"{field} mismatch vs trade record {trade_record.path}: trade_record={expected!r}, shadow={observed!r}",
                        candidate_id=trade_record.candidate_id,
                    )
                )
    return {
        "trade_records_seen": len(trade_records),
        "matched_candidate_shadow_rows": matched,
        "missing_candidate_shadow_rows": missing,
        "value_mismatches": mismatches,
        "documented_candidate_id_collisions": documented_collisions,
        "include_dates": sorted(item.isoformat() for item in include_dates),
        "skipped": skipped,
    }


def audit_mechanical_rows(
    candidates: dict[str, dict[str, Any]],
    latest_paths: dict[str, dict[str, Any]],
    mechanical_rows: list[dict[str, Any]],
    rollups: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_mech = latest_mechanical_by_key(mechanical_rows)
    missing: dict[str, list[str]] = {}
    extra: dict[str, list[str]] = {}
    outcome_mismatches: list[dict[str, Any]] = []
    strategy_counts: Counter[int] = Counter()
    for cid, candidate in candidates.items():
        expected = strategy_ids(candidate)
        path = latest_paths.get(cid) or {}
        asof = str(path.get("asof_latest_candle_utc") or "")
        if not expected or not asof:
            continue
        observed = {
            strategy_id
            for (candidate_id, strategy_id, row_asof), _row in latest_mech.items()
            if candidate_id == cid and row_asof == asof
        }
        strategy_counts[len(observed)] += 1
        missing_ids = sorted(expected - observed)
        extra_ids = sorted(observed - expected)
        if missing_ids:
            missing[cid] = missing_ids
            issues.append(
                issue(
                    "SERIOUS",
                    "MISSING_MECHANICAL_STRATEGY_ROWS",
                    "live_mechanical_strategy_shadow_outcomes.jsonl",
                    f"missing latest strategy rows at {asof}: {missing_ids}",
                    candidate_id=cid,
                )
            )
        if extra_ids:
            extra[cid] = extra_ids
            issues.append(
                issue(
                    "MODERATE",
                    "UNREGISTERED_MECHANICAL_STRATEGY_ROWS",
                    "live_mechanical_strategy_shadow_outcomes.jsonl",
                    f"observed strategy rows not registered on candidate snapshot: {extra_ids}",
                    candidate_id=cid,
                )
            )
        rollup = rollups.get(cid) or {}
        rollup_statuses = rollup.get("strategy_statuses") if isinstance(rollup.get("strategy_statuses"), dict) else {}
        if rollup_statuses:
            rollup_ids = set(rollup_statuses)
            if expected and rollup_ids != expected:
                issues.append(
                    issue(
                        "SERIOUS",
                        "ROLLUP_STRATEGY_SET_MISMATCH",
                        "live_candidate_strategy_rollups.jsonl",
                        f"rollup strategies differ from candidate snapshots: missing={sorted(expected - rollup_ids)}, extra={sorted(rollup_ids - expected)}",
                        candidate_id=cid,
                    )
                )
        expected_outcome = PATH_LABEL_TO_OUTCOME.get(str(path.get("path_label") or ""))
        if expected_outcome:
            for strategy_id in expected:
                row = latest_mech.get((cid, strategy_id, asof))
                if not row:
                    continue
                score_status = str(row.get("score_status") or "")
                outcome = str(row.get("outcome_status") or "")
                if score_status == "COMPUTED_FROM_CANDIDATE_PATH" and outcome != expected_outcome:
                    outcome_mismatches.append({"candidate_id": cid, "strategy_id": strategy_id, "expected": expected_outcome, "observed": outcome})
                    issues.append(
                        issue(
                            "SERIOUS",
                            "MECHANICAL_OUTCOME_PATH_MISMATCH",
                            "live_mechanical_strategy_shadow_outcomes.jsonl",
                            f"{strategy_id} computed outcome {outcome} does not match path-derived {expected_outcome}",
                            candidate_id=cid,
                        )
                    )
    return {
        "latest_strategy_row_counts": dict(strategy_counts),
        "missing_by_candidate": missing,
        "extra_by_candidate": extra,
        "outcome_mismatches": outcome_mismatches,
    }


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def audit_path_label_geometry(
    latest_paths: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    checked = 0
    mismatches: list[dict[str, Any]] = []
    for cid, row in latest_paths.items():
        label = str(row.get("path_label") or "").lower()
        if not label:
            continue
        checked += 1
        expectations: list[tuple[str, bool, str]] = []
        if "entry_touched" in label or "went_through_entry" in label:
            expectations.append(("touched_entry", True, "label implies entry was touched"))
        if "no_touch" in label or "without_entry_touch" in label:
            expectations.append(("touched_entry", False, "label implies entry was not touched"))
        if "tp1" in label or "tp_area" in label:
            expectations.append(("hit_tp1", True, "label implies TP/TP1 area was reached"))
        if label.endswith("_sl") or "_sl" in label or "continued_to_sl" in label:
            expectations.append(("hit_sl", True, "label implies SL area was reached"))
        for field, expected, reason in expectations:
            observed = _bool_value(row.get(field))
            if observed is None or observed == expected:
                continue
            detail = {
                "candidate_id": cid,
                "path_label": row.get("path_label"),
                "field": field,
                "expected": expected,
                "observed": observed,
                "reason": reason,
            }
            mismatches.append(detail)
            issues.append(
                issue(
                    "SERIOUS",
                    "PATH_LABEL_GEOMETRY_MISMATCH",
                    "candidate_path_follow.jsonl",
                    f"{reason}: {field}={observed!r} for path_label={row.get('path_label')!r}",
                    candidate_id=cid,
                )
            )
    return {"checked_latest_path_rows": checked, "mismatches": mismatches}


def audit_pending_lifecycle_consistency(
    candidates: dict[str, dict[str, Any]],
    lifecycle_joins: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    limit_placed_candidates: list[str] = []
    missing_join: list[str] = []
    unexpected_join: list[str] = []
    trade_id_mismatches: list[dict[str, Any]] = []
    joined_without_source: list[str] = []
    for cid, candidate in candidates.items():
        final_outcome = str(candidate.get("final_outcome_at_log") or "")
        candidate_trade_id = str(candidate.get("trade_id") or "")
        is_limit_placed = final_outcome == "LIMIT_PLACED" or bool(candidate_trade_id)
        join = lifecycle_joins.get(cid)
        if is_limit_placed:
            limit_placed_candidates.append(cid)
            if not join:
                missing_join.append(cid)
                issues.append(
                    issue(
                        "SERIOUS",
                        "MISSING_LIMIT_PLACED_LIFECYCLE_JOIN",
                        "pending_limit_lifecycle_join_backfill.jsonl",
                        "LIMIT_PLACED candidate has no lifecycle join/backfill row",
                        candidate_id=cid,
                    )
                )
                continue
        elif join and str(join.get("join_status") or "").startswith("MATCHED"):
            unexpected_join.append(cid)
            issues.append(
                issue(
                    "SERIOUS",
                    "UNEXPECTED_LIFECYCLE_JOIN_FOR_NON_LIMIT_CANDIDATE",
                    "pending_limit_lifecycle_join_backfill.jsonl",
                    f"non-LIMIT_PLACED candidate has matched lifecycle join_status={join.get('join_status')!r}",
                    candidate_id=cid,
                )
            )
        if not join:
            continue
        join_trade_id = str(join.get("trade_id") or "")
        if candidate_trade_id and join_trade_id and candidate_trade_id != join_trade_id:
            mismatch = {"candidate_id": cid, "candidate_trade_id": candidate_trade_id, "join_trade_id": join_trade_id}
            trade_id_mismatches.append(mismatch)
            issues.append(
                issue(
                    "SERIOUS",
                    "LIFECYCLE_TRADE_ID_MISMATCH",
                    "pending_limit_lifecycle_join_backfill.jsonl",
                    f"candidate trade_id={candidate_trade_id!r} != lifecycle join trade_id={join_trade_id!r}",
                    candidate_id=cid,
                )
            )
        join_status = str(join.get("join_status") or "")
        if join_status.startswith("MATCHED") and not join.get("source_lifecycle_trade_id"):
            joined_without_source.append(cid)
            issues.append(
                issue(
                    "SERIOUS",
                    "LIFECYCLE_JOIN_MISSING_SOURCE_TRADE_ID",
                    "pending_limit_lifecycle_join_backfill.jsonl",
                    f"matched lifecycle join lacks source_lifecycle_trade_id for join_status={join_status!r}",
                    candidate_id=cid,
                )
            )
    return {
        "limit_placed_candidates": limit_placed_candidates,
        "missing_limit_placed_join_candidates": missing_join,
        "unexpected_join_candidates": unexpected_join,
        "trade_id_mismatches": trade_id_mismatches,
        "joined_without_source_trade_id": joined_without_source,
    }


def audit_source_status_feature_interpretation(
    latest_logs: dict[str, dict[str, dict[str, Any]]],
    candidates: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []

    def add_mismatch(log_name: str, cid: str | None, message: str, row: dict[str, Any]) -> None:
        detail = {
            "log": log_name,
            "candidate_id": cid,
            "message": message,
            "status": row.get("status") or row.get("source_status") or row.get("feature_status"),
        }
        mismatches.append(detail)
        issues.append(
            issue(
                "SERIOUS",
                "SOURCE_STATUS_FEATURE_INTERPRETATION_MISMATCH",
                log_name,
                message,
                candidate_id=cid,
            )
        )

    for cid, row in latest_logs.get("sierra_depth_feature_snapshots.jsonl", {}).items():
        feature_status = str(row.get("feature_status") or "")
        features_present = _bool_value(row.get("features_present"))
        depth_path = row.get("depth_path")
        if feature_status == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL":
            if features_present is True or depth_path:
                add_mismatch(
                    "sierra_depth_feature_snapshots.jsonl",
                    cid,
                    "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL cannot carry extracted features or a depth path",
                    row,
                )
        if feature_status == "FEATURES_EXTRACTED":
            if features_present is False or not depth_path:
                add_mismatch(
                    "sierra_depth_feature_snapshots.jsonl",
                    cid,
                    "FEATURES_EXTRACTED requires features_present=true and a depth_path",
                    row,
                )

    for cid, row in latest_logs.get("sierra_confluence_source_status.jsonl", {}).items():
        source_status = str(row.get("source_status") or row.get("sierra_status") or "")
        interpretation = str(row.get("interpretation_status") or "")
        features_present = _bool_value(row.get("features_present"))
        if source_status == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL":
            if features_present is True or interpretation.startswith("USABLE"):
                add_mismatch(
                    "sierra_confluence_source_status.jsonl",
                    cid,
                    "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL cannot be interpreted as usable feature confluence",
                    row,
                )

    for cid, candidate in candidates.items():
        external = candidate.get("external_confluence") if isinstance(candidate.get("external_confluence"), dict) else {}
        sierra = external.get("sierra") if isinstance(external.get("sierra"), dict) else {}
        if not sierra:
            continue
        status = str(sierra.get("status") or sierra.get("source_status") or "")
        interpretation = str(sierra.get("interpretation_status") or "")
        features = sierra.get("features") if isinstance(sierra.get("features"), dict) else {}
        if status == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL" and (features or interpretation.startswith("USABLE")):
            add_mismatch(
                "strategy_follow_candidates.jsonl",
                cid,
                "candidate Sierra confluence says no registered proxy but carries usable interpretation/features",
                sierra,
            )

    return {"mismatches": mismatches}


def audit_opportunity_counts(clusters: dict[str, dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    by_opp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_counts: Counter[str] = Counter()
    version_counts: Counter[str] = Counter()
    unknown_status_candidates: list[str] = []
    for row in clusters.values():
        opp = str(row.get("opportunity_id") or "")
        if opp:
            by_opp[opp].append(row)
        status = str(row.get("opportunity_counting_status") or "UNKNOWN")
        status_counts[status] += 1
        if status not in KNOWN_OPPORTUNITY_COUNTING_STATUSES:
            cid = str(row.get("candidate_id") or "")
            unknown_status_candidates.append(cid)
            issues.append(
                issue(
                    "SERIOUS",
                    "OPPORTUNITY_UNKNOWN_COUNTING_STATUS",
                    "live_candidate_opportunity_clusters.jsonl",
                    f"unknown opportunity_counting_status={status!r}",
                    candidate_id=cid or None,
                )
            )
        version_counts[str(row.get("opportunity_assignment_algorithm_version") or "UNVERSIONED")] += 1

    countable_by_opp: dict[str, int] = {}
    primary_missing: list[str] = []
    primary_suppressed_by_overlap: list[str] = []
    duplicate_materiality_false: list[str] = []
    for opp, rows in by_opp.items():
        countable = [
            row for row in rows
            if row.get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
        ]
        countable_by_opp[opp] = len(countable)
        primary_rows = [
            row for row in rows
            if row.get("opportunity_duplicate_status") == "PRIMARY_UNIQUE_OPPORTUNITY"
            or int(row.get("opportunity_sequence_index") or -1) == 0
        ]
        duplicate_rows = [row for row in rows if row not in primary_rows]
        primary_blocked_by_overlap = (
            len(primary_rows) == 1
            and primary_rows[0].get("opportunity_counting_status") == "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP"
            and primary_rows[0].get("same_symbol_overlap_status") == "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE"
            and bool(primary_rows[0].get("overlapping_active_symbol_opportunity_ids"))
        )
        duplicates_follow_blocked_primary = all(
            row.get("opportunity_counting_status") == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
            and row.get("opportunity_duplicate_status") == "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"
            and row.get("opportunity_first_candidate_id") == primary_rows[0].get("candidate_id")
            for row in duplicate_rows
        ) if primary_blocked_by_overlap else False
        overlap_suppressed = (
            len(countable) == 0
            and primary_blocked_by_overlap
            and duplicates_follow_blocked_primary
        )
        if overlap_suppressed:
            primary_suppressed_by_overlap.append(opp)
        elif len(countable) != 1:
            severity = "SERIOUS"
            code = "OPPORTUNITY_PRIMARY_COUNT_INVALID"
            message = f"opportunity_id {opp} has {len(countable)} countable primary rows"
            issues.append(issue(severity, code, "live_candidate_opportunity_clusters.jsonl", message, candidate_id=None))
            if not countable:
                primary_missing.append(opp)
        for row in rows:
            status = row.get("opportunity_counting_status")
            similarity = row.get("opportunity_similarity") if isinstance(row.get("opportunity_similarity"), dict) else {}
            if status == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE" and similarity.get("materially_same_setup") is False:
                duplicate_materiality_false.append(str(row.get("candidate_id") or ""))
                issues.append(
                    issue(
                        "SERIOUS",
                        "DUPLICATE_MARKED_BUT_NOT_MATERIALLY_SAME",
                        "live_candidate_opportunity_clusters.jsonl",
                        "row is duplicate-not-countable while opportunity_similarity.materially_same_setup is false",
                        candidate_id=str(row.get("candidate_id") or ""),
                    )
                )
    return {
        "status_counts": dict(status_counts),
        "algorithm_versions": dict(version_counts),
        "unique_opportunity_ids": len(by_opp),
        "countable_primary_by_opportunity": countable_by_opp,
        "primary_missing_opportunity_ids": primary_missing,
        "primary_suppressed_by_overlap_opportunity_ids": primary_suppressed_by_overlap,
        "duplicate_materiality_false_candidates": duplicate_materiality_false,
        "unknown_status_candidates": unknown_status_candidates,
        "raw_cluster_rows": len(clusters),
        "classified_cluster_rows": sum(status_counts.values()),
    }


def audit_lane_expectations(all_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    modes: dict[str, list[str]] = defaultdict(list)
    row_counts_by_mode: Counter[str] = Counter()
    for log_name, mode in LANE_EXPECTATION_MODES.items():
        modes[mode].append(log_name)
        row_counts_by_mode[mode] += len(all_rows.get(log_name, []))
    return {
        "expectation_modes": {mode: sorted(names) for mode, names in modes.items()},
        "row_counts_by_mode": dict(row_counts_by_mode),
        "staleness_policy": {
            "candidate_registry": "candidate rows are event/candidate driven and must have dependent coverage when present",
            "candidate_driven_point_in_time": "one latest row per candidate or explicit source/status blocker",
            "candidate_driven_path_aligned": "latest asof must align to candidate_path_follow when candidate paths advance",
            "source_driven_lifecycle_join": "freshness follows source lifecycle events, not wall-clock churn",
            "source_driven_readiness_status": "freshness follows upstream evidence signatures, not wall-clock churn",
            "source_driven_preregistration_status": "freshness follows preregistration/source-status signatures, not wall-clock churn",
            "source_driven_observer_hardening_status": "freshness follows observer source/status signatures and stale-status transitions",
            "event_waiting_exit_management": "empty is valid only with no filled trade/trigger status",
            "approval_blocked_event_triggered_paid_data": "no paid live rows until approved trigger policy is active",
        },
    }


def audit_source_limitations(structural_rows: dict[str, dict[str, Any]], rollups: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_not_captured_fields: Counter[str] = Counter()
    legacy_source_not_captured_fields: Counter[str] = Counter()
    affected_strategies: Counter[str] = Counter()
    unresolved_score_statuses: Counter[str] = Counter()
    unresolved_strategy_statuses: Counter[str] = Counter()
    legacy_unresolved_score_statuses: Counter[str] = Counter()
    legacy_unresolved_strategy_statuses: Counter[str] = Counter()
    candidates_with_source_not_captured: list[str] = []
    for cid, row in structural_rows.items():
        missing = row.get("missing_exact_required_fields") if isinstance(row.get("missing_exact_required_fields"), dict) else {}
        is_legacy_candidate_capture = (
            row.get("decision_time_structural_capture_status")
            == "LEGACY_CANDIDATE_ROW_WITHOUT_STRUCTURAL_SOURCE_CAPTURE"
        )
        found = False
        for field, status in missing.items():
            if status == "SOURCE_NOT_CAPTURED":
                if is_legacy_candidate_capture:
                    legacy_source_not_captured_fields[str(field)] += 1
                else:
                    source_not_captured_fields[str(field)] += 1
                found = True
        if found:
            candidates_with_source_not_captured.append(cid)
        for strategy in row.get("affected_strategy_ids") or []:
            affected_strategies[str(strategy)] += 1
    for cid, row in rollups.items():
        structural = structural_rows.get(cid) or {}
        is_legacy_candidate_capture = (
            structural.get("decision_time_structural_capture_status")
            == "LEGACY_CANDIDATE_ROW_WITHOUT_STRUCTURAL_SOURCE_CAPTURE"
        )
        unresolved = row.get("unresolved_strategies") if isinstance(row.get("unresolved_strategies"), dict) else {}
        for strategy, details in unresolved.items():
            if not isinstance(details, dict):
                continue
            score_status = str(details.get("score_status") or "UNKNOWN")
            strategy_status = str(details.get("strategy_status") or strategy)
            if is_legacy_candidate_capture and score_status.startswith("MISSING"):
                legacy_unresolved_score_statuses[score_status] += 1
                legacy_unresolved_strategy_statuses[strategy_status] += 1
            else:
                unresolved_score_statuses[score_status] += 1
                unresolved_strategy_statuses[strategy_status] += 1
    return {
        "source_not_captured_fields": dict(source_not_captured_fields),
        "legacy_source_not_captured_fields": dict(legacy_source_not_captured_fields),
        "affected_strategies": dict(affected_strategies),
        "candidates_with_source_not_captured": candidates_with_source_not_captured,
        "unresolved_score_statuses": dict(unresolved_score_statuses),
        "unresolved_strategy_statuses": dict(unresolved_strategy_statuses),
        "legacy_unresolved_score_statuses": dict(legacy_unresolved_score_statuses),
        "legacy_unresolved_strategy_statuses": dict(legacy_unresolved_strategy_statuses),
        "backfill_rule": "Do not synthesize SOURCE_NOT_CAPTURED fields from later candles. Backfill only from original decision-time rows/files that contain the exact value.",
    }


def _is_null_like(value: Any) -> bool:
    return value is None or value == "" or value == []


def _is_conditionally_allowed_null(log_name: str, field: str, row: dict[str, Any]) -> bool:
    if log_name in {
        "live_candidate_opportunity_clusters.jsonl",
        "live_candidate_strategy_rollups.jsonl",
    } and field == "asof_latest_candle_utc":
        return str(row.get("candidate_path_status") or "") == "WAITING_FOR_PATH_ROW" or str(
            row.get("manual_backfill_status") or ""
        ) == "SOURCE_NOT_CAPTURED"
    if log_name == "sierra_depth_feature_snapshots.jsonl" and field in {
        "depth_path",
        "sierra_futures_symbol",
        "sierra_source_symbol",
    }:
        return str(row.get("feature_status") or "") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    if log_name == "sierra_confluence_source_status.jsonl" and field in {
        "sierra_futures_symbol",
        "sierra_source_symbol",
    }:
        return str(row.get("sierra_status") or "") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    if log_name == "candidate_ltf_path_order.jsonl" and field in {
        "terminal_event_utc",
        "terminal_event_r",
    }:
        return str(row.get("terminal_outcome_status") or "").endswith("_UNRESOLVED_BY_LTF_ASOF") or bool(
            row.get("terminal_order_ambiguity")
        )
    if log_name != "live_mechanical_strategy_shadow_outcomes.jsonl":
        return False
    if field == "strategy_proxy_r":
        score_status = str(row.get("score_status") or "")
        outcome_status = str(row.get("outcome_status") or "")
        if score_status not in {
            "COMPUTED_FROM_CANDIDATE_PATH",
            "COMPUTED_FROM_PENDING_LIFECYCLE",
            "COMPUTED_FROM_LTF_PATH_ORDER",
        }:
            return True
        return outcome_status in {
            "ENTRY_TOUCHED_UNRESOLVED",
            "M15_PATH_AMBIGUOUS_TP1_AND_SL",
            "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
            "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
            "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
        }
    if field == "pending_lifecycle_candidate_id":
        return str(row.get("pending_lifecycle_match_method") or "") == "symbol_side_exact_price_geometry"
    if field in {
        "ltf_path_order_label",
        "ltf_terminal_outcome_status",
        "ltf_terminal_event_utc",
        "ltf_terminal_order_ambiguity",
    }:
        return str(row.get("outcome_source") or "") != "candidate_ltf_path_order"
    return False


def audit_null_fields(
    latest_logs: dict[str, dict[str, dict[str, Any]]],
    latest_mechanical: dict[tuple[str, str, str], dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    allowed_null_counts: Counter[str] = Counter()
    unexpected_null_counts: Counter[str] = Counter()
    critical_null_counts: Counter[str] = Counter()
    critical_examples: dict[str, list[str]] = defaultdict(list)

    rows_by_log: dict[str, list[dict[str, Any]]] = {
        name: list(rows.values()) for name, rows in latest_logs.items()
    }
    rows_by_log["live_mechanical_strategy_shadow_outcomes.jsonl"] = list(latest_mechanical.values())

    for log_name, rows in rows_by_log.items():
        allowed_fields = COMMON_ALLOWED_NULL_FIELDS | ALLOWED_NULL_FIELDS_BY_LOG.get(log_name, set())
        critical_fields = CRITICAL_NON_NULL_FIELDS_BY_LOG.get(log_name, set())
        for row in rows:
            cid = str(row.get("candidate_id") or "")
            for field, value in row.items():
                if not _is_null_like(value):
                    continue
                key = f"{log_name}.{field}"
                if field in allowed_fields or _is_conditionally_allowed_null(log_name, field, row):
                    allowed_null_counts[key] += 1
                    continue
                unexpected_null_counts[key] += 1
                if field in critical_fields:
                    critical_null_counts[key] += 1
                    if len(critical_examples[key]) < 5:
                        critical_examples[key].append(cid)
                    issues.append(
                        issue(
                            "SERIOUS",
                            "CRITICAL_FIELD_NULL",
                            log_name,
                            f"critical field {field!r} is null/empty",
                            candidate_id=cid or None,
                        )
                    )

    return {
        "allowed_null_counts": dict(allowed_null_counts),
        "unexpected_null_counts": dict(unexpected_null_counts),
        "critical_null_counts": dict(critical_null_counts),
        "critical_null_examples": dict(critical_examples),
        "allowed_null_policy": "Allowed nulls are explicit non-decision or source-identity fields such as trade_id/source_symbol/regime/source_hash, plus point-in-time rows that intentionally have no asof_latest_candle_utc.",
    }


def status_from_issues(issues: list[dict[str, Any]]) -> str:
    if any(item["severity"] in {"CRITICAL", "SERIOUS"} for item in issues):
        return "ACTION_REQUIRED"
    if any(item["severity"] == "MODERATE" for item in issues):
        return "CHECK_WARNINGS_PRESENT"
    return "OK_WITH_DOCUMENTED_LIMITATIONS"


def build_report(root: Path) -> dict[str, Any]:
    shadow = root / "shadow_logs"
    issues: list[dict[str, Any]] = []
    all_rows: dict[str, list[dict[str, Any]]] = {}

    log_names = {
        "strategy_follow_candidates.jsonl",
        "live_mechanical_strategy_shadow_outcomes.jsonl",
        *EXTRA_SEMANTIC_LOGS,
        *POINT_IN_TIME_CANDIDATE_LOGS,
        *PATH_ALIGNED_CANDIDATE_LOGS,
    }
    for name in sorted(log_names):
        rows, parse_issues = read_jsonl(shadow / name)
        all_rows[name] = rows
        issues.extend(parse_issues)

    candidate_rows = latest_by_candidate(all_rows["strategy_follow_candidates.jsonl"])
    latest_logs = {
        name: latest_by_candidate(rows)
        for name, rows in all_rows.items()
        if name != "live_mechanical_strategy_shadow_outcomes.jsonl"
    }
    asof_latest_logs = {
        name: latest_by_candidate_asof(rows)
        for name, rows in all_rows.items()
        if name != "live_mechanical_strategy_shadow_outcomes.jsonl"
    }

    coverage = audit_candidate_coverage(candidate_rows, latest_logs, asof_latest_logs, issues) if candidate_rows else {}
    all_row_identity = audit_all_row_candidate_identity(candidate_rows, all_rows, issues) if candidate_rows else {}
    external = audit_external_confluence(candidate_rows, issues) if candidate_rows else {}
    trade_record_coverage = audit_trade_record_candidate_coverage(
        root,
        candidate_rows,
        issues,
        candidate_rows_all=all_rows["strategy_follow_candidates.jsonl"],
    )
    mechanical = audit_mechanical_rows(
        candidate_rows,
        latest_logs.get("candidate_path_follow.jsonl", {}),
        all_rows["live_mechanical_strategy_shadow_outcomes.jsonl"],
        latest_logs.get("live_candidate_strategy_rollups.jsonl", {}),
        issues,
    ) if candidate_rows else {}
    path_geometry = audit_path_label_geometry(latest_logs.get("candidate_path_follow.jsonl", {}), issues)
    lifecycle = audit_pending_lifecycle_consistency(
        candidate_rows,
        latest_logs.get("pending_limit_lifecycle_join_backfill.jsonl", {}),
        issues,
    ) if candidate_rows else {}
    source_feature = audit_source_status_feature_interpretation(latest_logs, candidate_rows, issues) if candidate_rows else {}
    opportunity = audit_opportunity_counts(latest_logs.get("live_candidate_opportunity_clusters.jsonl", {}), issues)
    lane_expectations = audit_lane_expectations(all_rows)
    limitations = audit_source_limitations(
        latest_logs.get("live_structural_strategy_metadata.jsonl", {}),
        latest_logs.get("live_candidate_strategy_rollups.jsonl", {}),
    )
    null_fields = audit_null_fields(
        latest_logs,
        latest_mechanical_by_key(all_rows["live_mechanical_strategy_shadow_outcomes.jsonl"]),
        issues,
    )

    path_labels = Counter(
        str(row.get("path_label") or "UNKNOWN")
        for row in latest_logs.get("candidate_path_follow.jsonl", {}).values()
    )
    final_outcomes = Counter(
        str(row.get("final_outcome_at_log") or "UNKNOWN")
        for row in candidate_rows.values()
    )

    report = {
        "schema_version": "live_shadow_data_health_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": status_from_issues(issues),
        "counts": {
            "latest_candidates": len(candidate_rows),
            "logs_inspected": len(all_rows),
            "raw_rows_inspected": sum(len(rows) for rows in all_rows.values()),
            "issue_count": len(issues),
        },
        "candidate_final_outcomes": dict(final_outcomes),
        "latest_path_labels": dict(path_labels),
        "coverage": coverage,
        "all_row_identity_health": all_row_identity,
        "mechanical_strategy_health": mechanical,
        "path_geometry_health": path_geometry,
        "pending_lifecycle_health": lifecycle,
        "source_feature_interpretation_health": source_feature,
        "opportunity_counting_health": opportunity,
        "lane_expectation_health": lane_expectations,
        "external_confluence_health": external,
        "trade_record_candidate_coverage": trade_record_coverage,
        "documented_limitations": limitations,
        "null_field_health": null_fields,
        "issues": issues,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    severity_counts = Counter(issue["severity"] for issue in report["issues"])
    lines = [
        "# Live Shadow Data Health Audit - 2026-05-04",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Scope",
        "",
        "This read-only audit checks cross-log candidate coverage, identity consistency, latest path alignment, path-label geometry sanity, pending-lifecycle joins, mechanical strategy coverage, opportunity-level duplicate counting, Sierra/Databento confluence and source/feature interpretation, lane expectation modes, critical null/empty fields, and explicit source-capture limitations.",
        "",
        "## Counts",
        "",
        f"- Latest candidates: `{report['counts']['latest_candidates']}`",
        f"- Logs inspected: `{report['counts']['logs_inspected']}`",
        f"- Raw rows inspected: `{report['counts']['raw_rows_inspected']}`",
        f"- Issues: `{report['counts']['issue_count']}`",
        f"- Candidate final outcomes: `{report['candidate_final_outcomes']}`",
        f"- Latest path labels: `{report['latest_path_labels']}`",
        "",
        "## Issue Counts",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for severity in ("CRITICAL", "SERIOUS", "MODERATE", "LOW"):
        lines.append(f"| `{severity}` | {severity_counts.get(severity, 0)} |")

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "| Log | Covered candidates | Missing | Asof mismatches |",
            "|---|---:|---:|---:|",
        ]
    )
    for log_name, row in report["coverage"].items():
        lines.append(
            f"| `{log_name}` | {row['covered_candidates']} | "
            f"{len(row['missing_candidates'])} | {len(row['asof_mismatch_candidates'])} |"
        )

    lines.extend(
        [
            "",
            "## Opportunity Counting",
            "",
            f"- Status counts: `{report['opportunity_counting_health']['status_counts']}`",
            f"- Algorithm versions: `{report['opportunity_counting_health']['algorithm_versions']}`",
            f"- Unique opportunity IDs: `{report['opportunity_counting_health']['unique_opportunity_ids']}`",
            "",
            "## All-Row Identity Health",
            "",
            f"- Candidate-scoped rows checked: `{report['all_row_identity_health'].get('candidate_scoped_rows_checked', 0)}`",
            f"- Orphan dependent rows by log: `{report['all_row_identity_health'].get('orphan_dependent_rows_by_log', {})}`",
            f"- Candidate identity variant conflicts: `{report['all_row_identity_health'].get('candidate_identity_variant_conflicts', {})}`",
            "",
            "## Mechanical Strategy Health",
            "",
            f"- Latest strategy row counts per candidate: `{report['mechanical_strategy_health'].get('latest_strategy_row_counts', {})}`",
            f"- Missing mechanical rows by candidate: `{report['mechanical_strategy_health'].get('missing_by_candidate', {})}`",
            f"- Outcome mismatches: `{report['mechanical_strategy_health'].get('outcome_mismatches', [])}`",
            "",
            "## Path Geometry Health",
            "",
            f"- Checked latest path rows: `{report['path_geometry_health'].get('checked_latest_path_rows', 0)}`",
            f"- Mismatches: `{report['path_geometry_health'].get('mismatches', [])}`",
            "",
            "## Pending Lifecycle Health",
            "",
            f"- LIMIT_PLACED candidates: `{report['pending_lifecycle_health'].get('limit_placed_candidates', [])}`",
            f"- Missing lifecycle joins: `{report['pending_lifecycle_health'].get('missing_limit_placed_join_candidates', [])}`",
            f"- Unexpected joins: `{report['pending_lifecycle_health'].get('unexpected_join_candidates', [])}`",
            f"- Trade ID mismatches: `{report['pending_lifecycle_health'].get('trade_id_mismatches', [])}`",
            "",
            "## Source / Feature Interpretation",
            "",
            f"- Mismatches: `{report['source_feature_interpretation_health'].get('mismatches', [])}`",
            "",
            "## External Confluence",
            "",
            f"- Sierra statuses: `{report['external_confluence_health'].get('sierra_statuses', {})}`",
            f"- Databento statuses: `{report['external_confluence_health'].get('databento_statuses', {})}`",
            f"- Paid fetch attempted count: `{report['external_confluence_health'].get('paid_fetch_attempted_count', 0)}`",
            "",
            "## Trade Record Candidate Coverage",
            "",
            f"- Trade-record candidates seen: `{report['trade_record_candidate_coverage'].get('trade_records_seen', 0)}`",
            f"- Matched candidate shadow rows: `{report['trade_record_candidate_coverage'].get('matched_candidate_shadow_rows', 0)}`",
            f"- Missing candidate shadow rows: `{report['trade_record_candidate_coverage'].get('missing_candidate_shadow_rows', [])}`",
            f"- Value mismatches: `{report['trade_record_candidate_coverage'].get('value_mismatches', [])}`",
            f"- Documented candidate-id collisions: `{report['trade_record_candidate_coverage'].get('documented_candidate_id_collisions', [])}`",
            "",
            "## Documented Limitations",
            "",
            f"- Source-not-captured fields: `{report['documented_limitations']['source_not_captured_fields']}`",
            f"- Legacy source-not-captured fields: `{report['documented_limitations'].get('legacy_source_not_captured_fields', {})}`",
            f"- Affected strategies: `{report['documented_limitations']['affected_strategies']}`",
            f"- Unresolved score statuses: `{report['documented_limitations']['unresolved_score_statuses']}`",
            f"- Legacy unresolved score statuses: `{report['documented_limitations'].get('legacy_unresolved_score_statuses', {})}`",
            f"- Backfill rule: {report['documented_limitations']['backfill_rule']}",
            "",
            "## Null Field Health",
            "",
            f"- Allowed null counts: `{report['null_field_health']['allowed_null_counts']}`",
            f"- Unexpected null counts: `{report['null_field_health']['unexpected_null_counts']}`",
            f"- Critical null counts: `{report['null_field_health']['critical_null_counts']}`",
            f"- Allowed null policy: {report['null_field_health']['allowed_null_policy']}",
            "",
            "## Lane Expectations",
            "",
            f"- Row counts by mode: `{report['lane_expectation_health']['row_counts_by_mode']}`",
            f"- Staleness policy: `{report['lane_expectation_health']['staleness_policy']}`",
            "",
            "## Issues",
            "",
        ]
    )
    if not report["issues"]:
        lines.append("No cross-log data-health issues found. Documented limitations remain explicit and non-fabricated.")
    else:
        lines.extend(["| Severity | Code | Log | Candidate | Message |", "|---|---|---|---|---|"])
        for item in report["issues"][:200]:
            message = str(item["message"]).replace("|", "\\|")
            lines.append(
                f"| `{item['severity']}` | `{item['code']}` | `{item['log']}` | "
                f"`{item.get('candidate_id') or ''}` | {message} |"
            )
        if len(report["issues"]) > 200:
            lines.append(f"\nOnly first 200 issues shown; JSON contains all `{len(report['issues'])}` issues.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    report = build_report(args.root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.output_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "issues": Counter(item["severity"] for item in report["issues"]),
                "source_not_captured_fields": report["documented_limitations"]["source_not_captured_fields"],
                "opportunity_status_counts": report["opportunity_counting_health"]["status_counts"],
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            default=dict,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
