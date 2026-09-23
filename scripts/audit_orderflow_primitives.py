#!/usr/bin/env python3
"""Audit LTO-033 orderflow primitive registry and cached-feature readiness.

This script writes an append-only status row plus a durable report. It reads
local cached artifacts only and makes no paid data, AI, canary, MT5, or order
calls.
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

from src.research_infra.forward_capture import append_jsonl  # noqa: E402
from src.research_infra.orderflow_primitives import (  # noqa: E402
    DEFAULT_CACHED_MBO,
    DEFAULT_CACHED_MBP10,
    DEFAULT_CACHED_TRADES,
    DEFAULT_LTO010,
    DEFAULT_LTO011,
    DEFAULT_LTO012,
    DEFAULT_LTO030,
    DEFAULT_NAS100_FORENSICS,
    PROMOTION_VERDICT,
    build_report_payload,
)

DEFAULT_STATUS_LOG = Path("shadow_logs/orderflow_primitives_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def append_status_row_if_missing(row: dict[str, Any], path: Path) -> int:
    row_key = str(row.get("row_key") or "")
    existing = {str(item.get("row_key") or "") for item in read_jsonl(path)}
    if not row_key or row_key in existing:
        return 0
    append_jsonl(path, row)
    return 1


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    status = payload["status_row"]
    registry = payload["primitive_registry"]
    lines = [
        "# LTO033 Orderflow Primitives - 2026-05-05",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Primitive Registry",
        "",
        *_table(
            ["Primitive", "Lane", "Family", "Schemas", "Status", "Roles"],
            [
                [
                    row["primitive_id"],
                    row["x_lane"],
                    row["family"],
                    ", ".join(row["schemas"]),
                    row["current_status"],
                    ", ".join(row["roles_to_evaluate"]),
                ]
                for row in registry
            ],
        ),
        "",
        "## Field Coverage",
        "",
        *_table(
            ["Primitive", "Coverage", "Missing decision fields", "Blockers"],
            [
                [
                    primitive_id,
                    row["coverage_ratio"],
                    ", ".join(row["missing_decision_fields"]) or "-",
                    ", ".join(row["blocker_codes"]) or "-",
                ]
                for primitive_id, row in status["field_coverage"].items()
            ],
        ),
        "",
        "## Role Matrix",
        "",
        *_table(
            ["Role", "Primitives"],
            [[role, ", ".join(primitives)] for role, primitives in status["roles_evaluated_separately"].items()],
        ),
        "",
        "## No-Lookahead And Cost Policy",
        "",
        f"- No-lookahead check: `{status['no_lookahead_check']['status']}`.",
        f"- Decision fields checked: `{status['no_lookahead_check']['fields_checked']}`.",
        f"- Post-event policy: {status['no_lookahead_check']['post_event_policy']}.",
        f"- Databento trigger cap: `${status['cost_policy']['max_cost_per_trigger_usd']}`.",
        f"- Databento daily cap: `${status['cost_policy']['daily_spend_cap_usd']}`.",
        f"- This audit paid-data calls: `{status['cost_policy']['this_audit_paid_data_calls']}`.",
        "",
        "## Cached Feature Stability",
        "",
        status["cached_feature_stability"]["claim_boundary"],
        "",
        *_table(
            [
                "Feed",
                "Candidate",
                "Context",
                "Actual R",
                "Top date share",
                "Depth sign flips",
                "Thin sign flips",
                "Imbalance sign flips",
            ],
            [
                [
                    feed,
                    row.get("candidate_rows"),
                    row.get("context_rows"),
                    row.get("actual_r_rows"),
                    row.get("top_candidate_date_share"),
                    row.get("event15_total_depth_leave_one_date_sign_flips"),
                    row.get("event15_thin_rate_leave_one_date_sign_flips"),
                    row.get("event15_imbalance_leave_one_date_sign_flips"),
                ]
                for feed, row in (status["cached_feature_stability"].get("feeds") or {}).items()
            ],
        ),
        "",
        "## Source Readiness",
        "",
        f"- Databento live status: `{status['source_readiness']['databento_live']['status']}`.",
        f"- Databento live license blocker: `{status['source_readiness']['databento_live']['license_blocker']}`.",
        f"- Sierra depth status: `{status['source_readiness']['sierra_depth']['status']}`.",
        f"- Sierra 6B/SI policy status: `{status['source_readiness']['sierra_6b_si_policy']['status']}`.",
        "",
        "## Boundary",
        "",
        status["claim_boundary"],
        "",
        "## Next Actions",
        "",
        *[f"- {item}" for item in payload["synthesis"]["next_actions"]],
        "",
        "## Non-Claims",
        "",
        *[f"- {item}" for item in payload["synthesis"]["non_claims"]],
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--cached-trades", default=str(DEFAULT_CACHED_TRADES))
    parser.add_argument("--cached-mbp10", default=str(DEFAULT_CACHED_MBP10))
    parser.add_argument("--cached-mbo", default=str(DEFAULT_CACHED_MBO))
    parser.add_argument("--nas100-forensics", default=str(DEFAULT_NAS100_FORENSICS))
    parser.add_argument("--lto010", default=str(DEFAULT_LTO010))
    parser.add_argument("--lto011", default=str(DEFAULT_LTO011))
    parser.add_argument("--lto012", default=str(DEFAULT_LTO012))
    parser.add_argument("--lto030", default=str(DEFAULT_LTO030))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    payload = build_report_payload(
        root=root,
        cached_trades_path=Path(args.cached_trades),
        cached_mbp10_path=Path(args.cached_mbp10),
        cached_mbo_path=Path(args.cached_mbo),
        nas100_forensics_path=Path(args.nas100_forensics),
        lto010_path=Path(args.lto010),
        lto011_path=Path(args.lto011),
        lto012_path=Path(args.lto012),
        lto030_path=Path(args.lto030),
    )
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    appended = append_status_row_if_missing(payload["status_row"], Path(args.status_log))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "primitive_count": payload["completion_evidence"]["primitive_count"],
                "no_lookahead_pass": payload["completion_evidence"]["no_lookahead_pass"],
                "status_rows_appended": appended,
                "paid_data_calls": 0,
                "output_json": str(output_json),
                "output_md": str(output_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
