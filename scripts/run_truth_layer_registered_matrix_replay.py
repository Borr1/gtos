#!/usr/bin/env python3
"""Run prequential replay over the full registered Phase 3 truth-layer matrix.

This wraps the generic replay harness with the frozen prospective candidate
matrix so every registered symbol/session/regime candidate is evaluated under
the same no-leak observation boundary. It remains research-only and cannot emit
an alpha promotion verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_truth_layer_effective_n import (
    DEFAULT_MATRIX_PATH,
    analyze_effective_n,
    load_matrix_registry,
)
from scripts.register_truth_layer_candidate_matrix import sha256_file
from scripts.run_truth_layer_prequential_replay import (
    DEFAULT_LAB_SPEC_PATH,
    DEFAULT_OUTPUT_ROOT as DEFAULT_REPLAY_OUTPUT_ROOT,
    markdown_table,
    run_prequential_replay,
    write_outputs as write_prequential_outputs,
)
from scripts.evaluate_truth_layer_controlled_hypotheses import find_latest_input


SCHEMA_VERSION = "truth_layer_registered_matrix_prequential_replay_v1"
DEFAULT_STRATEGY_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_REPLAY_STRATEGY_REGISTERED_MATRIX_V1.json"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/registered_matrix_replay"
)


def run_registered_matrix_replay(
    *,
    input_path: str | Path,
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    lab_spec_path: str | Path = DEFAULT_LAB_SPEC_PATH,
    strategy_spec_path: str | Path = DEFAULT_STRATEGY_SPEC_PATH,
    max_rows: int | None = None,
) -> dict[str, Any]:
    registry = load_matrix_registry(matrix_path)
    strategy_spec = build_registered_matrix_strategy_spec(
        registry,
        matrix_path=matrix_path,
    )
    write_strategy_spec(strategy_spec, strategy_spec_path)
    replay = run_prequential_replay(
        input_path=input_path,
        lab_spec_path=lab_spec_path,
        strategy_spec_path=strategy_spec_path,
        max_rows=max_rows,
    )
    effective_n = analyze_effective_n(
        input_path=input_path,
        matrix_path=matrix_path,
        analysis_context="historical_registered_matrix_prequential_replay",
        max_rows=max_rows,
    )
    candidate_rows = candidate_replay_rows(replay, registry)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_jsonl": str(Path(input_path)),
        "matrix_path": str(Path(matrix_path)),
        "strategy_spec_path": str(Path(strategy_spec_path)),
        "strategy_spec_sha256": sha256_file(strategy_spec_path),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": (
            "This is a same-dataset registered-matrix replay. It is useful for "
            "discovery mapping and stress diagnostics, but not alpha promotion."
        ),
        "candidate_count": len(candidate_rows),
        "matrix_replay": replay,
        "candidate_replay_rows": candidate_rows,
        "instrument_summary": aggregate_candidate_rows(candidate_rows, "symbol"),
        "session_summary": aggregate_candidate_rows(candidate_rows, "session"),
        "role_summary": aggregate_candidate_rows(candidate_rows, "role"),
        "research_buckets": research_bucket_counts(candidate_rows),
        "bucket_rules": bucket_rules(),
        "followup_lanes": followup_lanes(candidate_rows),
        "top_discovery_leads": top_rows(candidate_rows, bucket="STRONG_DISCOVERY_LEAD", limit=12),
        "positive_but_unstable": top_rows(candidate_rows, bucket="POSITIVE_BUT_UNSTABLE", limit=12),
        "negative_or_flat": bottom_rows(candidate_rows, buckets={"NEGATIVE_OR_FLAT"}, limit=12),
        "methodology_context": {
            "historical_pbo_reference": (registry.get("historical_pbo_reference") or {}),
            "effective_n": {
                "matrix_effective_n": effective_n.get("matrix_effective_n"),
                "primary_children_effective_n": effective_n.get("primary_children_effective_n"),
                "promotion_usable": effective_n.get("promotion_usable"),
                "promotion_usable_reason": effective_n.get("promotion_usable_reason"),
            },
        },
        "next_step": (
            "Use this matrix map to choose pre-registered replay families or raw-OHLC "
            "adapter targets. Do not narrow to the historical best candidate and call it proof."
        ),
    }


def build_registered_matrix_strategy_spec(
    registry: Mapping[str, Any],
    *,
    matrix_path: str | Path,
) -> dict[str, Any]:
    candidates = list(registry.get("candidates") or [])
    cohort_keys = [str(row.get("cohort_key") or "") for row in candidates]
    duplicate_keys = sorted({key for key in cohort_keys if cohort_keys.count(key) > 1})
    if not candidates:
        raise ValueError("registered matrix has no candidates")
    if any(not key for key in cohort_keys):
        raise ValueError("registered matrix contains an empty cohort_key")
    if duplicate_keys:
        raise ValueError(f"registered matrix contains duplicate cohort keys: {duplicate_keys}")
    return {
        "schema_version": "truth_layer_prequential_strategy_v1",
        "created_date": "2026-05-01",
        "strategy_id": "P3_REPLAY_REGISTERED_TRUTH_LAYER_MATRIX_V1",
        "strategy_type": "cohort_filter_v1",
        "run_mode": "REGISTERED_MATRIX_REPLAY",
        "evidence_class": "same_dataset_historical_diagnostic_matrix",
        "promotion_verdict_allowed": False,
        "description": (
            "Replay every frozen Phase 3 truth-layer matrix candidate through the "
            "prequential observation/scorer boundary."
        ),
        "source_matrix": {
            "path": str(Path(matrix_path)),
            "sha256": sha256_file(matrix_path),
            "candidate_count": len(cohort_keys),
        },
        "cohort_keys": cohort_keys,
        "decision_policy": {
            "match_action": "TAKE",
            "non_match_action": "SKIP",
        },
        "interpretation_boundary": [
            "The candidate matrix was frozen after historical diagnostics.",
            "Replay results are broad discovery/stress-map evidence only.",
            "Replay results are not alpha promotion proof.",
        ],
    }


def write_strategy_spec(spec: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    return target


def candidate_replay_rows(
    replay: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    score_rows = {
        str(row.get("cohort_key")): row
        for row in ((replay.get("score") or {}).get("cohort_scores") or [])
    }
    rows: list[dict[str, Any]] = []
    for candidate in registry.get("candidates") or []:
        key = str(candidate.get("cohort_key"))
        score = score_rows.get(key) or {}
        symbol, session, regime = split_cohort_key(key)
        outcomes = score.get("outcomes") or {}
        resolved = int(score.get("resolved_r_n") or 0)
        mean_r = score.get("mean_r")
        win_rate = score.get("win_rate")
        row = {
            "candidate_id": candidate.get("candidate_id"),
            "cohort_key": key,
            "symbol": symbol,
            "session": session,
            "regime": regime,
            "role": candidate.get("role"),
            "replay_actions": int(score.get("actions_taken") or 0),
            "population_actions": int(score.get("population_actions") or 0),
            "resolved_r_n": resolved,
            "sum_r": score.get("sum_r"),
            "mean_r": mean_r,
            "win_rate": win_rate,
            "tp": int(outcomes.get("TP") or 0),
            "sl": int(outcomes.get("SL") or 0),
            "timeout": int(outcomes.get("TIMEOUT") or 0),
            "no_entry": int(outcomes.get("NO_ENTRY") or 0),
            "pre_ai_poi_reject": int(outcomes.get("PRE_AI_POI_REJECT") or 0),
            "setup_not_refinable": int(outcomes.get("SETUP_NOT_REFINABLE") or 0),
            "same_bar": int(outcomes.get("SAME_BAR") or 0),
            "historical_valid_year_folds": candidate.get("historical_valid_year_folds"),
            "historical_positive_valid_year_folds": candidate.get("historical_positive_valid_year_folds"),
            "historical_max_year_resolved_share": candidate.get("historical_max_year_resolved_share"),
            "historical_active_periods": candidate.get("historical_active_periods"),
        }
        row["research_bucket"] = research_bucket(row)
        row["followup_note"] = followup_note(row)
        rows.append(row)
    return sorted(rows, key=lambda item: (str(item["symbol"]), str(item["session"]), str(item["regime"])))


def split_cohort_key(key: str) -> tuple[str, str, str]:
    parts = key.split("|")
    symbol = parts[0] if len(parts) >= 1 else "unknown"
    session = parts[1] if len(parts) >= 2 else "unknown"
    regime = "|".join(parts[2:]) if len(parts) >= 3 else "unknown"
    return symbol, session, regime


def research_bucket(row: Mapping[str, Any]) -> str:
    resolved = int(row.get("resolved_r_n") or 0)
    mean_r = as_float(row.get("mean_r"))
    win_rate = as_float(row.get("win_rate"))
    positive_years = int(row.get("historical_positive_valid_year_folds") or 0)
    valid_years = int(row.get("historical_valid_year_folds") or 0)
    max_share = as_float(row.get("historical_max_year_resolved_share"))
    if resolved < 150:
        return "UNDERPOWERED"
    if mean_r is None:
        return "NO_RESOLVED_SCORE"
    if mean_r <= 0:
        return "NEGATIVE_OR_FLAT"
    if valid_years and positive_years < valid_years:
        return "POSITIVE_BUT_UNSTABLE"
    if max_share is not None and max_share > 0.45:
        return "POSITIVE_BUT_DOMINATED"
    if mean_r >= 0.25 and (win_rate or 0.0) >= 0.50:
        return "STRONG_DISCOVERY_LEAD"
    return "MARGINAL_POSITIVE"


def followup_note(row: Mapping[str, Any]) -> str:
    bucket = str(row.get("research_bucket") or "")
    if row.get("role") == "primary_controlled_child":
        return "primary family; keep controlled reporting separate from broader matrix ranking"
    if bucket == "STRONG_DISCOVERY_LEAD":
        return "candidate for pre-registered family or raw-OHLC replay adapter"
    if bucket == "POSITIVE_BUT_UNSTABLE":
        return "inspect year/month instability before any controlled follow-up"
    if bucket == "POSITIVE_BUT_DOMINATED":
        return "inspect dominance and data concentration before follow-up"
    if bucket == "NEGATIVE_OR_FLAT":
        return "use as negative control or deprioritize"
    if bucket == "UNDERPOWERED":
        return "collect more rows or merge only via pre-registered family logic"
    return "keep as low-priority matrix context"


def aggregate_candidate_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    states: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in candidate_rows:
        key = str(row.get(field) or "unknown")
        resolved = float(row.get("resolved_r_n") or 0)
        states[key]["candidate_count"] += 1
        states[key]["replay_actions"] += float(row.get("replay_actions") or 0)
        states[key]["population_actions"] += float(row.get("population_actions") or 0)
        states[key]["resolved_r_n"] += resolved
        states[key]["sum_r"] += float(row.get("sum_r") or 0.0)
        win_rate = as_float(row.get("win_rate"))
        if win_rate is not None and resolved:
            states[key]["wins_estimate"] += win_rate * resolved
    rows: list[dict[str, Any]] = []
    for key, state in states.items():
        resolved = int(state["resolved_r_n"])
        sum_r = state["sum_r"]
        rows.append(
            {
                field: key,
                "candidate_count": int(state["candidate_count"]),
                "replay_actions": int(state["replay_actions"]),
                "population_actions": int(state["population_actions"]),
                "resolved_r_n": resolved,
                "sum_r": round(sum_r, 6),
                "mean_r": round(sum_r / resolved, 6) if resolved else None,
                "win_rate_estimate": round(state["wins_estimate"] / resolved, 6) if resolved else None,
            }
        )
    return sorted(rows, key=lambda row: (row.get("mean_r") is None, -(row.get("mean_r") or -9999), str(row.get(field))))


def research_bucket_counts(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    for row in candidate_rows:
        counts[str(row.get("research_bucket") or "UNKNOWN")] += 1
    return [
        {"research_bucket": bucket, "candidate_count": count}
        for bucket, count in sorted(counts.items())
    ]


def bucket_rules() -> list[dict[str, str]]:
    return [
        {
            "research_bucket": "STRONG_DISCOVERY_LEAD",
            "rule": "resolved_r_n >= 150, mean_r >= 0.25, win_rate >= 0.50, all valid years positive, max year share <= 0.45",
        },
        {
            "research_bucket": "POSITIVE_BUT_UNSTABLE",
            "rule": "mean_r > 0 but at least one valid year is non-positive",
        },
        {
            "research_bucket": "POSITIVE_BUT_DOMINATED",
            "rule": "mean_r > 0, all valid years positive, but max year share > 0.45",
        },
        {
            "research_bucket": "MARGINAL_POSITIVE",
            "rule": "mean_r > 0 but below strong-lead thresholds",
        },
        {
            "research_bucket": "NEGATIVE_OR_FLAT",
            "rule": "mean_r <= 0",
        },
        {
            "research_bucket": "UNDERPOWERED",
            "rule": "resolved_r_n < 150",
        },
    ]


def followup_lanes(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    primary = [
        row
        for row in candidate_rows
        if row.get("role") == "primary_controlled_child"
    ]
    strong_non_primary = [
        row
        for row in candidate_rows
        if row.get("research_bucket") == "STRONG_DISCOVERY_LEAD"
        and row.get("role") != "primary_controlled_child"
    ]
    dominated = [
        row
        for row in candidate_rows
        if row.get("research_bucket") == "POSITIVE_BUT_DOMINATED"
    ]
    unstable_high_mean = [
        row
        for row in candidate_rows
        if row.get("research_bucket") == "POSITIVE_BUT_UNSTABLE"
        and (as_float(row.get("mean_r")) or 0.0) >= 0.25
    ]
    negative_controls = [
        row
        for row in candidate_rows
        if row.get("research_bucket") == "NEGATIVE_OR_FLAT"
    ]
    return [
        lane_row(
            "lane_1_primary_controlled_family",
            primary,
            "continue controlled reporting separately; do not mix with broader discovery ranking",
        ),
        lane_row(
            "lane_2_non_primary_strong_leads",
            strong_non_primary,
            "pre-register a new family before any deeper same-dataset replay or raw-OHLC adapter work",
        ),
        lane_row(
            "lane_3_dominance_watchlist",
            dominated,
            "run dominance/year concentration audit before treating as a candidate family",
        ),
        lane_row(
            "lane_4_high_mean_unstable",
            unstable_high_mean,
            "inspect fold/month failure anatomy; only then decide whether to register a family",
        ),
        lane_row(
            "lane_5_negative_controls",
            negative_controls,
            "use as controls for new replay infrastructure and avoid pooled headline claims",
        ),
    ]


def lane_row(name: str, rows: Sequence[Mapping[str, Any]], next_action: str) -> dict[str, Any]:
    resolved = sum(int(row.get("resolved_r_n") or 0) for row in rows)
    sum_r = sum(float(row.get("sum_r") or 0.0) for row in rows)
    return {
        "lane": name,
        "candidate_count": len(rows),
        "resolved_r_n": resolved,
        "mean_r": round(sum_r / resolved, 6) if resolved else None,
        "cohort_keys": ", ".join(str(row.get("cohort_key")) for row in rows[:8]),
        "next_action": next_action,
    }


def top_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    *,
    bucket: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = [row for row in candidate_rows if row.get("research_bucket") == bucket]
    return sorted(
        rows,
        key=lambda row: (
            -(as_float(row.get("mean_r")) or -9999),
            -int(row.get("resolved_r_n") or 0),
            str(row.get("cohort_key")),
        ),
    )[:limit]


def bottom_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    *,
    buckets: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    rows = [row for row in candidate_rows if row.get("research_bucket") in buckets]
    return sorted(
        rows,
        key=lambda row: (
            as_float(row.get("mean_r")) if as_float(row.get("mean_r")) is not None else 9999,
            str(row.get("cohort_key")),
        ),
    )[:limit]


def render_report(summary: Mapping[str, Any]) -> str:
    replay = summary.get("matrix_replay") or {}
    score = replay.get("score") or {}
    methodology = summary.get("methodology_context") or {}
    effective_n = (methodology.get("effective_n") or {}).get("matrix_effective_n") or {}
    primary_effective_n = (methodology.get("effective_n") or {}).get("primary_children_effective_n") or {}
    pbo = methodology.get("historical_pbo_reference") or {}
    lines = [
        "# Phase 3 Registered Matrix Historical Replay Report",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Matrix:** `{summary.get('matrix_path')}`",
        f"**Strategy spec:** `{summary.get('strategy_spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This uses the same prequential replay boundary as the primary-cohort report.",
        "- The full registered matrix is evaluated so we do not narrow to only the historical winners.",
        "- Results are discovery/stress-map evidence because the matrix was registered after historical diagnostics.",
        "",
        "## Replay Guardrails",
        "",
        markdown_table(
            [
                {
                    "rows_replayed": replay.get("rows_replayed"),
                    "candidate_count": summary.get("candidate_count"),
                    "duplicate_opportunity_keys": replay.get("duplicate_opportunity_keys"),
                    "invalid_clock_rows": replay.get("invalid_clock_rows"),
                    "forbidden_exposure_violations": replay.get("forbidden_exposure_violations"),
                    "external_asof_violations": replay.get("external_asof_violations"),
                    "ai_attempted_rows": replay.get("ai_attempted_rows"),
                    "ai_call_count_sum": replay.get("ai_call_count_sum"),
                    "integrity_status": (replay.get("integrity") or {}).get("status"),
                }
            ]
        ),
        "",
        "## Matrix Score",
        "",
        markdown_table(
            [
                {
                    "actions_taken": score.get("actions_taken"),
                    "scoring_population_actions": score.get("scoring_population_actions"),
                    "resolved_r_n": score.get("resolved_r_n"),
                    "sum_r": score.get("sum_r"),
                    "mean_r": score.get("mean_r"),
                    "win_rate": score.get("win_rate"),
                }
            ]
        ),
        "",
        "## Methodology Context",
        "",
        markdown_table(
            [
                {
                    "historical_pbo": pbo.get("pbo"),
                    "pbo_status": pbo.get("status"),
                    "matrix_effective_n": effective_n.get("effective_n"),
                    "matrix_effective_n_status": effective_n.get("status"),
                    "primary_children_effective_n": primary_effective_n.get("effective_n"),
                    "promotion_usable": (methodology.get("effective_n") or {}).get("promotion_usable"),
                }
            ]
        ),
        "",
        "## Research Buckets",
        "",
        markdown_table(summary.get("research_buckets") or []),
        "",
        "## Bucket Rules",
        "",
        markdown_table(summary.get("bucket_rules") or []),
        "",
        "## Follow-Up Lanes",
        "",
        markdown_table(summary.get("followup_lanes") or []),
        "",
        "## Instrument Summary",
        "",
        markdown_table(summary.get("instrument_summary") or []),
        "",
        "## Session Summary",
        "",
        markdown_table(summary.get("session_summary") or []),
        "",
        "## Role Summary",
        "",
        markdown_table(summary.get("role_summary") or []),
        "",
        "## Strong Discovery Leads",
        "",
        markdown_table(compact_candidate_rows(summary.get("top_discovery_leads") or [])),
        "",
        "## Positive But Unstable",
        "",
        markdown_table(compact_candidate_rows(summary.get("positive_but_unstable") or [])),
        "",
        "## Negative Or Flat Controls",
        "",
        markdown_table(compact_candidate_rows(summary.get("negative_or_flat") or [])),
        "",
        "## Full Candidate Matrix",
        "",
        markdown_table(compact_candidate_rows(summary.get("candidate_replay_rows") or [])),
        "",
        "## Synthesis",
        "",
        "- Other instruments do add value now: they provide a broader discovery map under the same no-leak replay boundary.",
        "- The JPY Tokyo primary family remains separate because it was already pre-registered as the controlled child family.",
        "- Strong non-primary candidates should become new pre-registered families before deeper evaluation.",
        "- Negative and unstable candidates are useful as controls and as warnings against pooling everything into one headline.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def compact_candidate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    keep = [
        "candidate_id",
        "cohort_key",
        "role",
        "research_bucket",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "population_actions",
        "historical_positive_valid_year_folds",
        "historical_valid_year_folds",
        "historical_max_year_resolved_share",
        "followup_note",
    ]
    return [{key: row.get(key) for key in keep} for row in rows]


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_registered_matrix_replay_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--matrix-path", default=DEFAULT_MATRIX_PATH)
    parser.add_argument("--lab-spec-path", default=DEFAULT_LAB_SPEC_PATH)
    parser.add_argument("--strategy-spec-path", default=DEFAULT_STRATEGY_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = run_registered_matrix_replay(
        input_path=input_path,
        matrix_path=args.matrix_path,
        lab_spec_path=args.lab_spec_path,
        strategy_spec_path=args.strategy_spec_path,
        max_rows=args.max_rows,
    )
    if args.write:
        summary_path, report_path = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        # Also keep the generic replay report/JSON available for raw replay audit.
        replay_summary_path, replay_report_path = write_prequential_outputs(
            summary["matrix_replay"],
            output_root=DEFAULT_REPLAY_OUTPUT_ROOT,
            report_path=(
                "research/phase_3_external_feed_validation/"
                "HISTORICAL_REPLAY_REGISTERED_MATRIX_RAW_REPLAY_REPORT_2026-05-01.md"
            ),
        )
        summary = dict(summary)
        summary["output_summary"] = str(summary_path)
        summary["report_path"] = str(report_path)
        summary["raw_replay_summary"] = str(replay_summary_path)
        summary["raw_replay_report"] = str(replay_report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "candidate_count": summary.get("candidate_count"),
                    "rows_replayed": (summary.get("matrix_replay") or {}).get("rows_replayed"),
                    "actions_taken": ((summary.get("matrix_replay") or {}).get("score") or {}).get("actions_taken"),
                    "resolved_r_n": ((summary.get("matrix_replay") or {}).get("score") or {}).get("resolved_r_n"),
                    "mean_r": ((summary.get("matrix_replay") or {}).get("score") or {}).get("mean_r"),
                    "research_buckets": summary.get("research_buckets"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
