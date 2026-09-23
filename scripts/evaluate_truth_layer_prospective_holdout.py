#!/usr/bin/env python3
"""Evaluate prospective Phase 3 truth-layer holdout files.

This is a research-only guardrail wrapper. It refuses to evaluate files that
contain rows at or before the locked historical truth-layer cutoff, then reuses
the controlled hypothesis evaluator with promotion disabled.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    DEFAULT_SPEC_PATH,
    _hypothesis_summary_row,
    _markdown_cell,
    _parse_datetime,
    evaluate_controlled_hypotheses,
    iter_jsonl,
)


SCHEMA_VERSION = "truth_layer_prospective_holdout_evaluator_v1"
PROSPECTIVE_CUTOFF_UTC = datetime(2026, 4, 30, 17, 0, 0, tzinfo=timezone.utc)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/prospective_holdout"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_PROSPECTIVE_HOLDOUT_REPORT_2026-05-01.md"
)


def validate_prospective_input(
    input_path: str | Path,
    *,
    cutoff_utc: datetime = PROSPECTIVE_CUTOFF_UTC,
    max_rows: int | None = None,
) -> dict[str, Any]:
    rows_scanned = 0
    stale_rows = 0
    missing_timestamp_rows = 0
    duplicate_keys = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0
    min_candle_close_utc: str | None = None
    max_candle_close_utc: str | None = None
    keys_seen: set[str] = set()
    stale_examples: list[dict[str, Any]] = []

    for rows_scanned, row in enumerate(iter_jsonl(input_path), start=1):
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in keys_seen:
                duplicate_keys += 1
            keys_seen.add(key)
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)

        timestamp_text = row.get("candle_close_utc")
        timestamp = _parse_datetime(timestamp_text)
        if timestamp is None:
            missing_timestamp_rows += 1
        else:
            normalized = timestamp.isoformat()
            min_candle_close_utc = (
                normalized
                if min_candle_close_utc is None or normalized < min_candle_close_utc
                else min_candle_close_utc
            )
            max_candle_close_utc = (
                normalized
                if max_candle_close_utc is None or normalized > max_candle_close_utc
                else max_candle_close_utc
            )
            if timestamp <= cutoff_utc:
                stale_rows += 1
                if len(stale_examples) < 5:
                    stale_examples.append(
                        {
                            "opportunity_key": key,
                            "candle_close_utc": normalized,
                        }
                    )

        if max_rows is not None and rows_scanned >= max_rows:
            break

    valid = (
        rows_scanned > 0
        and stale_rows == 0
        and missing_timestamp_rows == 0
        and duplicate_keys == 0
        and ai_attempted_rows == 0
        and ai_call_count_sum == 0
    )
    return {
        "schema_version": f"{SCHEMA_VERSION}_validation",
        "input_jsonl": str(Path(input_path)),
        "prospective_cutoff_utc": cutoff_utc.isoformat(),
        "prospective_input_valid": valid,
        "rows_scanned": rows_scanned,
        "unique_keys": len(keys_seen),
        "duplicate_keys": duplicate_keys,
        "missing_timestamp_rows": missing_timestamp_rows,
        "stale_rows_at_or_before_cutoff": stale_rows,
        "stale_examples": stale_examples,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "min_candle_close_utc": min_candle_close_utc,
        "max_candle_close_utc": max_candle_close_utc,
    }


def evaluate_prospective_holdout(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    cutoff_utc: datetime = PROSPECTIVE_CUTOFF_UTC,
    max_rows: int | None = None,
) -> dict[str, Any]:
    validation = validate_prospective_input(
        input_path,
        cutoff_utc=cutoff_utc,
        max_rows=max_rows,
    )
    if not validation["prospective_input_valid"]:
        raise ValueError(_invalid_reason(validation))

    controlled = evaluate_controlled_hypotheses(
        input_path=input_path,
        spec_path=spec_path,
        max_rows=max_rows,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "input_validation": validation,
        "controlled_summary": controlled,
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": (
            "Prospective holdout evaluator skeleton does not compute DSR, PBO, "
            "or true effective_N."
        ),
        "methodology_gates": {
            "dsr_corrected_p": "NOT_COMPUTED",
            "pbo": "NOT_COMPUTED",
            "effective_n": "NOT_COMPUTED",
        },
    }


def render_report(summary: Mapping[str, Any]) -> str:
    validation = summary.get("input_validation") or {}
    controlled = summary.get("controlled_summary") or {}
    lines = [
        "# Phase 3 Prospective Truth-Layer Holdout Report",
        "",
        f"**Input:** `{validation.get('input_jsonl')}`",
        f"**Prospective cutoff UTC:** `{validation.get('prospective_cutoff_utc')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This evaluator refuses same-dataset rows at or before the registered cutoff.",
        "- DSR, PBO, and true effective_N are not computed here.",
        "- This report cannot promote alpha.",
        "",
        "## Input Validation",
        "",
        _markdown_table([validation]),
        "",
        "## Hypothesis Summary",
        "",
        _markdown_table([
            _hypothesis_summary_row(item)
            for item in controlled.get("hypotheses", [])
        ]),
        "",
        "## Synthesis",
        "",
        "- A valid prospective input can be monitored with this report.",
        "- A positive result remains interim until DSR, PBO, and true effective_N are computed by a promotion-grade evaluator.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_prospective_holdout_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Prospective truth-layer JSONL to evaluate.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--cutoff-utc", default=PROSPECTIVE_CUTOFF_UTC.isoformat())
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cutoff = _parse_datetime(args.cutoff_utc)
    if cutoff is None:
        raise ValueError(f"invalid --cutoff-utc: {args.cutoff_utc!r}")
    try:
        summary = evaluate_prospective_holdout(
            input_path=args.input,
            spec_path=args.spec_path,
            cutoff_utc=cutoff,
            max_rows=args.max_rows,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "promotion_verdict": "BLOCKED"}, indent=2, sort_keys=True))
        return 2
    if args.write:
        summary_path, report_path = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(summary_path)
        summary["report_path"] = str(report_path)
    if args.quiet:
        controlled = summary.get("controlled_summary") or {}
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "input_validation": summary.get("input_validation"),
                    "hypotheses": [
                        _hypothesis_summary_row(item)
                        for item in controlled.get("hypotheses", [])
                    ],
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _invalid_reason(validation: Mapping[str, Any]) -> str:
    return (
        "prospective input is invalid: "
        f"rows={validation.get('rows_scanned')}, "
        f"stale_rows_at_or_before_cutoff={validation.get('stale_rows_at_or_before_cutoff')}, "
        f"missing_timestamp_rows={validation.get('missing_timestamp_rows')}, "
        f"duplicate_keys={validation.get('duplicate_keys')}, "
        f"ai_attempted_rows={validation.get('ai_attempted_rows')}, "
        f"ai_call_count_sum={validation.get('ai_call_count_sum')}"
    )


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "prospective_input_valid",
        "rows_scanned",
        "unique_keys",
        "duplicate_keys",
        "missing_timestamp_rows",
        "stale_rows_at_or_before_cutoff",
        "ai_attempted_rows",
        "ai_call_count_sum",
        "min_candle_close_utc",
        "max_candle_close_utc",
        "hypothesis_id",
        "cohort_key",
        "role",
        "matching_setup_rows",
        "population_rows",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "no_entry",
        "valid_year_folds",
        "positive_valid_year_folds",
        "max_year_resolved_share",
        "promotion_verdict",
    )
    keys = list(rows[0].keys())
    columns = [key for key in preferred if key in keys]
    columns.extend(key for key in keys if key not in columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
