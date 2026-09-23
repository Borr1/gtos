#!/usr/bin/env python3
"""Backfill append-only LTO-018 regime/decay outcome join rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.regime_decay_outcome_join import (  # noqa: E402
    ACTION_REQUIRED,
    COMPLETE,
    DECAY_MISSING,
    PROMOTION_VERDICT,
    REGIME_MISSING,
    SCHEMA_VERSION,
    build_regime_decay_outcome_rows,
    build_rolling_status,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_BROKER_AUDIT = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_REGIME = Path("shadow_logs/regime_classifications.jsonl")
DEFAULT_OB_CONTINUATION = Path("shadow_logs/ob_continuation_daily.csv")
DEFAULT_MONTHLY_DECAY_DIR = Path("research/monthly_decay_monitor")
DEFAULT_OUTPUT = Path("shadow_logs/regime_decay_outcome_join.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def read_csv_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for line_no, row in enumerate(reader, start=2):
            rows.append((line_no, dict(row)))
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for _, row in read_jsonl_with_lines(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def latest_monthly_decay_report(path: Path, *, now_utc: datetime) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "MONTHLY_DECAY_REPORT_NOT_FOUND",
            "path": None,
            "mtime_utc": None,
            "age_days": None,
        }
    reports = sorted(path.glob("????-??_report*.md"), key=lambda item: item.stat().st_mtime if item.exists() else 0.0)
    if not reports:
        return {
            "status": "MONTHLY_DECAY_REPORT_NOT_FOUND",
            "path": None,
            "mtime_utc": None,
            "age_days": None,
        }
    latest = reports[-1]
    mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
    age_days = round((now_utc - mtime).total_seconds() / 86400, 3)
    status = "MONTHLY_DECAY_REPORT_PRESENT" if age_days <= 35 else "MONTHLY_DECAY_REPORT_STALE_GT_35D"
    try:
        report_path = str(latest.relative_to(ROOT))
    except ValueError:
        report_path = str(latest)
    return {
        "status": status,
        "path": report_path,
        "mtime_utc": mtime.isoformat(),
        "age_days": age_days,
    }


def latest_ob_continuation_by_scope(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        scope = str(row.get("scope") or "")
        date_utc = str(row.get("date_utc") or "")
        if not scope:
            continue
        prev = latest.get(scope)
        if prev is None or date_utc >= str(prev.get("date_utc") or ""):
            latest[scope] = {
                "date_utc": row.get("date_utc"),
                "window_size": row.get("window_size"),
                "continuation_count": row.get("continuation_count"),
                "total_count": row.get("total_count"),
                "rate_pct": row.get("rate_pct"),
                "alarm_fired": row.get("alarm_fired"),
                "insufficient_sample": row.get("insufficient_sample"),
                "window_start_date": row.get("window_start_date"),
                "window_end_date": row.get("window_end_date"),
            }
    return dict(sorted(latest.items()))


def build_report(
    rows: list[dict[str, Any]],
    appended_rows: list[dict[str, Any]],
    output_path: Path,
    *,
    monthly_decay_report: dict[str, Any],
    ob_rows: list[tuple[int, dict[str, Any]]],
) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    status_counts = Counter(str(row.get("regime_decay_context_status") or "UNKNOWN") for row in rows)
    action_rows = [
        {
            "row_key": row.get("row_key"),
            "row_type": row.get("row_type"),
            "candidate_id": row.get("candidate_id"),
            "fill_id": row.get("fill_id"),
            "symbol": row.get("symbol"),
            "action_required_codes": row.get("action_required_codes") or [],
        }
        for row in rows
        if row.get("regime_decay_context_status") == ACTION_REQUIRED or row.get("action_required_codes")
    ]
    ob_plain = [row for _, row in ob_rows]
    return {
        "schema_version": "lto018_regime_decay_outcome_join_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_rows else "OK_REGIME_DECAY_OUTCOME_JOIN_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "rows_computed": len(rows),
            "status_rows_available": len(read_jsonl_with_lines(output_path)),
            "status_rows_appended_this_run": len(appended_rows),
            "candidate_context_rows": rolling["row_type_counts"].get("candidate_regime_decay_context", 0),
            "filled_context_rows": rolling["row_type_counts"].get("filled_regime_decay_context", 0),
            "complete_joined_rows": status_counts.get(COMPLETE, 0),
            "regime_missing_rows": status_counts.get(REGIME_MISSING, 0),
            "decay_missing_rows": status_counts.get(DECAY_MISSING, 0),
            "regime_joined_rows": rolling["regime_joined_rows"],
            "ob_continuation_joined_rows": rolling["ob_continuation_joined_rows"],
            "actual_r_claim_allowed_rows": rolling["actual_r_claim_allowed_rows"],
            "action_required": len(action_rows),
        },
        "rolling_status": rolling,
        "monthly_decay_report": monthly_decay_report,
        "latest_ob_continuation_by_scope": latest_ob_continuation_by_scope(ob_plain),
        "action_required_examples": action_rows[:25],
        "claim_boundary": (
            "This report joins regime/decay context to candidate and filled outcome rows. "
            "It is analysis/ML substrate only and does not alter prompts, safety gates, risk, execution, or orders."
        ),
        "ml_goal_contribution": (
            "The lane turns regime labels, H4 regime raw features, OB-continuation decay snapshots, "
            "monthly decay report freshness, and account-history label status into K55-ready as-of "
            "feature/provenance/sample-eligibility fields."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    counts = report["counts"]
    rolling = report["rolling_status"]
    lines = [
        "# LTO-018 Regime / Decay Outcome Join - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Rows computed: `{counts['rows_computed']}`",
        f"- Status rows available: `{counts['status_rows_available']}`",
        f"- Status rows appended this run: `{counts['status_rows_appended_this_run']}`",
        f"- Candidate context rows: `{counts['candidate_context_rows']}`",
        f"- Filled context rows: `{counts['filled_context_rows']}`",
        f"- Complete joined rows: `{counts['complete_joined_rows']}`",
        f"- Regime joined rows: `{counts['regime_joined_rows']}`",
        f"- OB-continuation joined rows: `{counts['ob_continuation_joined_rows']}`",
        f"- Actual-R claim allowed rows: `{counts['actual_r_claim_allowed_rows']}`",
        f"- Action required: `{counts['action_required']}`",
        "",
        "## Status Breakdown",
        "",
        f"- Status counts: `{rolling['status_counts']}`",
        f"- Row type counts: `{rolling['row_type_counts']}`",
        f"- Symbol counts: `{rolling['symbol_counts']}`",
        f"- Regime counts: `{rolling['regime_counts']}`",
        f"- ML label eligibility counts: `{rolling['ml_label_eligibility_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        f"- Documented limitations: `{rolling['documented_limitation_code_counts']}`",
        "",
        "## Cadence Mix",
        "",
        f"- Daily regime mix: `{rolling['daily_regime_mix']}`",
        f"- Weekly regime mix: `{rolling['weekly_regime_mix']}`",
        "",
        "## Monthly / OB Decay Sources",
        "",
        f"- Monthly decay report: `{report['monthly_decay_report']}`",
        f"- Latest OB continuation by scope: `{report['latest_ob_continuation_by_scope']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
        "## ML Goal Contribution",
        "",
        report["ml_goal_contribution"],
        "",
        "## Safety Counters",
        "",
        f"- ai_calls: `{report['ai_calls']}`",
        f"- canary_calls: `{report['canary_calls']}`",
        f"- order_calls: `{report['order_calls']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--broker-audit", type=Path, default=DEFAULT_BROKER_AUDIT)
    parser.add_argument("--path-follow", type=Path, default=DEFAULT_PATH_FOLLOW)
    parser.add_argument("--regime-log", type=Path, default=DEFAULT_REGIME)
    parser.add_argument("--ob-continuation", type=Path, default=DEFAULT_OB_CONTINUATION)
    parser.add_argument("--monthly-decay-dir", type=Path, default=DEFAULT_MONTHLY_DECAY_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    now_utc = datetime.now(timezone.utc)
    generated_at = now_utc.isoformat()
    monthly_report = latest_monthly_decay_report(args.monthly_decay_dir, now_utc=now_utc)
    ob_rows = read_csv_rows(args.ob_continuation)
    rows = build_regime_decay_outcome_rows(
        read_jsonl_with_lines(args.candidates),
        broker_rows=read_jsonl_with_lines(args.broker_audit),
        path_rows=read_jsonl_with_lines(args.path_follow),
        regime_rows=read_jsonl_with_lines(args.regime_log),
        ob_rows=ob_rows,
        monthly_decay_report=monthly_report,
        generated_at_utc=generated_at,
    )
    existing = existing_row_keys(args.output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(args.output, appended)

    report = build_report(
        rows,
        appended,
        args.output,
        monthly_decay_report=monthly_report,
        ob_rows=ob_rows,
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows_computed": report["counts"]["rows_computed"],
                "status_rows_appended": len(appended),
                "status_rows_available": report["counts"]["status_rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
