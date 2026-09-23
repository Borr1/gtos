#!/usr/bin/env python3
"""Audit cross-instrument correlation decision capture status."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.cross_instrument_correlation_decision_status import (  # noqa: E402
    SCHEMA_VERSION,
    build_cross_instrument_correlation_decision_report,
    build_cross_instrument_correlation_decision_status,
)


DEFAULT_CONFIG = Path("config/agent_config.yaml")
DEFAULT_DECISION_LOG = Path("shadow_logs/cross_instrument_correlation_decisions.jsonl")
DEFAULT_RUNTIME_HALT = Path("pipeline_state/RESEARCH_RUNTIME_HALT.flag")
DEFAULT_OUTPUT = Path("shadow_logs/cross_instrument_correlation_decision_status.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/CROSS_INSTRUMENT_CORRELATION_DECISION_STATUS_2026-05-18.json")
DEFAULT_REPORT_MD = Path("research/program_control/CROSS_INSTRUMENT_CORRELATION_DECISION_STATUS_2026-05-18.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for row in read_jsonl(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def write_markdown(report: dict[str, Any], path: Path) -> None:
    row = report["status_row"]
    lines = [
        "# Cross-Instrument Correlation Decision Status - 2026-05-18",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Row status:** `{row['status']}`",
        "",
        "## Counts",
        "",
        f"- Decision rows: `{row['decision_rows']}`",
        f"- NONE rows: `{row['none_action_rows']}`",
        f"- RISK_REDUCE_HALF rows: `{row['risk_reduce_half_rows']}`",
        f"- REJECT rows: `{row['reject_rows']}`",
        f"- Action required codes: `{row['action_required_codes']}`",
        f"- Documented limitations: `{row['documented_limitation_codes']}`",
        "",
        "## Capture State",
        "",
        f"- Gate enabled: `{row['cross_instrument_correlation_gate_enabled']}`",
        f"- Logger enabled: `{row['cross_instrument_correlation_decisions_logger_enabled']}`",
        f"- Decision log exists: `{row['decision_log_exists']}`",
        f"- Runtime halt active: `{row['runtime_halt_active']}`",
        f"- Threshold: `{row['config_threshold']}`",
        f"- Min positions: `{row['config_min_positions']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--decision-log", type=Path, default=DEFAULT_DECISION_LOG)
    parser.add_argument("--runtime-halt", type=Path, default=DEFAULT_RUNTIME_HALT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    row = build_cross_instrument_correlation_decision_status(
        config=read_config(args.config),
        decision_rows=read_jsonl(args.decision_log),
        decision_log_path=str(args.decision_log),
        decision_log_exists=args.decision_log.exists(),
        runtime_halt_active=args.runtime_halt.exists(),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    existing = existing_row_keys(args.output)
    appended = [] if row["row_key"] in existing else [row]
    append_jsonl(args.output, appended)

    report = build_cross_instrument_correlation_decision_report(row)
    report["status_rows_appended_this_run"] = len(appended)
    report["status_log_schema"] = SCHEMA_VERSION
    report["status_log_path"] = str(args.output)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": row["status"],
                "decision_rows": row["decision_rows"],
                "status_rows_appended": len(appended),
                "action_required": len(row["action_required_codes"]),
            },
            sort_keys=True,
        )
    )
    return 1 if row["action_required_codes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
