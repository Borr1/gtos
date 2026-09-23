#!/usr/bin/env python3
"""Build vNext exit-management runtime rows from trailing/J46 evidence."""

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
ROWS_PATH = ROUTE_DIR / f"GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_SUMMARY_{DATE}.json"

EVIDENCE_FAMILY = "gtos_vnext_exit_management_trailing_j46"
WAVE_ID = "WAVE_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME"
SOURCE_COMPONENTS = (
    "trailing_stop_v1_shadow",
    "j46_j49_active_exit_policy",
    "j46_j49_actual_r_boundary",
    "exit_optimization_context",
)

SOURCE_ARTIFACTS = [
    ("UNIT_003451", "research/academic_pipeline/results/Q-5_Q-6_exits.md", "bbe822c76c066bf1e8219375a1648e57554738de", 115),
    ("UNIT_003452", "research/academic_pipeline/results/Q-5_Q-6_exits_v2.json", "3fdc90d233d05a054edc861cef8bf8e51a248a08", 1),
    ("UNIT_003453", "research/academic_pipeline/results/Q-5_Q-6_exits_v2.md", "b5146433cf6c80f64f94e71673d0bd1838dce1ad", 126),
    ("UNIT_003455", "research/academic_pipeline/results/Q-6_exits_part2.md", "b579b9a7d48d3ce0fde0dc6cf92b8e882aca08b8", 102),
    ("UNIT_003908", "research/diagnostics/trailing_stop_optimal/compute_optimal_trail_v1.py", "8edb991c7ef3de2e848d288529c7a71141bda30c", None),
    ("UNIT_003909", "research/diagnostics/trailing_stop_optimal/optimal_trailing_stop_data_v1_20260411_103903.json", "8c5a2d8548204dbeebed7dfd06fbc5366fe1bd60", 1),
    ("UNIT_003910", "research/diagnostics/trailing_stop_optimal/optimal_trailing_stop_data_v1_20260411_104226.json", "2492c03f68c729b04ca95592eb5044f55bef97c2", 1),
    ("UNIT_003911", "research/diagnostics/trailing_stop_optimal/optimal_trailing_stop_v1.md", "f346d944644dc03ba4d3c5bbe91d013d6e68b59e", 153),
    ("UNIT_004381", "research/kap_outputs/tests/test_trailing_stop.py", "fff8175201fa662e23c527427094b464f23c5ad2", None),
    ("UNIT_004382", "research/kap_outputs/tests/test_trailing_stop_full.py", "b06a8cfd6b5b4d8ebd802dfb0832b5d8a99d1277", None),
    ("UNIT_004383", "research/kap_outputs/tests/trailing_stop_details_overall.csv", "9b8f4cedb44ddb032aedb22103d8c57539a871b9", 101),
    ("UNIT_004384", "research/kap_outputs/tests/trailing_stop_details_XAUUSD_2024.csv", "96d7fe565d4f57e6b3a001a052ba35130a853f37", 22),
    ("UNIT_004385", "research/kap_outputs/tests/trailing_stop_details_XAUUSD_2025.csv", "3fe321ef57f781403a5f2523e5f010857c8b84e9", 57),
    ("UNIT_004386", "research/kap_outputs/tests/trailing_stop_details_XAUUSD_2026.csv", "cae5c170ed542aaf5f67d80bf567884afa064a7b", 24),
    ("UNIT_004387", "research/kap_outputs/tests/trailing_stop_details_year_2024.csv", "96d7fe565d4f57e6b3a001a052ba35130a853f37", 22),
    ("UNIT_004388", "research/kap_outputs/tests/trailing_stop_details_year_2025.csv", "3fe321ef57f781403a5f2523e5f010857c8b84e9", 57),
    ("UNIT_004389", "research/kap_outputs/tests/trailing_stop_details_year_2026.csv", "cae5c170ed542aaf5f67d80bf567884afa064a7b", 24),
    ("UNIT_004390", "research/kap_outputs/tests/trailing_stop_summary.csv", "a1f5ea7fc18a1d2ddec42470f5f60a0511803a9c", 4),
    ("UNIT_004664", "research/ml_program/forensics/2026-04-29/_pareto_frontier_j46_j49.csv", "2c604cb43ba0d4eea2390502436e084f965ec5da", 429),
    ("UNIT_004718", "research/ml_program/forensics/2026-04-29/agent_f_j46_component_attribution.json", "6c97c4bc6196911ae19ca5e6976cd2d4553e144d", 1),
    ("UNIT_005551", "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json", "3ebc1d9d21beb791909de2d405ec77a1715c131d", 1),
    ("UNIT_005552", "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md", "eb85a9d97408d02a89e9b2106914afb6674c31e1", 30),
    ("UNIT_013156", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/batch_symbol_map.json", "a3b570bdcab0a2777f70e1e2064fb658563482f1", 1),
    ("UNIT_013157", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/discover_symbols.py", "646ea61d277c644e73bad3d2ac01d14f4c38465b", None),
    ("UNIT_013158", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/per_trade_outcomes.jsonl", "99b6a4fd15b465a7e353e57fdc995e57cec704d7", 1004),
    ("UNIT_013159", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/PRE_REGISTRATION.md", "6683d8653be2ebefe41e19cc08d5b1620892a6f2", 59),
    ("UNIT_013160", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/run_metadata.json", "c19d724faff751a0ca8b90b87065b7d8bf5775f8", 1),
    ("UNIT_013161", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/trailing_stop_replay.py", "a193e250fa5dcf0a831595f3bc98b0d5c1d41c3a", None),
    ("UNIT_013162", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/variants_comparison.csv", "14bcd7fdbc221f655604a255baa8388e81dedb97", 6),
    ("UNIT_013163", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/variants_comparison.json", "d6d0523b0eaea2b6c1a5ed73f93a140a7e2ad4ff", 1),
    ("UNIT_013164", "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/verdict.md", "54a9130cb392d4f46730b0c4521700464606a5f9", 85),
]

J46_SYMBOL_DELTAS = {
    "XAUUSD": 0.396,
    "USDJPY": 0.690,
    "GBPJPY": 1.618,
    "GBPUSD": 2.091,
    "US30_cash": 0.419,
}
TRAILING_SYMBOLS = ("XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD")


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


def _base_row(row_id: str, component: str, review_action: str, scope: dict, **extra) -> dict:
    row = {
        "schema_version": "gtos_vnext_exit_management_runtime_row_v1",
        "row_type": "gtos_vnext_exit_management_runtime_row",
        "exit_management_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": "gtos_vnext_exit_management_trailing_j46_wave",
        "evidence_family": EVIDENCE_FAMILY,
        "source_component": component,
        "source_role": extra.pop("source_role", "exit_management_runtime_input"),
        "system_surface": "exit_management_shadow_runtime",
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
        "runtime_effect_now": "shadow_exit_management_observation",
        "batch_wave_id": WAVE_ID,
    }
    row.update(scope)
    row.update(extra)
    return row


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for symbol in TRAILING_SYMBOLS:
        rows.append(
            _base_row(
                f"exit_management:trailing_stop_v1:{symbol}",
                "trailing_stop_v1_shadow",
                "FOLLOW",
                {
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "market": symbol,
                    "route_session": "ALL_SESSIONS",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "source_component": "trailing_stop_v1_shadow",
                },
                action_class="exit_management_shadow_follow_pressure",
                r_evidence_class="TRAILING_STOP_V1_POSITIVE_SHADOW_REPLAY",
                source_role="trailing_stop_shadow_runtime",
                source_artifact="research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/variants_comparison.json",
                source_rows_represented=1004,
                activation_r=0.5,
                trail_distance_r=0.5,
                replay_trade_count=251,
                triggered_pct=59.36,
                hurt_pct_of_triggered=3.36,
                r_metric_traces={
                    "cost_adjusted_simulated_r": _metric(0.3693, 251),
                    "stress_simulated_r": _metric(0.2803, 251),
                    "effective_n": _metric(251.0, 251),
                    "proxy_score": _metric(0.3693, 251),
                },
            )
        )
    for symbol, delta_r in J46_SYMBOL_DELTAS.items():
        rows.append(
            _base_row(
                f"exit_management:j46_j49_policy:{symbol}",
                "j46_j49_active_exit_policy",
                "FOLLOW",
                {
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "market": symbol,
                    "route_session": "ALL_SESSIONS",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "source_component": "j46_j49_active_exit_policy",
                },
                action_class="exit_management_active_policy_follow_pressure",
                r_evidence_class="J46_J49_DSR_VALIDATED_EXIT_POLICY",
                source_role="active_exit_policy_runtime_anchor",
                source_artifact="research/ml_program/forensics/2026-04-29/agent_f_j46_component_attribution.json",
                source_rows_represented=321,
                partial_close_ratio=0.0,
                tp1_distance_r=3.0,
                higher_target_r=6.0,
                r_metric_traces={
                    "cost_adjusted_simulated_r": _metric(delta_r, 321),
                    "stress_simulated_r": _metric(delta_r, 321),
                    "effective_n": _metric(321.0, 321),
                    "proxy_score": _metric(delta_r, 321),
                },
            )
        )
    rows.append(
        _base_row(
            "exit_management:j46_j49_actual_r_boundary",
            "j46_j49_actual_r_boundary",
            "MIXED",
            {
                "route_session": "ALL_SESSIONS",
                "timeframe": "M15",
                "market_timeframe": "M15",
                "source_component": "j46_j49_actual_r_boundary",
            },
            action_class="exit_management_actual_r_label_guard",
            r_evidence_class="ACCOUNT_HISTORY_JOIN_BOUNDARY",
            source_role="actual_r_claim_boundary",
            source_artifact="research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json",
            source_rows_represented=211,
            filled_account_history_joined_rows=4,
            candidate_no_fill_context_rows=80,
            synthetic_candidate_path_rows=127,
        )
    )
    rows.append(
        _base_row(
            "exit_management:ou_trailing_context",
            "exit_optimization_context",
            "MIXED",
            {
                "route_session": "ALL_SESSIONS",
                "timeframe": "M15",
                "market_timeframe": "M15",
                "source_component": "exit_optimization_context",
            },
            action_class="exit_management_shadow_context_guard",
            r_evidence_class="OU_TRAILING_CONTEXT_NOT_LIVE_OVERRIDE",
            source_role="diagnostic_context_guard",
            source_artifact="research/diagnostics/trailing_stop_optimal/optimal_trailing_stop_v1.md",
            source_rows_represented=155,
            live_override_allowed=False,
        )
    )
    return rows


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
        "schema_version": "gtos_vnext_exit_management_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": str(ROWS_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "runtime_summary_path": str(SUMMARY_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(known_rows),
        "wave_source_rows_counted": sum(known_rows),
        "wave_source_artifact_count": len(SOURCE_ARTIFACTS),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": sum(1 for *_rest, count in SOURCE_ARTIFACTS if count is None),
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
        "trailing_stop_v1_shadow": {
            "activation_r": 0.5,
            "trail_distance_r": 0.5,
            "replay_trade_count": 251,
            "mean_delta_r_per_trade": 0.3693,
            "total_delta_r": 92.69,
            "triggered_pct": 59.36,
            "hurt_pct_of_triggered": 3.36,
            "bootstrap_ci_low": 0.2803,
            "bootstrap_ci_high": 0.4589,
            "runtime_effect_now": "shadow_log_only",
        },
        "j46_j49_policy": {
            "portfolio_delta_r_per_trade": 0.742,
            "portfolio_trade_count": 321,
            "baseline_mean_r": 0.342,
            "winner_mean_r": 1.084,
            "partial_close_ratio": 0.0,
            "tp1_distance_r": 3.0,
            "higher_target_r": 6.0,
            "active_runtime_path": "position_mgmt.j46_j49_v2",
        },
        "actual_r_boundary": {
            "computed_rows": 211,
            "filled_account_history_joined_rows": 4,
            "candidate_no_fill_context_rows": 80,
            "synthetic_candidate_path_rows": 127,
            "actual_r_claim_allowed_rows": 4,
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
