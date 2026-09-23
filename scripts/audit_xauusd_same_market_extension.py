#!/usr/bin/env python3
"""Audit LTO-028 XAUUSD same-market extension preregistration status.

This script writes source-status/preregistration evidence only. It does not
open outcomes, replay trades, call AI/canaries/MT5/orders, or use paid data.
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
from src.research_infra.xauusd_same_market_extension import (  # noqa: E402
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SIERRA_INVENTORY_PATH,
    DEFAULT_SOURCE_MAP_PATH,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_report_payload,
    render_markdown,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_EVALUATIONS = Path("shadow_logs/strategy_follow_evaluations.jsonl")
DEFAULT_STATUS_LOG = Path("shadow_logs/xauusd_same_market_extension_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


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
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--source-map", type=Path, default=DEFAULT_SOURCE_MAP_PATH)
    parser.add_argument("--sierra-inventory", type=Path, default=DEFAULT_SIERRA_INVENTORY_PATH)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--evaluations", type=Path, default=DEFAULT_EVALUATIONS)
    parser.add_argument("--status-log", type=Path, default=DEFAULT_STATUS_LOG)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = build_report_payload(
        registry=read_json(args.registry),
        source_map=read_json(args.source_map),
        sierra_inventory=read_json(args.sierra_inventory),
        candidate_rows=read_jsonl_with_lines(args.candidates),
        evaluation_rows=read_jsonl_with_lines(args.evaluations),
        registry_path=args.registry,
        source_map_path=args.source_map,
        sierra_inventory_path=args.sierra_inventory,
        generated_at_utc=generated_at,
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
                "rows_appended": appended,
                "opened_outcome_slices_at_registration": payload["status_row"]["opened_outcome_slices_at_registration"],
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
