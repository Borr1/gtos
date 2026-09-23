#!/usr/bin/env python3
"""Audit the LTO-010 Databento live trigger policy without making data calls."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.databento_live_shadow import (  # noqa: E402
    DEFAULT_BUDGET_LOG_PATH,
    DEFAULT_LOG_PATH,
    evaluate_live_trigger_policy,
    load_budget_rows,
    registered_policy_summary,
)

DEFAULT_TRIGGER_DECISIONS = Path("shadow_logs/databento_live_trigger_decisions.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def build_report(root: Path) -> dict[str, Any]:
    trigger_rows = read_jsonl(root / DEFAULT_TRIGGER_DECISIONS)
    confluence_rows = read_jsonl(root / DEFAULT_LOG_PATH)
    budget_rows = load_budget_rows(root / DEFAULT_BUDGET_LOG_PATH)
    disabled_decision = evaluate_live_trigger_policy(
        symbols=["NAS100"],
        schemas=["trades", "mbp-10"],
        trigger_id="LTO010_POLICY_AUDIT_DISABLED_CHECK",
        reason="policy audit disabled-environment check; no paid fetch",
        estimated_cost_usd=0.0,
        timeout_seconds=60.0,
        max_records=5000,
        env=os.environ,
        budget_rows=budget_rows,
    )
    paid_confluence_rows = [
        row
        for row in confluence_rows
        if row.get("paid_fetch_attempted") is True or float(row.get("paid_data_calls") or 0) > 0
    ]
    return {
        "schema_version": "lto010_databento_live_policy_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "status": "OK_OWNER_APPROVED_VALUE_MAX_POLICY_READY_ENV_GATED",
        "policy": registered_policy_summary(),
        "disabled_environment_policy_decision": disabled_decision,
        "counts": {
            "trigger_decision_rows": len(trigger_rows),
            "confluence_rows": len(confluence_rows),
            "budget_ledger_rows": len(budget_rows),
            "paid_confluence_rows": len(paid_confluence_rows),
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "databento_calls_made_by_audit": 0,
            "paid_data_calls_made_by_audit": 0,
        },
        "trigger_status_counts": counter(trigger_rows, "trigger_status"),
        "confluence_status_counts": counter(confluence_rows, "status"),
        "budget_status_counts": counter(budget_rows, "budget_status"),
        "guardrail": (
            "This audit only inspects local JSONL and evaluates policy in-process. It does not "
            "connect to Databento, call MT5, call AI, run canaries, or place orders. The owner "
            "approval is now recorded for value-max Databento usage; live collection is env/API/"
            "cost-cap gated, not approval-blocked."
        ),
    }


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    c = report["counts"]
    policy = report["policy"]
    lines = [
        "# LTO010 Databento Live Confluence Policy - 2026-05-05",
        "",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Registered Policy",
        "",
        f"- Policy id: `{policy['policy_id']}`",
        f"- Registered symbols/schemas: `{policy['registered_symbol_schemas']}`",
        f"- Max cost per trigger: `${policy['max_cost_per_trigger_usd']:.2f}`",
        f"- Daily spend cap: `${policy['daily_spend_cap_usd']:.2f}`",
        f"- Cooldown seconds: `{policy['cooldown_seconds']}`",
        f"- Max timeout seconds: `{policy['max_timeout_seconds']}`",
        f"- Max records per trigger: `{policy['max_records_per_trigger']}`",
        f"- Owner approval status: `{policy['owner_approval_status']}`",
        "",
        "## Current Rows",
        "",
        f"- Trigger-decision rows: `{c['trigger_decision_rows']}`",
        f"- Live confluence rows: `{c['confluence_rows']}`",
        f"- Budget ledger rows: `{c['budget_ledger_rows']}`",
        f"- Paid confluence rows: `{c['paid_confluence_rows']}`",
        f"- Audit AI/canary/order/Databento calls: `{c['ai_calls']}` / `{c['canary_calls']}` / `{c['order_calls']}` / `{c['databento_calls_made_by_audit']}`",
        "",
        "## Disabled-Environment Check",
        "",
        f"- Decision: `{report['disabled_environment_policy_decision']['decision']}`",
        f"- Trigger status: `{report['disabled_environment_policy_decision']['trigger_status']}`",
        f"- Block reasons: `{report['disabled_environment_policy_decision']['block_reasons']}`",
        "",
        "## Guardrail",
        "",
        report["guardrail"],
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(Path(args.root))
    write_outputs(report, Path(args.output_json), Path(args.output_md))
    print(json.dumps({"status": report["status"], **report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
