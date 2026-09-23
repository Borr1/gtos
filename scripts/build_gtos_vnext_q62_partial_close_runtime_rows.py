#!/usr/bin/env python3
"""Build Q62 partial-close exit-management runtime rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
ROWS_PATH = ROUTE_DIR / f"GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_DIR = REPO_ROOT / "research" / "q62_partial_close_optimization"
CSV_PATH = SOURCE_DIR / "q62_scheme_results.csv"
SUMMARY_SOURCE_PATH = SOURCE_DIR / "q62_summary.json"
REPORT_PATH = SOURCE_DIR / "q62_report_2026-04-18.md"
REPLAY_PATH = SOURCE_DIR / "q62_replay.py"

EVIDENCE_FAMILY = "gtos_vnext_q62_partial_close_exit_runtime"
SOURCE_NAME = "gtos_vnext_q62_partial_close_exit_runtime_wave"
WAVE_ID = "WAVE_Q62_PARTIAL_CLOSE_EXIT_RUNTIME"

SOURCE_ARTIFACTS = [
    (
        "UNIT_005669",
        "research/q62_partial_close_optimization/q62_replay.py",
        "82a11fb2427d470684745c73a35ab7d1c97d03e6",
    ),
    (
        "UNIT_005670",
        "research/q62_partial_close_optimization/q62_report_2026-04-18.md",
        "a6cab32218cf2a07d495dd499b4438afd2831f7a",
    ),
    (
        "UNIT_005671",
        "research/q62_partial_close_optimization/q62_scheme_results.csv",
        "10c4643a7b566d016b3ec838011e8f582427b882",
    ),
    (
        "UNIT_005672",
        "research/q62_partial_close_optimization/q62_summary.json",
        "facee440d9f6ca4dbe8f4d78831d089461ea8ebb",
    ),
]

SESSION_BY_KILL_ZONE = {
    "london": "london_core",
    "ny": "ny_core",
    "tokyo": "tokyo_kz",
}


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _metric(value: float | None, count: int) -> dict[str, Any]:
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
    source_component: str,
    review_action: str,
    event_scope: dict[str, str],
    **extra: Any,
) -> dict[str, Any]:
    row = {
        "schema_version": "gtos_vnext_q62_partial_close_runtime_row_v1",
        "row_type": "gtos_vnext_q62_partial_close_runtime_row",
        "q62_partial_close_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_component": source_component,
        "source_role": extra.pop("source_role", "q62_partial_close_exit_runtime_input"),
        "system_surface": "partial_close_exit_management_runtime",
        "review_action": review_action,
        "event_scope": event_scope,
        "symbol": event_scope.get("symbol", "XAUUSD"),
        "source_symbol": event_scope.get("source_symbol", "XAUUSD"),
        "market": event_scope.get("market", "XAUUSD"),
        "timeframe": event_scope.get("timeframe", "M15"),
        "market_timeframe": event_scope.get("market_timeframe", "M15"),
        "route_session": event_scope.get("route_session", "ALL_SESSIONS"),
        "source_bound": True,
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "partial_close_exit_management_shadow_context",
        "batch_wave_id": WAVE_ID,
    }
    if "side" in event_scope:
        row["side"] = event_scope["side"]
    row.update(event_scope)
    row.update(extra)
    return row


def _csv_rows() -> list[dict[str, Any]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _scheme_source_component(scheme: str) -> str:
    if scheme == "C":
        return "q62_variant_c_shadow_context"
    return "q62_variant_d_shadow_queue_guard"


def _scheme_action_class(scheme: str) -> str:
    if scheme == "C":
        return "partial_close_variant_c_shadow_maintain"
    return "partial_close_variant_d_shadow_kill"


def build_rows() -> list[dict[str, Any]]:
    source_summary = json.loads(SUMMARY_SOURCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []

    for source_line_no, item in enumerate(_csv_rows(), start=2):
        scheme = item["scheme"]
        triggered = _bool(item["triggered"])
        route_session = SESSION_BY_KILL_ZONE.get(item["kill_zone"], item["kill_zone"])
        side = item["direction"].upper()
        event_scope = {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market": "XAUUSD",
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "side": side,
            "source_component": "q62_partial_close_scheme_result",
        }
        delta_r = _float(item["delta_r_vs_baseline"])
        row_action_class = (
            "partial_close_scheme_not_triggered_context"
            if not triggered
            else _scheme_action_class(scheme)
        )
        rows.append(
            _base_row(
                f"q62:scheme_result:{item['trade_id']}:{scheme}",
                "q62_partial_close_scheme_result",
                "MIXED",
                event_scope,
                source_role="per_trade_partial_close_scheme_replay",
                action_class=row_action_class,
                r_evidence_class="Q62_PARTIAL_CLOSE_SCHEME_REPLAY_RESULT",
                source_artifact=CSV_PATH.relative_to(REPO_ROOT).as_posix(),
                source_row_number=source_line_no,
                trade_id=item["trade_id"],
                kill_zone=item["kill_zone"],
                exit_variant=scheme,
                scheme=scheme,
                triggered=triggered,
                has_r_path=_bool(item["has_r_path"]),
                mfe_r=_float(item["mfe_r"]),
                mae_r=_float(item["mae_r"]),
                actual_r_multiple=_float(item["actual_r_multiple"]),
                scheme_blended_r=_float(item["scheme_blended_r"]),
                delta_r_vs_baseline=delta_r,
                live_policy_change_allowed_now=False,
                variant_shadow_queue_allowed_now=False if scheme != "C" else True,
                r_metric_traces={
                    "effective_n": _metric(1.0, 1),
                    "cost_adjusted_simulated_r": _metric(delta_r, 1),
                    "proxy_score": _metric(delta_r, 1),
                },
            )
        )

    for scheme, stats in source_summary["schemes"].items():
        source_component = _scheme_source_component(scheme)
        review_action = "FOLLOW" if scheme == "C" else "AVOID"
        rows.append(
            _base_row(
                f"q62:scheme_summary:{scheme}",
                source_component,
                review_action,
                {
                    "symbol": "XAUUSD",
                    "source_symbol": "XAUUSD",
                    "market": "XAUUSD",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": "ALL_SESSIONS",
                    "source_component": source_component,
                },
                source_role=(
                    "variant_c_shadow_context"
                    if scheme == "C"
                    else "variant_d_shadow_queue_guard"
                ),
                action_class=_scheme_action_class(scheme),
                r_evidence_class=(
                    "Q62_VARIANT_C_DEFER_MAINTAIN_SHADOW"
                    if scheme == "C"
                    else "Q62_VARIANT_D_NOT_BETTER_THAN_C_DO_NOT_QUEUE"
                ),
                source_artifact=SUMMARY_SOURCE_PATH.relative_to(REPO_ROOT).as_posix(),
                exit_variant=scheme,
                scheme=scheme,
                triggered_trade_count=int(stats["n"]),
                exact_path_count=int(stats["n_exact"]),
                approximate_path_count=int(stats["n_approx"]),
                mean_delta_r=float(stats["mean_delta_r"]),
                wilcoxon_p_two_sided=float(stats["wilcoxon_p_two_sided"]),
                passes_bonferroni_0125=bool(stats["passes_bonferroni_0125"]),
                bootstrap_ci95_low=float(stats["bootstrap_ci95_lo"]),
                bootstrap_ci95_high=float(stats["bootstrap_ci95_hi"]),
                live_policy_change_allowed_now=False,
                variant_shadow_queue_allowed_now=scheme == "C",
                r_metric_traces={
                    "effective_n": _metric(float(stats["n"]), int(stats["n"])),
                    "cost_adjusted_simulated_r": _metric(
                        float(stats["mean_delta_r"]), int(stats["n"])
                    ),
                    "stress_simulated_r": _metric(
                        float(stats["bootstrap_ci95_lo"]), int(stats["n"])
                    ),
                    "proxy_score": _metric(float(stats["mean_delta_r"]), int(stats["n"])),
                },
            )
        )

    common = source_summary["common_subset_analysis"]
    for scheme, stats in common["schemes"].items():
        rows.append(
            _base_row(
                f"q62:common_trigger_runner_giveup:{scheme}",
                "q62_common_trigger_runner_giveup_guard",
                "AVOID",
                {
                    "symbol": "XAUUSD",
                    "source_symbol": "XAUUSD",
                    "market": "XAUUSD",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": "ALL_SESSIONS",
                    "source_component": "q62_common_trigger_runner_giveup_guard",
                },
                source_role="common_trigger_exit_policy_guard",
                action_class="partial_close_high_mfe_runner_giveup_guard",
                r_evidence_class="Q62_COMMON_TRIGGER_RUNNER_GIVEUP_POLICY_GUARD",
                source_artifact=SUMMARY_SOURCE_PATH.relative_to(REPO_ROOT).as_posix(),
                exit_variant=scheme,
                scheme=scheme,
                common_subset_n=int(stats["n"]),
                common_subset_mean_actual_r=float(common["subset_mean_actual_r"]),
                mean_delta_r=float(stats["mean_delta_r"]),
                cum_delta_r=float(stats["cum_delta_r"]),
                wilcoxon_p_two_sided=float(stats["wilcoxon_p_two_sided"]),
                live_policy_change_allowed_now=False,
                variant_shadow_queue_allowed_now=False,
                r_metric_traces={
                    "effective_n": _metric(float(stats["n"]), int(stats["n"])),
                    "cost_adjusted_simulated_r": _metric(
                        float(stats["mean_delta_r"]), int(stats["n"])
                    ),
                    "stress_simulated_r": _metric(float(stats["cum_delta_r"]), int(stats["n"])),
                    "proxy_score": _metric(float(stats["mean_delta_r"]), int(stats["n"])),
                },
            )
        )

    rows.append(
        _base_row(
            "q62:policy:partial_close_decision",
            "q62_partial_close_policy_guard",
            "MIXED",
            {
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "market": "XAUUSD",
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": "ALL_SESSIONS",
                "source_component": "q62_partial_close_policy_guard",
            },
            source_role="partial_close_policy_decision_guard",
            action_class="partial_close_policy_defer_active_change",
            r_evidence_class="Q62_PARTIAL_CLOSE_DEFER_NO_ACTIVE_POLICY_CHANGE",
            source_artifact=REPORT_PATH.relative_to(REPO_ROOT).as_posix(),
            exit_variant="policy_summary",
            verdict=source_summary["verdict"],
            verdict_note=source_summary["verdict_note"],
            valid_universe_size=int(source_summary["valid_universe_size"]),
            sample_threshold=int(source_summary["sample_threshold"]),
            bonferroni_alpha=float(source_summary["bonferroni_alpha"]),
            active_policy_change_allowed_now=False,
            variant_c_shadow_observation_enabled=True,
            variant_d_shadow_queue_allowed_now=False,
            live_triggered_events_required=30,
        )
    )
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    csv_rows = _csv_rows()
    source_summary = json.loads(SUMMARY_SOURCE_PATH.read_text(encoding="utf-8"))
    source_rows_counted = {
        REPLAY_PATH.relative_to(REPO_ROOT).as_posix(): _line_count(REPLAY_PATH),
        REPORT_PATH.relative_to(REPO_ROOT).as_posix(): _line_count(REPORT_PATH),
        CSV_PATH.relative_to(REPO_ROOT).as_posix(): _line_count(CSV_PATH),
        SUMMARY_SOURCE_PATH.relative_to(REPO_ROOT).as_posix(): _line_count(
            SUMMARY_SOURCE_PATH
        ),
    }
    coverage_fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "sides": "side",
        "exit_variants": "exit_variant",
    }
    coverage = {
        name: dict(Counter(str(row.get(field)) for row in rows if row.get(field)))
        for name, field in coverage_fields.items()
    }
    blank_anchor_counts = {
        field: sum(1 for row in rows if not row.get(field))
        for field in (
            "symbol",
            "source_symbol",
            "market",
            "timeframe",
            "market_timeframe",
            "route_session",
            "side",
            "entry_variant",
            "exit_variant",
            "source_component",
            "action_class",
            "target_stop_order_class",
        )
    }
    return {
        "schema_version": "gtos_vnext_q62_partial_close_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(source_rows_counted.values()),
        "wave_source_rows_counted": sum(source_rows_counted.values()),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "source_artifacts": [
            {
                "unit_id": unit_id,
                "path": path,
                "hash": hash_value,
                "hash_algorithm": "git_blob",
                "row_count": source_rows_counted[path],
            }
            for unit_id, path, hash_value in SOURCE_ARTIFACTS
        ],
        "source_row_counts": source_rows_counted,
        "decision_counts": dict(Counter(row["review_action"] for row in rows)),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "coverage_counts": coverage,
        "blank_anchor_counts": blank_anchor_counts,
        "csv_row_count": len(csv_rows),
        "trade_count": len({row["trade_id"] for row in csv_rows}),
        "triggered_scheme_row_count": sum(1 for row in csv_rows if _bool(row["triggered"])),
        "triggered_trade_count": len(
            {row["trade_id"] for row in csv_rows if _bool(row["triggered"])}
        ),
        "csv_scheme_counts": dict(Counter(row["scheme"] for row in csv_rows)),
        "csv_session_counts": dict(Counter(row["kill_zone"] for row in csv_rows)),
        "csv_side_counts": dict(Counter(row["direction"] for row in csv_rows)),
        "csv_has_r_path_counts": dict(Counter(row["has_r_path"] for row in csv_rows)),
        "scheme_summary": source_summary["schemes"],
        "common_subset_analysis": source_summary["common_subset_analysis"],
        "verdict": source_summary["verdict"],
        "verdict_note": source_summary["verdict_note"],
        "active_policy_change_allowed_now": False,
        "variant_c_shadow_observation_enabled": True,
        "variant_d_shadow_queue_allowed_now": False,
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row.get("paid_api_or_vendor_call")
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect")
        ),
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with ROWS_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    summary = build_summary(rows)
    if args.check:
        current_rows = ROWS_PATH.read_text(encoding="utf-8") if ROWS_PATH.exists() else ""
        expected_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        current_summary = (
            SUMMARY_PATH.read_text(encoding="utf-8") if SUMMARY_PATH.exists() else ""
        )
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if current_rows != expected_rows or current_summary != expected_summary:
            raise SystemExit("Q62 partial-close runtime outputs are stale")
        print("Q62 partial-close runtime outputs are current")
        return
    write_outputs(rows, summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
