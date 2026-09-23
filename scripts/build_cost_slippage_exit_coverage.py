#!/usr/bin/env python3
"""Build cost/slippage/exit accounting coverage report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "cost_slippage_exit_accounting_coverage_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def build_payload(
    *,
    slippage_rows: list[dict[str, Any]],
    time_in_trade_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    entry_rows = [
        row
        for row in slippage_rows
        if row.get("slippage_event_type") in (None, "", "entry")
    ]
    close_rows = [row for row in slippage_rows if row.get("slippage_event_type") == "close"]
    entry_spread_rows = sum(1 for row in entry_rows if row.get("spread_at_request") is not None)
    entry_slippage_rows = sum(1 for row in entry_rows if row.get("slippage_directional") is not None)
    close_slippage_rows = sum(1 for row in close_rows if row.get("slippage_directional") is not None)
    close_commission_rows = sum(1 for row in close_rows if row.get("commission") is not None)
    close_swap_rows = sum(1 for row in close_rows if row.get("swap") is not None)
    close_deal_id_rows = sum(1 for row in close_rows if row.get("mt5_deal_id") is not None)
    close_side_cost_rows = sum(
        1
        for row in lifecycle_rows
        if row.get("actual_r") is not None or row.get("slippage_price") is not None
    ) + close_slippage_rows + close_commission_rows + close_swap_rows
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "coverage": {
            "slippage_rows": len(slippage_rows),
            "entry_slippage_log_rows": len(entry_rows),
            "close_slippage_log_rows": len(close_rows),
            "entry_spread_rows": entry_spread_rows,
            "entry_slippage_rows": entry_slippage_rows,
            "close_slippage_rows": close_slippage_rows,
            "close_commission_rows": close_commission_rows,
            "close_swap_rows": close_swap_rows,
            "close_deal_id_rows": close_deal_id_rows,
            "time_in_trade_rows": len(time_in_trade_rows),
            "pending_lifecycle_rows": len(lifecycle_rows),
            "close_side_cost_rows": close_side_cost_rows,
        },
        "join_plan": [
            "Use slippage.ticket and pending lifecycle trade_state_ticket for entry fill quality.",
            "Use slippage_event_type=close rows for close-side slippage, BE, partial-close, commission/swap, and MT5 deal-id coverage.",
            "Use time-in-trade rows only after a closed broker trade exists; they are exit diagnostics, not live exit changes.",
            "Do not evaluate partial close, trailing, BE, or exit variants as promotion candidates until close-side spread/cost and actual broker-R are present.",
        ],
        "blocker": "Close-side spread/cost is not yet a complete live shadow log; add execution telemetry before exit-policy promotion work.",
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Cost, Slippage, And Exit Accounting Coverage",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Coverage",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in payload["coverage"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Join Plan",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(payload["join_plan"], start=1)],
            "",
            "## Blocker",
            "",
            payload["blocker"],
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slippage-log", default="shadow_logs/slippage.jsonl")
    parser.add_argument("--time-in-trade-log", default="shadow_logs/time_in_trade.jsonl")
    parser.add_argument("--lifecycle-log", default="shadow_logs/pending_limit_lifecycle.jsonl")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        slippage_rows=read_jsonl(Path(args.slippage_log)),
        time_in_trade_rows=read_jsonl(Path(args.time_in_trade_log)),
        lifecycle_rows=read_jsonl(Path(args.lifecycle_log)),
    )
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps(payload["coverage"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
