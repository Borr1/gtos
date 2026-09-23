#!/usr/bin/env python3
"""Audit LTO-027 V2 structural selector promotion-readiness.

This script writes an append-only status row plus a durable report. It is
research/tooling only and makes no AI, canary, MT5, order, or paid-data calls.
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

from src.research_infra.forward_capture import append_jsonl  # noqa: E402
from src.research_infra.v2_structural_selector_readiness import (  # noqa: E402
    DEFAULT_ACCOUNT_HISTORY_EXPORT,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_report_payload,
    render_markdown,
)


DEFAULT_V2B_AUDIT = Path("shadow_logs/v2b_forward_pair_resolution_audit.jsonl")
DEFAULT_V2B_PAIRS = Path("shadow_logs/v2b_forward_pairs.jsonl")
DEFAULT_PENDING_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle_audit.jsonl")
DEFAULT_BROKER_ACTUAL = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_STATUS_LOG = Path("shadow_logs/v2_structural_selector_readiness.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md")


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


def append_status_row_if_missing(row: dict[str, Any], path: Path) -> int:
    row_key = str(row.get("row_key") or "")
    existing = {str(item.get("row_key") or "") for _, item in read_jsonl_with_lines(path)}
    if not row_key or row_key in existing:
        return 0
    append_jsonl(path, row)
    return 1


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2b-audit", type=Path, default=DEFAULT_V2B_AUDIT)
    parser.add_argument("--v2b-pairs", type=Path, default=DEFAULT_V2B_PAIRS)
    parser.add_argument("--pending-lifecycle", type=Path, default=DEFAULT_PENDING_LIFECYCLE)
    parser.add_argument("--broker-actual", type=Path, default=DEFAULT_BROKER_ACTUAL)
    parser.add_argument("--account-history-export", type=Path, default=DEFAULT_ACCOUNT_HISTORY_EXPORT)
    parser.add_argument("--status-log", type=Path, default=DEFAULT_STATUS_LOG)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = build_report_payload(
        root=Path("."),
        generated_at_utc=generated_at,
        v2b_audit_rows=read_jsonl_with_lines(args.v2b_audit),
        v2b_pair_rows=read_jsonl_with_lines(args.v2b_pairs),
        pending_lifecycle_rows=read_jsonl_with_lines(args.pending_lifecycle),
        broker_actual_rows=read_jsonl_with_lines(args.broker_actual),
        account_history_export_path=args.account_history_export,
    )
    appended = append_status_row_if_missing(payload["status_row"], args.status_log)
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "promotion_verdict": PROMOTION_VERDICT,
                "status": payload["status"],
                "readiness_verdict": payload["readiness_verdict"],
                "rows_appended": appended,
                "status_log": str(args.status_log),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
