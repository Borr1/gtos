#!/usr/bin/env python3
"""Build vNext exit-management residue runtime rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
ROWS_PATH = ROUTE_DIR / f"GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_SUMMARY_{DATE}.json"
STATUS_LOG_PATH = REPO_ROOT / "shadow_logs" / "exit_management_shadow_status.jsonl"

EVIDENCE_FAMILY = "gtos_vnext_exit_management_residue"
WAVE_ID = "WAVE_EXIT_MANAGEMENT_RESIDUE_RUNTIME"
SOURCE_COMPONENTS = (
    "exit_policy_legacy_batch_context",
    "exit_policy_h29_risk_context",
    "exit_partial_split_policy_guard",
    "exit_session_timestamp_source_requirement",
    "exit_no_event_status_observability",
)

SOURCE_ARTIFACTS = [
    (
        "UNIT_003491",
        "research/academic_pipeline/scripts/Q5_Q6_exit_engineering.py",
        "02bdc0e82ea831e980d3d50cb8059c1f848200da",
        None,
    ),
    (
        "UNIT_003492",
        "research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py",
        "c696dc374ab319af351380a54b47fa3abe83e29f",
        None,
    ),
    (
        "UNIT_003511",
        "research/academic_pipeline/scripts/q_6_exits_part2.py",
        "45e47b57c2a0630f367ef6ca8e8e14518b87c7f5",
        None,
    ),
    (
        "UNIT_005563",
        "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
        "87c75763391a4c0c86c1593d62683d8baa7a4e12",
        1,
    ),
    (
        "UNIT_005564",
        "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md",
        "2adcf9d5cf651d2412dccd483151e2be36419be8",
        26,
    ),
]


def _metric(value: float | None, count: int) -> dict:
    if value is None:
        return {
            "sum": None,
            "mean": None,
            "match_rows_with_metric": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
        }
    return {
        "sum": round(value, 6),
        "mean": round(value, 6),
        "match_rows_with_metric": count,
        "positive_rows": count if value > 0 else 0,
        "negative_rows": count if value < 0 else 0,
        "zero_rows": count if value == 0 else 0,
    }


def _base_row(
    row_id: str,
    component: str,
    review_action: str,
    scope: dict,
    **extra,
) -> dict:
    row = {
        "schema_version": "gtos_vnext_exit_management_residue_runtime_row_v1",
        "row_type": "gtos_vnext_exit_management_residue_runtime_row",
        "exit_management_residue_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": "gtos_vnext_exit_management_residue_wave",
        "evidence_family": EVIDENCE_FAMILY,
        "source_component": component,
        "source_role": extra.pop("source_role", "exit_management_residue_runtime_input"),
        "system_surface": "exit_management_runtime",
        "review_action": review_action,
        "event_scope": scope,
        "route_session": scope.get("route_session", "ALL_SESSIONS"),
        "timeframe": scope.get("timeframe", "M15"),
        "market_timeframe": scope.get("market_timeframe", "M15"),
        "source_bound": bool(scope.get("symbol") or scope.get("source_symbol")),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "shadow_exit_management_residue_context",
        "batch_wave_id": WAVE_ID,
    }
    row.update(scope)
    row.update(extra)
    return row


def build_rows() -> list[dict]:
    rows: list[dict] = []
    xau_scope = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market": "XAUUSD",
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": "ALL_SESSIONS",
    }
    rows.append(
        _base_row(
            "exit_residue:q5_q6_v1_legacy_exit_context",
            "exit_policy_legacy_batch_context",
            "MIXED",
            {**xau_scope, "source_component": "exit_policy_legacy_batch_context"},
            action_class="exit_management_legacy_batch_rule_context",
            r_evidence_class="XAUUSD_LEGACY_EXIT_RULE_CONTEXT",
            source_role="legacy_exit_rule_context",
            source_artifact="research/academic_pipeline/scripts/Q5_Q6_exit_engineering.py",
            source_rows_represented=None,
            source_batch_trade_count=111,
            legacy_batch_rule="session_timeout_be_trail_tp3_runner",
            current_rule_context="config risk.tp1_close_pct=100 and position_mgmt.j46_j49_v2 partial_close_ratio=0.0",
            live_policy_change_allowed_now=False,
            r_metric_traces={
                "effective_n": _metric(111.0, 111),
                "proxy_score": _metric(0.0, 111),
            },
        )
    )
    rows.append(
        _base_row(
            "exit_residue:q5_q6_v2_h29_context",
            "exit_policy_h29_risk_context",
            "FOLLOW",
            {**xau_scope, "source_component": "exit_policy_h29_risk_context"},
            action_class="exit_management_h29_aware_replay_context",
            r_evidence_class="H29_AWARE_EXIT_REPLAY_CONTEXT",
            source_role="h29_exit_replay_context",
            source_artifact="research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py",
            source_rows_represented=None,
            source_batch_trade_count=111,
            h29_drawdown_trigger_pct=8.0,
            h29_reduced_risk_pct=0.5,
            best_pass_risk_pct=1.0,
            h29_on_best_pass_probability=0.8177,
            h29_on_best_dd10_probability=0.0216,
            live_policy_change_allowed_now=False,
            r_metric_traces={
                "effective_n": _metric(111.0, 111),
                "proxy_score": _metric(0.8177, 111),
                "stress_simulated_r": _metric(-0.0216, 111),
            },
        )
    )
    rows.append(
        _base_row(
            "exit_residue:q6_partial_split_policy_guard",
            "exit_partial_split_policy_guard",
            "MIXED",
            {**xau_scope, "source_component": "exit_partial_split_policy_guard"},
            action_class="exit_partial_split_no_active_change_guard",
            r_evidence_class="PARTIAL_SPLIT_UNDERPOWERED_NO_POLICY_CHANGE",
            source_role="partial_split_policy_guard",
            source_artifact="research/academic_pipeline/scripts/q_6_exits_part2.py",
            source_rows_represented=None,
            source_batch_trade_count=111,
            baseline_variant="B_50_25_25",
            best_point_variant="E_33_33_34",
            best_point_expectancy_r=0.162,
            baseline_expectancy_r=0.150,
            best_delta_r_vs_baseline=0.013,
            best_delta_ci95_low=-0.003,
            best_delta_ci95_high=0.029,
            best_delta_p_two_sided_boot=0.132,
            significant=False,
            partial_split_policy_action="NO_ACTIVE_POLICY_CHANGE_FROM_Q6_2",
            live_policy_change_allowed_now=False,
            r_metric_traces={
                "effective_n": _metric(111.0, 111),
                "cost_adjusted_simulated_r": _metric(0.013, 111),
                "stress_simulated_r": _metric(-0.003, 111),
                "proxy_score": _metric(0.013, 111),
            },
        )
    )
    for route_session, bucket_end in (("london_core", 14), ("ny_core", 16)):
        rows.append(
            _base_row(
                f"exit_residue:q6_session_timestamp_requirement:{route_session}",
                "exit_session_timestamp_source_requirement",
                "AVOID",
                {
                    "symbol": "XAUUSD",
                    "source_symbol": "XAUUSD",
                    "market": "XAUUSD",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": route_session,
                    "source_component": "exit_session_timestamp_source_requirement",
                },
                action_class="exit_session_close_forced_exit_avoid_until_timestamp_source",
                r_evidence_class="SESSION_OVERNIGHT_PROXY_CONFOUNDED_REQUIRES_TIMESTAMPS",
                source_role="session_timestamp_source_requirement",
                source_artifact="research/academic_pipeline/scripts/q_6_exits_part2.py",
                source_rows_represented=None,
                source_batch_trade_count=111,
                bucket_end_candles=bucket_end,
                bucket_counts={"intra": 39, "cross": 26, "overnight": 46},
                kruskal_wallis_p=0.0027,
                overnight_mean_r=0.682,
                overnight_skew=1.107,
                confound="legacy_exit_rule_survivorship",
                source_acquisition_required=True,
                required_event_fields=["entry_time_utc", "exit_time_utc"],
                prohibited_policy_action="SESSION_CLOSE_FORCED_EXIT_FROM_Q6_6_PROXY",
                live_policy_change_allowed_now=False,
            )
        )
    for symbol, symbol_rows in _status_symbol_counts().items():
        rows.append(
            _base_row(
                f"exit_residue:lto021_no_event_status:{symbol}",
                "exit_no_event_status_observability",
                "MIXED",
                {
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "market": symbol,
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": "ALL_SESSIONS",
                    "source_component": "exit_no_event_status_observability",
                },
                action_class="exit_management_no_event_status_complete_context",
                r_evidence_class="EXIT_MANAGEMENT_NO_EVENT_STATUS_DOCUMENTED",
                source_role="no_event_exit_status_context",
                source_artifact="research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
                source_rows_represented=symbol_rows,
                candidate_rows_considered=207,
                status_rows_available=704,
                status_symbol_rows=symbol_rows,
                no_event_documented=206,
                event_rows_present=1,
                action_required=0,
                no_event_status_complete=True,
                live_policy_change_allowed_now=False,
            )
        )
    return rows


def _status_symbol_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    try:
        with STATUS_LOG_PATH.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                symbol = str(row.get("symbol") or row.get("broker_symbol") or "").strip()
                if symbol:
                    counts[symbol] += 1
    except (OSError, json.JSONDecodeError):
        return {"ALL_SYMBOLS_STATUS_SOURCE_UNAVAILABLE": 704}
    return dict(sorted(counts.items()))


def _coverage(rows: list[dict], field: str) -> dict[str, int]:
    counts = Counter(str(row.get(field) or "") for row in rows if row.get(field))
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict]) -> dict[str, int]:
    fields = (
        "symbol",
        "source_symbol",
        "market",
        "timeframe",
        "market_timeframe",
        "route_session",
        "side",
        "framework",
        "route_family",
        "horizon_id",
        "primitive",
        "entry_variant",
        "target_stop_order_class",
    )
    return {
        field: sum(1 for row in rows if not row.get(field))
        for field in fields
        if any(not row.get(field) for row in rows)
    }


def build_summary(rows: list[dict]) -> dict:
    known_rows = [count for *_rest, count in SOURCE_ARTIFACTS if count is not None]
    decision_counts = Counter(str(row.get("review_action") or "MIXED") for row in rows)
    component_counts = Counter(str(row.get("source_component") or "") for row in rows)
    return {
        "schema_version": "gtos_vnext_exit_management_residue_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": str(ROWS_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "runtime_summary_path": str(SUMMARY_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(known_rows),
        "wave_source_rows_counted": sum(known_rows),
        "wave_source_artifact_count": len(SOURCE_ARTIFACTS),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": sum(
            1 for *_rest, count in SOURCE_ARTIFACTS if count is None
        ),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_component_counts": dict(sorted(component_counts.items())),
        "source_components": list(SOURCE_COMPONENTS),
        "coverage_counts": {
            "symbols": _coverage(rows, "symbol"),
            "source_symbols": _coverage(rows, "source_symbol"),
            "markets": _coverage(rows, "market"),
            "timeframes": _coverage(rows, "timeframe"),
            "sessions": _coverage(rows, "route_session"),
            "sides": _coverage(rows, "side"),
        },
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "exit_batch_trade_count": 111,
        "session_bucket_counts": {"intra": 39, "cross": 26, "overnight": 46},
        "status_candidate_rows_considered": 207,
        "status_rows_available": 704,
        "status_symbol_counts": _status_symbol_counts(),
        "status_no_event_documented": 206,
        "status_event_rows_present": 1,
        "partial_split_policy": {
            "baseline_variant": "B_50_25_25",
            "best_point_variant": "E_33_33_34",
            "best_delta_r_vs_baseline": 0.013,
            "best_delta_ci95": [-0.003, 0.029],
            "best_delta_p_two_sided_boot": 0.132,
            "active_policy_change_allowed_now": False,
        },
        "session_exit_policy": {
            "forced_session_close_policy_allowed_now": False,
            "source_acquisition_required": True,
            "required_event_fields": ["entry_time_utc", "exit_time_utc"],
        },
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "live_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "runtime_trading_or_live_broker_effect_rows": 0,
        "source_artifacts": [
            {
                "unit_id": unit_id,
                "path": path,
                "hash": sha1,
                "hash_algorithm": "git_blob",
                "row_count": count,
            }
            for unit_id, path, sha1, count in SOURCE_ARTIFACTS
        ],
    }


def write_outputs(rows: list[dict], summary: dict) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with ROWS_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_current_outputs(rows: list[dict], summary: dict) -> None:
    expected_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    if ROWS_PATH.exists() and ROWS_PATH.read_text(encoding="utf-8") != expected_rows:
        raise SystemExit(f"{ROWS_PATH} is stale; rerun without --check")
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if SUMMARY_PATH.exists() and SUMMARY_PATH.read_text(encoding="utf-8") != expected_summary:
        raise SystemExit(f"{SUMMARY_PATH} is stale; rerun without --check")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    summary = build_summary(rows)
    if args.check:
        _assert_current_outputs(rows, summary)
    else:
        write_outputs(rows, summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
