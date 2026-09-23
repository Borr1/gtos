#!/usr/bin/env python3
"""Build Lane 3 execution/telemetry verifier report.

Research/tooling only. This creates read-only diagnostics for O-1/O-8 follow-up
verifiers and classifies operator-only O-3/O-5 tasks.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.execution_telemetry_verifier import build_verification


OUT_JSON = ROOT / "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.json"
OUT_MD = ROOT / "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md"
INDEX_PATH = ROOT / "knowledge_base/index/_trade_index.json"
TRADE_RECORDS_ROOT = ROOT / "knowledge_base/trade_records"
LIVE_EVALUATIONS_ROOT = ROOT / "knowledge_base/live_evaluations"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_payload() -> dict[str, Any]:
    verification = build_verification(
        index_path=INDEX_PATH,
        trade_records_root=TRADE_RECORDS_ROOT,
        live_evaluations_root=LIVE_EVALUATIONS_ROOT,
        max_allowed_index_lag_days=1,
    )
    task_classifications = {
        "O-3": {
            "status": "BLOCKED_WITH_REASON",
            "classification": "Operator-only Task Scheduler setting; cannot be completed from repo without changing the Windows scheduled task.",
            "blocked_by": "CEO/operator must enable 'Wake the computer to run this task' for the watchdog/heartbeat scheduled task, then verify the next active kill-zone wake cycle.",
            "artifact": rel(OUT_MD),
        },
        "O-5": {
            "status": "BLOCKED_WITH_REASON",
            "classification": "Operator/system maintenance; disk cleanup and pagefile changes require OS/admin action outside repo research tooling.",
            "blocked_by": "CEO/operator must perform or approve Windows disk cleanup/pagefile change and then rerun ops checks.",
            "artifact": rel(OUT_MD),
        },
        "O1-INDEX-REBUILD-OR-STALE-VERIFIER": {
            "status": "DONE",
            "classification": "Research-only _trade_index staleness verifier implemented and run.",
            "current_verdict": verification["o1_index_verifier"]["status"],
            "artifact": rel(OUT_MD),
        },
        "O8-LIFECYCLE-COMPLETENESS-VERIFIER": {
            "status": "DONE",
            "classification": "Research-only lifecycle-aware completeness verifier implemented and run over trade_records/live_evaluations.",
            "current_verdict": verification["o8_lifecycle_completeness_verifier"]["status"],
            "artifact": rel(OUT_MD),
        },
    }
    return {
        "schema_version": "lane3_execution_telemetry_verifiers_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "research/tooling only",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "source_files": [
            rel(INDEX_PATH),
            rel(TRADE_RECORDS_ROOT),
            rel(LIVE_EVALUATIONS_ROOT),
            "research/operations/weekend_backlog_ops_triage_2026-05-03.md",
            "research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md",
        ],
        "task_classifications": task_classifications,
        "verification": verification,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(fmt(value).replace("|", "\\|") for value in row) + " |")
    return out


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    tasks = payload["task_classifications"]
    verification = payload["verification"]
    o1 = verification["o1_index_verifier"]
    o8 = verification["o8_lifecycle_completeness_verifier"]
    live = verification["live_evaluation_summary"]
    records = verification["trade_record_summary"]

    lines = [
        "# Lane 3 Execution / Telemetry Verifiers",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Classification",
        "",
        *table(
            ["id", "status", "classification", "current verdict / blocker"],
            [
                [
                    item_id,
                    row["status"],
                    row["classification"],
                    row.get("current_verdict") or row.get("blocked_by") or "",
                ]
                for item_id, row in tasks.items()
            ],
        ),
        "",
        "## O-1 Index Staleness Verifier",
        "",
        *table(
            ["index count", "record count", "index latest", "record latest", "stale days", "status"],
            [
                [
                    o1["index_trade_count"],
                    o1["trade_record_count"],
                    o1["index_latest_date"],
                    o1["trade_record_latest_date"],
                    o1["stale_by_days"],
                    o1["status"],
                ]
            ],
        ),
        "",
        "Interpretation: `_trade_index.json` remains stale versus current `trade_records`; do not use it for current live/OOS counts until rebuilt or consumers migrate to direct trade-record aggregation.",
        "",
        "## O-8 Lifecycle Completeness Verifier",
        "",
        *table(
            ["records", "latest", "status", "incomplete"],
            [[records["record_count"], records["latest_date"], o8["status"], o8["incomplete_count"]]],
        ),
        "",
        "Lifecycle state counts:",
        "",
        *table(["state", "count"], [[key, value] for key, value in o8["state_counts"].items()]),
        "",
        "Missing field counts:",
        "",
        *table(["field", "count"], [[key, value] for key, value in o8["missing_field_counts"].items()]),
        "",
        "Incomplete samples:",
        "",
        *table(
            ["path", "state", "missing"],
            [[row["path"], row["state"], ", ".join(row["missing_fields"])] for row in o8["incomplete_samples"][:10]],
        ),
        "",
        "Live evaluation stream:",
        "",
        *table(
            ["files", "rows", "latest", "decisions"],
            [[live["file_count"], live["row_count"], live["latest_date"], live["decision_counts"]]],
        ),
        "",
        "Interpretation: `trade_records` are still execution/outcome-incomplete for current LIMIT_PLACED rows. Rejected-L2 records can be complete as decision records, but LIMIT_PLACED rows need pending lifecycle and execution truth before actual-R, fill/no-fill, or V3 lifecycle validation can rely on them.",
        "",
        "## Operator-Only Tasks",
        "",
        "- `O-3` remains blocked by operator action: enable the Windows scheduled-task wake setting and verify the next active kill-zone wake cycle.",
        "- `O-5` remains blocked by operator/admin action: disk cleanup and pagefile changes are OS maintenance outside repo research tooling.",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This artifact adds read-only verifiers and operator blockers only. It does not change live trading logic, risk, prompts, or execution behavior.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(OUT_JSON))
    parser.add_argument("--output-md", default=str(OUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload()
    write_json(payload, Path(args.output_json))
    write_markdown(payload, Path(args.output_md))
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "classifications={}".format(
            {key: value["status"] for key, value in payload["task_classifications"].items()}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
