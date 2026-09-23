#!/usr/bin/env python3
"""Build the LTO-011 NAS100/NQ orderflow diagnostic-readiness report.

This audit is local/read-only except for the append-only LTO-011 status row.
It does not connect to Databento, Sierra, MT5, AI, canaries, or order code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.nas100_orderflow_adverse_selection import (  # noqa: E402
    DEFAULT_STATUS_LOG,
    build_report,
    append_status_row_if_missing,
)

DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return lines


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row = report["status_row"]
    counts = row["current_counts"]
    gates = row["readiness_gates"]
    live = row["databento_live_status"]
    lines = [
        "# LTO011 NAS100/NQ Orderflow Adverse-Selection Readiness - 2026-05-05",
        "",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        f"**Source signature:** `{report['source_dependency_signature']}`",
        "",
        "## Summary",
        "",
        report["synthesis"]["summary"],
        "",
        "## Registered Trigger Criteria",
        "",
        f"- Policy id: `{row['trigger_criteria']['policy_id']}`",
        f"- GTOS symbol: `{row['trigger_criteria']['gtos_symbol']}`",
        f"- Databento dataset/raw symbol: `{row['trigger_criteria']['databento_dataset']}` / `{row['trigger_criteria']['databento_raw_symbol']}`",
        f"- Eligible subjects: `{row['trigger_criteria']['eligible_subjects']}`",
        f"- Default window: `{row['trigger_criteria']['default_window']}`",
        f"- Join keys: `{row['trigger_criteria']['join_keys']}`",
        "",
        "## Counts And Floors",
        "",
        *_table(
            ["Metric", "Current", "Floor"],
            [
                [
                    "NAS100 broker actual-R rows",
                    counts["broker_actual_r_rows_nas100_unique"],
                    row["floors"]["broker_actual_r_rows"],
                ],
                [
                    "All-symbol broker actual-R rows",
                    counts["broker_actual_r_rows_all_symbols_unique"],
                    "context only",
                ],
                [
                    "Cached MBP10 candidate rows",
                    counts["cached_mbp10_candidate_rows"],
                    row["floors"]["mbp10_candidate_rows"],
                ],
                [
                    "Cached MBO candidate rows",
                    counts["cached_mbo_candidate_rows"],
                    "diagnostic only",
                ],
                [
                    "Live MBP10 rows",
                    counts["live_mbp10_candidate_rows"],
                    "waiting",
                ],
                [
                    "Declared NQ Databento requests",
                    counts["declared_nas100_nq_requests"],
                    "registered",
                ],
            ],
        ),
        "",
        "## Live Databento Status",
        "",
        f"- Latest confluence status: `{live['latest_status']}`",
        f"- Latest budget status: `{live['latest_budget_status']}`",
        f"- License blocker: `{live['license_blocker']}`",
        f"- Latest message: `{live['latest_message']}`",
        "",
        "## Readiness Gates",
        "",
        *_table(
            ["Gate", "State"],
            [[name, state] for name, state in gates.items()],
        ),
        "",
        "## Forward Feature Families",
        "",
        *_table(
            ["Family", "Priority", "Fields"],
            [
                [
                    item.get("family"),
                    item.get("priority"),
                    ", ".join(item.get("fields") or []),
                ]
                for item in row["feature_family_forward_plan"]
            ],
        ),
        "",
        "## Boundary",
        "",
        row["boundary"],
        "",
        "## Next Action",
        "",
        report["synthesis"]["next_action"],
        "",
        "## Non-Claims",
        "",
        "- This audit made zero Databento calls.",
        "- This audit made zero AI, canary, MT5 order, or execution calls.",
        "- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.",
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument(
        "--no-append-status",
        action="store_true",
        help="Write report only; do not append the status row.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    report = build_report(root=root)
    appended = False
    if not args.no_append_status:
        appended = append_status_row_if_missing(report["status_row"], root / args.status_log)
    report["status_row_appended"] = appended
    report["status_log"] = args.status_log
    write_outputs(report, Path(args.output_json), Path(args.output_md))
    print(
        json.dumps(
            {
                "status": report["status"],
                "status_row_appended": appended,
                "broker_actual_r_rows_nas100_unique": report["status_row"]["current_counts"][
                    "broker_actual_r_rows_nas100_unique"
                ],
                "cached_mbp10_candidate_rows": report["status_row"]["current_counts"][
                    "cached_mbp10_candidate_rows"
                ],
                "paid_data_calls_made_by_audit": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
